"""Third-party notices (T-28): the inventory, the committed texts and the folder check."""

import shutil

from scripts import third_party_notices as notices


def fake_installed_app(folder):
    """One file for every inventory pattern, plus the committed notices."""
    for component in notices.COMPONENTS:
        for pattern in component["files"]:
            path = folder / pattern.replace("*", "example.bin")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"shipped")
    shutil.copytree(notices.NOTICES, folder, dirs_exist_ok=True)
    return folder


def test_committed_notices_match_the_inventory():
    listed = {name for component in notices.COMPONENTS for name in component["notices"]}
    present = {path.name for path in (notices.NOTICES / "licenses").iterdir()}
    assert listed <= present
    assert present - listed == set(), "every shipped licence text is referenced"
    summary = (notices.NOTICES / "THIRD-PARTY-NOTICES.txt").read_text(encoding="utf-8")
    assert summary == notices.summary()
    for component in notices.COMPONENTS:
        assert component["name"] in summary and component["version"] in summary


def test_check_passes_for_a_complete_folder(tmp_path, capsys):
    assert notices.check(fake_installed_app(tmp_path), installed=True)
    assert "0 problems" in capsys.readouterr().out


def test_check_rejects_unlisted_files_and_changed_or_missing_notices(tmp_path, capsys):
    folder = fake_installed_app(tmp_path)
    (folder / "_internal" / "unexpected.dll").write_bytes(b"?")
    (folder / "licenses" / "Apache-2.0.txt").write_text("edited", encoding="utf-8")
    (folder / "licenses" / "CustomTkinter-5.2.2-LICENSE.txt").unlink()
    assert not notices.check(folder, installed=True)
    output = capsys.readouterr().out
    assert "not in the inventory: _internal/unexpected.dll" in output
    assert "notice differs from packaging/third-party: licenses/Apache-2.0.txt" in output
    assert "notice missing: licenses/CustomTkinter-5.2.2-LICENSE.txt" in output
