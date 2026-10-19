from app.schemas.request import AnalysisRequest
from app.schemas.common import InputConfigType
from . import ValidationResult, ValidationErrorDetail

def validate_modalities(request: AnalysisRequest) -> ValidationResult:
    errors = []
    
    config_type = request.input_configuration.type
    
    # We assume modality is provided in input.metadata.get("modality")
    modalities = [inp.metadata.get("modality", "").upper() for inp in request.inputs]
    
    if config_type == InputConfigType.OPTICAL_SAR:
        if len(modalities) == 2:
            if "OPTICAL" not in modalities or "SAR" not in modalities:
                errors.append(ValidationErrorDetail(
                    code="MISSING_MODALITY",
                    message="OPTICAL_SAR configuration requires one OPTICAL and one SAR input."
                ))
    
    if config_type == InputConfigType.SINGLE_IMAGE:
        pass # Single image could be any modality, no strict pair enforcement needed here
        
    if config_type == InputConfigType.BI_TEMPORAL:
        pass # Bi-temporal typically assumes same modality or at least two valid inputs, checked by input_validator

    if errors:
        return ValidationResult.failure(errors)
    return ValidationResult.success()
