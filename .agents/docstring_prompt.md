Femora agent prompt base

Use this file as the default instruction set before doing component documentation or documentation-adjacent cleanup work.

Read this first, then read the specific component files that are in scope for the current pass, then apply any additional task-specific instructions.

Core intent

- Preserve Femora's current runtime architecture.
- Do not reopen completed manager/model cleanup unless explicitly asked.
- Keep documentation high quality, consistent, and useful for users reading the generated API reference.
- Match the documentation generator and mkdocstrings configuration already used by the project.
- Do not change code logic, names, signatures, imports, or runtime behavior when doing documentation passes unless a tiny doc-correctness fix is explicitly required.

Current Femora architecture assumptions

- The root runtime object is `Model`.
- `Model` lives in `src/femora/core/model.py`.
- Managers are model-owned.
- Runtime ownership is explicit; old singleton/runtime-global patterns have been removed from non-GUI code.
- New examples in component docstrings should use explicit model construction:

```python
from femora.core.model import Model

model = Model()
```

- Do not use:
  - `import femora as fm`
  - `fm.Model()`
  - `MeshMaker`
  - old default-model patterns

Documentation system facts

- The docs generator is `website/gen_ref_pages.py`.
- MkDocs config is in `website/mkdocs.yml`.
- The docs use mkdocstrings with:
  - Google-style docstrings
  - `docstring_section_style: table`
  - `merge_init_into_class: true`
  - `members_order: source`
  - `show_if_no_docstring: false`

- Public class pages can be controlled with `__doc_controls__`.
- `merge_init_into_class: true` means the class page is class-first, with constructor details merged in from `__init__`.
- Package landing pages are built from `__init__.py` module docstrings by `website/gen_ref_pages.py`.

Because of that:

- the class docstring should explain the concept, behavior, and usage context
- the `__init__` docstring should explain construction, arguments, validation, and raised errors
- do not duplicate a full constructor `Args:` section in the class docstring
- package `__init__.py` docstrings should be treated as user-facing package landing-page content

`__doc_controls__` standard

For public component classes, place `__doc_controls__`:

- directly after the class docstring
- before `__init__`

Example:

```python
class ExampleComponent(BaseClass):
    """Short summary.

    Longer explanation.
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, ...):
        ...
```

Default policy:

- `show_docstring_attributes` should be `True`
- `members` should usually be minimal, but still intentionally useful
- for many component classes, a good starting point is:
  - `members: ["__init__"]`
- this is a default starting point, not a hard rule
- if a class has other meaningful user-facing methods, include them deliberately after understanding the code
- do not choose `members` mechanically

Important rule:

- If an attribute is important enough to appear in the rendered docs, its meaning should also be explained clearly in the `__init__` docstring where the user actually provides it.
- Do not rely on the attribute table alone to explain important inputs.
- The attribute table is supplementary; the `__init__` docstring is still the primary place to explain constructor arguments and their meaning.

Do not expose `to_tcl()` in `members` by default just because it exists.
Usually the class docstring already explains the OpenSees/Tcl form, so surfacing `to_tcl()` is unnecessary unless there is a specific reason.

Docstring style standard

Use Google-style docstrings consistently.

Use these section labels exactly:

- `Args:`
- `Returns:`
- `Raises:`
- `Attributes:`
- `Note:`
- `Warning:`
- `Tip:`
- `Example:`
- `Tcl form:`

Do not invent alternatives such as:

- `Parameters:`
- `Inputs:`
- `Usage:`
- `Example Usage:`
- `Exceptions:`

For public component classes, use this section order:

1. one-line summary
2. short explanatory paragraph
3. `Tcl form:`
4. optional advisory sections in this order when needed:
   - `Warning:`
   - `Note:`
   - `Tip:`
5. optional `Example:`

Do not add filler sections.

Class docstring responsibilities

The class docstring should explain:

- what the class represents
- what it does
- when it should be used
- conceptual context when that helps understanding
- Tcl form when relevant
- required usage example

Do not put in the class docstring:

- a full duplicated constructor `Args:` section
- repetitive constructor validation details that belong in `__init__`

Class docstring guidance

- The summary should say what the component is.
- The explanatory paragraph should say what it represents, when it is used, and any important domain context.
- `OpenSees form:` or `Tcl form:` should reflect the actual exported command shape.
- Use the advisory sections only when they add real value.

Advisory keyword discipline

- `Example:` only for a real usage example.
- `Note:` only for one important point.
- `Warning:` only for real misuse risk, invalid assumptions, or behavior that can surprise users.
- `Tip:` only for practical usage guidance.

Do not sprinkle these headings mechanically.

If multiple advisory sections are needed in the same docstring, keep them in this order:

1. `Warning:`
2. `Note:`
3. `Tip:`
4. `Example:`

`Example:` should generally be last.

Use `Note:` only, not `Notes:`.
If multiple note points are needed, keep them as bullets under a single `Note:` section.

`Attributes:` guidance

- `Attributes:` is optional in the class docstring.
- Include it only when the class exposes important user-facing runtime state that adds real value on the rendered API page.
- Do not use `Attributes:` for internal implementation details such as `_owner`, compatibility registries, or other non-user-facing fields.
- If `Attributes:` is included, `show_docstring_attributes` should remain `True`.

`__init__` docstring standard

Use:

- one-line summary
- `Args:`
- `Raises:`

Do not just restate parameter names.

Explain parameter meaning where needed, especially for:

- physical inputs
- numerical parameters
- tags or references to other managed objects
- units or sign conventions
- assumptions or valid ranges when they matter

If a constructor argument becomes an important stored attribute, document it meaningfully in `Args:` as well. Do not assume the class-level attribute rendering is enough.

Do not add `Returns:` to `__init__`.

