# Sushi House

Proyecto escolar web de reservas con Flask, HTML, CSS, JavaScript y **Microsoft SQL Server**. La base de datos se administra desde SQL Server Management Studio (SSMS). Incluye registro e inicio de sesión, creación de reservas asociadas a la cuenta, consulta y cancelación de las reservas propias.

## 1. Requisitos

- Python 3.14
- Microsoft SQL Server instalado y en ejecución
- SQL Server Management Studio (SSMS)
- Microsoft ODBC Driver 18 for SQL Server en Windows: [descargar desde Microsoft](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server)

La aplicación usa `pyodbc` para conectarse a SQL Server. SQL Server y MySQL son sistemas de base de datos distintos; este proyecto ya está configurado para SQL Server.

## 2. Crear la base y las tablas desde SSMS

1. Abre SSMS y conéctate a la instancia que vas a usar.
2. Abre `schema.sql` (Archivo → Abrir → Archivo).
3. Ejecuta el script con el botón **Ejecutar**.
4. Actualiza el panel **Bases de datos**. Debe aparecer `sushi_house` con las tablas `dbo.users` y `dbo.reservations`.

`users` guarda las cuentas registradas. `reservations` guarda la fecha, hora, cantidad de personas, notas y estado, y su columna `user_id` indica a qué usuario pertenece. Al iniciar sesión, Flask identifica esa cuenta y muestra sus reservas.

## 3. Abrir y preparar en Visual Studio Code

Abre la carpeta del proyecto en VS Code. En Terminal → Nueva terminal, ejecuta:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

Si PowerShell bloquea la activación, puedes instalar e iniciar usando el ejecutable del entorno directamente:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

En VS Code, selecciona el intérprete `.venv` si te lo solicita (`Ctrl+Shift+P` → **Python: Select Interpreter**).

## 4. Configurar la conexión

1. Copia `.env.example` y nombra la copia `.env` (en VS Code puedes duplicar el archivo desde el explorador).
2. En SSMS, revisa el nombre que aparece en la ventana **Conectar al servidor**. Pon ese mismo valor en `SQL_SERVER` dentro de `.env`.
   - Instancia predeterminada: normalmente `localhost` o `.`
   - SQL Express: a menudo `localhost\SQLEXPRESS`
   - Puedes pegar el nombre exacto de servidor/instancia que muestra SSMS.
3. Si en SSMS seleccionas **Autenticación de Windows**, deja:

   ```text
   SQL_TRUSTED_CONNECTION=true
   ```

   La aplicación se conectará con la cuenta de Windows que ejecuta VS Code. Esa cuenta debe tener acceso a SQL Server y a la base `sushi_house`.

4. Si en SSMS seleccionas **Autenticación de SQL Server**, usa:

   ```text
   SQL_TRUSTED_CONNECTION=false
   SQL_USERNAME=tu_usuario_de_sql
   SQL_PASSWORD=tu_contraseña_de_sql
   ```

   Es el mismo usuario y contraseña que usas en SSMS. No compartas el archivo `.env` con otras personas.

5. Deja `SQL_DRIVER=ODBC Driver 18 for SQL Server`. Para el servidor local de la clase, deja `SQL_TRUST_SERVER_CERTIFICATE=true`.
6. Cambia `SECRET_KEY` por una frase larga propia, por ejemplo `sushi-house-clase-2026-clave-local`.

## 5. Ejecutar

Con el entorno virtual activo, ejecuta:

```powershell
py app.py
```

Abre <http://127.0.0.1:5000>, registra una cuenta y crea una reserva. En SSMS puedes actualizar las tablas para consultar las filas guardadas.

## Estructura principal

```text
app.py                 Rutas web y conexión a SQL Server
schema.sql             Base de datos y tablas para ejecutar en SSMS
.env.example           Ejemplo de configuración local
requirements.txt       Paquetes Python
templates/             Páginas HTML
static/css/style.css   Estilos
static/js/app.js       Interacciones sencillas
```

La contraseña se guarda como hash para que la demo no almacene la contraseña visible. La sesión recuerda qué cuenta inició sesión para asociar y filtrar sus reservas.
