from typing import Dict, List, Union, Optional
from femora.core.material_base import Material
from femora.core.element_base import Element

class ASDEmbeddedNodeElement3D(Element):
    """
    OpenSees ASDEmbeddedNodeElement for 3D problems.

    This element is used to constrain a node (constrained node) to a domain
    defined by 3 or 4 retained nodes. For 3D Solid domains, 4 retained nodes
    forming a tetrahedron are used.
    """

    def __init__(
        self, 
        ndof: int, 
        rot: bool = False, 
        p: bool = False, 
        K: Optional[float] = None, 
        KP: Optional[float] = None, 
        contact: bool = False, 
        Kn: float = 1.0e8, 
        Kt: float = 1.0e8, 
        mu: float = 0.5, 
        orient: list = None, 
        orient_map: dict = None, 
        int_type: int = 1,
        **kwargs
    ):
        """
        Args:
            ndof (int): Number of degrees of freedom per node. Must be 3, 4, or 6.
            rot (bool, optional): Optional flag to constrain rotations. 
                Defaults to False.
            p (bool, optional): Optional flag to constrain pressure. 
                Defaults to False.
            K (float, optional): User-defined penalty stiffness. 
                Defaults to 1.0e18.
            KP (float, optional): User-defined penalty stiffness for pressure. 
                Defaults to 1.0e18.
            contact (bool, optional): Optional flag to enable frictional contact. 
                Defaults to False.
            Kn (float, optional): Penalty stiffness for normal contact. 
                Defaults to 1.0e8.
            Kt (float, optional): Penalty stiffness for tangential contact. 
                Defaults to 1.0e8.
            mu (float, optional): Friction coefficient. 
                Defaults to 0.5.
            orient (list, optional): Orientation vector if orient_map is None. 
                Defaults to [1, 0, 0].
            orient_map (dict, optional): Orientation mapping. 
                Defaults to None.
            int_type (int, optional): Integration type (0: Implicit, 1: IMPL-EX). 
                Defaults to 1.

        OpenSees command syntax:
            ``element ASDEmbeddedNodeElement $eleTag $Cnode $Rnode1 $Rnode2 $Rnode3 $Rnode4 [-rot] [-p] [-K $K] [-KP $KP] [ -contact $Kn $Kt $mu [-orient $orient] [-int_type $int_type]]``

        Note:
            ``1) Using ASDEmbeddedNodeElement3D is solely for 3D problems could be very hard. This element is implemented to use with EmbeddedNodeInterFace element.``

        Example:
            ```python
            element = ASDEmbeddedNodeElement3D(ndof=6, rot=True)
            print(element.rot)
            ```
        """
        if ndof not in [3, 4, 6]:
            raise ValueError(f"ASDEmbeddedNodeElement3D requires 3, 4, or 6 DOFs, but got {ndof}")
        
        # Store and validate parameters
        self.rot = bool(rot)
        self.p = bool(p)
        self.K = float(K) if K is not None else None
        self.KP = float(KP) if KP is not None else None
        self.contact = bool(contact)
        self.Kn = float(Kn)
        self.Kt = float(Kt)
        self.mu = float(mu)
        
        if orient is not None:
            if not isinstance(orient, (list, tuple)) or len(orient) != 3:
                raise ValueError("orient must be a list/tuple of 3 floats")
            self.orient = [float(x) for x in orient]
        else:
            self.orient = None
            
        if orient_map is not None:
            if not isinstance(orient_map, dict):
                raise ValueError("orient_map must be a dictionary")
            self.orient_map = {k: [float(x) for x in v] for k, v in orient_map.items()}
        else:
            self.orient_map = None
            
        self.int_type = int(int_type)
        if self.int_type not in [0, 1]:
            raise ValueError("int_type must be 0 or 1")
        
        super().__init__('ASDEmbeddedNodeElement', ndof, material=None, **kwargs)

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Generate the OpenSees TCL command.
        
        Args:
            tag: Element tag.
            nodes: List of nodes [Cnode, Rnode1, Rnode2, Rnode3, Rnode4].
        
        Returns:
            str: TCL command string.
        """
        if len(nodes) != 5:
            raise ValueError("ASDEmbeddedNodeElement3D requires 5 nodes (1 constrained, 4 retained)")
        
        nodes_str = " ".join(str(node) for node in nodes)
        cmd = f"element ASDEmbeddedNodeElement {tag} {nodes_str}"
        
        if self.rot:
            cmd += " -rot"
        if self.p:
            cmd += " -p"
        if self.K is not None:
            cmd += f" -K {self.K}"
        if self.KP is not None:
            cmd += f" -KP {self.KP}"
        
        if self.contact:
            cmd += f" -contact {self.Kn} {self.Kt} {self.mu}"
            
            # Orientation
            orient = None
            if self.orient_map and nodes[0] in self.orient_map:
                orient = self.orient_map[nodes[0]]
            elif self.orient:
                orient = self.orient
            
            if orient:
                cmd += f" -orient {orient[0]} {orient[1]} {orient[2]}"
                
            cmd += f" -int_type {self.int_type}"
            
        return cmd

