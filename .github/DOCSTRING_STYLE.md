# Femora Docstring Standard

This file is the single source of truth for docstrings in `src/femora`.

The goal is a strict, repeatable Femora docstring format that:

- renders cleanly in MkDocs
- stays consistent across different AI tools
- matches real Femora usage patterns

---

## 1. Rendering Model

Femora API docs are rendered with `mkdocstrings` and
`merge_init_into_class: true`.

This means:

- the class page is class-first
- the main explanation should come from the class docstring
- constructor parameters should come from the `__init__` docstring
- examples written in the class docstring will appear on the class page

Because of this, class docstrings and `__init__` docstrings must have different
responsibilities.

---

## 2. Core Rules

These rules apply to all Femora Python files.

1. Every class should have a complete docstring.
2. Every method should have a complete docstring, whether it is public or
   private.
3. Do not change code logic, names, signatures, imports, or behavior when
   editing docstrings.
4. Keep wording factual, technical, and concise.
5. Explain the concept of a class or method when that explanation is necessary
   to understand what it represents or does.
6. Do not use REPL style `>>>`.
7. If an example is included, it must use fenced `python` code blocks.
8. If an example is included for normal Femora usage, prefer manager-based
   creation through:

   ```python
   from femora.core.model import Model

   model = Model()
   ```

9. If type hints already exist in the signature, do not repeat types in
   parentheses in `Args`.
10. Use the section labels in this file exactly.
11. An AI should read related project files for context before writing
    docstrings, especially the relevant manager, base classes, and nearby
    components, and should understand that context before editing.
12. When linking to documented classes or methods inside docstrings, use the
    MkDocs/autorefs Markdown reference format:

    ```text
    [Label][full.python.path]
    ```

    or

    ```text
    [full.python.path][]
    ```

    Do not use Sphinx-style roles such as `:class:` or `:meth:`.

---

## 3. Class vs. Constructor Responsibilities

### Class docstring documents:

- what the class represents
- what it does
- when it should be used
- conceptual context when needed
- Tcl/OpenSees form if relevant
- required examples
- user-facing attributes if useful

### `__init__` docstring documents:

- how to create the object
- constructor arguments
- constructor validation and raised errors

### Do not put in the class docstring:

- a duplicate full `Args:` section that belongs in `__init__`
- repetitive constructor validation details

### Do not put in `__init__`:

- long conceptual explanation that belongs to the class
- `Returns:`
- example-heavy usage guidance unless there is a special reason

---

## 4. Required Class Docstring Format

Every class docstring should use this structure and order:

1. Summary line
2. Short description paragraph
3. `Tcl form:` if applicable
4. `Note:` if needed
5. `Tip:` if needed
5. `Attributes:` only if they add real user-facing value
6. `Example:` required for classes

### Class template

