from app.schemas.request import AnalysisRequest
from app.schemas.common import InputConfigType
from . import ValidationResult, ValidationErrorDetail

def validate_request_basics(request: AnalysisRequest) -> ValidationResult:
    errors = []

    # A. Query validity
    if not request.query or not request.query.strip():
        errors.append(ValidationErrorDetail(code="EMPTY_QUERY", message="Query cannot be empty."))

    # B. Input count
    num_inputs = len(request.inputs)
    if num_inputs == 0:
        errors.append(ValidationErrorDetail(code="NO_INPUT", message="At least one input is required."))
    else:
        config_type = request.input_configuration.type
        if config_type == InputConfigType.SINGLE_IMAGE and num_inputs != 1:
            errors.append(ValidationErrorDetail(
                code="INVALID_INPUT_COUNT", 
                message="SINGLE_IMAGE configuration requires exactly one input."
            ))
        elif config_type == InputConfigType.BI_TEMPORAL and num_inputs != 2:
            errors.append(ValidationErrorDetail(
                code="INVALID_INPUT_COUNT", 
                message="BI_TEMPORAL configuration requires exactly two inputs."
            ))
        elif config_type == InputConfigType.OPTICAL_SAR and num_inputs != 2:
            errors.append(ValidationErrorDetail(
                code="INVALID_INPUT_COUNT", 
                message="OPTICAL_SAR configuration requires exactly two inputs."
            ))

    # D. File format
    # Simple check for format support based on extension/type
    supported_formats = ["image/tiff", "image/png", "image/jpeg"]
    for i, inp in enumerate(request.inputs):
        if inp.type not in supported_formats:
            errors.append(ValidationErrorDetail(
                code="UNSUPPORTED_FORMAT",
                message=f"Input {i} has unsupported format: {inp.type}"
            ))

    if errors:
        return ValidationResult.failure(errors)
    return ValidationResult.success()
