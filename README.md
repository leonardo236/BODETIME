# BODETIME

Aplicación de escritorio en español para gestionar trabajadores, registrar asistencia y generar reportes PDF. Está construida con Python, PySide6, SQLAlchemy ORM 2.x, MySQL 8, PyMySQL y ReportLab.

La rúbrica de pre-defensa guía el alcance: interfaz PySide6 navegable con validaciones visibles, CRUD mediante ORM sobre MySQL, marcajes con reglas de negocio y reporte PDF generado desde la interfaz con datos consultados en la base. Las diapositivas JUDC organizan la exposición en introducción, objetivos, metodología, resultados y discusión, y conclusiones.

## Requisitos

- Windows 10/11 de 64 bits.
- Python 3.9 o posterior (se recomienda Python 3.13 de 64 bits en Windows).
- MySQL Server 8.0 en ejecución y una base de datos accesible.
- Visual Studio Code (entorno de edición recomendado).

## Preparación de MySQL

1. Abre MySQL Workbench o el cliente `mysql` con una cuenta administradora.
2. Ejecuta el archivo `schema.sql`. Este crea la base `bodetime`, el usuario `bodetime_app` y las tablas relacionales.
3. Cambia la contraseña de ejemplo del usuario SQL por una clave propia y actualiza `DB_PASSWORD` en `.env` con la misma clave.
4. En el proyecto, copia `.env.example` como `.env` y revisa host, puerto, base, usuario y contraseña.

El usuario de la aplicación necesita `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `INDEX` y `ALTER` si `DB_CREATE_SCHEMA=true`, porque SQLAlchemy crea las tablas que falten al iniciar. Si las tablas se administran manualmente, configura `DB_CREATE_SCHEMA=false` después de ejecutar `schema.sql`.

La hora laboral y la tolerancia no se precargan con valores inventados. Al iniciar por primera vez, abre **Configuración**, registra los valores aprobados por la bodega y pulsa **Guardar configuración**. Hasta entonces, el sistema no permite marcar entradas.

## Instalación y ejecución en Windows

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
- **Trabajadores:** alta, consulta, edición y desactivación lógica con confirmación. Código único; nombres, apellidos y código obligatorios.
- **Asistencia:** entrada y salida con reloj del sistema; historial por rango de fechas y trabajador; rechazo de entradas diarias duplicadas, salida sin entrada y hora de salida no posterior a la entrada.
- **Tardanzas:** se marcan cuando la entrada supera la hora de inicio más la tolerancia. Se evalúan con la configuración vigente al registrar la entrada.
- **Reportes:** consulta de MySQL con fechas y trabajador opcional. El botón **Generar PDF** usa ReportLab (`Table`, `TableStyle`), pide ruta y permite abrir el archivo creado. Si no hay resultados, no crea un PDF vacío.
- **Configuración:** hora de entrada y tolerancia, guardadas en MySQL.

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
- `schema.sql`: contiene la estructura inicial de MySQL.

Las claves de conexión se leen desde `.env`, que está excluido de Git. La tabla `asistencias` relaciona cada registro con un trabajador y limita la versión actual a una asistencia por persona y fecha.

## Material para la defensa

En [`Material_Defensa`](Material_Defensa/) están la presentación de siete diapositivas y la guía breve para practicar la explicación y la demostración. La plantilla JUDC original y la rúbrica se conservan sin cambios.

## Pruebas

Activa el entorno e invoca:

```powershell
pytest -q
```

Las pruebas unitarias cubren las reglas de dominio, los mensajes de diagnóstico para errores de conexión de Windows y la protección de credenciales, además de la generación del PDF con una fila sintética identificada expresamente como fixture. La integración con MySQL se verifica por separado y usa registros temporales que se eliminan al terminar.

## Esquema y configuración

`schema.sql` define `trabajadores`, `asistencias` y `configuracion_horario`, con claves, unicidad, integridad referencial e índices. SQLAlchemy puede crear estas tablas al iniciar, pero no crea el servidor ni la base de datos: la base y el usuario deben prepararse primero.

Variables soportadas en `.env`: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_CHARSET`, `DB_CONNECT_TIMEOUT` y `DB_CREATE_SCHEMA`.

## Alcance de la verificación local

En la configuración local revisada el 3 de noviembre de 2026 (MySQL 8, servicio Windows `MySQL80`, host `127.0.0.1`, puerto `3306`):

- `python -m compileall -q bodetime main.py` terminó correctamente y la última ejecución de `pytest -q` reportó **8 pruebas aprobadas**.
- La consulta de conexión SQLAlchemy/PyMySQL y la aplicación pudieron leer la base MySQL. La ventana PySide6 quedó abierta y el panel confirmó el estado **MySQL conectado**.
- Una verificación de integración temporal comprobó alta, lectura, actualización, código duplicado, desactivación, entradas y salidas válidas, rechazo de marcajes inválidos o duplicados, historial y generación ReportLab con filas recuperadas de MySQL. Los registros temporales y el PDF se eliminaron y la configuración de horario previa se restauró. No se incluyeron datos personales en el repositorio.
- `git diff --check` terminó sin errores y se confirmó que `.env` y los entornos locales están excluidos de Git.

El esquema y la interfaz se contrastaron con los cinco criterios de la rúbrica de pre-defensa. La plantilla JUDC aporta la estructura de exposición (introducción, objetivos, metodología, resultados y discusión, conclusiones), no criterios funcionales adicionales. Usa la configuración laboral y los datos autorizados por la bodega para la demostración.

La generación del PDF con filas leídas de MySQL se verificó en la prueba de integración; no se comprobó manualmente el diálogo **Generar PDF** desde la ventana.

La versión no integra biometría, RFID, nómina, vacaciones, sincronización remota ni turnos múltiples.
