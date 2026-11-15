"""第3回宿題: TestModel で承認前・承認後・拒否時の副作用を検証する。"""

import json
import sys

import pytest
from pydantic_ai import DeferredToolRequests, DeferredToolResults
from pydantic_ai.messages import ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import agent as agent_module, tools


@pytest.fixture
def log_dir(tmp_path, monkeypatch):
    path = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", path)
    return path


def start_save():
    model = TestModel(call_tools=["save_learning_log"])
    result = agent_module.agent.run_sync("今日の学習を記録して", model=model)
    assert isinstance(result.output, DeferredToolRequests)
    assert len(result.output.approvals) == 1
    assert result.output.approvals[0].tool_name == "save_learning_log"
    return model, result


def resume_save(model, result, approved):
    call = result.output.approvals[0]
    return agent_module.agent.run_sync(
        model=model,
        message_history=result.all_messages(),
        deferred_tool_results=DeferredToolResults(approvals={call.tool_call_id: approved}),
    )


def test_save_waits_for_approval(log_dir):
    start_save()
    assert not log_dir.exists()


def test_approval_saves_exactly_the_displayed_content(log_dir):
    model, result = start_save()
    expected = result.output.approvals[0].args_as_dict()
    result = resume_save(model, result, True)
    files = list(log_dir.glob("*.json"))
    assert len(files) == 1
    record = json.loads(files[0].read_text(encoding="utf-8"))
    assert record["topic"] == expected["topic"]
    assert record["content"] == expected["content"]
    assert record["created_at"]
    assert isinstance(result.output, str)
    assert "保存しました" in result.output


@pytest.mark.parametrize("existing", [False, True])
def test_denial_never_creates_or_changes_files(log_dir, existing):
    if existing:
        log_dir.mkdir()
        (log_dir / "previous.json").write_bytes(b"keep this record\n")
    before = {p.name: p.read_bytes() for p in log_dir.glob("*")}
    model, result = start_save()
    result = resume_save(model, result, False)
    assert {p.name: p.read_bytes() for p in log_dir.glob("*")} == before
    assert log_dir.exists() == existing
    returns = [
        p for m in result.all_messages() for p in m.parts
        if isinstance(p, ToolReturnPart) and p.tool_name == "save_learning_log"
    ]
    assert len(returns) == 1
    assert "denied" in str(returns[0].content).lower()


def test_saving_twice_preserves_previous_record_and_japanese(log_dir):
    tools.save_learning_log("LoRA", "低ランクの行列を学習する。")
    original = {p.name: p.read_bytes() for p in log_dir.glob("*")}
    tools.save_learning_log("../同じ名前", "量子化も復習した。")
    assert len(list(log_dir.glob("*.json"))) == 2
    for name, content in original.items():
        assert (log_dir / name).read_bytes() == content
        assert json.loads(content)["content"] == "低ランクの行列を学習する。"


@pytest.mark.parametrize(
    "response,approved",
    [("y", True), (" Y ", True), ("n", False), ("", False), ("yes", False), ("unexpected", False)],
)
def test_cli_approves_only_explicit_y(log_dir, monkeypatch, capsys, response, approved):
    monkeypatch.setattr(sys, "argv", ["app.agent", "--trace", "学習を記録して"])
    monkeypatch.setattr(agent_module, "build_model", lambda: TestModel(call_tools=["save_learning_log"]))

    def answer(prompt):
        print(prompt)
        assert not log_dir.exists()  # 確認画面が出た時点では未保存
        return response

    monkeypatch.setattr("builtins.input", answer)
    agent_module.main()
    output = capsys.readouterr().out
    assert "[承認待ち] save_learning_log" in output
    assert '"topic"' in output and '"content"' in output
    assert "[tool call]" in output and "[tool return]" in output
    assert len(list(log_dir.glob("*.json"))) == (1 if approved else 0)
    assert ("[承認]" if approved else "[拒否]") in output


@pytest.mark.parametrize("error", [EOFError, KeyboardInterrupt])
def test_cli_input_end_or_interrupt_denies_save(log_dir, monkeypatch, capsys, error):
    monkeypatch.setattr(sys, "argv", ["app.agent", "学習を記録して"])
    monkeypatch.setattr(agent_module, "build_model", lambda: TestModel(call_tools=["save_learning_log"]))

    def interrupted(prompt):
        raise error

    monkeypatch.setattr("builtins.input", interrupted)
    agent_module.main()
    assert not log_dir.exists()
    assert "[拒否]" in capsys.readouterr().out


def test_each_pending_save_requires_its_own_decision(log_dir, monkeypatch):
    model = TestModel(call_tools=["save_learning_log", "save_learning_log"])
    result = agent_module.agent.run_sync("2件記録して", model=model)
    assert isinstance(result.output, DeferredToolRequests)
    assert len(result.output.approvals) == 2
    assert not log_dir.exists()
    answers = iter(["y", "n"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    result = agent_module.resolve_approvals(agent_module.agent, result, model)
    assert isinstance(result.output, str)
    assert len(list(log_dir.glob("*.json"))) == 1
