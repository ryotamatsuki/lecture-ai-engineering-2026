"""第3回演習: 用語集に対応した復習問題とツール登録を検証する。"""

import json

import pytest
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import tools
from app.agent import agent


@pytest.mark.parametrize("lecture", sorted({e["lecture"] for e in tools.load_glossary()}))
def test_quiz_uses_a_term_and_definition_from_requested_lecture(lecture):
    quiz = json.loads(tools.make_quiz(lecture))
    candidates = [e for e in tools.load_glossary() if e["lecture"] == lecture]
    assert any(
        e["term"] in quiz["question"] and e["definition"] == quiz["answer"]
        for e in candidates
    )


@pytest.mark.parametrize("lecture", [0, -1, 99])
def test_unknown_lecture_returns_guidance_without_crashing(lecture):
    quiz = json.loads(tools.make_quiz(lecture))
    assert quiz["question"] == quiz["answer"] == ""
    assert f"第{lecture}回" in quiz["message"]


def test_quiz_is_offered_called_and_returned_to_model():
    model = TestModel(call_tools=["make_quiz"])
    result = agent.run_sync("第2回の確認問題を出して", model=model)
    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert {"make_quiz", "save_learning_log"} <= offered
    parts = [p for m in result.all_messages() for p in m.parts]
    assert any(isinstance(p, ToolCallPart) and p.tool_name == "make_quiz" for p in parts)
    returned = [p for p in parts if isinstance(p, ToolReturnPart) and p.tool_name == "make_quiz"]
    assert len(returned) == 1
    assert {"question", "answer"} <= json.loads(returned[0].content).keys()
