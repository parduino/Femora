import os
import subprocess
from dataclasses import dataclass

import yaml


@dataclass
class Config:
    STYLE_GUIDE_PATH: str = "STYLE_GUIDE.md"
    TARGETS_PATH: str = ".github/docstring_targets_copilot.yml"
    MODEL_ENV_NAME: str = "COPILOT_MODEL"
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


def build_prompt(style_guide: str, target_file: str, original_code: str, target_prompt: str) -> str:
    extra_prompt_block = ""
    if target_prompt:
        extra_prompt_block = f"""

Additional file-specific instructions:
{target_prompt}
"""

    return f"""
You are editing docstrings for the Femora project.

Follow the STYLE_GUIDE below exactly.

Task:
- Review the entire target file first.
- Read related project files when needed to understand managers, base classes,
  or usage patterns before editing.
- Only change docstrings in the target file.
- Do not change logic, imports, signatures, names, or behavior.
- Rewrite inconsistent docstrings to match the Femora docstring standard.
- Add missing docstrings for all classes and all methods.
- Every method docstring must be complete, whether the method is public or private.
- Keep class docstrings focused on concept, behavior, Tcl form, notes,
  attributes when useful, and required examples.
- Keep __init__ docstrings focused on Args and Raises.
- Because MkDocs merges __init__ into the class page, do not duplicate Args in
  the class docstring.
- Never use >>>.
- Every class must include at least one example.
- Method examples are optional.
- If examples are included, use fenced python blocks.
- If examples are included for normal Femora usage, prefer:
  from femora.core.model import Model
  model = Model()
  and manager-based creation such as model.pattern..., model.time_series...,
  model.material..., or other appropriate managers.
- Return ONLY the final valid Python code for this one file. No markdown fences.
- The target file path is: {target_file}
{extra_prompt_block}

STYLE_GUIDE:
{style_guide}

TARGET CODE:
{original_code}
""".strip()


def run_copilot(prompt: str) -> str:
    """Run Copilot CLI in programmatic mode and return its response."""
    env = os.environ.copy()
    cmd = ["copilot", "-s", "--allow-all", "--no-ask-user"]

    model = env.get(Config.MODEL_ENV_NAME, "").strip()
    if model:
        cmd.extend(["--model", model])

    result = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Copilot CLI failed with exit code {result.returncode}: {stderr}")
    return result.stdout


def clean_response(text: str) -> str:
    """Remove markdown fences if the model returned them."""
    text = text.strip()
    if text.startswith("```python"):
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip() + "\n"
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip() + "\n"
    return text + ("\n" if not text.endswith("\n") else "")


def main():
    append_github_output("refactored_count", "0")
    token = os.getenv("COPILOT_GITHUB_TOKEN")
    if not token:
        print("Skipping: COPILOT_GITHUB_TOKEN not found.")
        return

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
        print("No Copilot docstring targets are queued.")
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

        print(f"Refactoring docstrings with Copilot for: {target_file}")
        original_code = read_file(target_file)
        prompt = build_prompt(style_guide, target_file, original_code, target_prompt)

        try:
            new_code = clean_response(run_copilot(prompt))
        except Exception as e:
            print(str(e))
            break

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

