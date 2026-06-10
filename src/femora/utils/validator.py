# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from qtpy.QtGui import QDoubleValidator, QIntValidator



class DoubleValidator(QDoubleValidator):
    def validate(self, input_string, pos):
        if ',' in input_string:
            return (QDoubleValidator.Invalid, input_string, pos)
        return super().validate(input_string, pos)
    
class IntValidator(QIntValidator):
    def validate(self, input_string, pos):
        if ',' in input_string or input_string.startswith('0'):
            return (QIntValidator.Invalid, input_string, pos)
        return super().validate(input_string, pos)
    
class PositiveDoubleValidator(QDoubleValidator):
    def validate(self, input_string, pos):
        if ',' in input_string or float(input_string) <= 0:
            return (QDoubleValidator.Invalid, input_string, pos)
        return super().validate(input_string, pos)