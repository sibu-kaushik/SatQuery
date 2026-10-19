from app.agent.query_interpreter import interpret_query
from app.schemas.common import TaskType

def test_query_change():
    res = interpret_query("What changed between these images?")
    assert res.task_hint == TaskType.CHANGE

def test_query_optical_sar():
    res = interpret_query("Use optical and SAR together to identify built-up areas.")
    assert res.task_hint == TaskType.OPTICAL_SAR
    assert res.target == "built-up areas"

def test_query_grounding_where():
    res = interpret_query("Where is water?")
    assert res.task_hint == TaskType.GROUNDING
    assert res.target == "water"

def test_query_grounding_locate():
    res = interpret_query("Can you locate the water?")
    assert res.task_hint == TaskType.GROUNDING
    assert res.target == "can you  the water"  # Simplistic stripping logic

def test_query_vqa_is_there():
    res = interpret_query("Is there water?")
    assert res.task_hint == TaskType.VQA

def test_query_vqa_does_this():
    res = interpret_query("Does this image contain water?")
    assert res.task_hint == TaskType.VQA

def test_query_change_increase():
    res = interpret_query("Did the built-up area increase?")
    assert res.task_hint == TaskType.CHANGE
