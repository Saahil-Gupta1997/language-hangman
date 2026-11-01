# Release validation tooling

The scripts that produce a release's evidence. They live in the repository, not in
a scratch folder, so that a release can be reproduced by someone else — and so they survive
(incident I-6: an earlier set was lost when a temporary folder was cleaned).

| Module | What it does |
| --- | --- |
| `window.py` | Launches the installed program, times start-up, captures its window only (DPI aware, never a screen grab), resizes and closes it |
| `fixtures.py` | Creates learner data with the application's own services: the upgrade profile, and the supported-history performance dataset |
| `verify.py` | Checks data after an upgrade, a beta import or a restore, using the release's own code |
| `measure.py` | Performance figures with sample counts; window layout at three scalings and two text sizes |
| `evidence.py` | Scrubs personal paths and copies evidence into `docs/evidence/`, refusing screenshots that are not the app's own window |
| `beta_database.py` | Rebuilds a v1.0.0-beta database with the beta's own code, for the import check; run it from a checkout of `023f2bd` |
| `kit.py` | Builds the printable manual-check sheet from `docs/ACCEPTANCE.md` |
| `demo.py` | Records the captioned demo (needs `imageio-ffmpeg` in a scratch environment) |

Nothing here writes a result into an acceptance record: human gates are filled in by the
people who run them.

**If the app is installed and in use on this machine,** set `LANGUAGE_HANGMAN_DATA_DIR` to a
scratch folder for every step, or validation will read, damage and restore that person's real
data. Get their agreement before replacing the installed program, and note whether they have a
desktop shortcut: uninstalling removes it, and a silent install only restores it with
`/MERGETASKS=desktopicon`.

Run checks with the system temp folder. A very long `TEMP` makes the release-check test's
`git init` fail on Windows' path limit (incident I-10).

## Order for a candidate

Full sequence and the gates each step feeds: [RELEASE_CHECKLIST.md](../../RELEASE_CHECKLIST.md).

```powershell
# 1. Hygiene first, on an untouched checkout (caches would be reported, correctly)
$env:PYTHONDONTWRITEBYTECODE = "1"; python -m src.cli release-check
python -m ruff check .; python scripts/check_curated_content.py; python -m pytest -rs
python desktop_app.py --smoke-test <folder>

# 2. Build, then copy the installer out of the build tree immediately (incident I-1)
./scripts/build_desktop.ps1 -Python <clean 3.12.1 environment>\python.exe

# 3. Validate that exact installer: install the previous release, make data with ITS code,
#    upgrade, then check the installed program
python -m scripts.validation.fixtures release-data        # from the PREVIOUS release's checkout
python -m scripts.validation.verify upgraded              # from THIS release's checkout
python scripts/third_party_notices.py check <install folder> --installed
python -m scripts.validation.verify beta-import
python -m scripts.validation.verify restore-newest <copy of the damaged file>

# 4. Measurements, evidence and the kit
python -m scripts.validation.measure performance <dataset folder>
python -m scripts.validation.measure round                # guess to redrawn screen
python -m scripts.validation.measure round Spanish Expert # the same, in a word list
python -m scripts.validation.measure long 200             # early and late in one long session
python -m scripts.validation.measure scaling <output folder>
python -m scripts.validation.evidence collect <staging> docs/evidence/<date>-<version>-<revision>
python -m scripts.validation.kit <release package>/acceptance-kit <installer sha256>
```
