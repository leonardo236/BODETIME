BODETIME - instalación rápida
============================

REQUISITO
---------
MySQL Server 8 debe estar instalado y en ejecución. BODETIME no incluye el
servidor MySQL. No necesitas MySQL Workbench ni usar comandos para configurar
la base de BODETIME.

INSTALACIÓN
-----------
1. Ejecuta BODETIME-Setup.exe y sigue el asistente.
2. Deja marcada la opción “Configurar MySQL ahora”. Se abrirá el asistente.
3. Escribe una cuenta MySQL con permisos para crear la base y el usuario de la aplicación.
   Esa contraseña solo se usa para crear la base y no se guarda.
4. Pulsa “Probar y configurar”. BODETIME crea la base, las tablas, un usuario
   limitado con contraseña aleatoria y su configuración local protegida en
   %APPDATA%\BODETIME\.env.
5. Cuando aparezca la confirmación, abre BODETIME desde el menú Inicio.
   En Configuración, registra el horario y tolerancia aprobados por la bodega.

Si cancelas el asistente, puedes abrir “Configurar conexión de MySQL” desde el
menú Inicio más tarde. Si MySQL aún no está instalado, instala MySQL Server 8
y vuelve a abrir ese acceso directo.

No compartas el archivo %APPDATA%\BODETIME\.env: contiene la contraseña local
aleatoria que usa BODETIME para acceder a su base de datos.
