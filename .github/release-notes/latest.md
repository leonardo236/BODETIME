## Novedades de BODETIME 1.0.5

- Los nombres y apellidos rechazan números y símbolos fuera del formato permitido.
- El cargo ahora se selecciona desde el catálogo de puestos de bodega; ya no acepta texto libre.
- El administrador puede agregar cargos personalizados con una clave protegida por hash.
- El administrador puede borrar trabajadores; una confirmación advierte que también se eliminarán sus asistencias.

## Primera actualización

Los usuarios de BODETIME 1.0.4 reciben esta versión desde el aviso dentro de la app. La versión 1.0.3 no tiene comprobador y debe instalar la 1.0.4 manualmente una vez antes de recibir avisos internos.

## Instalación

Descarga **BODETIME-Setup.exe** desde los archivos de esta publicación. Se requiere MySQL Server 8 instalado y en ejecución. La aplicación no incluye ni reemplaza el servidor MySQL.

## Datos y límites

La base de datos existente conserva sus datos; se crea una tabla para cargos personalizados. Si `DB_CREATE_SCHEMA=false`, ejecuta el `schema.sql` actualizado antes de abrir la app. La suite local se ejecuta como parte de GitHub Actions.
