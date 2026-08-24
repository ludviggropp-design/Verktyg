from monitor import main
from monitor.models import Mention


def fake_source(search_term):
    return [
        Mention(source="fake", category="redaktionellt", title="Träff 1", url="https://example.com/1"),
        Mention(source="fake", category="socialt", title="Träff 2", url="https://example.com/2"),
    ]


def test_run_reports_new_then_nothing_on_second_run(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "SOURCE_REGISTRY", {"fake": fake_source})

    args = main.parse_args(["--sources", "fake", "--data-dir", str(tmp_path)])
    first = main.run(args)
    assert len(first) == 2

    second = main.run(args)
    assert second == []


def test_run_include_seen_bypasses_dedup(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "SOURCE_REGISTRY", {"fake": fake_source})

    args = main.parse_args(["--sources", "fake", "--data-dir", str(tmp_path)])
    main.run(args)

    args_include = main.parse_args(
        ["--sources", "fake", "--data-dir", str(tmp_path), "--include-seen"]
    )
    again = main.run(args_include)
    assert len(again) == 2


def test_run_rejects_unknown_source(tmp_path):
    args = main.parse_args(["--sources", "does_not_exist", "--data-dir", str(tmp_path)])
    try:
        main.run(args)
        assert False, "förväntade SystemExit"
    except SystemExit as exc:
        assert "does_not_exist" in str(exc)


def test_run_continues_when_one_source_fails(tmp_path, monkeypatch):
    def broken_source(search_term):
        raise RuntimeError("nätverksfel")

    monkeypatch.setattr(
        main, "SOURCE_REGISTRY", {"broken": broken_source, "fake": fake_source}
    )

    args = main.parse_args(
        ["--sources", "broken,fake", "--data-dir", str(tmp_path)]
    )
    mentions = main.run(args)
    assert len(mentions) == 2
