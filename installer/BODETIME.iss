#define AppName "BODETIME"
#ifndef AppVersion
  #define AppVersion "1.0.0"
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
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayName=BODETIME

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; Flags: unchecked

[Files]
Source: "..\dist\BODETIME\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\schema.sql"; DestDir: "{app}\database"; Flags: ignoreversion
Source: "..\.env.example"; DestDir: "{userappdata}\BODETIME"; DestName: ".env"; Flags: onlyifdoesntexist
Source: "..\README-INSTALADOR.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\BODETIME"; Filename: "{app}\BODETIME.exe"
Name: "{autodesktop}\BODETIME"; Filename: "{app}\BODETIME.exe"; Tasks: desktopicon
Name: "{autoprograms}\Guía de configuración BODETIME"; Filename: "{app}\README-INSTALADOR.txt"

[Run]
Filename: "{app}\README-INSTALADOR.txt"; Description: "Abrir guía rápida para conectar MySQL"; Flags: postinstall shellexec skipifsilent