Other public method docstrings

Document public methods when they are meaningful to users.

Every method in scope for a documentation pass should have a complete docstring, whether public or private, unless the current task explicitly limits the scope further.

Method section order:

1. summary line
2. short explanation if behavior is not obvious
3. `Args:` if needed
4. `Returns:` if needed
5. `Raises:` if needed
6. `Example:` if useful

For `to_tcl()`:

- keep the docstring short
- explain what it returns
- include `Raises:` if there is a real managed/unmanaged/tag-related failure mode

Naming and quality bar

- Prefer accurate architectural language:
  - `Model`
  - `Model-owned`
  - `material`, `section`, `pattern`, `time series`, etc.

- Avoid stale wording:
  - `Model`
  - `OpenSeesGUI`
  - old singleton assumptions

- Do not write shallow docstrings that only mirror code identifiers.
- If an argument is important, explain what it means physically, numerically, or structurally.
- If a component has important constraints, compatibility rules, or assumptions, say that clearly.
- Before writing or rewriting a docstring, understand the code well enough to describe:
  - what the component actually does
  - what it depends on
  - what its inputs really mean
  - what behavior or constraints matter to users

Do not write docstrings by pattern-matching names alone.

Examples standard

Examples should:

- be small
- be valid in the current architecture
- use explicit `Model()`
- focus on the component being documented

Prefer:

```python
from femora.core.model import Model

model = Model()
mat = model.material.nd.elastic_isotropic(
    user_name="soil",
    e_mod=30000.0,
    nu=0.3,
    rho=2.0,
)
```

Avoid examples that depend on removed runtime surfaces.
Avoid `import femora as fm` and `fm.Model()` in new docstrings.

Example rules

- Every public component class should include at least one example.
- Method examples are optional.
- Always use fenced `python` code blocks.
- Never use REPL-style `>>>`.
- Keep examples short, realistic, and aligned with the actual current API.
- Verify the real manager or sub-manager path from the implementation before writing the example. Do not guess.
- Direct class construction is acceptable only when the class is intentionally low-level or direct construction is the actual point of the example.

Cross-references

- When linking to documented classes or methods inside docstrings, use MkDocs/autorefs Markdown reference format:
  - `[Label][full.python.path]`
  - `[full.python.path][]`
- Do not use Sphinx roles such as `:class:` or `:meth:`.

Scope rules for documentation passes

- Keep the component family the same for a given pass unless explicitly asked to broaden scope.
- Preserve the package/folder identity of the component family being edited.
- Example: if the task is about `material`, keep the pass focused on `src/femora/components/material/**`.

- Do not drift into unrelated architecture work.
- Do not change runtime behavior unless a tiny doc-related correctness fix is unavoidable.
- Do not touch GUI files unless explicitly asked.
- For runtime classes, document runtime behavior only. Do not describe GUI forms, widgets, editor flows, or legacy GUI behavior unless the file itself is explicitly GUI-related.

Package `__init__.py` docstring standard

Package `__init__.py` files are part of the generated docs surface.

Their top-level module docstring should be concise, package-oriented, and written for the package landing page.

Use this structure when a package is in scope:

1. one-line summary
2. short explanatory paragraph
3. normal manager entry path paragraph
4. optional short bullet list describing subpackages or major contents

Package `__init__.py` docstrings should:

- explain what the package contains
- explain how it is normally accessed from `Model`
- mention important subpackages or groupings when useful
- use current architecture terminology
- stay at the package or family level first, not at the level of a single current implementation
- remain reasonably future-proof if more components are added later
- avoid duplicating class inventories that are already generated automatically by the docs system

Package `__init__.py` docstrings should not use:

- `Args:`
- `Returns:`
- `Raises:`
- `Tcl form:`
- `Example:`
- `__doc_controls__`

Example package style:

```python
"""Material component package for Femora.

This package contains runtime material component classes that are registered
through Femora's material managers and exported to OpenSees Tcl.

Normal runtime usage should go through `Model` manager entry points such as
`model.material.nd.*` and `model.material.uniaxial.*`. Direct imports from this
package are mainly useful for typed references, tests, and low-level component
work.

This package includes:
- nD material components
- uniaxial material components
"""
```

Package `__init__.py` quality rules

- Do not overfit the package landing page to the currently implemented classes if the package represents a broader family.
- Prefer category-level wording such as:
  - what kind of components live here
  - what modeling role they serve
  - what the normal manager path is
- If you mention concrete classes, do it sparingly and only when it improves orientation.
- Keep package docstrings concise; they should orient the reader, not duplicate every class page.
- Do not add manual “This package includes:” or similar class inventory blocks when the generated page already lists classes automatically.

When doing a component-family pass

1. Read this file.
2. Read `website/gen_ref_pages.py`.
3. Read `website/mkdocs.yml`.
4. Read the component files in scope carefully enough to understand how they work.
5. Identify the strongest existing examples in that family and align weaker files to that standard.
6. Standardize:
   - package `__init__.py` docstrings when they are in scope
   - class docstrings
   - `__doc_controls__` placement
   - `__doc_controls__` values
   - `__init__` docstrings
   - all method docstrings in scope, including private methods where the pass covers them
7. Preserve behavior.

Preferred output summary from the agent

After the pass, report:

- which files/classes were updated
- what standard was applied
- whether any files were already close to the target style
- whether any docstrings were intentionally left minimal and why

How to use this prompt in later tasks

For later component-specific tasks, give instructions like:

- "Read `prompt.txt` first."
- "Then do the documentation standardization pass for `src/femora/components/material/**`."
- "Do not broaden beyond that family."

This file is the base style/architecture contract. Component-specific task prompts should add scope and any family-specific nuances, but should not redefine the general style unless explicitly intended.