```python
class SomeComponent:
    """One-line summary.

    Short paragraph describing what the component represents, what it does, and
    when it should be used.

    Tcl form:
        ``command Name <arg1> <arg2> ...``

    Note:
        - Add only meaningful user-facing or developer-facing notes here.
        - If there are multiple notes, write each one as its own bullet.
        - Start note bullets with `-`.

    Tip:
        - Add only when the code or runtime behavior suggests a practical
          usage tip, caveat, or modeling shortcut.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        component = model.some_manager.some_factory(...)
        print(component.tag)

        If the class has an especially useful method or a natural follow-up use,
        the example may continue to show that method in action.
        ```
    """
```

### Class rules

- The summary line must be a single sentence.
- The description should usually be one short paragraph.
- `Tcl form:` is required for classes that directly emit Tcl commands or Tcl
  blocks.
- `Note:` is optional.
- `Tip:` is optional.
- Skip `Attributes:` by default.
- Only include `Attributes:` when the class exposes important public runtime
  state that is not already obvious from the constructor or methods.
- Do not use `Attributes:` for internal implementation details such as
  `_owner`, compatibility dictionaries, or other non-user-facing fields.
- Add `Note:` or `Tip:` only when they communicate something meaningful that is
  not already obvious from the summary, constructor, or method docs.
- If the implementation has important corner cases, limitations, geometry
  assumptions, unmanaged-state behavior, or modeling caveats, document them in
  `Note:` or `Tip:` instead of forcing a generic paragraph.
- Every class must include at least one example.
- Prefer manager-based creation through `model = Model()` when that is
  the normal API.

---

## 5. Required `__init__` Docstring Format

Every constructor docstring should use this structure and order:

1. Summary line
2. `Args:` if the constructor has parameters
3. `Raises:` if the constructor validates and raises
4. `Note:` if truly needed

### Constructor template

```python
def __init__(self, a: int, b: float = 1.0):
    """Create a component with validated inputs.

    Args:
        a: Description of the first argument.
        b: Optional description of the second argument.

    Raises:
        ValueError: If the provided values are invalid.

    """
```

### Constructor rules

- Use `Args:` for constructor parameters.
- Use `Raises:` only when the constructor actually raises.
- Do not add `Returns:` to `__init__`.
- Keep conceptual explanation in the class docstring, not `__init__`.

---

## 6. Method Docstring Format

Every method docstring should be complete, whether the method is public or
private.

Use this order:

1. Summary line
2. Short explanation if the behavior is not obvious
3. `Args:` if needed
4. `Returns:` if needed
5. `Raises:` if needed
6. `Example:` if useful

### Method template

```python
def to_tcl(self) -> str:
    """Render this component as an OpenSees Tcl command.

    Returns:
        Tcl command string for this component.
    """
```

### Method rules

- Every method should have a complete docstring.
- "Complete" means the docstring should document behavior, inputs, outputs, and
  raised errors as needed for that method.
- Do not add empty sections only to satisfy a template.
- When `Returns:` is included, prefer starting the description with the return
  type when that improves clarity, for example `str: ...`.
- `Raises:` should document only errors that the current implementation can
  actually raise. Do not guess or invent exceptions.
- `Example:` are optional for methods.
- If a method example is included and the method belongs to a manager-driven
  Femora workflow, prefer calling it through `model = Model()` and the
  appropriate manager path when practical.

---

## 7. Example Policy

Class examples are required. Method examples are optional. When examples are
included, they must follow a unified format.

### Required example format

- Always use fenced code blocks:

```python
from femora.core.model import Model

model = Model()
```

- Use `model` as the Model variable name.
- Prefer `from femora.core.model import Model`.
- Use manager-based creation whenever that is the normal Femora API:
  - `model.material...`
  - `model.element...`
  - `model.time_series...`
  - `model.ground_motion...`
  - `model.pattern...`
  - other manager entry points as appropriate
- Show realistic dependency creation when tags or manager ownership matter.
- Make sure the example uses the correct manager path. Some classes are created
  through sub-managers rather than directly from the top-level manager.
- Verify the correct manager path from the current implementation before writing
  the example. Do not guess whether creation belongs to a top-level manager or a
  sub-manager.

### Direct construction rule

Direct class construction is acceptable only when:

- the class is intentionally low-level
- direct construction is the point of the example
- manager-based creation is not the actual public usage path

### Example content rules

- Keep examples short and realistic.
- Do not use fake APIs.
- Do not use placeholder pseudo-code if a real Femora call can be shown.
- Do not use `>>>`.
- Do not include huge outputs unless output is essential.

### Example template

```python
Example:
    ```python
    from femora.core.model import Model

    model = Model()
    ts = model.time_series.path(dt=0.01, filePath="ground.acc")
    pattern = model.pattern.uniform_excitation(dof=1, time_series=ts)
    print(pattern.tag)
    ```
```

---

## 8. Formatting and Indentation

Indentation is critical for automatic parsers.

- Use 4 spaces for the body of each section.
- Wrapped section descriptions should align under the description text with an
  extra 4 spaces.
- Use a blank line after the summary line.
- Use a blank line before each section header.
- Keep indentation consistent inside fenced `python` examples.

### Correct indentation

```python
def example(value: float, other: str):
    """Do something useful.

    Args:
        value: The main numeric value used to create the output. If the
            description wraps, the next line is indented further.
        other: Secondary input.

    Returns:
        Description of the returned value.
    """
```

---

## 9. Section Labels

Use these labels exactly:

- `Args:`
- `Returns:`
- `Raises:`
- `Attributes:`
- `Note:`
- `Tip:`
- `Example:`
- `Tcl form:`

Do not use alternatives such as:

- `Parameters:`
- `Inputs:`
- `Usage:`
- `Example Usage:`
- `Exceptions:`

Consistency matters more than preference.

---

## 10. Explanation Rules

Docstrings should explain the concept behind a class or method when that
context improves understanding.

Example:

- a class may need a short explanation of what physical or computational idea
  it represents
- a manager method may need a short explanation of what it creates or registers
- a helper method may only need a direct behavior description
- For runtime classes, document runtime behavior only. Do not describe GUI
  forms, widgets, editor flows, or legacy GUI behavior unless the file itself is
  explicitly GUI-related.

Do not add theory for its own sake. Add conceptual explanation only when it
helps the reader understand the code and API.

---

## 11. Doc Controls For Generated API Pages

Femora API pages use class-level metadata to control what `mkdocstrings`
renders for that class page.

Every public runtime class should define a class attribute named
`__doc_controls__`.

Example:

```python
class SomeComponent:
    __doc_controls__ = {
        "show_docstring_attributes": False,
        "members": ["__init__"],
    }
```

Rules:

- `__doc_controls__` is mandatory for public runtime classes that appear in the
  generated API reference.
- Keep it small and machine-readable.
- Do not describe `__doc_controls__` in the user-facing docstring.
- Use it instead of hardcoding page-specific exceptions in the docs generator.
- The `members` list should be chosen intentionally after understanding the code
  and deciding which methods help users understand or use the class.
- Prefer including constructors, primary runtime methods, important helpers, and
  user-facing utilities.
- Do not include every public method mechanically.
- Do not include `to_tcl` in `members` by default, because the Tcl form is
  usually already documented in the class docstring. Include `to_tcl` only when
  its method-level behavior has important special cases worth surfacing on the
  page.
- Avoid using `members` to expose internal helpers unless they provide real
  user-facing value.

---

## 12. What AI Must Not Do

When updating docstrings, an AI must not:

- change code logic
- change names
- change signatures
- add fake APIs
- insert process narration, planning text, status updates, or assistant-style
  commentary into the source file
- introduce mojibake, encoding artifacts, or unnecessary non-ASCII punctuation
  into docstrings
- use `>>>`
- add markdown headings inside docstrings
- use Sphinx-style cross-reference roles such as `:class:` or `:meth:`
- duplicate constructor `Args:` in both the class docstring and `__init__`
- add `Returns:` to `__init__`
- skip private method docstrings
- write long essays where a short paragraph is enough

---

## 13. AI Review and Rewrite Instructions

Use the following instructions whenever an AI is asked to review or complete
docstrings for a Femora file.

### AI task instructions

1. Review the entire target file before editing.
2. Read related project files when needed to understand the relevant manager,
   base classes, usage patterns, or neighboring components, and understand
   that context before editing.
3. Only modify docstrings in the target file unless explicitly instructed
   otherwise.
4. Preserve all code logic, imports, signatures, names, and behavior.
5. Rewrite existing docstrings to follow this file exactly.
6. Add missing docstrings for all classes and all methods.
7. Every method docstring must be complete, whether the method is public or
   private.
8. Keep class docstrings focused on concept, behavior, Tcl form, notes,
   tips when useful, attributes when useful, and required examples.
9. Keep `__init__` docstrings focused on constructor arguments and validation.
10. Because MkDocs merges `__init__` into the class page, do not duplicate
    constructor `Args:` in the class docstring.
11. Every class must include at least one example.
12. Method examples are optional.
13. If examples are included, use fenced `python` blocks, never `>>>`.
14. If examples are included for normal Femora usage, prefer:

    ```python
    from femora.core.model import Model

    model = Model()
    ```

    and then use manager-based creation when practical.
15. Do not add `Note:` or `Tip:` mechanically. Read the implementation first
    and add them only when they communicate real runtime caveats, corner cases,
    or practical usage guidance.
16. Examples must be meaningful, current, and aligned with the actual runtime
    API. Prefer the updated manager or sub-manager path used by the code today.
17. When a public runtime class appears in the generated API docs, maintain or
    add a meaningful `__doc_controls__` block and choose its `members` list
    intentionally based on the code.
18. Do not include `to_tcl` in `__doc_controls__["members"]` by default unless
    the method has important special behavior that deserves separate visibility.
19. Return the full valid Python file, with no markdown fences around the full
    file.

### Reusable AI prompt

```text
You are editing docstrings for the Femora project.

Follow `.github/DOCSTRING_STYLE.md` exactly.

Task:
- Review the entire target file first.
- Read related project files when needed to understand the relevant manager,
  base classes, or usage patterns before editing, and make sure that context is
  understood before writing docstrings.
- Only change docstrings in the target file.
- Do not change logic, imports, signatures, names, or behavior.
- Rewrite inconsistent docstrings to match the Femora docstring standard.
- Add missing docstrings for all classes and all methods.
- Every method docstring must be complete, whether the method is public or private.
- Keep class docstrings focused on concept, behavior, Tcl form, notes,
  tips when useful, attributes when useful, and required examples.
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
- If the target class participates in the generated API docs, preserve or add a
  meaningful __doc_controls__ block and choose the members list intentionally.
- Do not include to_tcl in __doc_controls__["members"] by default. Include it
  only when its behavior has a meaningful special case worth showing as a
  separate API entry.
- Do not add Note or Tip sections mechanically. Understand the code first and
  add them only when there is a real runtime caveat, edge case, or practical
  usage insight worth surfacing.
- Understand the code and methods first, then decide what belongs in
  __doc_controls__["members"] for the best documentation page.

Return only the final valid Python code for the full file.
```

---

## 14. AI Checklist

Any human or AI reviewing a docstring update must verify:

1. [ ] Every class has a docstring.
2. [ ] Every method has a docstring, whether public or private.
3. [ ] Class docstrings explain what the class is and does.
4. [ ] `__init__` docstrings document constructor arguments.
5. [ ] No constructor `Args:` are duplicated between the class docstring and
       `__init__`.
6. [ ] `Tcl form:` exists where relevant.
7. [ ] Every class includes at least one example.
8. [ ] Method examples are optional, not required.
9. [ ] If examples are present, they use fenced `python` blocks and not `>>>`.
10. [ ] If examples are present, they prefer real Femora usage through
       `model = Model()` and manager-based creation when practical.
11. [ ] Section labels match this file exactly.
12. [ ] Wrapped indentation is correct.
13. [ ] No code logic was changed.

