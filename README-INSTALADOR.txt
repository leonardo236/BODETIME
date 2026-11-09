BODETIME - instalación rápida
============================

1. Instala BODETIME con BODETIME-Setup.exe y abre el acceso directo.
2. BODETIME necesita MySQL Server 8 en ejecución. El instalador de BODETIME
   no instala MySQL ni crea cuentas administrativas.
3. La primera vez, configura MySQL usando database\schema.sql y completa
   %APPDATA%\BODETIME\.env con los datos de tu usuario MySQL.
4. Cierra y vuelve a abrir BODETIME. Si MySQL se inicia después, usa
   “Reintentar conexión”.

No compartas el archivo .env: puede contener la contraseña de MySQL.
