from app.schemas.request import AnalysisRequest, InputConfiguration, InputItem
from app.schemas.common import TaskType, InputConfigType
from app.specialists.test_doubles.vqa import TestVQASpecialist
from app.specialists.test_doubles.grounding import TestGroundingSpecialist
from app.specialists.test_doubles.change import TestChangeSpecialist
from app.specialists.test_doubles.optical_sar import TestOpticalSARSpecialist
from tests.contracts.test_generic_specialist_contract import run_specialist_contract_tests

def test_vqa_contract():
    specialist = TestVQASpecialist()
    req = AnalysisRequest(
        query="Is there water?",
        input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE),
        inputs=[InputItem(url="test.tif", type="image/tiff")]
    )
    assert run_specialist_contract_tests(specialist, TaskType.VQA, req)

def test_grounding_contract():
    specialist = TestGroundingSpecialist()
    req = AnalysisRequest(
        query="Where is the water?",
        input_configuration=InputConfiguration(type=InputConfigType.SINGLE_IMAGE),
        inputs=[InputItem(url="test.tif", type="image/tiff")]
    )
    assert run_specialist_contract_tests(specialist, TaskType.GROUNDING, req)

def test_change_contract():
    specialist = TestChangeSpecialist()
    req = AnalysisRequest(
        query="What changed?",
        input_configuration=InputConfiguration(type=InputConfigType.BI_TEMPORAL),
        inputs=[
            InputItem(url="t1.tif", type="image/tiff"),
            InputItem(url="t2.tif", type="image/tiff")
        ]
    )
    assert run_specialist_contract_tests(specialist, TaskType.CHANGE, req)

def test_optical_sar_contract():
    specialist = TestOpticalSARSpecialist()
    req = AnalysisRequest(
        query="Find buildings using SAR and optical.",
        input_configuration=InputConfiguration(type=InputConfigType.OPTICAL_SAR),
        inputs=[
            InputItem(url="opt.tif", type="image/tiff"),
            InputItem(url="sar.tif", type="image/tiff")
        ]
    )
    assert run_specialist_contract_tests(specialist, TaskType.OPTICAL_SAR, req)
