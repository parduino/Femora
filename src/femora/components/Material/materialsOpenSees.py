from typing import List, Dict
from .materialBase import Material, MaterialRegistry
from typing import Union


class ElasticIsotropicMaterial(Material):
    def __init__(self, user_name: str = "Unnamed", **kwargs):
        # validate the parameters
        kwargs = self.validate(**kwargs)
        super().__init__('nDMaterial', 'ElasticIsotropic', user_name)
        self.params = kwargs if kwargs else {}

    
    def to_tcl(self):
        param_order = self.get_parameters()
        params_str = " ".join(str(self.params[param]) for param in param_order if param in self.params)

        return f"{self.material_type} ElasticIsotropic {self.tag} {params_str}; # {self.user_name}"
    
    @staticmethod
    def validate(**params) -> Dict[str, Union[float, int, str, None]]:
        # Extract and validate E
        E = params.get("E")
        if E is None:
            raise ValueError("ElasticIsotropicMaterial requires the 'E' parameter.")
        try:
            E = float(E)
            if E <= 0:
                raise ValueError("Elastic modulus 'E' must be positive.")
        except (ValueError, TypeError):
            raise ValueError("Invalid value for 'E'. It must be a positive number.")

        # Extract and validate nu
        nu = params.get("nu")
        if nu is None:
            raise ValueError("ElasticIsotropicMaterial requires the 'nu' parameter.")
        try:
            nu = float(nu)
            if not (0 <= nu < 0.5):
                raise ValueError("Poisson's ratio 'nu' must be in the range [0, 0.5).")
        except (ValueError, TypeError):
            raise ValueError("Invalid value for 'nu'. It must be a number in range [0, 0.5).")

        # Extract and validate rho
        rho = params.get("rho", 0.0)
        try:
            rho = float(rho)
            if rho < 0:
                raise ValueError("Density 'rho' must be non-negative.")
        except (ValueError, TypeError):
            raise ValueError("Invalid value for 'rho'. It must be a non-negative number.")

        return {"E": E, "nu": nu, "rho": rho}
        
    @classmethod 
    def get_parameters(cls) -> List[str]:
        return ["E", "nu", "rho"]
    
    @classmethod
    def get_description(cls) -> List[str]:
        return ['Young\'s modulus', 
                'Poisson\'s ratio', 
                'Mass density of the material']
    


class ElasticUniaxialMaterial(Material):
    def __init__(self, user_name: str = "Unnamed", **kwargs):
        # validate the parameters
        kwargs = self.validate(**kwargs)
        super().__init__('uniaxialMaterial', 'Elastic', user_name)
        self.params = kwargs if kwargs else {}

    def to_tcl(self):
        param_order = self.get_parameters()
        params_str = " ".join(str(self.params[param]) for param in param_order if param in self.params)
        return f"{self.material_type} Elastic {self.tag} {params_str}; # {self.user_name}"
    
    @staticmethod
    def validate(**params) -> Dict[str, Union[float, int, str, None]]:
        # Extract and validate E
        E = params.get("E")
        if E is None:
            raise ValueError("ElasticUniaxialMaterial requires the 'E' parameter.")
        try:
            E = float(E)
            if E <= 0:
                raise ValueError("Elastic modulus 'E' must be positive.")
        except (ValueError, TypeError):
            raise ValueError("Invalid value for 'E'. It must be a positive number.")

        # Extract and validate eta
        eta = params.get("eta", 0.0)
        try:
            eta = float(eta)
            if eta < 0:
                raise ValueError("Damping ratio 'eta' must be non-negative.")
        except (ValueError, TypeError):
            raise ValueError("Invalid value for 'eta'. It must be a non-negative number.")

        # Extract and validate Eneg
        Eneg = params.get("Eneg", E)
        try:
            Eneg = float(Eneg)
            if Eneg <= 0:
                raise ValueError("Negative elastic modulus 'Eneg' must be positive.")
        except (ValueError, TypeError):
            raise ValueError("Invalid value for 'Eneg'. It must be a positive number.")

        return {"E": E, "eta": eta, "Eneg": Eneg}
        
    @classmethod 
    def get_parameters(cls) -> List[str]:
        return ["E", "eta", "Eneg"]
    
    @classmethod
    def get_description(cls) -> List[str]:
        return ['Tangent', 
                'Damping tangent (optional, default=0.0)',
                'Tangent in compression (optional, default=E)']
    




