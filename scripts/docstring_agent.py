import os
from dataclasses import dataclass
from google import genai
import yaml

@dataclass
class Config:
    STYLE_GUIDE_PATH: str = ".github/DOCSTRING_STYLE.md"
    TARGETS_PATH: str = ".github/docstring_targets.yml"
    EXTENSIONS: tuple = (".py",)
    BATCH_SIZE: int = int(os.getenv("DOCSTRING_BATCH_SIZE", "3"))

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_targets(path: str) -> dict:
    """Load the YAML target manifest."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("Target manifest must be a YAML mapping.")
    targets = data.get("targets", [])
    if targets is None:
        targets = []
    if not isinstance(targets, list):
        raise ValueError("The 'targets' entry must be a list.")
    data["targets"] = targets
    return data


def save_targets(path: str, data: dict) -> None:
    """Write the YAML target manifest back to disk."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def normalize_target(entry: dict) -> tuple[str, str]:
    """Return the file path and optional prompt for one target entry."""
    if not isinstance(entry, dict):
        raise ValueError("Each target entry must be a YAML mapping.")
    path = entry.get("path")
    prompt = entry.get("prompt", "")
    if not isinstance(path, str) or not path.strip():
        raise ValueError("Each target entry must include a non-empty 'path'.")
    if prompt is None:
        prompt = ""
    if not isinstance(prompt, str):
        raise ValueError("Target 'prompt' must be a string when provided.")
    return path.strip(), prompt.strip()


def append_github_output(name: str, value: str) -> None:
    """Append one output entry to the GitHub Actions output file."""
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as f:
        if "\n" in value:
            f.write(f"{name}<<EOF\n{value}\nEOF\n")
        else:
            f.write(f"{name}={value}\n")

def main():
    append_github_output("refactored_count", "0")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Skipping: GEMINI_API_KEY not found.")
        return

    client = genai.Client(api_key=api_key)
    
    # 1. Load Context
    try:
        style_guide = read_file(Config.STYLE_GUIDE_PATH)
    except FileNotFoundError:
        print(f"Error: {Config.STYLE_GUIDE_PATH} not found.")
        return

    try:
        targets_data = load_targets(Config.TARGETS_PATH)
    except FileNotFoundError:
        print(f"Error: {Config.TARGETS_PATH} not found.")
        return
    except Exception as e:
        print(f"Error loading target manifest: {e}")
        return

    if not targets_data["targets"]:
        print("No docstring targets are queued.")
        return

    batch_size = max(1, Config.BATCH_SIZE)
    queued_targets = targets_data["targets"][:batch_size]
    processed_files: list[str] = []

    for index, target_entry in enumerate(queued_targets):
        try:
            target_file, target_prompt = normalize_target(target_entry)
        except Exception as e:
            print(f"Error in target entry {index + 1}: {e}")
            break

        if not os.path.exists(target_file):
            print(f"Error: target file does not exist: {target_file}")
            break

        print(f"Refactoring docstrings for: {target_file}")
        original_code = read_file(target_file)

        extra_prompt_block = ""
        if target_prompt:
            extra_prompt_block = f"""

    Additional file-specific instructions:
    {target_prompt}
    """

        prompt = f"""
    You are editing docstrings for the Femora project.

    Follow the DOCSTRING_STYLE guide below exactly.

    Task:
    - Review the entire file first.
    - Read related project files when needed to understand managers, base classes, or usage patterns before editing.
    - Only change docstrings.
    - Do not change logic, imports, signatures, names, or behavior.
    - Rewrite inconsistent docstrings to match the Femora docstring standard.
    - Add missing docstrings for all classes and all methods.
    - Every method docstring must be complete, whether the method is public or private.
    - Keep class docstrings focused on concept, behavior, Tcl form, notes, attributes when needed, and required examples.
    - Keep __init__ docstrings focused on Args and Raises.
    - Because MkDocs merges __init__ into the class page, do not duplicate Args in the class docstring.
    - Never use >>> in examples.
    - Every class must include at least one example.
    - Method examples are optional.
    - If examples are included, use fenced python blocks.
    - If examples are included for normal Femora usage, prefer:
      from femora.core.model import Model
      model = Model()
      and manager-based creation such as model.pattern..., model.time_series..., model.material..., or other appropriate managers.
    - Return ONLY the full valid Python code. No markdown fences.
    {extra_prompt_block}

    DOCSTRING_STYLE:
    {style_guide}

    TARGET CODE:
    {original_code}
    """

        models_to_try = [
            'gemini-2.5-flash',
            'gemini-2.0-flash',
            'gemini-flash-latest',
            'gemini-2.5-pro',
            'gemini-2.0-flash-001'
        ]

        new_code = None

        for model_name in models_to_try:
            print(f"Trying model: {model_name}...")
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                new_code = response.text
                print(f"Success with {model_name}!")
                break
            except Exception as e:
                print(f"Failed with {model_name}: {e}")

        if not new_code:
            print("ALL models failed.")
            print("DEBUG: Listing available models for this API Key:")
            try:
                for m in client.models.list():
                    try:
                        name = getattr(m, 'name', 'Unknown')
                        disp = getattr(m, 'display_name', '')
                        print(f" - {name} ({disp})")
                    except:
                        print(f" - {m}")
            except Exception as e2:
                print(f"Error listing models: {e2}")
            break

        if new_code.startswith("```python"):
            lines = new_code.splitlines()
            if lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            new_code = "\n".join(lines)
        elif new_code.startswith("```"):
            lines = new_code.splitlines()
            new_code = "\n".join(lines[1:-1])

        with open(target_file, "w", encoding="utf-8") as f:
            f.write(new_code)

        processed_files.append(target_file)
        print(f"Successfully updated docstrings for {target_file}")

    if not processed_files:
        return

    targets_data["targets"] = targets_data["targets"][len(processed_files):]
    save_targets(Config.TARGETS_PATH, targets_data)

    append_github_output("refactored_count", str(len(processed_files)))
    append_github_output("refactored_summary", ", ".join(processed_files))
    append_github_output("refactored_files", "\n".join(processed_files))

if __name__ == "__main__":
    main()

