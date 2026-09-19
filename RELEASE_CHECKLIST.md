# Release checklist

1. Run Ruff, all Python tests and scripts/check_curated_content.py.
2. Run the Desktop release candidate Windows workflow; review installed-app results.
3. Complete every blocking gate in docs/ACCEPTANCE.md and record actual evidence.
4. Build with scripts/build_desktop.ps1; retain the installer SHA256 and build logs.
5. Verify source ZIP contains no user databases, keys, backup files or local environments.
6. Publish only the supported artifacts and exact limitations; never mark an unrun gate passed.
7. Promote 1.0.0rc1 to 1.0.0 only after acceptance. Keep rollback backups and prior installers.