class J2CyclicBoundingSurfaceMaterial(Material):
    def __init__(self, user_name: str = "Unnamed", **kwargs):
        # validate parameters
        kwargs = self.validate(**kwargs)
        super().__init__('nDMaterial', 'J2CyclicBoundingSurface', user_name)
        self.params = kwargs if kwargs else {}

    def to_tcl(self):
        param_order = self.get_parameters()
        params_str = " ".join(str(self.params[param]) for param in param_order if param in self.params)
        return f"{self.material_type} J2CyclicBoundingSurface {self.tag} {params_str}; # {self.user_name}"
    
    @staticmethod
    def validate(**params) -> Dict[str, Union[float, int, str, None]]:
        required_params = ['G', 'K', 'Su', 'Den', 'h', 'm', 'h0', 'chi']
        validated_params = {}
        
        # Check required parameters
        for param in required_params:
            value = params.get(param)
            if value is None:
                raise ValueError(f"J2CyclicBoundingSurfaceMaterial requires the '{param}' parameter.")
            
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid value for '{param}'. It must be a number.")
            
            # Specific validations
            if param in ['G', 'K', 'Su'] and value <= 0:
                raise ValueError(f"'{param}' must be positive.")
            if param == 'Den' and value < 0:
                raise ValueError("Mass density 'Den' must be non-negative.")
            
            validated_params[param] = value
            
        # Optional parameter
        beta = params.get('beta', 0.5)  # Default value
        try:
            beta = float(beta)
            if not (0 <= beta <= 1):
                raise ValueError("Integration variable 'beta' must be in range [0, 1].")
        except (ValueError, TypeError):
            raise ValueError("Invalid value for 'beta'. It must be a number in range [0, 1].")
        
        validated_params['beta'] = beta
        
        return validated_params
    
    @classmethod
    def get_parameters(cls) -> List[str]:
        return ['G', 'K', 'Su', 'Den', 'h', 'm', 'h0', 'chi', 'beta']
    
    @classmethod
    def get_description(cls) -> List[str]:
        return ['Shear modulus', 
                'Bulk modulus',
                'Undrained shear strength',
                'Mass density',
                'Hardening parameter',
                'Hardening exponent',
                'Initial hardening parameter',
                'Initial damping (viscous). chi = 2*dr_o/omega (dr_o = damping ratio at zero strain, omega = angular frequency)',
                'Integration variable (0 = explicit, 1 = implicit, 0.5 = midpoint rule)']
    

    def updateMaterialStage(self, state: str)-> str:
        if state.lower() == 'elastic':
            return "updateMaterialStage -material {self.tag} -stage 0"
        elif state.lower() == 'plastic':
            return "updateMaterialStage -material {self.tag} -stage 1"
        else:
            return ""


