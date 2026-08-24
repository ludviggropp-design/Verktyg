import json

from monitor.models import Mention
from monitor.state import State


def make_mention(url="https://example.com/a"):
    return Mention(source="google_news", category="redaktionellt", title="Titel", url=url)


def test_new_state_reports_everything_as_new(tmp_path):
    state = State(tmp_path)
    m = make_mention()
    assert state.is_new(m) is True


def test_marked_seen_persists_across_instances(tmp_path):
    state = State(tmp_path)
    m = make_mention()
    state.mark_seen([m])
    state.save()

    state2 = State(tmp_path)
    assert state2.is_new(m) is False


def test_append_log_writes_jsonl(tmp_path):
    state = State(tmp_path)
    m = make_mention()
    state.append_log([m])

    lines = state.log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["url"] == m.url
    assert "checked_at" in entry


def test_corrupt_seen_file_does_not_crash(tmp_path):
    (tmp_path / "seen.json").write_text("{not valid json", encoding="utf-8")
    state = State(tmp_path)
    assert state.is_new(make_mention()) is True
