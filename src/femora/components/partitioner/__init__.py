"""---
icon: material/graph-outline
---

Partitioner package for Femora.

This package contains components and algorithms for mesh partitioning and domain 
decomposition, mapping mesh cells to specific processors or cores for parallel 
OpenSees computations.

Normal runtime usage configures partitioners through Model assembler section 
creation, typically using `model.assembler.create_section` with parameters for 
the partition count and the specific partitioner type (such as "morton", 
"hilbert", "geometric", or "kd-tree"). Direct imports are mainly useful for 
typed references, tests, and low-level component work.
"""

from .partitioner import PartitionerError, PartitionerRegistry

__all__ = [
    "PartitionerError",
    "PartitionerRegistry",
]