class DruckerPragerMaterial(Material):
    def __init__(self, user_name: str = "Unnamed", **kwargs):
        # validate parameters
        kwargs = self.validate(**kwargs)
        super().__init__('nDMaterial', 'DruckerPrager', user_name)
        self.params = kwargs if kwargs else {}

    def to_tcl(self):
        param_order = self.get_parameters()
        params_str = " ".join(str(self.params[param]) for param in param_order if param in self.params)
        return f"{self.material_type} DruckerPrager {self.tag} {params_str}; # {self.user_name}"
    
    @staticmethod
    def validate(**params) -> Dict[str, Union[float, int, str, None]]:
        required_params = ['k', 'G', 'sigmaY', 'rho']
        validated_params = {}
        
        # Check required parameters
        for param in required_params:
            value = params.get(param)
            if value is None:
                raise ValueError(f"DruckerPragerMaterial requires the '{param}' parameter.")
            
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid value for '{param}'. It must be a number.")
            
            # Specific validations
            if param in ['k', 'G', 'sigmaY'] and value <= 0:
                raise ValueError(f"'{param}' must be positive.")
            
            validated_params[param] = value
        
        # Optional parameters with specific validations
        optional_params = {
            'rhoBar': {'default': validated_params['rho'], 'min': 0, 'max': validated_params['rho'], 
                      'message': "rhoBar must be in the range [0, rho]"},
            'Kinf': {'default': 0.0, 'min': 0, 'message': "Kinf must be non-negative"},
            'Ko': {'default': 0.0, 'min': 0, 'message': "Ko must be non-negative"},
            'delta1': {'default': 0.0, 'min': 0, 'message': "delta1 must be non-negative"},
            'delta2': {'default': 0.0, 'min': 0, 'message': "delta2 must be non-negative"},
            'H': {'default': 0.0, 'min': 0, 'message': "H must be non-negative"},
            'theta': {'default': 0.0, 'min': 0, 'max': 1, 'message': "theta must be in range [0, 1]"},
            'density': {'default': 0.0, 'min': 0, 'message': "density must be non-negative"},
            'atmPressure': {'default': 101.0, 'min': 0, 'message': "atmPressure must be non-negative"}
        }
        
        for param, constraints in optional_params.items():
            value = params.get(param, constraints['default'])
            try:
                value = float(value)
                if 'min' in constraints and value < constraints['min']:
                    raise ValueError(constraints['message'])
                if 'max' in constraints and value > constraints['max']:
                    raise ValueError(constraints['message'])
            except (ValueError, TypeError):
                raise ValueError(f"Invalid value for '{param}'. It must be a number.")
            
            validated_params[param] = value
        
        return validated_params

    @classmethod 
    def get_parameters(cls) -> List[str]:
        return ['k', 'G', 'sigmaY', 'rho', 'rhoBar', 'Kinf', 'Ko', 'delta1', 'delta2', 'H', 'theta', 'density', 'atmPressure']
    
    @classmethod
    def get_description(cls) -> List[str]:
        return ['Bulk modulus', 
                'Shear modulus',
                'Yield stress',
                'Frictional strength parameter',
                'Controls evolution of plastic volume change: 0 ≤ rhoBar ≤ rho',
                'Nonlinear isotropic strain hardening parameter: Kinf ≥ 0',
                'Nonlinear isotropic strain hardening parameter: Ko ≥ 0',
                'Nonlinear isotropic strain hardening parameter: delta1 ≥ 0',
                'Tension softening parameter: delta2 ≥ 0',
                'Linear strain hardening parameter: H ≥ 0',
                'Controls relative proportions of isotropic and kinematic hardening: 0 ≤ theta ≤ 1',
                'Mass density of the material',
                'Optional atmospheric pressure for update of elastic bulk and shear moduli (default = 101 kPa)']





