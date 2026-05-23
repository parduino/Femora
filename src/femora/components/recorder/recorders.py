from typing import List, Dict, Optional, Union

from femora.core.recorder_base import Recorder
from femora.components.interface.embedded_beam_solid_interface import EmbeddedBeamSolidInterface


def _results_folder(recorder: Recorder) -> str:
    mesh_maker = recorder._mesh_maker()
    if mesh_maker is None:
        raise ValueError(
            "Recorder must belong to a MeshMaker recorder manager to resolve results paths"
        )
    folder = mesh_maker.get_results_folder()
    if folder == "":
        return "./"
    return folder + "/"


class EmbeddedBeamSolidInterfaceRecorder(Recorder):
    """
    Recorder for embedded beam-solid interfaces.
    
    This recorder is used to monitor the interaction between embedded beams and solid elements.
    It generates output files containing the interface points and connectivity information.

    Args:
        interface (EmbeddedBeamSolidInterface | str): The interface to record. (required)
        resp_type (str | List[str] | None): The type of responses to record. (required)
        If None, only displacement is recorded.
        Valid response types include:
            - "displacement"
            - "localDisplacement"
            - "axialDisp"
            - "radialDisp"  
            - "tangentialDisp"
            - "globalForce"
            - "localForce"
            - "axialForce"
            - "radialForce"
            - "tangentialForce"
            - "solidForce"
            - "beamForce"
            - "beamLocalForce"
    Raises:
        ValueError: If the interface is not an instance of EmbeddedBeamSolidInterface or a valid interface name.
        TypeError: If resp_type is not a string or a list of strings.
        ValueError: If resp_type contains invalid response types.

    Returns:
        EmbeddedBeamSolidInterfaceRecorder: An instance of the recorder.
        
    """
    def __init__(self, 
                 interface: Union[str, 'EmbeddedBeamSolidInterface', List[Union[str, 'EmbeddedBeamSolidInterface']]],
                 resp_type: Union[str, List[str]] = ["displacement", "localDisplacement", "axialDisp", "radialDisp",
                            "tangentialDisp", "globalForce", "localForce", "axialForce",
                            "radialForce", "tangentialForce", "solidForce", "beamForce","beamLocalForce"],
                 dt : Union[float, None] = None,
                 cores: Optional[Union[int, List[int]]] = None,
                 ):
        """
        Initialize an EmbeddedBeamSolidInterfaceRecorder
        
        Args:
            - interface (EmbeddedBeamSolidInterface | str): The interface to record.
            - resp_type (str | List[str]): The type of responses to record.

    
        """
        super().__init__("EmbeddedBeamSolidInterface", cores=cores)
        if isinstance(interface, list):
            if not interface:
                raise ValueError("interface list must not be empty")
            for iface in interface:
                if not isinstance(iface, (str, EmbeddedBeamSolidInterface)):
                    raise ValueError(
                        "All interfaces must be instances of EmbeddedBeamSolidInterface or valid names"
                    )
            self._interface_input = interface
        elif isinstance(interface, (str, EmbeddedBeamSolidInterface)):
            self._interface_input = interface
        else:
            raise ValueError(
                "interface must be an instance of EmbeddedBeamSolidInterface or a valid interface name"
            )

        if isinstance(resp_type, str):
            resp_type = [resp_type]
        elif not isinstance(resp_type, list):
            raise TypeError("resp_type must be a string or a list of strings")

        self.resp_type = resp_type

        for resp in self.resp_type:
            if resp not in ["displacement", "localDisplacement", "axialDisp", "radialDisp",
                            "tangentialDisp", "globalForce", "localForce", "axialForce",
                            "radialForce", "tangentialForce", "solidForce", "beamForce","beamLocalForce"]:
                raise ValueError(f"Invalid response type: {resp}. ")

        self.dt = dt

    def _resolve_interfaces(self) -> List[EmbeddedBeamSolidInterface]:
        mesh_maker = self._mesh_maker()
        if mesh_maker is None:
            raise ValueError(
                "EmbeddedBeamSolidInterfaceRecorder must belong to a MeshMaker recorder manager before export"
            )
        interface_manager = mesh_maker.interface

        def resolve_one(item: Union[str, EmbeddedBeamSolidInterface]) -> EmbeddedBeamSolidInterface:
            if isinstance(item, str):
                resolved = interface_manager.require(item)
                if not isinstance(resolved, EmbeddedBeamSolidInterface):
                    raise ValueError(
                        f"Interface '{item}' is registered but is not an EmbeddedBeamSolidInterface"
                    )
                return resolved
            if isinstance(item, EmbeddedBeamSolidInterface):
                interface_manager.require_registered(item)
                return item
            raise TypeError("interfaces must be EmbeddedBeamSolidInterface instances or valid names")

        if isinstance(self._interface_input, list):
            return [resolve_one(item) for item in self._interface_input]
        return [resolve_one(self._interface_input)]

    def _to_tcl_impl(self) -> str:
        """
        Convert the EmbeddedBeamSolidInterfaceRecorder to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """
        # This recorder does not generate a TCL command, it writes directly to a file
        cmd = "# recorder EmbeddedBeamSolidInterface\n"
        results_folder = _results_folder(self)

        for interface in self._resolve_interfaces():
           cmd += interface._get_recorder(self.resp_type,
                                          dt=self.dt,
                                          results_folder=results_folder)
           cmd += "\n"
        return cmd
    

    

