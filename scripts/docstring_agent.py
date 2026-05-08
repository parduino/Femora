import os
from dataclasses import dataclass
from google import genai
import yaml

@dataclass
class Config:
    STYLE_GUIDE_PATH: str = "STYLE_GUIDE.md"
    TARGETS_PATH: str = ".github/docstring_targets.yml"
    EXTENSIONS: tuple = (".py",)

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

def main():
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

    # 2. Pick the First Explicit Target
    try:
        target_file, target_prompt = normalize_target(targets_data["targets"][0])
    except Exception as e:
        print(f"Error in first target entry: {e}")
        return

    if not os.path.exists(target_file):
        print(f"Error: target file does not exist: {target_file}")
        return

    print(f"Refactoring docstrings for: {target_file}")
    
    original_code = read_file(target_file)
    
    # 3. Prompt Engineering
    extra_prompt_block = ""
    if target_prompt:
        extra_prompt_block = f"""

    Additional file-specific instructions:
    {target_prompt}
    """

    prompt = f"""
    You are editing docstrings for the Femora project.

    Follow the STYLE_GUIDE below exactly.

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
      import femora as fm
      model = fm.MeshMaker()
      and manager-based creation such as model.pattern..., model.timeSeries..., model.material..., or other appropriate managers.
    - Return ONLY the full valid Python code. No markdown fences.
    {extra_prompt_block}

    STYLE_GUIDE:
    {style_guide}

    TARGET CODE:
    {original_code}
    """

    # 4. Agent Execution with Retry Logic
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
                # Safely inspect the model object
                try:
                    name = getattr(m, 'name', 'Unknown')
                    disp = getattr(m, 'display_name', '')
                    print(f" - {name} ({disp})")
                except:
                    print(f" - {m}")
        except Exception as e2:
            print(f"Error listing models: {e2}")
        return
    
    # Clean possible markdown fences
    if new_code.startswith("```python"):
        lines = new_code.splitlines()
        # Remove first line (```python) and last line (```)
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        new_code = "\n".join(lines)
    elif new_code.startswith("```"):
         lines = new_code.splitlines()
         new_code = "\n".join(lines[1:-1])

        
    # 5. Save Changes
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(new_code)

    # Remove the completed target from the queue.
    targets_data["targets"].pop(0)
    save_targets(Config.TARGETS_PATH, targets_data)
    
    print(f"Successfully updated docstrings for {target_file}")

    # Set output for GitHub Action
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"refactored_file={target_file}\n")

if __name__ == "__main__":
    main()
