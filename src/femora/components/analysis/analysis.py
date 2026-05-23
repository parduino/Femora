from typing import Optional
from femora.core.analysis_component_base import AnalysisComponent
from .numberers import Numberer
from .integrators import Integrator, StaticIntegrator, TransientIntegrator
from .algorithms import Algorithm
from .systems import System
from .constraint_handlers import ConstraintHandler
from .convergenceTests import Test


class Analysis(AnalysisComponent):
    """Main class for managing an OpenSees structural analysis.

    An Analysis object combines six essential components (constraint handler, numberer,
    system solver, solution algorithm, convergence test, and integrator) to define
    how the finite element analysis is performed. It supports static, transient,
    and variable time-step transient analyses.

    Attributes:
        tag: The unique sequential identifier for this analysis.
        name: User-specified name for the analysis (must be unique).
        analysis_type: Type of analysis ("Static", "Transient", or "VariableTransient").
        constraint_handler: The constraint handler for enforcing boundary conditions.
        numberer: The DOF numberer for equation numbering.
        system: The system solver for solving equations.
        algorithm: The solution algorithm for nonlinear iterations.
        test: The convergence test for checking solution convergence.
        integrator: The integrator for time or load stepping.
        num_steps: Number of analysis steps (required for Static).
        final_time: Final time for analysis (optional for Transient).
        dt: Time step increment (required for Transient/VariableTransient).
        dt_min: Minimum time step (required for VariableTransient).
        dt_max: Maximum time step (required for VariableTransient).
        jd: Desired iterations per step (required for VariableTransient).
        num_sublevels: Number of sublevels for analysis failure recovery.
        num_substeps: Number of substeps to try at each sublevel.

    Example:
        >>> from femora.components.analysis.analysis import Analysis
        >>> # Create analysis components first
        >>> # handler = analysis_manager.constraint.transformation()
        >>> # numberer = analysis_manager.numberer.rcm()
        >>> # system = analysis_manager.system.bandgeneral()
        >>> # algorithm = analysis_manager.algorithm.newton()
        >>> # test = analysis_manager.test.normunbalance(tol=1e-6, max_iter=100)
        >>> # integrator = analysis_manager.integrator.loadcontrol(incr=0.1)
        >>> # Create a static analysis
        >>> # analysis = Analysis(
        >>> #     name="PushoverAnalysis",
        >>> #     analysis_type="Static",
        >>> #     constraint_handler=handler,
        >>> #     numberer=numberer,
        >>> #     system=system,
        >>> #     algorithm=algorithm,
        >>> #     test=test,
        >>> #     integrator=integrator,
        >>> #     num_steps=10
        >>> # )
        >>> # print(analysis.tag)
    """
    def __init__(self, name: str, analysis_type: str, constraint_handler: ConstraintHandler,
                 numberer: Numberer, system: System, algorithm: Algorithm,
                 test: Test, integrator: Integrator, num_steps: Optional[int] = None,
                 final_time: Optional[float] = None, dt: Optional[float] = None,
                 dt_min: Optional[float] = None, dt_max: Optional[float] = None,
                 jd: Optional[int] = None, num_sublevels: Optional[int] = None,
                 num_substeps: Optional[int] = None):
        """Initializes the Analysis with all required components.

        This method validates component compatibility and analysis parameters
        before creating the analysis object.

        Args:
            name: Name of the analysis for identification. Must be unique.
            analysis_type: Type of analysis. Must be one of "Static", "Transient",
                or "VariableTransient".
            constraint_handler: The constraint handler for the analysis.
            numberer: The numberer for the analysis.
            system: The system solver for the analysis.
            algorithm: The solution algorithm for the analysis.
            test: The convergence test for the analysis.
            integrator: The integrator for the analysis. Must be compatible with
                analysis_type (StaticIntegrator for Static, TransientIntegrator
                for Transient/VariableTransient).
            num_steps: Number of analysis steps. Required for Static analysis,
                optional for others (mutually exclusive with final_time).
            final_time: Final time for analysis. Optional for Transient/VariableTransient
                (mutually exclusive with num_steps).
            dt: Time step increment. Required for Transient or VariableTransient analysis.
            dt_min: Minimum time step. Required for VariableTransient analysis.
            dt_max: Maximum time step. Required for VariableTransient analysis.
            jd: Number of iterations desired at each step. Required for
                VariableTransient analysis.
            num_sublevels: Number of sublevels in case of analysis failure. Optional,
                must be provided with num_substeps.
            num_substeps: Number of substeps to try at each sublevel. Optional,
                must be provided with num_sublevels.

        Raises:
            ValueError: If integrator type is incompatible with analysis type.
            ValueError: If analysis parameters are inconsistent with analysis type.
            ValueError: If analysis name is not unique.
            ValueError: If analysis_type is not one of the valid types.
        """
        super().__init__()
        self.name = name
        self.analysis_type = analysis_type

        # Validate analysis type
        if analysis_type not in ["Static", "Transient", "VariableTransient"]:
            raise ValueError(f"Unknown analysis type: {analysis_type}. Must be 'Static', 'Transient', or 'VariableTransient'.")

        # Set all components
        self.constraint_handler = constraint_handler
        self.numberer = numberer
        self.system = system
        self.algorithm = algorithm
        self.test = test

        # Validate integrator compatibility
        if analysis_type == "Static" and not isinstance(integrator, StaticIntegrator):
            raise ValueError(f"Static analysis requires a static integrator. {integrator.integrator_type} is not compatible.")

        elif analysis_type in ["Transient", "VariableTransient"] and not isinstance(integrator, TransientIntegrator):
            raise ValueError(f"Transient analysis requires a transient integrator. {integrator.integrator_type} is not compatible.")

        self.integrator = integrator

        # Validate and set analysis parameters
        if analysis_type == "Static":
            if num_steps is None:
                raise ValueError("Static analysis requires num_steps parameter.")
            if final_time is not None:
                raise ValueError("Static analysis does not use final_time parameter.")
        else:  # Transient or VariableTransient
            if num_steps is None and final_time is None:
                raise ValueError("Transient analysis requires either num_steps or final_time parameter.")
            if num_steps is not None and final_time is not None:
                raise ValueError("Only one of num_steps or final_time should be provided, not both.")

        self.num_steps = num_steps
        self.final_time = final_time

        # Time step parameters
        if analysis_type in ["Transient", "VariableTransient"] and dt is None:
            raise ValueError(f"{analysis_type} analysis requires a time step (dt).")

        self.dt = dt

        # VariableTransient specific parameters
        if analysis_type == "VariableTransient":
            if dt_min is None or dt_max is None:
                raise ValueError("VariableTransient analysis requires dt_min and dt_max parameters.")

            if jd is None:
                raise ValueError("VariableTransient analysis requires jd parameter (desired iterations per step).")

        self.dt_min = dt_min
        self.dt_max = dt_max
        self.jd = jd

        # Optional sublevel parameters (only applicable to Transient analyses)
        if analysis_type == "Static" and (num_sublevels is not None or num_substeps is not None):
            raise ValueError("num_sublevels and num_substeps are only applicable to Transient analysis.")

        if (num_sublevels is not None and num_substeps is None) or (num_sublevels is None and num_substeps is not None):
            raise ValueError("Both num_sublevels and num_substeps must be provided if either is specified.")

        self.num_sublevels = num_sublevels
        self.num_substeps = num_substeps

    def to_tcl(self) -> str:
        """Converts the analysis to a TCL command string for OpenSees.

        This method generates the complete TCL script for setting up and
        running the analysis, including all component definitions and the
        analysis loop.

        Returns:
            The TCL command string for all components and the analysis.

        """
        # Generate TCL commands for each component
        commands = []
        commands.append("if {$pid == 0} {" + f'puts [string repeat "=" 120] ' + "}")
        commands.append("if {$pid == 0} {" + f'puts "Starting analysis : {self.name}"' + "}")
        commands.append(commands[0])
        commands.append(self.constraint_handler.to_tcl())
        commands.append(self.numberer.to_tcl())
        commands.append(self.system.to_tcl())
        commands.append(self.algorithm.to_tcl())
        commands.append(self.test.to_tcl())
        commands.append(self.integrator.to_tcl())

        # Add analysis command
        commands.append(f"analysis {self.analysis_type}")

        # add analyze command with parameters
        if self.analysis_type == "Static":
            commands.append(f"analyze {self.num_steps}")
        elif self.analysis_type in ["Transient", "VariableTransient"]:
            if self.final_time is not None:
                commands.append("while {[getTime] < %f} {" % self.final_time)
                commands.append('\tif {$pid == 0} {puts "Time : [getTime]"}\n')
                commands.append(f"\tset Ok [analyze 1 {self.dt}]\n")
                commands.append("}")
            else:
                commands.append(f"set AnalysisStep 0")
                commands.append("while {"+f" $AnalysisStep < {self.num_steps}"+"} {")
                commands.append('\tif {$pid==0} {puts "$AnalysisStep' +f'/{self.num_steps}"' +"}")
                commands.append(f"\tset Ok [analyze 1 {self.dt}]")
                commands.append(f"\tincr AnalysisStep 1")
                commands.append("}")

        # wipe analysis command
        commands.append("wipeAnalysis")




        return "\n".join(commands)


__all__ = ["Analysis", "AnalysisManager"]


def __getattr__(name: str):
    if name == "AnalysisManager":
        from femora.core.analysis_manager import AnalysisManager

        return AnalysisManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
