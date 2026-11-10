# BODETIME

Aplicación de escritorio en español para gestionar trabajadores, registrar asistencia y generar reportes PDF. Está construida con Python, PySide6, SQLAlchemy ORM 2.x, MySQL 8, PyMySQL y ReportLab.

La rúbrica de pre-defensa guía el alcance: interfaz PySide6 navegable con validaciones visibles, CRUD mediante ORM sobre MySQL, marcajes con reglas de negocio y reporte PDF generado desde la interfaz con datos consultados en la base. Las diapositivas JUDC organizan la exposición en introducción, objetivos, metodología, resultados y discusión, y conclusiones.

## Requisitos

- Windows 10/11 de 64 bits.
- Python 3.9 o posterior (se recomienda Python 3.13 de 64 bits en Windows).
- MySQL Server 8.0 en ejecución y una base de datos accesible.
- Visual Studio Code (entorno de edición recomendado).

## Preparación de MySQL

1. Abre MySQL Workbench o el cliente `mysql` con una cuenta que tenga permisos para preparar la base de datos.
2. Ejecuta el archivo `schema.sql`. Este crea la base `bodetime`, el usuario `bodetime_app` y las tablas relacionales.
3. Cambia la contraseña de ejemplo del usuario SQL por una clave propia y actualiza `DB_PASSWORD` en `.env` con la misma clave.
4. En el proyecto, copia `.env.example` como `.env` y revisa host, puerto, base, usuario y contraseña.

El usuario de la aplicación necesita `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `INDEX` y `ALTER` si `DB_CREATE_SCHEMA=true`, porque SQLAlchemy crea las tablas que falten al iniciar. Si las tablas se administran manualmente, configura `DB_CREATE_SCHEMA=false` después de ejecutar `schema.sql`.

La hora laboral y la tolerancia no se precargan con valores inventados. Al iniciar por primera vez, abre **Configuración**, registra los valores aprobados por la bodega y pulsa **Guardar configuración**. Hasta entonces, el sistema no permite marcar entradas.

## Instalación y ejecución en Windows

### Instalador para usuarios

Al publicar una etiqueta `v*` en GitHub, Actions ejecuta las pruebas, empaqueta la aplicación y adjunta `BODETIME-Setup.exe` a la publicación. También se puede iniciar manualmente desde la pestaña **Actions**. El instalador crea accesos directos y ofrece un asistente para preparar la base MySQL y guardar credenciales de aplicación aleatorias en `%APPDATA%\BODETIME\.env`.

**Requisito:** cada computadora debe tener MySQL Server 8 instalado y en ejecución. El asistente de BODETIME configura la base y la cuenta de aplicación, pero no instala el servidor MySQL. La contraseña de la cuenta de administración de MySQL solo se usa durante esa configuración; no se guarda. No publiques `.env` ni credenciales en GitHub.

La aplicación comprueba si hay una versión más reciente al iniciar y cada seis horas. En **Configuración**, **Buscar e instalar** busca una versión y, si hay una nueva, permite instalarla desde BODETIME después de confirmar. La descarga comprueba su SHA-256 antes de abrir el instalador. Windows puede pedir permiso de administrador. La base de datos y el archivo de configuración del usuario no forman parte de la actualización, y el asistente inicial de MySQL no vuelve a abrirse si esa configuración ya existe. Las versiones anteriores a la 1.0.4 deben instalar esta versión manualmente una primera vez; después recibirán los avisos dentro de la aplicación.

Todos los usuarios pueden agregar cargos y eliminar trabajadores. Antes de borrar, BODETIME muestra una confirmación que indica cuántas asistencias históricas también se eliminarán.

Abre PowerShell en esta carpeta:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
code .
python main.py
```

Completa `.env` antes de ejecutar. En VS Code puedes seleccionar `.venv` con **Python: Select Interpreter** y ejecutar `main.py` desde el depurador. Si PowerShell bloquea la activación del entorno, ejecuta los comandos usando `.venv\Scripts\python.exe` directamente.

Si aparece un error que apunta a un Python que ya desinstalaste (por ejemplo, el Python incluido con Visual Studio), el entorno virtual conserva esa ruta antigua. Cierra VS Code y renombra `.venv` para guardarlo como respaldo; crea uno nuevo con `py -3.13 -m venv .venv`, activa el entorno y reinstala `requirements.txt`. Después selecciona el intérprete de `.venv` desde **Python: Select Interpreter**. No es necesario reinstalar VS Code.

La pantalla principal intenta conectar a MySQL al abrirse. Si el servidor no responde, BODETIME mantiene la ventana abierta y reintenta cada 15 segundos; también puedes usar **Reintentar conexión**. Si el servicio `MySQL80` está detenido, inícialo desde **Servicios** de Windows. Al volver a estar disponible, BODETIME actualizará las pantallas sin reiniciarse. El servidor debe estar en ejecución para consultar o guardar datos. No hay registros de trabajadores de demostración ni se usa SQLite.

## Funciones

