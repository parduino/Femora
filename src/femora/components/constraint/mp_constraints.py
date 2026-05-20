from typing import List

from femora.core.constraint_base import MPConstraint





class EqualDOF(MPConstraint):
    """Equal DOF constraint"""
    
    def __init__(self, master_node: int, slave_nodes: List[int], dofs: List[int]):
        """
        Initialize EqualDOF constraint
        
        Args:
            master_node: Retained node tag
            slave_node: Constrained node tag
            dofs: List of DOFs to be constrained
        """
        super().__init__(master_node, slave_nodes)
        self.dofs = dofs
    
    def to_tcl(self) -> str:
        tcl_str = ""
        for slave in self.slave_nodes:
            dofs_str = " ".join(str(dof) for dof in self.dofs)
            tcl_str += f"equalDOF {self.master_node} {slave} {dofs_str}"
        return tcl_str







class RigidLink(MPConstraint):
    """Rigid link constraint"""
    
    def __init__(self, type_str: str, master_node: int, slave_nodes: List[int]):
        """
        Initialize RigidLink constraint
        
        Args:
            type_str: Type of rigid link ('bar' or 'beam')
            master_node: Retained node tag
            slave_node: Constrained node tag
        """
        super().__init__(master_node, slave_nodes)
        if type_str not in ['bar', 'beam']:
            raise ValueError("RigidLink type must be 'bar' or 'beam'")
        self.type = type_str
    
    def to_tcl(self) -> str:
        tcl_str = ""
        for slave in self.slave_nodes:
            tcl_str += f"rigidLink {self.type} {self.master_node} {slave}"
        # return f"rigidLink {self.type} {self.master_node} {self.slave_nodes[0]}"






class RigidDiaphragm(MPConstraint):
    """Rigid diaphragm constraint"""
    
    def __init__(self, direction: int, master_node: int, slave_nodes: List[int]):
        """
        Initialize RigidDiaphragm constraint
        
        Args:
            direction: Direction perpendicular to rigid plane (3D) or direction of motion (2D)
            master_node: Retained node tag
            slave_nodes: List of constrained node tags
        """
        super().__init__(master_node, slave_nodes)
        self.direction = direction
    
    def to_tcl(self) -> str:
        slaves_str = " ".join(str(node) for node in self.slave_nodes)
        return f"rigidDiaphragm {self.direction} {self.master_node} {slaves_str}"
    






__all__ = ["MPConstraint", "EqualDOF", "RigidLink", "RigidDiaphragm"]