class PressureDependMultiYieldMaterial(Material):
    """
    OpenSees nD material wrapper for PressureDependMultiYield.

    This material models pressure-sensitive soils with multi-surface (nested)
    plasticity, capturing dilatancy and cyclic mobility. It supports both 2D
    plane strain (nd=2) and 3D (nd=3) analyses.

    Features:
    - Elastic response during gravity/static phase; elastic-plastic in dynamic
      phase when switched via updateMaterialStage.
    - Drucker–Prager type yield surfaces with non-associative flow.
    - Automatic generation of yield surfaces or user-defined γ–Gs backbone.

    See: PressureDependMultiYield material (OpenSees Wiki).
    """
    def __init__(self, user_name: str = "Unnamed", **kwargs):
        """
        Initialize the material with required and optional parameters.

        Required parameters:
        - nd: 2 or 3. Number of spatial dimensions (2=plane strain, 3=3D)
        - rho: Saturated soil mass density
        - refShearModul (Gr): Reference low-strain shear modulus at refPress
        - refBulkModul (Br): Reference bulk modulus at refPress
        - frictionAng (Φ): Friction angle at peak strength, in degrees
        - peakShearStra (γmax): Octahedral shear strain at peak strength
        - refPress (p'r): Reference confining pressure
        - pressDependCoe: Pressure dependence coefficient
        - PTAng (ΦPT): Phase transformation angle, in degrees
        - contrac, dilat1, dilat2: Contraction and dilatancy parameters
        - liquefac1, liquefac2, liquefac3: Liquefaction parameters

        Yield surface definition:
        - noYieldSurf: Number of yield surfaces (< 40). If negative, provide
          'pairs' that define the shear modulus reduction backbone, either as
          a flat list [g1, Gs1, ..., gN, GsN] or a list of tuples
          [(g1, Gs1), ..., (gN, GsN)].

        Optional keyword tail (OpenSees keyword style):
        - e (default 0.6), cs1 (0.9), cs2 (0.02), cs3 (0.7), pa (101.0), c (0.3)

        Raises:
        - ValueError: If any parameter is invalid or inconsistent
        """
        # validate parameters
        kwargs = self.validate(**kwargs)
        super().__init__('nDMaterial', 'PressureDependMultiYield', user_name)
        self.params = kwargs if kwargs else {}

    def to_tcl(self):
        """
        Convert the material to its OpenSees TCL command string.

        Format:
        nDMaterial PressureDependMultiYield tag nd rho Gr Br frictionAng peakShearStra \
          refPress pressDependCoe PTAng contrac dilat1 dilat2 liquefac1 liquefac2 liquefac3 \
          noYieldSurf=<N| -N> [gamma1 Gs1 ... gammaN GsN] \
          e=<val> cs1=<val> cs2=<val> cs3=<val> pa=<val> c=<val>

        Notes:
        - When noYieldSurf is negative, exactly |noYieldSurf| (γ, Gs) pairs must
          be provided and are appended after the noYieldSurf token.

        Returns:
        - str: Complete TCL command with trailing comment of the user_name
        """
        p = self.params
        # Required portion (without user-defined backbone pairs)
        parts = [
            self.material_type,
            'PressureDependMultiYield',
            str(self.tag),
            str(int(p['nd'])),
            str(p['rho']),
            str(p['refShearModul']),
            str(p['refBulkModul']),
            str(p['frictionAng']),
            str(p['peakShearStra']),
            str(p['refPress']),
            str(p['pressDependCoe']),
            str(p['PTAng']),
            str(p['contrac']),
            str(p['dilat1']),
            str(p['dilat2']),
            str(p['liquefac1']),
            str(p['liquefac2']),
            str(p['liquefac3'])
        ]

        # Optional: number of yield surfaces and optional custom backbone pairs
        no_yield = int(p.get('noYieldSurf', 20))
        parts.append(str(no_yield))

        if no_yield < 0:
            pairs = p.get('pairs', [])
            for gamma, gs in pairs:
                parts.append(str(gamma))
                parts.append(str(gs))

        # Optional critical state and atmospheric pressure parameters
        parts.extend([
            str(p['e']),
            str(p['cs1']),
            str(p['cs2']),
            str(p['cs3']),
            str(p['pa']),
            str(p['c'])
        ])

        return " ".join(parts) + f"; # {self.user_name}"

    @staticmethod
    def validate(**params) -> Dict[str, Union[float, int, str, None]]:
        """
        Validate and normalize input parameters.

        - Coerces numeric fields to proper types
        - Checks dimensions, positivity, and ranges (e.g., angles in [0, 90])
        - Validates noYieldSurf and optional 'pairs' structure when negative
        - Applies defaults for e, cs1, cs2, cs3, pa, c

        When noYieldSurf < 0, 'pairs' may be either a flat list [g1, Gs1, ...]
        or a list of tuples [(g1, Gs1), ...].

        Returns:
        - dict: Validated parameters ready for serialization

        Raises:
        - ValueError: On missing params, type issues, range violations, or
          mismatched/invalid backbone pairs
        """
        validated: Dict[str, Union[float, int]] = {}

        # Required parameters
        required = [
            'nd', 'rho', 'refShearModul', 'refBulkModul', 'frictionAng',
            'peakShearStra', 'refPress', 'pressDependCoe', 'PTAng',
            'contrac', 'dilat1', 'dilat2', 'liquefac1', 'liquefac2', 'liquefac3'
        ]

        for key in required:
            value = params.get(key)
            if value is None:
                raise ValueError(f"PressureDependMultiYield requires the '{key}' parameter.")
            try:
                if key == 'nd':
                    value = int(value)
                else:
                    value = float(value)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid value for '{key}'. It must be numeric.")

            # Basic constraints
            if key == 'nd' and value not in (2, 3):
                raise ValueError("'nd' must be 2 (plane strain) or 3 (3D).")
            if key in ['rho', 'refShearModul', 'refBulkModul'] and float(value) <= 0:
                raise ValueError(f"'{key}' must be positive.")
            if key in ['frictionAng', 'PTAng'] and not (0 <= float(value) <= 90):
                raise ValueError(f"'{key}' must be in degrees within [0, 90].")
            if key == 'pressDependCoe' and float(value) < 0:
                raise ValueError("'pressDependCoe' must be non-negative.")
            if key == 'peakShearStra' and float(value) <= 0:
                raise ValueError("'peakShearStra' must be positive.")

            validated[key] = value

        # Optional noYieldSurf and optional custom backbone pairs
        no_yield = params.get('noYieldSurf', 20)
        try:
            no_yield_int = int(no_yield)
        except (ValueError, TypeError):
            raise ValueError("'noYieldSurf' must be an integer.")
        if no_yield_int == 0 or abs(no_yield_int) >= 40:
            raise ValueError("'noYieldSurf' must be non-zero and less than 40 in magnitude.")
        validated['noYieldSurf'] = no_yield_int

        if no_yield_int < 0:
            expected_pairs = abs(no_yield_int)
            pairs_param = params.get('pairs', None)
            if pairs_param is None:
                raise ValueError("When 'noYieldSurf' is negative, provide 'pairs' as a list of (gamma, Gs) or a flat list of length 2N.")

            pairs_list = []
            if isinstance(pairs_param, list):
                # flat list [g1, Gs1, g2, Gs2, ...]
                if len(pairs_param) == 2 * expected_pairs and all(isinstance(x, (int, float)) for x in pairs_param):
                    it = iter(pairs_param)
                    pairs_list = [(float(g), float(gs)) for g, gs in zip(it, it)]
                else:
                    # list of tuples
                    try:
                        pairs_list = [(float(g), float(gs)) for g, gs in pairs_param]
                    except Exception:
                        raise ValueError("'pairs' must be a list of (gamma, Gs) or a flat list of numeric values of length 2N.")
            else:
                raise ValueError("'pairs' must be provided as a list.")

            if len(pairs_list) != expected_pairs:
                raise ValueError(f"Expected {expected_pairs} (gamma, Gs) pairs, got {len(pairs_list)}.")

            for g, gs in pairs_list:
                if g <= 0:
                    raise ValueError("Each gamma must be positive.")
                if not (0 < gs <= 1.0):
                    raise ValueError("Each Gs must be in (0, 1].")

            validated['pairs'] = pairs_list

        # Optional parameters with defaults from OpenSees wiki
        optionals = {
            'e': 0.6,
            'cs1': 0.9,
            'cs2': 0.02,
            'cs3': 0.7,
            'pa': 101.0,
            'c': 0.3,
        }
        for key, default in optionals.items():
            value = params.get(key, default)
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid value for '{key}'. It must be numeric.")

            # Basic constraints
            if key in ['e', 'cs1', 'cs2', 'cs3'] and value < 0:
                raise ValueError(f"'{key}' must be non-negative.")
            if key == 'pa' and value <= 0:
                raise ValueError("'pa' must be positive.")
            if key == 'c' and value < 0:
                raise ValueError("'c' must be non-negative.")

            validated[key] = value

        return validated

    @classmethod
    def get_parameters(cls) -> List[str]:
        """
        Parameter keys for GUI/registry.

        Note: 'pairs' applies only when 'noYieldSurf' is negative and allows
        user-defined backbone input in either flat or tuple-list form.
        """
        return [
            'nd', 'rho', 'refShearModul', 'refBulkModul', 'frictionAng',
            'peakShearStra', 'refPress', 'pressDependCoe', 'PTAng',
            'contrac', 'dilat1', 'dilat2', 'liquefac1', 'liquefac2', 'liquefac3', 'noYieldSurf', 'pairs',
            'e', 'cs1', 'cs2', 'cs3', 'pa', 'c'
        ]

    @classmethod
    def get_description(cls) -> List[str]:
        """
        Human-readable descriptions for parameters returned by get_parameters().
        """
        return [
            'Number of dimensions (2 for plane strain, 3 for 3D)',
            'Saturated soil mass density',
            'Reference low-strain shear modulus Gr at refPress',
            'Reference bulk modulus Br at refPress',
            'Friction angle at peak shear strength Φ (degrees)',
            'Octahedral shear strain γmax at peak strength at refPress',
            'Reference mean effective confining pressure p\'r (kPa)',
            'Pressure dependence coefficient',
            'Phase transformation angle ΦPT (degrees)',
            'Contraction parameter',
            'First dilatancy parameter',
            'Second dilatancy parameter',
            'Liquefaction parameter 1',
            'Liquefaction parameter 2',
            'Liquefaction parameter 3',
            'Number of yield surfaces (<40). Use negative with programmatic "pairs" to define γ-Gs backbone',
            'Pairs of γ-Gs backbone',
            'Void ratio e (default 0.6)',
            'Critical state parameter cs1 (default 0.9)',
            'Critical state parameter cs2 (default 0.02)',
            'Critical state parameter cs3 (default 0.7)',
            'Atmospheric pressure pa (kPa, default 101)',
            'Cohesion intercept c (default 0.3)'
        ]

    def updateMaterialStage(self, state: str) -> str:
        """
        Build an OpenSees updateMaterialStage command for this material.

        Parameters:
        - state: 'elastic' -> stage 0; 'plastic' -> stage 1. Any other value
          returns an empty string.

        Returns:
        - str: Command or empty string if state is unrecognized
        """
        if state.lower() == 'elastic':
            return f"updateMaterialStage -material {self.tag} -stage 0"
        elif state.lower() == 'plastic':
            return f"updateMaterialStage -material {self.tag} -stage 1"
        else:
            return ""


