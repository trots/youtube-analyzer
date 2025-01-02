; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "YouTube Analyzer"
#define MyAppVersion "4.0"
#define MyAppPublisher "Alexander Trotsenko"
#define MyAppURL "https://github.com/trots/youtube-analyzer"
#define MyAppExeName "youtube-analyzer.exe"
#define MyAppDistDir "__main__.dist"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{6CBD04A3-42AC-4633-9AAB-C4C78566550E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=D:\git\youtube-analyzer\youtube-analyzer\LICENSE
; Uncomment the following line to run in non administrative install mode (install for current user only.)
;PrivilegesRequired=lowest
OutputBaseFilename=youtube-analyzer-setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyAppDistDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\_asyncio.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\_bz2.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\_ctypes.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\_decimal.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\_hashlib.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\_lzma.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\_multiprocessing.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\_overlapped.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\_queue.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\_socket.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\_ssl.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\_uuid.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\libcrypto-3.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\libffi-8.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\libssl-3.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\logo.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\msvcp140.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\msvcp140_1.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\msvcp140_2.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\pyexpat.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\pyside6.abi3.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\python3.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\python311.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\qt6charts.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\qt6core.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\qt6gui.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\qt6network.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\qt6opengl.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\qt6openglwidgets.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\qt6pdf.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\qt6svg.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\qt6widgets.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\select.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\shiboken6.abi3.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\unicodedata.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\vcruntime140.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\vcruntime140_1.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\certifi\*"; DestDir: "{app}\certifi"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyAppDistDir}\charset_normalizer\*"; DestDir: "{app}\charset_normalizer"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyAppDistDir}\googleapiclient\*"; DestDir: "{app}\googleapiclient"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyAppDistDir}\PySide6\*"; DestDir: "{app}\PySide6"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyAppDistDir}\shiboken6\*"; DestDir: "{app}\shiboken6"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyAppDistDir}\translations\*"; DestDir: "{app}\translations"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyAppDistDir}\zstandard\*"; DestDir: "{app}\zstandard"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