- **Inicio:** recuento de trabajadores activos, asistencias del día, tardanzas y turnos abiertos; listado de marcajes del día.
- **Trabajadores:** alta, consulta, edición de la fila seleccionada y desactivación/reactivación. El cargo se elige de un catálogo con puestos comunes de bodega; cualquier usuario puede agregar cargos desde el botón **+ Cargo** o Configuración. Eliminar definitivamente a un trabajador pide confirmación y borra sus asistencias históricas.
- **Asistencia:** entrada y salida con reloj del sistema; historial por rango de fechas y trabajador; rechazo de entradas diarias duplicadas, salida sin entrada y hora de salida no posterior a la entrada.
- **Tardanzas:** se marcan cuando la entrada supera la hora de inicio más la tolerancia. Se evalúan con la configuración vigente al registrar la entrada.
- **Reportes:** consulta de MySQL con fechas y trabajador opcional. El botón **Generar PDF** usa ReportLab (`Table`, `TableStyle`), pide ruta y permite abrir el archivo creado. Si no hay resultados, no crea un PDF vacío.
- **Configuración:** tema claro/oscuro, acento de color predeterminado o personalizado, animaciones, estilo del calendario (cristal claro o blanco clásico), hora de entrada y tolerancia. La apariencia se guarda para la cuenta de Windows; el horario se guarda en MySQL.
- **Actualizaciones:** comprobación de versiones publicadas, aviso integrado, descarga verificada y apertura del instalador de Windows.
- **Cargos de bodega:** Almacenista, Auxiliar de bodega, Bodeguero, Despachador de bodega, Encargado de bodega, Montacarguista y Recepcionista de mercancía; cualquier usuario puede agregar opciones propias.
- **Apariencia:** inicio animado con la marca BODETIME, reloj local con segundos y tarjeta de fecha, calendario flotante con aparición suave y estilos cristal claro o blanco clásico. Las transiciones son breves y se pueden desactivar desde Configuración.

## Arquitectura

```text
Usuario
  ↓
Interfaz PySide6 (bodetime/ui.py)
  ↓
Servicios y reglas (bodetime/services.py)
  ↓
SQLAlchemy: modelos y sesiones (bodetime/models.py, bodetime/database.py)
  ↓
MySQL 8 (schema.sql)

Consulta de asistencia → ReportLab (bodetime/reports.py) → archivo PDF
```

En palabras sencillas: `main.py` abre la ventana. La pantalla recoge lo que hace el usuario y se lo pide a un servicio. El servicio valida la acción y usa una sesión de SQLAlchemy para leer o guardar en MySQL. Si una escritura falla, la transacción se revierte. Para un reporte, el servicio consulta las filas y ReportLab las presenta en una tabla PDF.

Así se reparten las tareas del código:

- `main.py`: inicia la aplicación y muestra la ventana.
- `bodetime/ui.py`: dibuja las cinco pantallas y presenta mensajes.
- `bodetime/services.py`: aplica las reglas de trabajadores y asistencia.
- `bodetime/models.py`: describe las tablas como clases de Python.
- `bodetime/database.py`: configura la conexión, las sesiones y las transacciones.
- `bodetime/reports.py`: crea el PDF con la información consultada.
- `bodetime/appearance.py`: crea la paleta clara/oscura y los colores de acento.
- `bodetime/animations.py`: ejecuta transiciones con el motor de animación de Qt.
- `bodetime/calendar.py`: contiene el selector de fecha y su calendario flotante.
- `bodetime/splash.py`: presenta la marca de BODETIME mientras se inicia la conexión.
- `schema.sql`: contiene la estructura inicial de MySQL.

Las claves de conexión se leen desde `.env`, que está excluido de Git. La tabla `asistencias` relaciona cada registro con un trabajador y limita la versión actual a una asistencia por persona y fecha.

## Material para la defensa

En [`Material_Defensa`](Material_Defensa/) están la presentación de siete diapositivas y la guía breve para practicar la explicación y la demostración. La plantilla JUDC original y la rúbrica se conservan sin cambios.

## Pruebas

Activa el entorno e invoca:

```powershell
pytest -q
```

Las pruebas unitarias cubren validaciones, reglas de asistencia, estilos claro/oscuro, selector de calendario, transiciones y generación de PDF con datos sintéticos. Las pruebas de interfaz usan Qt en modo sin ventana.

## Esquema y configuración

`schema.sql` define `trabajadores`, `cargos_personal`, `asistencias` y `configuracion_horario`, con claves, unicidad, integridad referencial e índices. SQLAlchemy puede crear estas tablas al iniciar, pero no crea el servidor ni la base de datos: la base y el usuario deben prepararse primero. Si `DB_CREATE_SCHEMA=false`, ejecuta `schema.sql` en la base existente para crear `cargos_personal` antes de iniciar esta versión.

Variables soportadas en `.env`: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_CHARSET`, `DB_CONNECT_TIMEOUT` y `DB_CREATE_SCHEMA`.

## Verificación local

La actualización de apariencia se verificó en Windows con estas comprobaciones:

- `pytest -q`: 37 pruebas aprobadas, incluyendo selector y estilos del calendario y el flujo de búsqueda/instalación simulado con metadatos de una publicación.
- `compileall` y `git diff --check`: completados sin errores.
- MySQL: conexión de solo lectura comprobada con `SELECT 1`; no se consultaron ni modificaron datos de trabajadores durante esa comprobación.
- Prueba manual de interfaz: BODETIME abrió con MySQL, mostró el panel y permitió navegar a Configuración y Asistencia. Se abrió el calendario desde el filtro.
- La descarga e instalación completa de una versión nueva se verificará cuando GitHub Actions publique el instalador de la versión 1.0.7. La prueba de interfaz simuló una versión disponible y comprobó que se inicie el flujo de descarga tras la búsqueda.

El esquema y la interfaz se contrastaron con los cinco criterios de la rúbrica de pre-defensa. La plantilla JUDC aporta la estructura de exposición (introducción, objetivos, metodología, resultados y discusión, conclusiones), no criterios funcionales adicionales. Usa la configuración laboral y los datos autorizados por la bodega para la demostración.

La generación del PDF con filas leídas de MySQL se probó anteriormente con registros temporales sintéticos; no se comprobó manualmente el diálogo **Generar PDF** durante esta actualización.

La versión no integra biometría, RFID, nómina, vacaciones, sincronización remota ni turnos múltiples.
