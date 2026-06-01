---
title: API Reference
icon: material/book-open-page-variant-outline
---

# API Reference

The Femora API is organized into four reference areas: `components`, `core`,
`tools`, and `io`. They are related, but they do not serve the same purpose.
Understanding that boundary makes the rest of the reference much easier to use.

In most cases, users begin with `components`, which is the concrete modeling
surface of Femora. The `core` layer sits underneath it and explains how those
objects are owned, managed, registered, tagged, and coordinated inside the
runtime. The `tools` and `io` sections support surrounding workflows such as
helper utilities, preprocessing/postprocessing tasks, and data exchange.

## The Structure Of The API

Femora separates concrete modeling objects from runtime infrastructure on
purpose. In the reference, that means `components` answers the question
"what object represents this modeling concept?" while `core` answers
"how does Femora manage and coordinate that object internally?" The
`tools` and `io` sections cover supporting capabilities around that main
runtime surface.

!!! tip "A practical rule"
    Start in `components` when you are looking for a modeling concept. Move to
    `core` when you need to understand the ownership, manager behavior, or
    runtime architecture behind that concept.

## Where To Go

<div class="grid cards" markdown>

-   [:material-puzzle-outline: **components**](components/)
    ---
    *Concrete modeling objects.*

    The main user-facing surface of Femora. Use this section for materials,
    elements, sections, loads, patterns, recorders, analyses, and other
    runtime objects that directly describe a model.

-   [:material-cog-outline: **core**](core/)
    ---
    *Runtime infrastructure and ownership.*

    The layer behind the component surface. Use this section for managers, base
    classes, ownership rules, tagging, registries, and process coordination.

-   [:material-tools: **tools**](tools/)
    ---
    *Focused utility workflows.*

    Helper modules and task-oriented utilities that support engineering work
    around the main API without being the primary model-owned surface.

-   [:material-import: **io**](io/)
    ---
    *Data exchange and interoperability.*

    Import, export, and interoperability modules for moving data into and out
    of Femora and connecting it to external workflows.

</div>

## How To Read This Reference

Most tasks follow a simple path. If you are modeling, begin with
`components`. If you need to understand ownership, manager behavior, or runtime
coordination, move from the relevant component page into `core`. If the task is
about external data exchange, start with `io`. If it is about helper utilities
around the main model surface, look in `tools`.

This also means that some concepts appear in more than one place in the
reference, but from different angles. A component page describes what an
object represents and how it is used. A related `core` page describes how
Femora manages that object internally.
