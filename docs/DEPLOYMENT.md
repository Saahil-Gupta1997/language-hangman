# Distribution

This version ships as a local Windows desktop application. Follow the root README
and `scripts/build_desktop.ps1`. There is no hosted deployment step.

The old Dockerfile and browser entry points are compatibility/development material.
They do not distribute the native application. The supported installer bundles its
own Python runtime; it does not install a service or require network access at runtime.

Build on Windows x64 with Python 3.12 and Inno Setup 6. Use the desktop-release GitHub
Actions workflow for clean builds and retain its results before distributing an EXE.
Manual smoke tests on a clean Windows account remain required. The current package
includes build definitions, not an independently verified Windows binary.
