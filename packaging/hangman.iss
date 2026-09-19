; The build script passes /DMyAppVersion from src/__init__.py; this default must match it.
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0rc2"
#endif
[Setup]
AppId={{D16E40D9-2223-4FBE-A30C-B2A17B3D4506}
AppName=Language Hangman
AppVersion={#MyAppVersion}
DefaultDirName={localappdata}\Programs\LanguageHangman
DefaultGroupName=Language Hangman
OutputDir=..\dist\installer
OutputBaseFilename=LanguageHangman-{#MyAppVersion}-Setup
SetupIconFile=..\assets\app.ico
UninstallDisplayIcon={app}\LanguageHangman.exe
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
[Files]
Source: "..\dist\LanguageHangman\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
[Icons]
Name: "{group}\Language Hangman"; Filename: "{app}\LanguageHangman.exe"
Name: "{autodesktop}\Language Hangman"; Filename: "{app}\LanguageHangman.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\LanguageHangman.exe"; Description: "Launch Language Hangman"; Flags: nowait postinstall skipifsilent
; App data is deliberately outside {app}; uninstall never deletes learner progress.
