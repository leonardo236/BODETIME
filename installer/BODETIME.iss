#define AppName "BODETIME"
#ifndef AppVersion
  #define AppVersion "1.1.1"
#endif

[Setup]
AppId={{7A89B4B1-4E2F-4D59-9627-21570A0C2026}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=BODETIME
DefaultDirName={autopf}\BODETIME
DefaultGroupName=BODETIME
OutputDir=..\output
OutputBaseFilename=BODETIME-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
PrivilegesRequired=admin
CloseApplications=yes
RestartApplications=no
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayName=BODETIME

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; Flags: unchecked

[Files]
Source: "..\dist\BODETIME\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\schema.sql"; DestDir: "{app}\database"; Flags: ignoreversion
Source: "..\README-INSTALADOR.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\BODETIME"; Filename: "{app}\BODETIME.exe"
Name: "{autodesktop}\BODETIME"; Filename: "{app}\BODETIME.exe"; Tasks: desktopicon
Name: "{autoprograms}\Configurar conexión de MySQL"; Filename: "{app}\BODETIME.exe"; Parameters: "--configurar-base"
Name: "{autoprograms}\Guía de configuración BODETIME"; Filename: "{app}\README-INSTALADOR.txt"

[Run]
Filename: "{app}\BODETIME.exe"; Parameters: "--configurar-base --setup-inicial"; Description: "Configurar MySQL ahora (recomendado)"; Flags: postinstall runasoriginaluser skipifsilent
