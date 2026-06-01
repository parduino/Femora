"""---
icon: material/calculator
---

Analysis components for Femora.

This package contains the concrete runtime pieces used to assemble an OpenSees
analysis stack. Together, these components define how a structural simulation
enforces equilibrium, orders equations, solves the linear system, checks
convergence, and advances through load or time steps. In OpenSees, an
"analysis" is not a single solver switch. It is a coordinated stack of
decisions about constraint enforcement, degree-of-freedom numbering, linear
system solution, nonlinear iteration strategy, convergence criteria, and the
static or transient stepping rule used to advance the model.

Normal runtime usage is centered on `model.analysis`. Users build the required
analysis stack through its sub-managers, then create a registered static or
transient analysis directly through the analysis manager. This is the
highest-level Femora representation of an OpenSees analysis setup: the full
stack is captured as one `Analysis` object that can be named, stored, reused,
and added to a process as a single step.

Femora also allows the same OpenSees analysis stack to be expressed more
explicitly at the process level. In that lower-level style, the user pushes the
individual stack components into `model.process` and then adds the final Tcl
execution step manually. Both styles represent the same OpenSees idea. The
difference is only whether the stack is managed as one analysis object or
spelled out step by step in the process sequence.

!!! example "Full analysis object workflow"

    ```python
    from femora.core.model import Model

    model = Model()

    handler = model.analysis.constraint.transformation()
    numberer = model.analysis.numberer.rcm()
    system = model.analysis.system.bandgeneral()
    algorithm = model.analysis.algorithm.newton()
    test = model.analysis.test.normunbalance(tol=1e-6, max_iter=100)
    integrator = model.analysis.integrator.loadcontrol(incr=0.1)

    analysis = model.analysis.static(
        name="pushover",
        constraint_handler=handler,
        numberer=numberer,
        system=system,
        algorithm=algorithm,
        test=test,
        integrator=integrator,
        num_steps=10,
    )

    model.process.add_step(analysis, description="run pushover analysis")
    ```

!!! tip "Equivalent low-level process workflow"

    ```python
    from femora.core.model import Model

    model = Model()

    handler = model.analysis.constraint.transformation()
    numberer = model.analysis.numberer.rcm()
    system = model.analysis.system.bandgeneral()
    algorithm = model.analysis.algorithm.newton()
    test = model.analysis.test.normunbalance(tol=1e-6, max_iter=100)
    integrator = model.analysis.integrator.loadcontrol(incr=0.1)

    model.process.add_step(handler, description="configure constraints")
    model.process.add_step(numberer, description="configure DOF numbering")
    model.process.add_step(system, description="configure linear solver")
    model.process.add_step(algorithm, description="configure nonlinear algorithm")
    model.process.add_step(test, description="configure convergence test")
    model.process.add_step(integrator, description="configure integrator")
    model.process.add_step(
        model.actions.tcl(command="analysis Static"),
        description="select static analysis type",
    )
    model.process.add_step(
        model.actions.tcl(command="analyze 10"),
        description="run 10 static analysis steps",
    )
    model.process.add_step(
        model.actions.wipe_analysis(),
        description="clear the active OpenSees analysis stack",
    )
    ```
"""
