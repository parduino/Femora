import numpy as np

from femora.core.material_manager import MaterialManager
from femora.core.element_base import Element
from femora.core.element_manager import ElementManager
from femora.core.ground_motion_manager import GroundMotionManager
from femora.core.assembler import Assembler
from femora.core.damping_manager import DampingManager
from femora.core.region_manager import RegionManager
from femora.core.constraint_manager import ConstraintManager
from femora.core.load_manager import LoadManager
from femora.core.meshpart_manager import MeshPartManager
from femora.components.mesh import *
from femora.core.time_series_manager import TimeSeriesManager
from femora.core.analysis_manager import AnalysisManager
from femora.core.pattern_manager import PatternManager
from femora.core.recorder_manager import RecorderManager
from femora.core.process_manager import ProcessManager
from femora.core.transformation_manager import TransformationManager
from femora.core.interface_base import InterfaceManager
from femora.core.section_manager import SectionManager
from femora.core.mass_manager import MassManager
from femora.components.geometry_ops.spatial_transform_manager import SpatialTransformManager
from femora.core.mask_manager import MaskManager
from femora.core.action_manager import ActionManager
from femora.core.event_bus import ModelEventBus
from femora.core.part_registry import FemoraPart, FemoraPartRegistry
from femora.core.group import GroupManager