class NodeRecorder(Recorder):
    """Node recorder for recording nodal responses at every converged step.

    This recorder monitors the response of specified nodes throughout the
    analysis, writing output to files, XML, binary format, or TCP/IP streams.

    Attributes:
        file_name: Name of file to which output is sent.
        xml_file: Name of XML file to which output is sent.
        binary_file: Name of binary file to which output is sent.
        inet_addr: IP address of remote machine for TCP/IP output.
        port: Port on remote machine awaiting TCP connection.
        precision: Number of significant digits in output.
        time_series: Tag of previously constructed TimeSeries.
        time: Flag to place domain time in first output column.
        delta_t: Time interval for recording.
        close_on_write: Flag to open and close file on each write.
        nodes: Tags of nodes whose response is being recorded.
        node_range: Start and end node tags for range specification.
        region: Tag of previously defined region.
        dofs: List of DOF at nodes whose response is requested.
        resp_type: String indicating response required.

    Example:
        >>> from femora.components.recorder.recorders import NodeRecorder
        >>> # recorder = NodeRecorder(
        >>> #     file_name="displacement.out",
        >>> #     time=True,
        >>> #     nodes=[1, 2, 3],
        >>> #     dofs=[1, 2],
        >>> #     resp_type="disp"
        >>> # )
        >>> # print(recorder.to_tcl())
    """
    def __init__(self, **kwargs):
        """
        Initialize a Node Recorder
        
        Args:
            file_name (str, optional): Name of file to which output is sent
            xml_file (str, optional): Name of XML file to which output is sent
            binary_file (str, optional): Name of binary file to which output is sent
            inet_addr (str, optional): IP address of remote machine
            port (int, optional): Port on remote machine awaiting TCP
            precision (int, optional): Number of significant digits (default: 6)
            time_series (int, optional): Tag of previously constructed TimeSeries
            time (bool, optional): Places domain time in first output column
            delta_t (float, optional): Time interval for recording
            close_on_write (bool, optional): Opens and closes file on each write
            nodes (List[int], optional): Tags of nodes whose response is being recorded
            node_range (List[int], optional): Start and end node tags
            region (int, optional): Tag of previously defined region
            dofs (List[int]): List of DOF at nodes whose response is requested
            resp_type (str): String indicating response required
        """
        super().__init__("Node", cores=kwargs.get("cores", None))
        self.file_name = kwargs.get("file_name", None)
        self.xml_file = kwargs.get("xml_file", None)
        self.binary_file = kwargs.get("binary_file", None)
        self.inet_addr = kwargs.get("inet_addr", None)
        self.port = kwargs.get("port", None)
        self.precision = kwargs.get("precision", 6)
        self.time_series = kwargs.get("time_series", None)
        self.time = kwargs.get("time", False)
        self.delta_t = kwargs.get("delta_t", None)
        self.close_on_write = kwargs.get("close_on_write", False)
        self.nodes = kwargs.get("nodes", None)
        self.node_range = kwargs.get("node_range", None)
        self.region = kwargs.get("region", None)
        self.dofs = kwargs.get("dofs", [])
        self.resp_type = kwargs.get("resp_type", "")

        output_options = [
            self.file_name is not None,
            self.xml_file is not None,
            self.binary_file is not None,
            (self.inet_addr is not None and self.port is not None),
        ]
        if sum(output_options) > 1:
            raise ValueError("Only one of -file, -xml, -binary, or -tcp may be used")

        node_options = [
            self.nodes is not None,
            self.node_range is not None,
            self.region is not None,
        ]
        if sum(node_options) > 1:
            raise ValueError("Only one of -node, -nodeRange, or -region may be used")
        if sum(node_options) == 0:
            raise ValueError("One of -node, -nodeRange, or -region must be specified")
        if not self.dofs:
            raise ValueError("DOFs must be specified")
        if not self.resp_type:
            raise ValueError("Response type must be specified")
        valid_resp_types = [
            "disp", "vel", "accel", "incrDisp", "reaction", "rayleighForces",
        ]
        if not (self.resp_type in valid_resp_types or self.resp_type.startswith("eigen ")):
            raise ValueError(
                f"Invalid response type: {self.resp_type}. "
                f"Valid types are: {', '.join(valid_resp_types)}, or 'eigen $mode'"
            )

    def _to_tcl_impl(self) -> str:
        """
        Convert the Node recorder to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """
        cmd = "recorder Node"
        
        # Output destination
        if self.file_name:
            cmd += f" -file {self.file_name}"
        elif self.xml_file:
            cmd += f" -xml {self.xml_file}"
        elif self.binary_file:
            cmd += f" -binary {self.binary_file}"
        elif self.inet_addr and self.port:
            cmd += f" -tcp {self.inet_addr} {self.port}"
        
        # Other options
        if self.precision != 6:
            cmd += f" -precision {self.precision}"
        
        if self.time_series:
            cmd += f" -timeSeries {self.time_series}"
        
        if self.time:
            cmd += " -time"
        
        if self.delta_t:
            cmd += f" -dT {self.delta_t}"
        
        if self.close_on_write:
            cmd += " -closeOnWrite"
        
        # Node selection
        if self.nodes:
            cmd += f" -node {' '.join(map(str, self.nodes))}"
        elif self.node_range:
            cmd += f" -nodeRange {self.node_range[0]} {self.node_range[1]}"
        elif self.region:
            cmd += f" -region {self.region}"
        
        # DOFs and response type
        cmd += f" -dof {' '.join(map(str, self.dofs))} {self.resp_type}"
        
        return cmd


