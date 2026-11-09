BODETIME - instalación rápida
============================

ANTES DE INSTALAR BODETIME
--------------------------
MySQL Server 8 debe estar instalado y en ejecución. BODETIME no incluye el
servidor MySQL. MySQL Workbench es opcional y se usa aquí para preparar la base.

INSTALACIÓN
-----------
1. Ejecuta BODETIME-Setup.exe y sigue el asistente. El instalador crea accesos
   directos y una configuración inicial en %APPDATA%\BODETIME\.env.
2. Abre MySQL Workbench y conecta a tu servidor local como administrador.
3. Abre el archivo database\schema.sql dentro de la carpeta de instalación
   de BODETIME y ejecútalo completo (icono del rayo). Esto crea la base,
   las tablas y el usuario limitado que usa la aplicación.
4. Abre BODETIME desde el menú Inicio. En Configuración, guarda el horario
   y tolerancia reales antes de registrar asistencias.

Si MySQL Workbench no está instalado, abre CMD y ejecuta (ajusta la ruta si
instalaste MySQL en otra carpeta):
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p < "C:\Program Files\BODETIME\database\schema.sql"

La plantilla y schema.sql usan una contraseña de demostración coincidente.
Para uso real, cambia la contraseña en MySQL y también en
%APPDATA%\BODETIME\.env (DB_PASSWORD). No publiques ni compartas ese archivo.

No compartas el archivo .env: puede contener la contraseña de MySQL.
