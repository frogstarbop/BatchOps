[Setup]
AppId={{0931B856-BDFA-44E3-9E53-D332502ACFE4}
AppName=BatchOps
AppVersion=1.0.0
DefaultDirName={autopf}\BatchOps
DefaultGroupName=BatchOps
UninstallDisplayIcon={app}\BatchOps.exe
SetupIconFile=bundled\icon.ico
OutputDir=installer
OutputBaseFilename=BatchOps-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; per-user install, so no admin prompt
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "dist\BatchOps\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\BatchOps"; Filename: "{app}\BatchOps.exe"
Name: "{autodesktop}\BatchOps"; Filename: "{app}\BatchOps.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\BatchOps.exe"; Description: "Launch BatchOps"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\BatchOps"