class DriftRecorder(Recorder):
    """Recorder for inter-story drift ratios.

    This wraps the OpenSees `recorder Drift` command.

        Note:
                - In MPI runs, multiple processes must not write to the same file.
                    This recorder automatically injects `$pid` into the output filename
                    (before the extension if present).
                - Optionally, `cores` can be provided to emit the recorder only on
                    the specified MPI process ids.

    Example:
        >>> import femora as fm
        >>> from femora.components.MeshMaker import MeshMaker
        >>> model = MeshMaker()
        >>> rec = model.recorder.drift(
        ...     file_name="StoryDrift_Story01_X.out",
        ...     i_nodes=1,
        ...     j_nodes=101,
        ...     dof=1,
        ...     perp_dirn=3,
        ...     time=True,
        ... )
        >>> print(rec.to_tcl())
    """

    def __init__(self, **kwargs):
        # Accept both legacy `core` and new `cores` arguments.
        cores = kwargs.get("cores", None)
        core = kwargs.get("core", None)
        if cores is None and core is not None:
            cores = int(core)

        super().__init__("Drift", cores=cores)

        self.file_name: str = str(kwargs.get("file_name", ""))

        i_nodes = kwargs.get("i_nodes", None)
        j_nodes = kwargs.get("j_nodes", None)

        self.i_nodes: List[int] = self._normalize_nodes(i_nodes, "i_nodes")
        self.j_nodes: List[int] = self._normalize_nodes(j_nodes, "j_nodes")

        self.dof: int = int(kwargs.get("dof", 0))
        self.perp_dirn: int = int(kwargs.get("perp_dirn", 3))
        self.time: bool = bool(kwargs.get("time", False))
        self.delta_t: Optional[float] = kwargs.get("delta_t", None)
        self.precision: Optional[int] = kwargs.get("precision", None)

        if not self.file_name:
            raise ValueError("file_name must be specified for DriftRecorder")
        if not self.i_nodes or not self.j_nodes:
            raise ValueError("Both i_nodes and j_nodes must be specified")
        if len(self.i_nodes) != len(self.j_nodes):
            raise ValueError("i_nodes and j_nodes must have the same length")
        for n in self.i_nodes + self.j_nodes:
            if not isinstance(n, int) or n <= 0:
                raise ValueError("All node tags must be positive integers")
        if self.dof not in (1, 2, 3, 4, 5, 6):
            raise ValueError("dof must be an integer in [1..6]")
        if self.perp_dirn not in (1, 2, 3):
            raise ValueError("perp_dirn must be an integer in [1..3]")
        if self.delta_t is not None:
            self.delta_t = float(self.delta_t)
            if self.delta_t <= 0:
                raise ValueError("delta_t must be > 0 when provided")
        if self.precision is not None:
            self.precision = int(self.precision)
            if self.precision <= 0:
                raise ValueError("precision must be > 0 when provided")
        if self.cores is not None:
            if isinstance(self.cores, int):
                if self.cores < 0:
                    raise ValueError("cores must be >= 0 when provided")
            elif isinstance(self.cores, (list, tuple)):
                for c in self.cores:
                    if not isinstance(c, int) or c < 0:
                        raise ValueError("each entry in cores must be a non-negative integer")
            else:
                raise TypeError("cores must be an int or list/tuple of ints")

    @staticmethod
    def _normalize_nodes(value, name: str) -> List[int]:
        if value is None:
            return []
        if isinstance(value, int):
            return [int(value)]
        if isinstance(value, (list, tuple)):
            return [int(v) for v in value]

        # Allow numpy arrays without importing numpy at module import time.
        try:
            import numpy as _np  # local import

            if isinstance(value, _np.ndarray):
                return [int(v) for v in value.tolist()]
        except Exception:
            pass
        raise TypeError(f"{name} must be an int or a list/tuple of ints")

    @staticmethod
    def _inject_pid_in_filename(file_name: str) -> str:
        parts = file_name.split(".")
        if len(parts) > 1:
            ext = parts[-1]
            return file_name[: -(len(ext) + 1)] + f"$pid.{ext}"
        return file_name + "$pid"

    def _to_tcl_impl(self) -> str:
        results_folder = _results_folder(self)
        file_path = DriftRecorder._inject_pid_in_filename(self.file_name)
        if results_folder != "./":
            file_path = results_folder + file_path

        cmd = f"recorder Drift -file {file_path}"
        if self.precision is not None:
            cmd += f" -precision {int(self.precision)}"

        cmd += " -iNode " + " ".join(str(n) for n in self.i_nodes)
        cmd += " -jNode " + " ".join(str(n) for n in self.j_nodes)
        cmd += f" -dof {int(self.dof)} -perpDirn {int(self.perp_dirn)}"

        if self.time:
            cmd += " -time"
        if self.delta_t is not None:
            cmd += f" -dT {float(self.delta_t)}"

        # Do not wrap here; `Recorder.to_tcl` will apply any core-guarding
        return cmd


