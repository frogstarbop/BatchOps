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
; admin is needed to install VC++ runtime
PrivilegesRequired=admin

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "dist\BatchOps\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\BatchOps"; Filename: "{app}\BatchOps.exe"
Name: "{autodesktop}\BatchOps"; Filename: "{app}\BatchOps.exe"; Tasks: desktopicon

[Run]
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Installing Visual C++ runtime..."; Check: VCRedistNeeded
Filename: "{app}\BatchOps.exe"; Description: "Launch BatchOps"; Flags: nowait postinstall skipifsilent

[Code]
function VCRedistNeeded: Boolean;
var
  Installed: Cardinal;
begin
  Result := not (RegQueryDWordValue(HKLM64, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64',
  'Installed', Installed) and (Installed = 1));
end;

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\BatchOps"