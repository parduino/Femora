"""Generate the code reference pages and navigation."""

from __future__ import annotations

import ast
from pathlib import Path

import mkdocs_gen_files

# Folders to completely hide from the generated API docs.
SKIP_FOLDERS = {"gui", "constants", "constant", "styles", "utils"}

# Modules to skip (legacy shims without valid imports — break mkdocstrings if scanned).
SKIP_MODULE_NAMES = {"materialsOpenSees"}

nav = mkdocs_gen_files.Nav()

script_dir = Path(__file__).parent
src_root = (script_dir.parent / "src").resolve()
TOP_LEVEL_LABELS = {
    "components": "🧩 components",
    "core": "⚙ core",
    "tools": "🛠 tools",
}
def display_parts(parts: tuple[str, ...]) -> tuple[str, ...]:
    """Return navigation parts with the top-level ``femora`` package collapsed."""
    if parts and parts[0] == "femora":
        parts = parts[1:]
    if not parts:
        return parts
    head = TOP_LEVEL_LABELS.get(parts[0], parts[0])
    return (head,) + parts[1:]


def doc_parts(parts: tuple[str, ...]) -> tuple[str, ...]:
    """Return filesystem doc parts with the top-level ``femora`` package collapsed."""
    if parts and parts[0] == "femora":
        return parts[1:]
    return parts


def should_skip(parts: tuple[str, ...]) -> bool:
    """Return True when a module path should not appear in the docs."""
    if parts and parts[-1] in SKIP_MODULE_NAMES:
        return True
    if set(parts).intersection(SKIP_FOLDERS):
        return True
    if any(part.startswith("_") for part in parts if part != "__init__"):
        return True
    if parts[-1] == "__main__":
        return True
    return "gui" in parts[-1].lower()


def parse_public_classes(path: Path) -> list[tuple[str, dict]]:
    """Return top-level public class names and doc controls from a module."""
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception as exc:
        print(f"WARNING: Could not parse {path}: {exc}")
        return []

    classes: list[tuple[str, dict]] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            doc_controls: dict = {}
            for class_node in node.body:
                if not isinstance(class_node, ast.Assign):
                    continue
                for target in class_node.targets:
                    if isinstance(target, ast.Name) and target.id == "__doc_controls__":
                        try:
                            doc_controls = ast.literal_eval(class_node.value)
                        except Exception as exc:
                            print(
                                f"WARNING: Could not parse __doc_controls__ "
                                f"for {path}:{node.name}: {exc}",
                            )
                            doc_controls = {}
                        break
            classes.append((node.name, doc_controls))
    return classes


def parse_module_docstring(path: Path) -> str:
    """Return the top-level module docstring, or an empty string."""
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception as exc:
        print(f"WARNING: Could not parse docstring from {path}: {exc}")
        return ""
    return ast.get_docstring(tree) or ""


def write_package_index(
    doc_path: Path,
    ident: str,
    title: str,
    description: str,
    class_links: list[tuple[str, str]],
    edit_path: Path,
) -> None:
    """Write a minimal package landing page with links to class pages."""
    with mkdocs_gen_files.open(doc_path, "w") as fd:
        fd.write(f"# {title}\n\n")
        if description:
            fd.write(f"{description}\n\n")
        if class_links:
            fd.write("Classes in this package:\n\n")
            for class_name, href in class_links:
                fd.write(f"- [{class_name}]({href})\n")
    mkdocs_gen_files.set_edit_path(doc_path, edit_path)


def write_class_page(doc_path: Path, ident: str, edit_path: Path, doc_controls: dict | None = None) -> None:
    """Write one page for an individual public class."""
    with mkdocs_gen_files.open(doc_path, "w") as fd:
        fd.write(f"::: {ident}\n")
        if doc_controls:
            fd.write("    options:\n")
            for key, value in doc_controls.items():
                if isinstance(value, bool):
                    rendered = "true" if value else "false"
                    fd.write(f"      {key}: {rendered}\n")
                elif isinstance(value, list):
                    fd.write(f"      {key}:\n")
                    for item in value:
                        fd.write(f"        - {item}\n")
                else:
                    fd.write(f"      {key}: {value}\n")
    mkdocs_gen_files.set_edit_path(doc_path, edit_path)


files = sorted(src_root.rglob("*.py"))
print(f"DEBUG: Found {len(files)} python files in {src_root}")

package_infos: list[tuple[tuple[str, ...], Path, str]] = []
package_classes: dict[tuple[str, ...], list[str]] = {}

for path in files:
    module_path = path.relative_to(src_root).with_suffix("")
    parts = tuple(module_path.parts)

    if should_skip(parts):
        continue

    if parts[-1] == "__init__":
        nav_parts = parts[:-1]
        if not nav_parts:
            continue
        if nav_parts == ("femora",):
            continue
        package_infos.append((nav_parts, path, parse_module_docstring(path)))
        continue

    class_entries = parse_public_classes(path)

    # Keep the older class-page style, but flatten the navigation so packages
    # list classes directly instead of showing a file name before the class.
    if class_entries:
        package_classes.setdefault(parts[:-1], []).extend(
            class_name for class_name, _ in class_entries
        )
        for class_name, doc_controls in class_entries:
            class_doc_path = Path("reference", *doc_parts(parts[:-1]), class_name, "index.md")
            nav[display_parts(parts[:-1]) + (class_name,)] = class_doc_path.relative_to("reference").as_posix()
            write_class_page(class_doc_path, ".".join(parts) + "." + class_name, path, doc_controls)
    else:
        doc_path = Path("reference", *doc_parts(parts)).with_suffix(".md")
        nav[display_parts(parts)] = doc_path.relative_to("reference").as_posix()
        with mkdocs_gen_files.open(doc_path, "w") as fd:
            fd.write(f"::: {'.'.join(parts)}")
        mkdocs_gen_files.set_edit_path(doc_path, path)

for nav_parts, path, description in package_infos:
    doc_path = Path("reference", *doc_parts(nav_parts), "index.md")
    nav[display_parts(nav_parts)] = doc_path.relative_to("reference").as_posix()
    class_links = [
        (class_name, f"{class_name}/")
        for class_name in package_classes.get(nav_parts, [])
    ]
    write_package_index(
        doc_path=doc_path,
        ident=".".join(nav_parts),
        title=nav_parts[-1],
        description=description,
        class_links=class_links,
        edit_path=path,
    )

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.write("- [Overview](index.md)\n")
    nav_file.writelines(nav.build_literate_nav())
