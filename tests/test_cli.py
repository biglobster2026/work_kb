from work_kb.cli import main
from work_kb.store import Store


def test_add_build_validate_stats_flow(tmp_path, capsys):
    root = str(tmp_path)
    assert main(["--root", root, "add", "--tier", "foundation", "--title", "Mission"]) == 0
    assert (
        main(
            ["--root", root, "add", "--tier", "detail", "--title", "Auth jitter", "--tags", "auth"]
        )
        == 0
    )
    assert main(["--root", root, "build"]) == 0
    assert (tmp_path / ".github" / "copilot-instructions.md").exists()
    assert (tmp_path / "kb" / "00-foundation" / "INDEX.md").exists()
    assert (tmp_path / "kb" / "10-details" / "by-tag" / "auth.md").exists()

    assert main(["--root", root, "validate"]) == 0
    assert main(["--root", root, "stats"]) == 0
    out = capsys.readouterr().out
    assert "2 items total" in out


def test_add_rejects_duplicate_slug(tmp_path, capsys):
    root = str(tmp_path)
    main(["--root", root, "add", "--tier", "detail", "--title", "Dup"])
    rc = main(["--root", root, "add", "--tier", "detail", "--title", "Dup"])
    assert rc == 1
    assert "already exists" in capsys.readouterr().err


def test_promote_moves_tier(tmp_path, capsys):
    root = str(tmp_path)
    main(["--root", root, "add", "--tier", "detail", "--title", "Rising star"])
    assert main(["--root", root, "promote", "rising-star", "--to", "foundation"]) == 0
    item, _ = Store(tmp_path).find("rising-star")
    assert item.tier.value == "foundation"


def test_validate_nonzero_on_error(tmp_path):
    root = str(tmp_path)
    store = Store(tmp_path)
    from work_kb.models import Item, Tier

    store.write_item(Item(slug="a", tier=Tier.DETAIL, title="A", links=["ghost"]))
    assert main(["--root", root, "validate"]) == 1


def test_pack_writes_context_file(tmp_path):
    root = str(tmp_path)
    main(["--root", root, "add", "--tier", "detail", "--title", "Auth jitter", "--body", "jitter"])
    out_file = tmp_path / "CONTEXT.md"
    assert main(["--root", root, "pack", "jitter", "--out", str(out_file)]) == 0
    assert "Auth jitter" in out_file.read_text(encoding="utf-8")
