# Build on Windows with Python 3.12. The runtime never launches a browser server.
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

root = Path(SPECPATH).parent
resources = collect_data_files('customtkinter')
resources += [(str(root / 'src/desktop/content'), 'src/desktop/content')]
a = Analysis([str(root / 'desktop_app.py')], pathex=[str(root)], datas=resources,
             hiddenimports=['PIL.ImageGrab'],
             excludes=['streamlit', 'fastapi', 'uvicorn', 'pytest', 'pandas', 'numpy'],
             noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='LanguageHangman',
          debug=False, strip=False, upx=False, console=False,
          icon=str(root / 'assets/app.ico'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='LanguageHangman')
