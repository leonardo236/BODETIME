## Novedades de BODETIME 1.0.6

- Cualquier usuario puede agregar cargos de bodega; la lista se comparte con las instalaciones conectadas a la misma base MySQL.
- Se quitó la contraseña y el permiso de administrador propios de BODETIME; cualquier usuario puede borrar trabajadores. La confirmación informa cuántas asistencias se eliminarán.
- Nuevo tema claro y oscuro, con colores de acento predeterminados o elegidos por el usuario. La preferencia se guarda en Windows.
- Se corrigieron el fondo y el texto del selector de cargos, también al usar el tema oscuro.
- Transiciones y movimientos breves con temporizador preciso, adaptados a la pantalla hasta 120 Hz; se pueden desactivar.

## Actualizar

Las versiones con comprobador integrado muestran el aviso al abrir la aplicación y vuelven a consultar periódicamente. Versiones anteriores a 1.0.4 deben instalar una versión reciente manualmente una vez.

## Instalación y base de datos

Descarga **BODETIME-Setup.exe** desde los archivos de esta publicación. Se requiere MySQL Server 8 instalado y en ejecución. Si `DB_CREATE_SCHEMA=false`, ejecuta el `schema.sql` actualizado antes de abrir la aplicación.

Las preferencias visuales se guardan por cuenta de Windows. Los trabajadores, las asistencias y los cargos personalizados permanecen en MySQL.