class VTKHDFRecorder(Recorder):
    """
    The VTKHDF recorder type is a whole model recorder designed to record 
    the model geometry and metadata, along with selected response quantities.
    The output of this recorder is in the .h5 file format, which can be 
    visualized using visualization tools like ParaView.

    Args:
        file_base_name (str): Base name of the file to which output is sent
        resp_types (List[str]): List of strings indicating response types to record
        delta_t (float, optional): Time interval for recording
        r_tol_dt (float, optional): Relative tolerance for time step matching

    Raises:
        ValueError: If file_base_name is not specified
        ValueError: If resp_types is not specified or contains invalid types    
    Returns:
        VTKHDFRecorder: An instance of the recorder.
    """
    def __init__(self, **kwargs):
        """
        Initialize a VTKHDF Recorder
        
        Args:
            file_base_name (str): Base name of the file to which output is sent
            resp_types (List[str]): List of strings indicating response types to record
            delta_t (float, optional): Time interval for recording
            r_tol_dt (float, optional): Relative tolerance for time step matching
        """
        super().__init__("VTKHDF", cores=kwargs.get("cores", None))
        self.file_base_name = kwargs.get("file_base_name", "")
        self.resp_types = kwargs.get("resp_types", [])
        self.delta_t = kwargs.get("delta_t", None)
        self.r_tol_dt = kwargs.get("r_tol_dt", None)

        if not self.file_base_name:
            raise ValueError("File base name must be specified")
        if not self.resp_types:
            raise ValueError("At least one response type must be specified")
        valid_resp_types = [
            "disp", "vel", "accel", "stress3D6", "strain3D6", "stress2D3", "strain2D3",
        ]
        for resp_type in self.resp_types:
            if resp_type not in valid_resp_types:
                raise ValueError(
                    f"Invalid response type: {resp_type}. "
                    f"Valid types are: {', '.join(valid_resp_types)}"
                )

    def _to_tcl_impl(self) -> str:
        """
        Convert the VTKHDF recorder to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """

        # separete name and format of the file
        name = self.file_base_name.split(".")
        if len(name) <2:
            fileformat = "vtkhdf"
        else:
            fileformat = name[-1]
        name = name[0]
        name = name + "$pid"
        results_folder = _results_folder(self)
        if results_folder != "./":
            name = results_folder + name
        file_base_name = name + "." + fileformat

        cmd = f"recorder vtkhdf {file_base_name}"
        
        # Add optional parameters
        if self.delta_t is not None:
            cmd += f" -dT {self.delta_t}"

        if self.r_tol_dt is not None:
            cmd += f" -rTolDt {self.r_tol_dt}"

        # Add response types
        for resp_type in self.resp_types:
            cmd += f" {resp_type}"
        
        
        
        return cmd


