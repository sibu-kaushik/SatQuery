from app.schemas.request import AnalysisRequest
from app.schemas.common import InputConfigType
from . import ValidationResult, ValidationErrorDetail

def validate_compatibility(request: AnalysisRequest) -> ValidationResult:
    errors = []
    
    query = request.query.lower()
    config_type = request.input_configuration.type

    # E.g., Question: "What changed?" but Input: SINGLE_IMAGE
    if "change" in query and config_type not in [InputConfigType.BI_TEMPORAL]:
        errors.append(ValidationErrorDetail(
            code="TEMPORAL_PAIR_REQUIRED",
            message="Change detection queries require a BI_TEMPORAL input configuration."
        ))

    # E.g., Question: "Use optical and SAR together..." but Input: SINGLE_IMAGE
    if ("sar" in query and "optical" in query) and config_type != InputConfigType.OPTICAL_SAR:
        errors.append(ValidationErrorDetail(
            code="OPTICAL_SAR_PAIR_REQUIRED",
            message="Queries explicitly requesting optical and SAR require an OPTICAL_SAR input configuration."
        ))
        
    if errors:
        return ValidationResult.failure(errors)
    return ValidationResult.success()

def validate_request_full(request: AnalysisRequest) -> ValidationResult:
    from .input_validator import validate_request_basics
    from .modality_validator import validate_modalities
    
    res1 = validate_request_basics(request)
    if not res1.valid:
        return res1
        
    res2 = validate_modalities(request)
    if not res2.valid:
        return res2
        
    res3 = validate_compatibility(request)
    if not res3.valid:
        return res3
        
    return ValidationResult.success()