# Register material types
MaterialRegistry.register_material_type('nDMaterial', 'ElasticIsotropic', ElasticIsotropicMaterial)
MaterialRegistry.register_material_type('uniaxialMaterial', 'Elastic', ElasticUniaxialMaterial)
MaterialRegistry.register_material_type('nDMaterial', 'J2CyclicBoundingSurface', J2CyclicBoundingSurfaceMaterial)
MaterialRegistry.register_material_type('nDMaterial', 'DruckerPrager', DruckerPragerMaterial)
MaterialRegistry.register_material_type('nDMaterial', 'PressureDependMultiYield', PressureDependMultiYieldMaterial)


class Steel01Material(Material):
    """
    OpenSees uniaxial bilinear steel model (Steel01) with kinematic hardening
    and optional isotropic hardening parameters.

    Reference: OpenSees Wiki – Steel01 Material
    https://opensees.berkeley.edu/wiki/index.php/Steel01_Material
    
    parameters:
        Fy: Yield strength
        E0: Initial elastic tangent
        b: Strain-hardening ratio (post-yield tangent / E0)
        a1, a2: Compression envelope growth parameters
        a3, a4: Tension envelope growth parameters
        If any of a1..a4 is provided, all four must be provided. If none are provided, the TCL output will not include these optional arguments.
    """

    def __init__(self, user_name: str = "Unnamed", **kwargs):
        """
        Initialize Steel01.

        Required parameters:
        - Fy: Yield strength
        - E0: Initial elastic tangent
        - b: Strain-hardening ratio (post-yield tangent / E0)

        Optional isotropic hardening parameters (all-or-none):
        - a1, a2: Compression envelope growth parameters
        - a3, a4: Tension envelope growth parameters
        If any of a1..a4 is provided, all four must be provided. If none are
        provided, the TCL output will not include these optional arguments.

        Raises:
        - ValueError for missing/invalid inputs
        """
        kwargs = self.validate(**kwargs)
        super().__init__('uniaxialMaterial', 'Steel01', user_name)
        self.params = kwargs if kwargs else {}

    def to_tcl(self) -> str:
        """
        Render the OpenSees TCL command for this Steel01 material.

        Format:
        - Without isotropic hardening:
          uniaxialMaterial Steel01 tag Fy E0 b
        - With isotropic hardening (all four provided):
          uniaxialMaterial Steel01 tag Fy E0 b a1 a2 a3 a4
        """
        p = self.params
        ordered = [
            self.material_type,
            'Steel01',
            str(self.tag),
            str(p['Fy']),
            str(p['E0']),
            str(p['b']),
        ]
        # Append isotropic hardening params only if user provided all four
        if all(k in p for k in ['a1', 'a2', 'a3', 'a4']):
            ordered.extend([
                str(p['a1']),
                str(p['a2']),
                str(p['a3']),
                str(p['a4']),
            ])
        return " ".join(ordered) + f"; # {self.user_name}"

    @staticmethod
    def validate(**params) -> Dict[str, Union[float, int, str, None]]:
        """
        Validate parameters for Steel01.
        - Fy, E0 must be positive
        - b must be >= 0
        - a1..a4: either all provided or none; when provided, each must be >= 0
        """
        validated: Dict[str, Union[float, int]] = {}

        # Required
        for key in ['Fy', 'E0', 'b']:
            value = params.get(key)
            if value is None:
                raise ValueError(f"Steel01 requires '{key}'.")
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid value for '{key}'. Must be numeric.")
            if key in ['Fy', 'E0'] and value <= 0:
                raise ValueError(f"'{key}' must be positive.")
            if key == 'b' and value < 0:
                raise ValueError("'b' must be non-negative.")
            validated[key] = value

        # Optional isotropic hardening params a1..a4: require all or none
        provided_keys = [k for k in ['a1', 'a2', 'a3', 'a4'] if k in params]
        if len(provided_keys) not in (0, 4):
            raise ValueError("If specifying isotropic parameters, provide all of a1, a2, a3, a4.")
        if len(provided_keys) == 4:
            for key in ['a1', 'a2', 'a3', 'a4']:
                value = params.get(key)
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid value for '{key}'. Must be numeric.")
                if value < 0:
                    raise ValueError(f"'{key}' must be non-negative.")
                validated[key] = value

        return validated

    @classmethod
    def get_parameters(cls) -> List[str]:
        return ['Fy', 'E0', 'b', 'a1', 'a2', 'a3', 'a4']

    @classmethod
    def get_description(cls) -> List[str]:
        return [
            'Yield strength Fy',
            'Initial elastic tangent E0',
            'Strain-hardening ratio b (post-yield tangent / E0)',
            'Isotropic hardening: compression envelope growth a1',
            'Isotropic hardening parameter a2',
            'Isotropic hardening: tension envelope growth a3',
            'Isotropic hardening parameter a4',
        ]


# Register Steel01
MaterialRegistry.register_material_type('uniaxialMaterial', 'Steel01', Steel01Material)