class MPCORecorder(Recorder):
    """
    MPCO recorder writes model responses into an HDF5 database readable by STKO (*.mpco).

    Command form (see official docs):
        recorder mpco $fileName \
            <-N nodeResponses...> \
            <-E elementResponses...> \
            <-NS name1 par1 name2 par2 ...> \
            <-R regionTag> ... \
            <-T dt $deltaTime | -T nsteps $numSteps>

    Reference: OpenSees MPCO Recorder documentation.
    """
    def __init__(self, **kwargs):
        """
        Initialize an MPCO Recorder

        Args:
            file_name (str): Output file name (e.g., "results.mpco")
            node_responses (List[str], optional): Node response names per docs
            element_responses (List[str], optional): Element/section/material response names
            node_sensitivities (List[tuple[str,int]] | List[dict], optional): Pairs of (name, parameterId)
            regions (List[int], optional): Region tags to record (can repeat)
            delta_t (float, optional): Recording time interval (mutually exclusive with num_steps)
            num_steps (int, optional): Recording step interval (mutually exclusive with delta_t)
        """
        super().__init__("MPCO", cores=kwargs.get("cores", None))
        self.file_name = kwargs.get("file_name", "")
        self.node_responses = kwargs.get("node_responses", [])
        self.element_responses = kwargs.get("element_responses", [])
        self.node_sensitivities = kwargs.get("node_sensitivities", [])
        self.regions = self._resolve_regions(kwargs.get("regions", []))
        self.delta_t = kwargs.get("delta_t", None)
        self.num_steps = kwargs.get("num_steps", None)

        if not self.file_name:
            raise ValueError("File name must be specified for MPCO recorder")
        if self.node_responses is None:
            self.node_responses = []
        if not isinstance(self.node_responses, list):
            raise TypeError("node_responses must be a list of strings")
        valid_node_responses = [
            "displacement", "rotation",
            "velocity", "angularVelocity",
            "acceleration", "angularAcceleration",
            "reactionForce", "reactionMoment",
            "reactionForceIncludingInertia", "reactionMomentIncludingInertia",
            "rayleighForce", "rayleighMoment",
            "unbalancedForce", "unbalancedForceIncludingInertia",
            "unbalancedMoment", "unbalancedMomentIncludingInertia",
            "pressure",
            "modesOfVibration", "modesOfVibrationRotational",
        ]
        for resp in self.node_responses:
            if not isinstance(resp, str):
                raise TypeError("Each node response must be a string")
            if resp not in valid_node_responses:
                raise ValueError(
                    f"Invalid node response: {resp}. Valid: {', '.join(valid_node_responses)}"
                )
        if self.element_responses is None:
            self.element_responses = []
        if not isinstance(self.element_responses, list):
            raise TypeError("element_responses must be a list of strings")
        for er in self.element_responses:
            if not isinstance(er, str):
                raise TypeError("Each element response must be a string")
        if self.node_sensitivities is None:
            self.node_sensitivities = []
        valid_sensitivity_names = [
            "displacementSensitivity", "rotationSensitivity",
            "velocitySensitivity", "angularVelocitySensitivity",
            "accelerationSensitivity", "angularAccelerationSensitivity",
        ]
        normalized_pairs = []
        if not isinstance(self.node_sensitivities, list):
            raise TypeError("node_sensitivities must be a list of pairs or dicts")
        for item in self.node_sensitivities:
            if isinstance(item, dict):
                name = item.get("name")
                par = item.get("param")
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                name, par = item[0], item[1]
            else:
                raise TypeError("node_sensitivities items must be (name, param) or {'name','param'}")
            if name not in valid_sensitivity_names:
                raise ValueError(
                    f"Invalid node sensitivity: {name}. Valid: {', '.join(valid_sensitivity_names)}"
                )
            if not isinstance(par, int):
                raise TypeError("Sensitivity parameter id must be an integer")
            normalized_pairs.append((name, par))
        self.node_sensitivities = normalized_pairs
        if self.regions is None:
            self.regions = []
        if not isinstance(self.regions, list):
            raise TypeError("regions must be a list of integers")
        for r in self.regions:
            if not isinstance(r, int):
                raise TypeError("Each region tag must be an integer")
        if self.delta_t is not None and self.num_steps is not None:
            raise ValueError("Only one of delta_t or num_steps may be specified")

    def _to_tcl_impl(self) -> str:
        """
        Convert the MPCO recorder to a TCL command string for OpenSees

        Returns:
            str: The TCL command string
        """
        results_folder = _results_folder(self)
        file_path = self.file_name

        file_ext = self.file_name.split(".")[-1]
        if len(self.file_name.split(".")) > 1:
            file_path = self.file_name.replace("." + file_ext, "$pid." + file_ext)
        else:
            file_path = self.file_name + "$pid"

        if results_folder != "./":
            file_path = results_folder + file_path

        cmd = f'recorder mpco "{file_path}"'

        if self.node_responses:
            cmd += " -N " + " ".join(self.node_responses)

        if self.element_responses:
            cmd += " -E " + " ".join(self.element_responses)

        if self.node_sensitivities:
            ns_parts = []
            for name, par in self.node_sensitivities:
                ns_parts.append(name)
                ns_parts.append(str(par))
            cmd += " -NS " + " ".join(ns_parts)

        for r in self.regions:
            cmd += f" -R {r}"

        if self.delta_t is not None:
            cmd += f" -T dt {self.delta_t}"
        elif self.num_steps is not None:
            cmd += f" -T nsteps {self.num_steps}"

        return cmd