class Model:
    """
    Root runtime object for Femora model construction, assembly, and export.
    """

    def __init__(self, **kwargs):
        """
        Initialize a Femora Model instance.
        
        Args:
            **kwargs: Keyword arguments including:
                - model_name (str): Name of the model
                - model_path (str): Path to save the model
        """
        self.model = None
        # Primary public assembled-mesh path for runtime, export, and downstream consumers.
        self.assembled_mesh = None
        self.events = ModelEventBus()
        self._part_registry = FemoraPartRegistry()
        self.model_name = kwargs.get('model_name')
        self.model_path = kwargs.get('model_path')
        self._results_folder = ""
        self.material = MaterialManager(mesh_maker=self)
        self.element = ElementManager(mesh_maker=self)
        self.time_series = TimeSeriesManager(mesh_maker=self)
        self.ground_motion = GroundMotionManager(mesh_maker=self, time_series_manager=self.time_series)
        self.damping = DampingManager(mesh_maker=self)
        self.mass = MassManager(mesh_maker=self)
        self.region = RegionManager(mesh_maker=self)
        self.constraint = ConstraintManager(mesh_maker=self)
        self.load = LoadManager(mesh_maker=self)
        self.meshpart = MeshPartManager(mesh_maker=self)
        self.assembler = Assembler(mesh_maker=self)
        self.analysis = AnalysisManager(mesh_maker=self)
        self.pattern = PatternManager(
            mesh_maker=self,
            time_series_manager=self.time_series,
            ground_motion_manager=self.ground_motion,
        )
        self.group = GroupManager(mesh_maker=self)
        self.recorder = RecorderManager(mesh_maker=self)
        self.interface = InterfaceManager(mesh_maker=self)
        self.transformation = TransformationManager(mesh_maker=self)
        self.section = SectionManager(mesh_maker=self)
        self.actions = ActionManager(mesh_maker=self)
        self.mask = MaskManager(mesh_maker=self)
        self.spatial_transform = SpatialTransformManager()
        self.process = ProcessManager(mesh_maker=self)
        
        # Tag start controls for node and element IDs written to TCL
        # These control only exported OpenSees node/element tags (not Material/Element class tags)
        self._start_nodetag: int = 1
        self._start_ele_tag: int = 1
        self._start_core_tag: int = 0

        self._register_model_event_subscribers()

    def _register_model_event_subscribers(self) -> None:
        self.mass.register_events()
        self.mask.register_events()
        
    # ------------------------------------------------------------------
    # Progress helpers
    # ------------------------------------------------------------------

    def set_nodetag_start(self, start_tag: int) -> None:
        """
        Set the starting tag number for nodes in exported TCL.

        Args:
            start_tag (int): First node tag to use (must be >= 1)
        """
        if not isinstance(start_tag, int) or start_tag < 1:
            raise ValueError("Node tag start must be an integer >= 1")
        self._start_nodetag = start_tag

    def set_eletag_start(self, start_tag: int) -> None:
        """
        Set the starting tag number for elements in exported TCL.

        Args:
            start_tag (int): First element tag to use (must be >= 1)
        """
        if not isinstance(start_tag, int) or start_tag < 1:
            raise ValueError("Element tag start must be an integer >= 1")
        self._start_ele_tag = start_tag

    def set_start_core_tag(self, start_tag: int) -> None:
        """
        Set the starting tag number for cores in exported TCL.

        Args:
            start_tag (int): First core tag to use (must be >= 0)
        """
        if not isinstance(start_tag, int) or start_tag < 0:
            raise ValueError("Core tag start must be an integer >= 0")
        self._start_core_tag = start_tag

    def export_to_tcl(self, filename=None, progress_callback=None, decimals=5):
        """
        Export the model to a TCL file

        Args:
            filename (str, optional): The filename to export to. If None,
                                     uses model_name in model_path
            progress_callback (callable, optional): Callback function to report progress.
                                                  If None, uses tqdm progress bar.

        Returns:
            bool: True if export was successful, False otherwise

        Raises:
            ValueError: If no filename is provided and model_name/model_path are not set
        """
        from femora.io.export_tcl import export_to_tcl as _export_to_tcl

        return _export_to_tcl(
            self,
            filename=filename,
            progress_callback=progress_callback,
            decimals=decimals,
        )

    def export_to_vtk(self, filename=None, write_info_json=False, indent=2):
        '''
        Export the model to a vtk file

        Args:
            filename (str, optional): The filename to export to. If None,
                                    uses model_name in model_path
            write_info_json (bool, optional): When True, also write a
                                    lightweight sidecar JSON file.
            indent (int, optional): JSON indentation level for sidecar info.

        Returns:
            bool: True if export was successful, False otherwise
        '''
        from femora.io.export_vtk import export_to_vtk as _export_to_vtk

        return _export_to_vtk(
            self,
            filename=filename,
            write_info_json=write_info_json,
            indent=indent,
        )

    def export_to_json(self, filename=None, indent=2):
        '''
        Export a lightweight structural snapshot of the model to JSON.

        Args:
            filename (str, optional): The filename to export to. If None,
                                    uses model_name in model_path
            indent (int, optional): JSON indentation level. Defaults to 2.

        Returns:
            bool: True if export was successful
        '''
        from femora.io.export_json import export_to_json as _export_to_json

        return _export_to_json(self, filename=filename, indent=indent)

    def set_model_info(self, model_name=None, model_path=None):
        """
        Update model information
        
        Args:
            model_name (str, optional): New model name
            model_path (str, optional): New model path
        """
        if model_name is not None:
            self.model_name = model_name
        if model_path is not None:
            self.model_path = model_path

    def set_results_folder(self, folder_name):
        """
        Set the results folder for the model
        This method updates the results folder where simulation results will be stored.

        Args:
            folder_name (str): path to the results folder
        """
        self._results_folder = folder_name

    def get_results_folder(self):
        """
        Get the current results folder path
        
        Returns:
            str: The path to the results folder
        """
        return self._results_folder if self._results_folder else ""

    def get_femora_parts(self) -> list[dict]:
        """Return a read-only snapshot of source parts registered for VTK export."""
        return self._part_registry.get_all()

    def _register_femora_part(
        self,
        *,
        kind: str,
        name: str,
        source_tag: int | None = None,
    ) -> FemoraPart:
        return self._part_registry.get_or_create(
            kind=kind,
            name=name,
            source_tag=source_tag,
        )

    def _assign_femora_part_data(
        self,
        mesh,
        *,
        kind: str,
        name: str,
        source_tag: int | None = None,
    ) -> FemoraPart:
        part = self._register_femora_part(
            kind=kind,
            name=name,
            source_tag=source_tag,
        )
        mesh.cell_data["FemoraPartTag"] = np.full(mesh.n_cells, part.tag, dtype=np.int32)
        mesh.cell_data["FemoraPartKind"] = np.full(mesh.n_cells, part.kind_id, dtype=np.int16)
        return part
    

    def print_info(self):
        '''
        Print information about the current model on the console

        Args:
            None

        Returns:
            None
        '''

        if self.assembled_mesh is None:
            print("No mesh found")
        else:
            numpoints = self.assembled_mesh.n_points
            numcells = self.assembled_mesh.n_cells
            print(f"Number of nodes: {numpoints}")
            print(f"Number of elements: {numcells}")    
        
        
    def get_max_ele_tag(self):
        '''
        Get the maximum element tag in the assembled mesh 

        Args:
            None

        Returns:
            positive int: maximum element tag
            -1: if no mesh is assembled
        '''

        max_ele_tag = self.assembler.get_num_cells()

        if max_ele_tag < 0:
            return -1
        return max_ele_tag + self._start_ele_tag - 1
    
    def get_max_node_tag(self):
        '''
        Get the maximum node tag in the assembled mesh 

        Args:
            None

        Returns:
            positive int: maximum node tag
            -1: if no mesh is assembled
        '''

        max_node_tag = self.assembler.get_num_points()

        if max_node_tag < 0:
            return -1
        return max_node_tag + self._start_nodetag - 1

    def get_start_ele_tag(self):
        """
        Get the start element tag

        Args:
            None

        Returns:
            int: start element tag
        """
        return self._start_ele_tag
    

    def get_start_node_tag(self):
        """
        Get the start node tag

        Args:
            None

        Returns:
            int: start node tag
        """
        return self._start_nodetag

    def clear_model(self):
        """
        Clear the current model and reset all components to their initial state.
        This method wipes the current mesh, materials, elements, constraints, and all other components,
        allowing you to start fresh without needing to create a new Model instance.
        """
        self.model = None
        self.mass.unregister_events()
        self.mask.unregister_events()
        self.mask.clear()
        self.events.clear()
        self._part_registry.clear()
        self.assembled_mesh = None
        self.assembler.reset()
        self.material.clear()
        self.element.clear()
        self.damping.clear()
        self.damping.set_tag_start(1)
        self.mass.clear()
        self.region.clear()
        self.constraint.clear()
        self.constraint.set_tag_start(1)
        self.load.clear()
        self.load.set_tag_start(1)
        self.meshpart.clear()
        self.meshpart.set_tag_start(1)
        self.time_series.clear()
        self.ground_motion.clear()
        self.analysis.clear()
        self.pattern.clear()
        self.group.clear()
        self.recorder.clear()
        self.recorder.set_tag_start(1)
        self.process.clear()
        self.interface.clear()
        self.transformation.clear()
        self.section.clear()
        self.spatial_transform.clear()
        self.actions.clear()
        self.time_series.set_tag_start(1)
        self.ground_motion.set_tag_start(1)
        self.pattern.set_tag_start(1)
        self.transformation.set_tag_start(1)
        self.material.set_tag_start(1)
        self.section.set_tag_start(1)
        self.region.set_tag_start(1)
        self._start_nodetag = 1
        self._start_ele_tag = 1
        self._start_core_tag = 0
        self._register_model_event_subscribers()
