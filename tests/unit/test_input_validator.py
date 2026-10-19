import pytest
from app.schemas.request import AnalysisRequest, InputConfiguration, InputItem
from app.schemas.common import InputConfigType
from app.validation.input_validator import validate_request_basics
from app.validation.compatibility import validate_request_full

def test_empty_query():
    req = AnalysisRequest(
        query="",
        inputs=[InputItem(url="t.tif", type="image/tiff")],
        input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE)
    )
    res = validate_request_basics(req)
    assert not res.valid
    assert res.errors[0].code == "EMPTY_QUERY"

def test_no_input():
    req = AnalysisRequest(
        query="water?",
        inputs=[],
        input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE)
    )
    res = validate_request_basics(req)
    assert not res.valid
    assert res.errors[0].code == "NO_INPUT"

def test_bitemporal_one_input():
    req = AnalysisRequest(
        query="change?",
        inputs=[InputItem(url="t.tif", type="image/tiff")],
        input_configuration=InputConfiguration(type=InputConfigType.BI_TEMPORAL)
    )
    res = validate_request_basics(req)
    assert not res.valid
    assert res.errors[0].code == "INVALID_INPUT_COUNT"

def test_optical_sar_one_input():
    req = AnalysisRequest(
        query="change?",
        inputs=[InputItem(url="t.tif", type="image/tiff")],
        input_configuration=InputConfiguration(type=InputConfigType.OPTICAL_SAR)
    )
    res = validate_request_basics(req)
    assert not res.valid
    assert res.errors[0].code == "INVALID_INPUT_COUNT"

def test_optical_sar_wrong_modalities():
    req = AnalysisRequest(
        query="test",
        inputs=[
            InputItem(url="1.tif", type="image/tiff", metadata={"modality": "OPTICAL"}),
            InputItem(url="2.tif", type="image/tiff", metadata={"modality": "OPTICAL"}),
        ],
        input_configuration=InputConfiguration(type=InputConfigType.OPTICAL_SAR)
    )
    res = validate_request_full(req)
    assert not res.valid
    assert res.errors[0].code == "MISSING_MODALITY"

def test_unsupported_format():
    req = AnalysisRequest(
        query="water?",
        inputs=[InputItem(url="t.doc", type="application/msword")],
        input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE)
    )
    res = validate_request_basics(req)
    assert not res.valid
    assert res.errors[0].code == "UNSUPPORTED_FORMAT"
