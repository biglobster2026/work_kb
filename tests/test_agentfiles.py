"""Tests for the multi-agent instruction-file renderers. Pure string output, so
we assert on the format-specific wrappers and the shared protocol body."""

from work_kb.agentfiles import (
    TARGETS,
    render_agent_files,
    render_agents_md,
    render_claude_md,
    render_copilot_pathscoped,
    render_copilot_repo,
    render_cursor_mdc,
)
from work_kb.models import Tier

COUNTS = {Tier.FOUNDATION: 3, Tier.DETAIL: 12, Tier.ARTIFACT: 40}


def test_every_target_renders_the_protocol():
    files = render_agent_files(COUNTS)
    assert len(files) == len(TARGETS)
    for content in files.values():
        # Shared protocol markers appear in every format.
        assert "kb/00-foundation/INDEX.md" in content
        assert "SEARCH" in content
        assert "kb/index.json" in content


def test_counts_are_substituted():
    out = render_copilot_repo(COUNTS)
    assert "(3 items)" in out
    assert "(12 items)" in out
    assert "(40 items)" in out


def test_copilot_repo_is_plain_markdown_no_frontmatter():
    out = render_copilot_repo(COUNTS)
    assert not out.lstrip().startswith("---")


def test_copilot_pathscoped_has_applyto_frontmatter():
    out = render_copilot_pathscoped(COUNTS)
    assert out.startswith("---\n")
    assert 'applyTo: "**"' in out


def test_cursor_mdc_has_mdc_frontmatter():
    out = render_cursor_mdc(COUNTS)
    assert out.startswith("---\n")
    assert "alwaysApply: true" in out


def test_agents_md_and_claude_md_are_plain():
    for fn in (render_agents_md, render_claude_md):
        out = fn(COUNTS)
        assert not out.lstrip().startswith("---")
        assert "# Working with this knowledge base" in out


def test_agents_md_under_codex_size_limit():
    # Codex stops reading AGENTS.md past 32 KiB; our generated file must be tiny.
    assert len(render_agents_md(COUNTS).encode("utf-8")) < 32 * 1024


def test_target_paths_are_unique():
    paths = [t.path for t in TARGETS]
    assert len(paths) == len(set(paths))
