"""Controllers package."""
from .patient_controller import patient_bp
from .doctor_controller  import doctor_bp

__all__ = ["patient_bp", "doctor_bp"]
