import pytest

from backend.markdown_service import read_md_file, write_md_file, rebuild_md_file, remove_entry_from_md, list_available_dates


def test_write_and_read_md_file():
    content = "# 2026-05-05\n\n## Work\n### Standup\n- Discussed timeline\n"
    write_md_file("2026-05-05", content)
    result = read_md_file("2026-05-05")
    assert result == content


def test_read_nonexistent_file_returns_empty():
    result = read_md_file("1999-01-01")
    assert result == ""


def test_rebuild_md_file_combines_sections():
    sections = {
        "work": ["### Standup\n- Discussed timeline", "### Reviews\n- Reviewed PR"],
        "personal": ["### Health\n- Morning run 5km"],
        "finance": []
    }
    result = rebuild_md_file("2026-05-05", sections)
    assert "# 2026-05-05" in result
    assert "## Work" in result
    assert "### Standup" in result
    assert "### Reviews" in result
    assert "## Personal" in result
    assert "### Health" in result
    assert "## Finance" not in result


def test_list_available_dates():
    write_md_file("2026-04-01", "# 2026-04-01\n")
    write_md_file("2026-05-01", "# 2026-05-01\n")
    dates = list_available_dates()
    assert "2026-04-01" in dates
    assert "2026-05-01" in dates
    assert dates == sorted(dates, reverse=True)