class BeamForceRecorder(Recorder):
    """
    Specialized Element recorder for beam meshes to record forces.

    This recorder inspects the assembled mesh, resolves the element tags that
    correspond to selected beam mesh parts (line meshes), and emits one or more
    recorder Element commands per compute core.

    Args:

        meshparts (List[Union[str, int, object]]):
            MeshPart identifiers (user_name strings or MeshPart instances).
            If omitted or empty, all line mesh parts will be used.

        force_type (str): 'globalForce' or 'localForce'. Default: 'globalForce'.

        file_prefix (str): Prefix for output files. Default: 'Beam'.

        delta_t (float | None): Optional -dT value. Default: None.

        include_time (bool): Include -time flag. Default: True.

        output_format (str): 'file', 'xml', or 'binary' (-file/-xml/-binary). Default: 'file'.

        precision (int | None): Number of significant digits (-precision). Default: None.

    Raises:
        ValueError: If force_type is invalid or if specified meshparts are not found.
    
    Returns:
        BeamForceRecorder: An instance of the recorder.

    Example:
    '''
        import femora as fm
        fm.recorder = fm.BeamForceRecorder(
            meshparts=["BeamMeshPart1", "BeamMeshPart2"],
            force_type="localForce",
            file_prefix="MyBeamForces",
            delta_t=0.1,
            include_time=True
        )
    '''
    """
    def __init__(self, **kwargs):
        super().__init__("BeamForce", cores=kwargs.get("cores", None))
        self.meshparts = kwargs.get("meshparts", [])
        self.force_type = kwargs.get("force_type", "globalForce")
        self.file_prefix = kwargs.get("file_prefix", "Beam")
        self.delta_t = kwargs.get("delta_t", None)
        self.include_time = kwargs.get("include_time", True)
        self.output_format = kwargs.get("output_format", "file")
        self.precision = kwargs.get("precision", None)

        # Validate force type
        if self.force_type not in ("globalForce", "localForce"):
            raise ValueError("force_type must be 'globalForce' or 'localForce'")
        if self.output_format not in ("file", "xml", "binary"):
            raise ValueError("output_format must be one of 'file', 'xml', 'binary'")

    def _resolve_meshparts(self):
        from femora.core.meshpart_base import MeshPart

        mesh_maker = self._mesh_maker()
        if mesh_maker is None:
            raise ValueError(
                "BeamForceRecorder must belong to a MeshMaker recorder manager before resolving meshparts"
            )
        manager = mesh_maker.meshpart
        if not self.meshparts:
            return {
                name: part
                for name, part in manager.get_all().items()
                if part.category.lower() == "line mesh"
            }
        resolved: Dict[str, object] = {}
        for mp in self.meshparts:
            if isinstance(mp, str):
                part = manager.get(mp)
                if part is None:
                    raise ValueError(f"MeshPart '{mp}' not found")
                resolved[mp] = part
            elif isinstance(mp, MeshPart):
                resolved[mp.user_name] = mp
            else:
                raise TypeError("meshparts must be MeshPart instances or user_name strings")
        return resolved

    @staticmethod
    def _compress_to_ranges(sorted_tags: List[int]) -> List[Union[int, tuple]]:
        if not sorted_tags:
            return []
        ranges: List[Union[int, tuple]] = []
        start = prev = sorted_tags[0]
        for t in sorted_tags[1:]:
            if t == prev + 1:
                prev = t
                continue
            # close current range
            if start == prev:
                ranges.append(start)
            else:
                ranges.append((start, prev))
            start = prev = t
        # close last range
        if start == prev:
            ranges.append(start)
        else:
            ranges.append((start, prev))
        return ranges

    def _to_tcl_impl(self) -> str:
        import numpy as np
        try:
            import pyvista as pv
        except Exception:
            pv = None

        mm = self._mesh_maker()
        if mm is None:
            raise ValueError(
                "BeamForceRecorder must belong to a MeshMaker recorder manager before export"
            )
        assembled = mm.assembler.AssembeledMesh
        if assembled is None:
            raise ValueError("No assembled mesh found. Assemble the model before creating BeamForceRecorder.")

        results_folder = _results_folder(self)

        start_ele_tag = mm._start_ele_tag

        # Resolve meshparts
        parts = self._resolve_meshparts()

        # Determine beam cell types mask, if pyvista is available
        celltypes = getattr(assembled, "celltypes", None)
        beam_mask_all = None
        if pv is not None and celltypes is not None:
            beam_types = set()
            if hasattr(pv, "CellType"):
                # Common line-like cell types
                for name in ("LINE", "POLY_LINE"):
                    if hasattr(pv.CellType, name):
                        beam_types.add(getattr(pv.CellType, name))
            if beam_types:
                beam_mask_all = np.isin(celltypes, list(beam_types))

        cores = assembled.cell_data.get("Core")
        mesh_tags = assembled.cell_data.get("MeshPartTag_celldata")
        if mesh_tags is None or cores is None:
            raise ValueError("Assembled mesh missing required cell_data ('MeshPartTag_celldata' or 'Core')")

        lines: List[str] = []
        # For each meshpart, build recorder(s) grouped by core
        for name, part in parts.items():
            # mask by mesh tag
            mask = (mesh_tags == part.tag)
            if beam_mask_all is not None:
                mask = mask & beam_mask_all

            idxs = np.where(mask)[0]
            if idxs.size == 0:
                lines.append(f"# No beam elements found for meshpart '{name}'")
                continue

            # Map indices to element tags
            ele_tags = (start_ele_tag + idxs).astype(int)

            # group by core
            part_cores = cores[idxs]
            unique_cores = np.unique(part_cores)
            for core in unique_cores:
                core_mask = (part_cores == core)
                core_tags = np.sort(ele_tags[core_mask])
                if core_tags.size == 0:
                    continue

                # File name per meshpart per core with extension by format
                ext = ".out" if self.output_format == "file" else (".xml" if self.output_format == "xml" else ".bin")
                file_name = f"{results_folder}{self.file_prefix}_{name}_Core{int(core)}_{self.force_type}{ext}"

                # Build command
                file_flag = "-file" if self.output_format == "file" else ("-xml" if self.output_format == "xml" else "-binary")
                cmd = f"if {{$pid == {int(core)}}} {{\n\trecorder Element {file_flag} {file_name}"
                if self.precision is not None:
                    cmd += f" -precision {int(self.precision)}"
                if self.include_time:
                    cmd += " -time"
                if self.delta_t is not None:
                    cmd += f" -dT {self.delta_t}"

                # Always use explicit element tags with -ele
                tags_list = core_tags.tolist()
                if self.output_format == "xml":
                    # Avoid multiple XML recorders writing to same file; single line with all tags
                    cmd += " -ele " + " ".join(str(t) for t in tags_list)
                    cmd += f" {self.force_type}\n}}"
                    lines.append(cmd)
                else:
                    # Split into chunks if long (text/binary append-friendly)
                    CHUNK = 1000
                    head, rest = tags_list[:CHUNK], tags_list[CHUNK:]
                    if head:
                        cmd += " -ele " + " ".join(str(t) for t in head)
                        cmd += f" {self.force_type}\n"
                    # For remaining chunks, create additional recorder lines with same file
                    while rest:
                        chunk, rest = rest[:CHUNK], rest[CHUNK:]
                        cmd += f"\trecorder Element {file_flag} {file_name}"
                        if self.precision is not None:
                            cmd += f" -precision {int(self.precision)}"
                        if self.include_time:
                            cmd += " -time"
                        if self.delta_t is not None:
                            cmd += f" -dT {self.delta_t}"
                        cmd += " -ele " + " ".join(str(t) for t in chunk)
                        cmd += f" {self.force_type}\n"
                    cmd += "}"
                    lines.append(cmd)

        return "\n".join(lines)

