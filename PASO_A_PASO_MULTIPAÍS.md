# PASO A PASO — Extensión Multi-País (Colombia + Argentina)
## Sistema PTO Novedades — Solvo Global
### Versión resultante: v3.0

---

## ¿QUÉ SE VA A LOGRAR?

Al terminar este paso a paso, el sistema:

1. **Al iniciar** (`julia main.jl`) se conectará a SQL Server y descargará datos tanto de Colombia (tablas actuales: `dbo.ausentismos`, `dbo.incapacidades`, `dbo.vacaciones` en la base `midasoft`) como de Argentina (tablas: `dbo.AusentismosArgentina`, `dbo.IncapacidadesArgentina`, `dbo.VacacionesArgentina` en la base `MidasoftArgentina`). También descargará SharePoint y archivos locales para ambos países.

2. **Al abrir el panel** aparecerá primero una **pantalla de selección de país** donde el usuario escoge Colombia o Argentina y pulsa **Procesar**.

3. **Procesamiento** del país seleccionado con los 3 núcleos y sub-núcleos ya existentes.

4. **Al terminar**, aparecen 3 botones:
   - **Exportar y Salir** → genera archivos y cierra
   - **Exportar y Volver** → genera archivos y regresa a la selección de país
   - **Salir** → cierra sin exportar

5. **Archivos exportados** con prefijo del país (`CO_` o `AR_`) y en subcarpetas separadas dentro de `output/`:
   - `output/CO/CO_Def_2025-06-18.xlsx`
   - `output/AR/AR_Def_2025-06-18.xlsx`

6. **Mejoras visuales** al panel GTK.

---

## MAPA DE ARCHIVOS QUE SE MODIFICAN

| Archivo | Tipo de cambio |
|---------|---------------|
| `src/Config.jl` | Agregar constantes Argentina + rutas por país |
| `src/SynapseConnector.jl` | Parametrizar queries por país (tablas distintas) |
| `src/DataLoader.jl` | Aceptar parámetro de país |
| `src/Validator.jl` | Usar festivos del país correcto |
| `src/DefManager.jl` | Rutas de Def por país |
| `src/Exporter.jl` | Prefijo de país + subcarpetas |
| `src/Panel.jl` | Pantalla selección país + 3 botones + mejoras visuales |
| `main.jl` | Cargar ambos países + orquestar panel multi-país |

---

---

# PASO 1 — Modificar `src/Config.jl`

**Qué hacer:** Abra el archivo `src/Config.jl` con su editor. **Reemplace TODO el contenido** por el siguiente código completo:

```julia
"""
src/Config.jl
─────────────────────────────────────────────────────────────────────────────
Centraliza TODAS las constantes del sistema:
    • Credenciales de conexión  ← EDITAR ANTES DE EJECUTAR
    • Rutas de archivos locales ← EDITAR si cambian de lugar
    • Parámetros de procesamiento
    • Festivos por país (Colombia y Argentina)
    • Columnas y prefijos de novedades
─────────────────────────────────────────────────────────────────────────────
"""
module Config

using Dates

# ── SECCIÓN DE CREDENCIALES — EDITAR ANTES DE EJECUTAR ───────────────────

# Azure Synapse — servidor compartido para AMBOS países
const SYNAPSE_SERVER   = "asasolvodataecosystemdev-ondemand.sql.azuresynapse.net"
const SYNAPSE_PORT     = 1433

# Base de datos Colombia
const SYNAPSE_DATABASE_CO = "midasoft"

# Base de datos Argentina (folder MidasoftArgentina)
const SYNAPSE_DATABASE_AR = "MidasoftArgentina"

# Autenticación
const SYNAPSE_AUTH_MODE = "AAD_INTEGRATED"  # CAMBIAR si desea modo diferente
const SYNAPSE_USER     = ""                 # CAMBIAR si usa AAD_PASSWORD o SQL
const SYNAPSE_PASSWORD = ""

# Driver ODBC
const ODBC_DRIVER = "ODBC Driver 18 for SQL Server"

# SharePoint (Novedades.xlsx) — igual para ambos países
const SHAREPOINT_SITE    = "https://onesourcecorp.sharepoint.com/sites/SolvoGlobal"
const SHAREPOINT_ITEM_ID = ""
const SHAREPOINT_LIBRARY = ""
const SHAREPOINT_USER     = ""
const SHAREPOINT_PASSWORD = ""

# Azure AD
const AZURE_TENANT_ID = "a5ec6523-d52d-443d-bebc-eecf13aae7ac"
const AZURE_CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"

# Archivos locales
const ROSTER_FILE    = raw"C:\Users\Santiago.Betancur\OneDrive - Employer Solutions\Desktop\PTO\Roster.xlsx"
const TYPES_PTO_FILE = raw"C:\Users\Santiago.Betancur\OneDrive - Employer Solutions\Desktop\PTO\PTO\TYPES OF PTO.xlsx"

# ── PARÁMETROS DEL SISTEMA ────────────────────────────────────────────────

# Directorio raíz de salida
const OUTPUT_DIR = joinpath(@__DIR__, "..", "output")

# Subdirectorio por país
country_output_dir(country::Symbol) = joinpath(OUTPUT_DIR, string(country))

# Rutas de Def por país
country_def_xlsx(country::Symbol) = joinpath(country_output_dir(country), "Def.xlsx")
country_def_csv(country::Symbol)  = joinpath(country_output_dir(country), "Def.csv")

# Retrocompatibilidad (Colombia por defecto)
const DEF_XLSX = country_def_xlsx(:CO)
const DEF_CSV  = country_def_csv(:CO)

const LOGS_DIR = joinpath(@__DIR__, "..", "logs")

# Filtro de fecha mínima
const FECHA_MINIMA = Date(2025, 1, 1)

# Filtro SOLID por país
const SOLID_FILTER_CO = "SOLA"
const SOLID_FILTER_AR = "SOLA"   # ← CAMBIAR si Argentina usa prefijo distinto

country_solid_filter(country::Symbol) =
    country == :AR ? SOLID_FILTER_AR : SOLID_FILTER_CO

# Tamaño de sub-núcleo
const SUBCORE_SIZE = 500

# Prefijos de núcleos (iguales para ambos países)
const PREFIX_VAC = "VAC"
const PREFIX_INC = "INC"
const PREFIX_AUS = "AUS"

# Jerarquía de prioridad
const PRIORITY = Dict(PREFIX_INC => 3, PREFIX_AUS => 2, PREFIX_VAC => 1)

# ── NOMBRES DE TABLAS POR PAÍS ────────────────────────────────────────────

# Colombia
const TABLE_AUS_CO = "ausentismos"
const TABLE_INC_CO = "incapacidades"
const TABLE_VAC_CO = "vacaciones"

# Argentina
const TABLE_AUS_AR = "AusentismosArgentina"
const TABLE_INC_AR = "IncapacidadesArgentina"
const TABLE_VAC_AR = "VacacionesArgentina"

function country_tables(country::Symbol)
    if country == :AR
        return (aus = TABLE_AUS_AR, inc = TABLE_INC_AR, vac = TABLE_VAC_AR)
    else
        return (aus = TABLE_AUS_CO, inc = TABLE_INC_CO, vac = TABLE_VAC_CO)
    end
end

# ── NOVEDADES EXCLUIDAS ───────────────────────────────────────────────────

const EXCLUDED_NOVEDADES = Set([
    "0", "Actualización de Líder", "Actualización de Supervisor",
    "Apercibimiento", "Ascenso", "Asignacion de Cuenta",
    "Ausencia pendiente por reporte", "Cambio de cargo",
    "Cambio de Departamento", "Cambio de horario", "Cambio de modalidad",
    "Cambio de Sede", "Carta de compromiso", "Cierre de cuenta",
    "Demotion", "Despido", "Festivo Americano laborado",
    "Festivo argentino laborado", "Festivo colombiano laborado",
    "Festivo estadounidense laborado", "Festivo no laborado",
    "Horas extra", "Horas extra nocturna", "Horas extras",
    "Lactancia", "No Call/No Show", "Posicion Ganada",
    "Posición Ganada", "Posicion Perdida", "Promoción",
    "Promocion de Lider", "Reemplazo", "Renuncia", "Reporte de Sede",
    "Salida de cuenta - Ingreso a Transición", "Separación de Cargo",
    "Separación de cargo", "Terminación de práctica", "Warning email",
    "Warning escrito", "Warning verbal", "Workation", "Workstoppage",
])

# ── FESTIVOS COLOMBIA 2024 – 2027 ────────────────────────────────────────

const FESTIVOS_COLOMBIA = Set([
    # 2024
    Date(2024,1,1),  Date(2024,1,8),  Date(2024,3,25), Date(2024,3,28),
    Date(2024,3,29), Date(2024,5,1),  Date(2024,5,13), Date(2024,6,3),
    Date(2024,6,10), Date(2024,7,1),  Date(2024,7,20), Date(2024,8,7),
    Date(2024,8,19), Date(2024,10,14),Date(2024,11,4), Date(2024,11,11),
    Date(2024,12,8), Date(2024,12,25),
    # 2025
    Date(2025,1,1),  Date(2025,1,6),  Date(2025,3,24), Date(2025,4,17),
    Date(2025,4,18), Date(2025,5,1),  Date(2025,6,2),  Date(2025,6,23),
    Date(2025,6,30), Date(2025,7,20), Date(2025,8,7),  Date(2025,8,18),
    Date(2025,10,13),Date(2025,11,3), Date(2025,11,17),Date(2025,12,8),
    Date(2025,12,25),
    # 2026
    Date(2026,1,1),  Date(2026,1,12), Date(2026,3,23), Date(2026,4,2),
    Date(2026,4,3),  Date(2026,5,1),  Date(2026,5,18), Date(2026,6,8),
    Date(2026,6,29), Date(2026,7,20), Date(2026,8,7),  Date(2026,8,17),
    Date(2026,10,12),Date(2026,11,2), Date(2026,11,16),Date(2026,12,8),
    Date(2026,12,25),
    # 2027
    Date(2027,1,1),  Date(2027,1,11), Date(2027,3,22), Date(2027,4,1),
    Date(2027,4,2),  Date(2027,5,1),  Date(2027,5,17), Date(2027,6,7),
    Date(2027,6,28), Date(2027,7,20), Date(2027,8,7),  Date(2027,8,16),
    Date(2027,10,18),Date(2027,11,1), Date(2027,11,15),Date(2027,12,8),
    Date(2027,12,25),
])

# ── FESTIVOS ARGENTINA 2024 – 2027 ───────────────────────────────────────
# Fuente: Ley 27.399 + Decretos anuales publicados en Boletín Oficial.
# Los feriados trasladables se ajustan al lunes anterior (si caen mar/mié)
# o al lunes siguiente (si caen jue/vie). Verifique fechas trasladables
# contra https://www.argentina.gob.ar/interior/feriados cada año.

const FESTIVOS_ARGENTINA = Set([
    # 2024
    Date(2024,1,1),   # Año Nuevo
    Date(2024,2,12),  # Carnaval lunes
    Date(2024,2,13),  # Carnaval martes
    Date(2024,3,24),  # Memoria (inamovible)
    Date(2024,3,29),  # Viernes Santo
    Date(2024,4,2),   # Malvinas (inamovible)
    Date(2024,5,1),   # Trabajadores (inamovible)
    Date(2024,5,25),  # Rev. Mayo (inamovible)
    Date(2024,6,17),  # Güemes (trasladado)
    Date(2024,6,20),  # Belgrano (inamovible)
    Date(2024,7,9),   # Independencia (inamovible)
    Date(2024,8,19),  # San Martín (trasladado: 17 ago sáb → lun 19)
    Date(2024,10,14), # Diversidad Cultural (trasladado: 12 oct sáb → lun 14)
    Date(2024,11,18), # Soberanía (trasladado: 20 nov mié → lun 18)
    Date(2024,12,8),  # Inmaculada Concepción (inamovible)
    Date(2024,12,25), # Navidad (inamovible)
    # 2025
    Date(2025,1,1),   # Año Nuevo
    Date(2025,3,3),   # Carnaval lunes
    Date(2025,3,4),   # Carnaval martes
    Date(2025,3,24),  # Memoria (inamovible)
    Date(2025,4,2),   # Malvinas (inamovible)
    Date(2025,4,18),  # Viernes Santo
    Date(2025,5,1),   # Trabajadores (inamovible)
    Date(2025,5,25),  # Rev. Mayo (inamovible)
    Date(2025,6,16),  # Güemes (trasladado: 17 jun mar → lun 16)
    Date(2025,6,20),  # Belgrano (inamovible)
    Date(2025,7,9),   # Independencia (inamovible)
    Date(2025,8,18),  # San Martín (trasladado: 17 ago dom → lun 18)
    Date(2025,10,13), # Diversidad (trasladado: 12 oct dom → lun 13)
    Date(2025,11,24), # Soberanía (trasladado: 20 nov jue → lun 24)
    Date(2025,12,8),  # Inmaculada (inamovible)
    Date(2025,12,25), # Navidad (inamovible)
    # 2026
    Date(2026,1,1),   # Año Nuevo
    Date(2026,2,16),  # Carnaval lunes
    Date(2026,2,17),  # Carnaval martes
    Date(2026,3,24),  # Memoria (inamovible)
    Date(2026,4,2),   # Malvinas (inamovible)
    Date(2026,4,3),   # Viernes Santo
    Date(2026,5,1),   # Trabajadores (inamovible)
    Date(2026,5,25),  # Rev. Mayo (inamovible)
    Date(2026,6,15),  # Güemes (trasladado: 17 jun mié → lun 15)
    Date(2026,6,20),  # Belgrano (inamovible)
    Date(2026,7,9),   # Independencia (inamovible)
    Date(2026,8,17),  # San Martín (ya cae en lunes)
    Date(2026,10,12), # Diversidad (ya cae en lunes)
    Date(2026,11,23), # Soberanía (trasladado: 20 nov vie → lun 23)
    Date(2026,12,8),  # Inmaculada (inamovible)
    Date(2026,12,25), # Navidad (inamovible)
    # 2027
    Date(2027,1,1),   # Año Nuevo
    Date(2027,2,8),   # Carnaval lunes
    Date(2027,2,9),   # Carnaval martes
    Date(2027,3,24),  # Memoria (inamovible)
    Date(2027,3,26),  # Viernes Santo
    Date(2027,4,2),   # Malvinas (inamovible)
    Date(2027,5,1),   # Trabajadores (inamovible)
    Date(2027,5,25),  # Rev. Mayo (inamovible)
    Date(2027,6,20),  # Belgrano (inamovible)
    Date(2027,6,21),  # Güemes (trasladado: 17 jun jue → lun 21)
    Date(2027,7,9),   # Independencia (inamovible)
    Date(2027,8,16),  # San Martín (trasladado: 17 ago mar → lun 16)
    Date(2027,10,11), # Diversidad (trasladado: 12 oct mar → lun 11)
    Date(2027,11,22), # Soberanía (trasladado: 20 nov sáb → lun 22)
    Date(2027,12,8),  # Inmaculada (inamovible)
    Date(2027,12,25), # Navidad (inamovible)
])

# ── Función helper: obtener festivos por país ─────────────────────────────

function country_festivos(country::Symbol)::Set{Date}
    country == :AR ? FESTIVOS_ARGENTINA : FESTIVOS_COLOMBIA
end

# ── COLUMNAS DEL DEF ──────────────────────────────────────────────────────

const DEF_COLUMNS = [
    "INDEX", "ID", "Column1", "LISTO", "SOLID",
    "Fecha Salida", "Fecha Llegada", "Nombre y Apellido",
    "Novedad", "Numero novedad", "Dias (Numeros)", "Horas (Numeros)",
    "Date of PTO", "Horas", "Hours of PTO", "Column2",
    "IN/OUT", "PROCESADA",
]

# ── Nombre legible del país ───────────────────────────────────────────────

country_name(country::Symbol) = country == :AR ? "Argentina" : "Colombia"
country_prefix(country::Symbol) = string(country)  # "CO" o "AR"

end # module Config
```

---

# PASO 2 — Modificar `src/SynapseConnector.jl`

**Qué hacer:** Abra `src/SynapseConnector.jl` y **reemplace TODO el contenido** por este código. La diferencia principal es que ahora `fetch_all_from_synapse` acepta un parámetro `country::Symbol` y adapta el nombre de la base de datos y las tablas:

```julia
"""
src/SynapseConnector.jl
─────────────────────────────────────────────────────────────────────────────
Conecta a Azure Synapse y descarga las tres tablas para el país indicado.

Colombia (:CO) → base midasoft, tablas: ausentismos / incapacidades / vacaciones
Argentina (:AR) → base MidasoftArgentina, tablas: AusentismosArgentina /
                  IncapacidadesArgentina / VacacionesArgentina

Si alguna columna necesaria no existe en la tabla del país, se muestra
un mensaje descriptivo y la tabla se retorna vacía (sin abortar todo).
─────────────────────────────────────────────────────────────────────────────
"""
module SynapseConnector

using DataFrames, ODBC, Dates, Logging, Printf
using ..Config

export fetch_all_from_synapse

# ── Connection string ──────────────────────────────────────────────────────

function build_connection_string(database::String)::String
    base =  "Driver={$(Config.ODBC_DRIVER)};" *
            "Server=$(Config.SYNAPSE_SERVER),$(Config.SYNAPSE_PORT);" *
            "Database=$(database);" *
            "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=360;"

    if Config.SYNAPSE_AUTH_MODE == "AAD_PASSWORD"
        return base *
                "Authentication=ActiveDirectoryPassword;" *
                "UID=$(Config.SYNAPSE_USER);" *
                "PWD=$(Config.SYNAPSE_PASSWORD);"
    elseif Config.SYNAPSE_AUTH_MODE == "AAD_INTEGRATED"
        return base * "Authentication=ActiveDirectoryIntegrated;"
    elseif Config.SYNAPSE_AUTH_MODE == "SQL"
        return base *
                "UID=$(Config.SYNAPSE_USER);" *
                "PWD=$(Config.SYNAPSE_PASSWORD);"
    else
        error("SYNAPSE_AUTH_MODE desconocido: $(Config.SYNAPSE_AUTH_MODE).")
    end
end

# ── Helpers de conversión ──────────────────────────────────────────────────

safe_str(v)  = ismissing(v) ? "" : strip(string(v))
safe_date(v) = begin
    ismissing(v) && return missing
    v isa Date && return v
    v isa DateTime && return Date(v)
    tryparse(Date, string(v))
end
safe_num(v) = begin
    ismissing(v) && return missing
    v isa Number && return Float64(v)
    r = tryparse(Float64, string(v)); isnothing(r) ? missing : r
end

# ── Validación de columnas requeridas en tabla ─────────────────────────────

"""
    check_required_columns(conn, table, required_cols) -> Bool

Consulta las columnas que existen en `table` y avisa si falta alguna de
`required_cols`. Retorna true si todas existen, false en caso contrario.
"""
function check_required_columns(conn, table::String, required_cols::Vector{String})::Bool
    sql_cols = """
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = '$table'
    """
    existing = try
        df = DBInterface.execute(conn, sql_cols) |> DataFrame
        Set(uppercase.(string.(df.COLUMN_NAME)))
    catch e
        @warn "No se pudo verificar columnas de $table: $e"
        return true   # asumir OK si no se puede verificar
    end

    missing_cols = [c for c in required_cols if uppercase(c) ∉ existing]
    if !isempty(missing_cols)
        @error """
        ⚠ COLUMNAS FALTANTES en la tabla '$table':
          Columnas requeridas que NO se encontraron:
            $(join(missing_cols, "\n            "))
          Verifique que la tabla tenga estas columnas en la base de datos.
        """
        return false
    end
    return true
end

# ── Queries SQL por país ───────────────────────────────────────────────────

function build_sql_ausentismos(table::String, solid_filter::String, fecha_minima::Date)::String
    """
    SELECT
        UPPER(CAST(Empleado AS NVARCHAR(50)))    AS SOLID,
        CAST(Finir  AS DATE)                     AS Fecha_Salida,
        CAST(ISNULL(Ffinr, Finir) AS DATE)       AS Fecha_Llegada,
        LTRIM(RTRIM(Nombre)) + ' ' +
        LTRIM(RTRIM(Apellido))                   AS Nombre_y_Apellido,
        LTRIM(RTRIM(DescAusencia))               AS Novedad,
        'AUS-' + LTRIM(RTRIM(CAST(NAusencia AS NVARCHAR(20)))) AS Numero_novedad,
        NULL                                     AS Dias_Numeros,
        CAST(Horas AS FLOAT)                     AS Horas_Numeros
    FROM dbo.$(table)
    WHERE Finir IS NOT NULL
        AND UPPER(CAST(Empleado AS NVARCHAR(50))) LIKE '%$(solid_filter)%'
        AND CAST(Finir AS DATE) >= '$(fecha_minima)'
    ORDER BY Fecha_Salida ASC
    """
end

function build_sql_incapacidades(table::String, solid_filter::String, fecha_minima::Date)::String
    """
    SELECT
        UPPER(CAST(Empleado AS NVARCHAR(50)))    AS SOLID,
        CAST(Finir  AS DATE)                     AS Fecha_Salida,
        CAST(ISNULL(Ffinr, Finir) AS DATE)       AS Fecha_Llegada,
        LTRIM(RTRIM(Nombre)) + ' ' +
        LTRIM(RTRIM(Apellido))                   AS Nombre_y_Apellido,
        CASE LTRIM(RTRIM(DescInc))
            WHEN 'INC ENFERMEDAD GENERAL INTEGRA' THEN 'INC ENFERMEDAD GENERAL'
            WHEN 'INCAPACIDAD MAYOR 90 DIAS'       THEN 'INC ENFERMEDAD GENERAL'
            WHEN 'INCAPACIDAD MAYOR A 180 DIAS'    THEN 'INC ENFERMEDAD GENERAL'
            WHEN 'INCAPACIDAD MAYOR A 542 DIAS'    THEN 'MATERNIDAD'
            ELSE LTRIM(RTRIM(DescInc))
        END                                      AS Novedad,
        'INC-' + LTRIM(RTRIM(CAST(Cnsine AS NVARCHAR(20)))) AS Numero_novedad,
        CAST(DIncapc AS BIGINT)                  AS Dias_Numeros,
        NULL                                     AS Horas_Numeros
    FROM dbo.$(table)
    WHERE Finir IS NOT NULL
        AND UPPER(CAST(Empleado AS NVARCHAR(50))) LIKE '%$(solid_filter)%'
        AND CAST(Finir AS DATE) >= '$(fecha_minima)'
    ORDER BY Fecha_Salida ASC
    """
end

function build_sql_vacaciones(table::String, solid_filter::String, fecha_minima::Date)::String
    """
    SELECT
        UPPER(CAST(Empleado AS NVARCHAR(50)))    AS SOLID,
        CAST(Empleado AS NVARCHAR(50))           AS Empleado_Raw,
        CAST(FSalR AS DATE)                      AS Fecha_Salida,
        CAST(ISNULL(FRegR, FSalR) AS DATE)       AS Fecha_Llegada,
        LTRIM(RTRIM(Apellido))                   AS Apellido,
        'VACACIONES'                             AS Novedad,
        'VAC-' + LTRIM(RTRIM(CAST(Cnsvac AS NVARCHAR(20)))) AS Numero_novedad,
        CAST(DiasVac AS BIGINT)                  AS Dias_Numeros,
        NULL                                     AS Horas_Numeros
    FROM dbo.$(table)
    WHERE FSalR IS NOT NULL
        AND UPPER(CAST(Empleado AS NVARCHAR(50))) LIKE '%$(solid_filter)%'
        AND CAST(FSalR AS DATE) >= '$(fecha_minima)'
    ORDER BY Fecha_Salida ASC
    """
end

function build_sql_solid_name(table_aus::String, table_inc::String)::String
    """
    SELECT DISTINCT
        CAST(Empleado AS NVARCHAR(50))           AS Empleado,
        LTRIM(RTRIM(Nombre)) + ' ' +
        LTRIM(RTRIM(Apellido))                   AS Nombre_y_Apellido
    FROM (
        SELECT Empleado, Nombre, Apellido FROM dbo.$(table_aus)
        UNION ALL
        SELECT Empleado, Nombre, Apellido FROM dbo.$(table_inc)
    ) t
    WHERE Empleado IS NOT NULL
    """
end

# ── Ejecución de queries ───────────────────────────────────────────────────

function run_query(conn, sql::String, label::String)::Union{DataFrame, Nothing}
    try
        df = DBInterface.execute(conn, sql) |> DataFrame
        println("     ✓ $label: $(nrow(df)) filas")
        return df
    catch e
        @error "Error ejecutando query '$label': $e"
        return nothing
    end
end

# ── API pública ────────────────────────────────────────────────────────────

"""
    fetch_all_from_synapse(country) -> NamedTuple | nothing

Conecta a Azure Synapse para el país indicado (:CO o :AR),
descarga las tres tablas y el mapa SOLID→Nombre.
Valida que las columnas necesarias existan antes de ejecutar.
"""
function fetch_all_from_synapse(country::Symbol = :CO)::Union{NamedTuple, Nothing}
    database = country == :AR ? Config.SYNAPSE_DATABASE_AR : Config.SYNAPSE_DATABASE_CO
    tables   = Config.country_tables(country)
    solid_filter = Config.country_solid_filter(country)
    pais     = Config.country_name(country)

    println("   Conectando a Azure Synapse para $(pais)...")
    println("   Servidor:    $(Config.SYNAPSE_SERVER)")
    println("   Base de datos: $(database)")
    println("   Modo de auth:  $(Config.SYNAPSE_AUTH_MODE)")
    println("   Tablas:        $(tables.aus) | $(tables.inc) | $(tables.vac)")

    conn = try
        ODBC.Connection(build_connection_string(database))
    catch e
        @error """
        No se pudo conectar a Azure Synapse ($(pais)).
        Error: $e

        Verifique en src/Config.jl:
            • SYNAPSE_AUTH_MODE  (AAD_PASSWORD / AAD_INTEGRATED / SQL)
            • ODBC_DRIVER        (nombre exacto del driver instalado)
            • Base de datos:     $(database)
        """
        return nothing
    end

    println("   ✓ Conexión establecida. Validando columnas y descargando...\n")

    # Columnas requeridas por tabla
    cols_aus = ["Empleado","Finir","Ffinr","Nombre","Apellido","DescAusencia","NAusencia","Horas"]
    cols_inc = ["Empleado","Finir","Ffinr","Nombre","Apellido","DescInc","Cnsine","DIncapc"]
    cols_vac = ["Empleado","FSalR","FRegR","Apellido","Cnsvac","DiasVac"]

    ok_aus = check_required_columns(conn, tables.aus, cols_aus)
    ok_inc = check_required_columns(conn, tables.inc, cols_inc)
    ok_vac = check_required_columns(conn, tables.vac, cols_vac)

    aus_df = ok_aus ? run_query(conn,
        build_sql_ausentismos(tables.aus, solid_filter, Config.FECHA_MINIMA),
        "$(tables.aus) [$(pais)]") : nothing

    inc_df = ok_inc ? run_query(conn,
        build_sql_incapacidades(tables.inc, solid_filter, Config.FECHA_MINIMA),
        "$(tables.inc) [$(pais)]") : nothing

    vac_df = ok_vac ? run_query(conn,
        build_sql_vacaciones(tables.vac, solid_filter, Config.FECHA_MINIMA),
        "$(tables.vac) [$(pais)]") : nothing

    solid_name_df = run_query(conn,
        build_sql_solid_name(tables.aus, tables.inc),
        "SOLID & NAME map [$(pais)]")

    DBInterface.close!(conn)
    println("\n   Conexión cerrada ($(pais)).")

    solid_name_map = Dict{String,String}()
    if !isnothing(solid_name_df)
        for r in eachrow(solid_name_df)
            k = safe_str(r.Empleado)
            v = safe_str(r.Nombre_y_Apellido)
            !isempty(k) && !isempty(v) && (solid_name_map[k] = v)
        end
    end

    return (
        aus            = aus_df,
        inc            = inc_df,
        vac            = vac_df,
        solid_name_map = solid_name_map,
        country        = country,
    )
end

end # module SynapseConnector
```

---

# PASO 3 — Modificar `src/DataLoader.jl`

**Qué hacer:** Abra `src/DataLoader.jl` y **reemplace TODO el contenido** por el siguiente código. Los cambios principales: la función pública `load_all_sources` ahora acepta un parámetro `country::Symbol`, y el festivo del país correcto llega desde `Config`:

```julia
"""
src/DataLoader.jl
─────────────────────────────────────────────────────────────────────────────
Orquesta todas las fuentes para un país dado (:CO o :AR) y construye
la tabla unificada con Fecha Del Evento expandida.
─────────────────────────────────────────────────────────────────────────────
"""
module DataLoader

using DataFrames, Dates, Logging
using ..Config
using ..SynapseConnector
using ..SharePointConnector
using ..LocalFilesConnector

export load_all_sources

# ── Novedades de un solo día ───────────────────────────────────────────────

const SINGLE_DAY_MIDASOFT = Set([
    "DIA DE LA FAMILIA", "PAID LEAVE BIRTHDAY", "PAID LEAVE BREASTFEEDING",
    "PAID LEAVE EXTERNAL TOPICS", "PAID LEAVE MEDICAL APPOINTMENT",
    "PAID LEAVE PERSONAL TOPICS", "PAID LEAVE TECH ISSUES", "PAID LEAVE TRAINING",
])

const SINGLE_DAY_FORMS = Set([
    "Cita médica", "Día de la Familia", "Día de la Familia (Día libre)",
    "Día de la familia", "Flexisolvo", "Llegada tarde", "Llegadas tarde",
    "PAID LEAVE BIRTHDAY", "Salida temprano", "Salidas temprano",
])

# ── Helpers ────────────────────────────────────────────────────────────────

safe_f64(v) = ismissing(v) ? 0.0 : Float64(v)

function workdays_in_range(d1::Date, d2::Date)::Vector{Date}
    d1, d2 = min(d1, d2), max(d1, d2)
    filter(d -> Dates.dayofweek(d) ∉ (6, 7), collect(d1:Day(1):d2))
end

function novedad_tipo(nov::AbstractString)::Symbol
    u = uppercase(strip(nov))
    occursin("VAC", u) && return :VAC
    (occursin("INC", u) || occursin("MATERNI", u) || occursin("PATERNI", u)) && return :INC
    return :AUS
end

# ── Expansión de Fecha Del Evento ──────────────────────────────────────────

function fecha_evento_range(
    tipo::Symbol, novedad::String, fs::Date, fl::Date,
    horas::Float64, source::Symbol,
)::Vector{Date}
    single_day_set = source == :midasoft ? SINGLE_DAY_MIDASOFT : SINGLE_DAY_FORMS
    if novedad in single_day_set
        return filter(d -> Dates.dayofweek(d) ∉ (6, 7), [fs])
    end
    if source == :midasoft && novedad == "FLEXI SOLVO" && (horas <= 9 || horas > 18)
        return filter(d -> Dates.dayofweek(d) ∉ (6, 7), [fs])
    end
    if tipo == :VAC
        fs >= fl && return filter(d -> Dates.dayofweek(d) ∉ (6, 7), [fs])
        return workdays_in_range(fs, fl - Day(1))
    else
        fs >= fl && return filter(d -> Dates.dayofweek(d) ∉ (6, 7), [fs])
        return workdays_in_range(fs, fl)
    end
end

# ── Expansión de un DataFrame ──────────────────────────────────────────────

function expand_rows(df::DataFrame, source::Symbol)::DataFrame
    isempty(df) && return df
    expanded = []
    for r in eachrow(df)
        fs = get(r, :Fecha_Salida, missing)
        fl = get(r, :Fecha_Llegada, missing)
        ismissing(fs) && continue
        ismissing(fl) && (fl = fs)

        novedad   = string(coalesce(get(r, :Novedad, ""), ""))
        dias_num  = safe_f64(get(r, :Dias_Numeros, missing))
        horas_num = safe_f64(get(r, :Horas_Numeros, missing))
        num_nov   = string(coalesce(get(r, :Numero_novedad, ""), ""))
        horas_total = dias_num * 8.0 + horas_num

        tipo = let p = length(num_nov) >= 3 ? uppercase(num_nov[1:3]) : ""
            p == "VAC" ? :VAC : p == "INC" ? :INC : p == "AUS" ? :AUS :
            novedad_tipo(novedad)
        end

        fechas = fecha_evento_range(tipo, novedad, fs, fl, horas_total, source)

        for fde in fechas
            tiempo_afec = if horas_total >= 8.0
                8.0
            elseif horas_total > 7.0
                ceil(horas_total)
            else
                ceil(horas_total * 100) / 100
            end
            dow = Dates.dayofweek(fde)
            weekday_pq = dow % 7
            push!(expanded, (
                SOLID             = string(coalesce(get(r, :SOLID, ""), "")),
                Fecha_Salida      = fs,
                Fecha_Llegada     = fl,
                Nombre_y_Apellido = string(coalesce(get(r, :Nombre_y_Apellido, ""), "")),
                Novedad           = novedad,
                Numero_novedad    = num_nov,
                Dias_Numeros      = dias_num > 0 ? dias_num : missing,
                Horas_Numeros     = horas_num > 0 ? horas_num : missing,
                Fecha_Del_Evento  = fde,
                Horas_total       = horas_total,
                Tiempo_Afectacion = tiempo_afec,
                Hours_of_PTO      = tiempo_afec,
                Weekday           = weekday_pq,
                _source           = source,
                _tipo             = tipo,
            ))
        end
    end
    isempty(expanded) && return DataFrame()
    return DataFrame(expanded)
end

# ── Tabla Midasoft ─────────────────────────────────────────────────────────

function build_midasoft_table(synapse_data::NamedTuple)::DataFrame
    aus = synapse_data.aus
    inc = synapse_data.inc
    vac = synapse_data.vac
    solid_name_map = synapse_data.solid_name_map
    parts = DataFrame[]

    !isnothing(aus) && nrow(aus) > 0 && push!(parts, expand_rows(aus, :midasoft))
    !isnothing(inc) && nrow(inc) > 0 && push!(parts, expand_rows(inc, :midasoft))

    if !isnothing(vac) && nrow(vac) > 0
        vac.Nombre_y_Apellido = [
            get(solid_name_map,
                string(coalesce(get(r, :Empleado_Raw, ""), "")),
                string(coalesce(get(r, :Apellido, ""), "")))
            for r in eachrow(vac)
        ]
        push!(parts, expand_rows(vac, :midasoft))
    end

    isempty(parts) && return DataFrame()
    combined = vcat(parts...; cols=:union)
    sort!(combined, :Fecha_Salida)
    println("   Nov Midasoft: $(nrow(combined)) filas expandidas.")
    return combined
end

# ── Tabla Forms ────────────────────────────────────────────────────────────

function build_forms_table(forms_df::DataFrame)::DataFrame
    isempty(forms_df) && return DataFrame()
    expanded = expand_rows(forms_df, :forms)
    sort!(expanded, :Fecha_Salida)
    println("   Nov Forms: $(nrow(expanded)) filas expandidas.")
    return expanded
end

# ── Enriquecimiento con lookups ────────────────────────────────────────────

function enrich_with_lookups(unified, types_df, roster_df)
    if !isnothing(types_df) && "Novedad" ∈ names(unified)
        try unified = leftjoin(unified, types_df; on=:Novedad, makeunique=true)
        catch e; @warn "No se pudo hacer join con Types_of_PTO: $e"; end
    end
    if !isnothing(roster_df) && "SOLID" ∈ names(unified)
        try unified = leftjoin(unified, roster_df; on=:SOLID, makeunique=true)
        catch e; @warn "No se pudo hacer join con Roster: $e"; end
    end
    for col in ["SOLID", "Nombre_y_Apellido", "Novedad", "Numero_novedad"]
        col ∈ names(unified) &&
            (unified[!, col] = strip.(string.(coalesce.(unified[!, col], ""))))
    end
    return unified
end

# ── API pública ────────────────────────────────────────────────────────────

"""
    load_all_sources(country=:CO) -> DataFrame | nothing

Descarga y unifica todas las fuentes para el país indicado.
:CO = Colombia (default), :AR = Argentina.
"""
function load_all_sources(country::Symbol = :CO)::Union{DataFrame, Nothing}
    pais = Config.country_name(country)

    println("\n  [1/4] Conectando a Azure Synapse (Midasoft — $(pais))...")
    synapse_data = SynapseConnector.fetch_all_from_synapse(country)
    if isnothing(synapse_data)
        @error "No se pudo conectar a Synapse para $(pais). Abortando."
        return nothing
    end

    println("\n  [2/4] Descargando Novedades.xlsx desde SharePoint...")
    forms_df = SharePointConnector.fetch_novedades_from_sharepoint()
    if isnothing(forms_df)
        @warn "No se pudo obtener Forms de SharePoint. Se procesará solo Midasoft."
        forms_df = DataFrame()
    end

    println("\n  [3/4] Cargando archivos locales (Roster, Types of PTO)...")
    roster_df    = LocalFilesConnector.load_roster()
    types_pto_df = LocalFilesConnector.load_types_of_pto()

    println("\n  [4/4] Procesando y unificando fuentes ($(pais))...")
    midasoft_expanded = build_midasoft_table(synapse_data)
    forms_expanded    = isempty(forms_df) ? DataFrame() : build_forms_table(forms_df)

    parts = DataFrame[]
    !isempty(midasoft_expanded) && push!(parts, midasoft_expanded)
    !isempty(forms_expanded)    && push!(parts, forms_expanded)

    if isempty(parts)
        @error "No se obtuvieron datos de ninguna fuente para $(pais)."
        return nothing
    end

    unified = vcat(parts...; cols=:union)
    unified = enrich_with_lookups(unified, types_pto_df, roster_df)
    sort!(unified, :Fecha_Salida)

    println("\n  ✓ [$(pais)] Tabla unificada: $(nrow(unified)) filas, $(ncol(unified)) columnas.")
    return unified
end

end # module DataLoader
```

---

# PASO 4 — Modificar `src/Validator.jl`

**Qué hacer:** En `src/Validator.jl` hay que cambiar **únicamente** la función `count_festivos` (línea 95 aproximadamente) para que use los festivos del país correcto, y agregar un método con parámetro de país.

Busque esta línea exacta en el archivo:
```julia
count_festivos(dates) = count(d -> d ∈ Config.FESTIVOS_COLOMBIA, dates)
```

**Reemplácela** por estas dos líneas:
```julia
count_festivos(dates) = count(d -> d ∈ Config.FESTIVOS_COLOMBIA, dates)
count_festivos_country(dates, country::Symbol) = count(d -> d ∈ Config.country_festivos(country), dates)
```

Luego busque la función `validate_vac` (aproximadamente en la línea 154). Dentro de ella, busque esta línea:
```julia
        fest      = count_festivos(fechas)
```

**Reemplácela** por:
```julia
        fest      = count_festivos_country(fechas, get(sub[1,:], :_country, :CO))
```

Luego busque la función `validate_group` (al final del archivo, línea ~523). Localice su firma:
```julia
function validate_group(
    ids::Vector{String},
    unified::DataFrame,
    nucleus_type::Symbol,
    id_index::Dict{String,Int} = Dict{String,Int}(),
)::Vector{ValidResult}
```

**Reemplácela** por (agrega parámetro `country`):
```julia
function validate_group(
    ids::Vector{String},
    unified::DataFrame,
    nucleus_type::Symbol,
    id_index::Dict{String,Int} = Dict{String,Int}(),
    country::Symbol = :CO,
)::Vector{ValidResult}
```

> **Nota:** Para que el parámetro `country` llegue a `validate_vac`, la forma más limpia es agregar una columna `_country` al DataFrame `unified` en `main.jl` antes de procesar. Eso se hace en el PASO 8.

---

# PASO 5 — Modificar `src/DefManager.jl`

**Qué hacer:** Abra `src/DefManager.jl`. Busque la función `load_def` (actualmente usa `Config.DEF_XLSX` y `Config.DEF_CSV`). Localice estas líneas:

```julia
function load_def()::DataFrame
    xlsx_path = Config.DEF_XLSX
    csv_path  = Config.DEF_CSV
```

**Reemplácelas** por:
```julia
function load_def(country::Symbol = :CO)::DataFrame
    xlsx_path = Config.country_def_xlsx(country)
    csv_path  = Config.country_def_csv(country)
```

Luego busque la función `save_def`:
```julia
function save_def(def_df::DataFrame)
    isdir(Config.OUTPUT_DIR) || mkpath(Config.OUTPUT_DIR)

    # XLSX
    try
        XLSX.openxlsx(Config.DEF_XLSX; mode="w") do xf
```

**Reemplácela** por:
```julia
function save_def(def_df::DataFrame, country::Symbol = :CO)
    out_dir = Config.country_output_dir(country)
    isdir(out_dir) || mkpath(out_dir)

    xlsx_path = Config.country_def_xlsx(country)
    csv_path  = Config.country_def_csv(country)

    # XLSX
    try
        XLSX.openxlsx(xlsx_path; mode="w") do xf
```

Y dentro del mismo bloque, busque la línea que guarda CSV:
```julia
        CSV.write(Config.DEF_CSV, def_df; missingstring="")
```

**Reemplácela** por:
```julia
        CSV.write(csv_path, def_df; missingstring="")
```

---

# PASO 6 — Modificar `src/Exporter.jl`

**Qué hacer:** Abra `src/Exporter.jl`. Busque la función `export_all` y **reemplace toda la firma y su contenido** desde `function export_all(` hasta el `end # module Exporter`, por el siguiente código. El resto del archivo (structs, helpers `write_df_xlsx`, `write_df_csv`, `build_rejected_df`) queda **igual**:

```julia
# API pública

"""
    export_all(proc_state, def_df, unified, country) -> ExportResult

Genera los 6 archivos de salida con prefijo del país.
Todos los archivos van a output/<PAÍS>/ .
"""
function export_all(
    proc_state::ProcessorState,
    def_df::DataFrame,
    unified::DataFrame,
    country::Symbol = :CO,
)::ExportResult

    out_dir = Config.country_output_dir(country)
    isdir(out_dir) || mkpath(out_dir)

    stamp  = Dates.format(today(), "yyyy-mm-dd")
    prefix = Config.country_prefix(country)   # "CO" o "AR"

    # 1. Actualizar Def completo
    println("\n   Actualizando Def histórico ($(Config.country_name(country)))...")
    updated_def = DefManager.update_def(
        def_df,
        proc_state.valid_ids,
        proc_state.out_ids,
        unified,
    )
    DefManager.save_def(updated_def, country)

    # 2. Snapshot del día (solo válidos)
    snap_df = filter(updated_def) do r
        r["IN/OUT"] != "OUT" &&
        string(coalesce(r["INDEX"], "")) != "NOT FOUND"
    end
    snap_xlsx = joinpath(out_dir, "$(prefix)_Def_$(stamp).xlsx")
    snap_csv  = joinpath(out_dir, "$(prefix)_Def_$(stamp).csv")
    write_df_xlsx(snap_xlsx, "Def", snap_df)
    write_df_csv(snap_csv, snap_df)
    println("   ✓ Snapshot $(stamp): $(nrow(snap_df)) novedades válidas → $(snap_xlsx)")

    # 3. Rechazados
    rej_df = build_rejected_df(
        proc_state.rejected_ids,
        proc_state.rejected_reasons,
        unified,
    )
    rej_xlsx = joinpath(out_dir, "$(prefix)_Rejected_$(stamp).xlsx")
    rej_csv  = joinpath(out_dir, "$(prefix)_Rejected_$(stamp).csv")
    write_df_xlsx(rej_xlsx, "Rejected", rej_df)
    write_df_csv(rej_csv, rej_df)
    println("   ✓ Rechazados $(stamp): $(nrow(rej_df)) novedades → $(rej_xlsx)")

    return ExportResult(
        Config.country_def_xlsx(country), Config.country_def_csv(country),
        snap_xlsx, snap_csv,
        rej_xlsx, rej_csv,
        nrow(snap_df), nrow(rej_df),
    )
end

end # module Exporter
```

---

# PASO 7 — Modificar `src/Panel.jl`

Este es el cambio más grande. Se modifican 3 secciones:
- **7A**: Agregar pantalla de selección de país (GTK + terminal)
- **7B**: Agregar los 3 nuevos botones al finalizar
- **7C**: Mejoras visuales al CSS

---

## 7A — Agregar struct CountrySelectionResult y función de selección

**Ubicación:** En `src/Panel.jl`, busque la línea donde están los `export`:
```julia
export run_panel, PanelResult
```

**Reemplácela** por:
```julia
export run_panel, PanelResult, run_country_selector, CountrySelectionResult
```

Luego, justo DESPUÉS de la definición de `struct PanelResult` (que termina en `end`), agregue este nuevo struct y función:

```julia
# ── Resultado de selección de país ────────────────────────────────────────

struct CountrySelectionResult
    country::Symbol          # :CO o :AR
    proceed::Bool            # true = usuario pulsó Procesar; false = canceló
end

# ── Selector de país — panel GTK ──────────────────────────────────────────

"""
    run_country_selector_gtk(available_countries) -> CountrySelectionResult

Muestra una ventana GTK para que el usuario elija Colombia o Argentina.
`available_countries` es un Vector con los símbolos de países que tienen
novedades nuevas (ej: [:CO, :AR]).
"""
function run_country_selector_gtk(available_countries::Vector{Symbol})::CountrySelectionResult
    css_sel = """
    window { background-color: #0d1117; }
    .sel-title {
        font-family: "Consolas","JetBrains Mono",monospace;
        font-size: 18px; font-weight: bold; color: #e6edf3;
    }
    .sel-subtitle {
        font-family: monospace; font-size: 13px; color: #8b949e;
    }
    .btn-co {
        background-color: #1a6b3a; color: #ffffff;
        font-weight: bold; font-size: 14px;
        border-radius: 8px; padding: 12px 32px; border: none;
        min-width: 200px;
    }
    .btn-ar {
        background-color: #5b3ab5; color: #ffffff;
        font-weight: bold; font-size: 14px;
        border-radius: 8px; padding: 12px 32px; border: none;
        min-width: 200px;
    }
    .btn-disabled {
        background-color: #21262d; color: #484f58;
        font-size: 14px; border-radius: 8px;
        padding: 12px 32px; border: 1px solid #30363d;
        min-width: 200px;
    }
    .btn-procesar {
        background-color: #1f6feb; color: #ffffff;
        font-weight: bold; font-size: 14px;
        border-radius: 8px; padding: 12px 40px; border: none;
    }
    .btn-salir-sel {
        background-color: #21262d; color: #8b949e;
        font-size: 12px; border-radius: 6px;
        padding: 8px 20px; border: 1px solid #30363d;
    }
    .badge-ok  { font-family: monospace; font-size: 11px; color: #3fb950; }
    .badge-no  { font-family: monospace; font-size: 11px; color: #484f58; }
    .selected-indicator { font-family: monospace; font-size: 12px; color: #d29922; font-weight: bold; }
    """

    win_sel = GtkWindow("Selección de País — PTO Novedades", 520, 380)
    set_gtk_property!(win_sel, :default_width,  520)
    set_gtk_property!(win_sel, :default_height, 380)
    set_gtk_property!(win_sel, :resizable, false)

    provider_sel = GtkCssProviderLeaf(data = css_sel)
    try
        screen = Gtk.GAccessor.screen(win_sel)
        Gtk.GAccessor.add_provider_for_screen(screen, provider_sel, 600)
    catch
        try
            display = Gtk.GAccessor.display(win_sel)
            Gtk.GAccessor.add_provider_for_display(display, provider_sel, 600)
        catch; end
    end

    outer = GtkBox(:v)
    set_gtk_property!(outer, :margin_top, 28)
    set_gtk_property!(outer, :margin_bottom, 24)
    set_gtk_property!(outer, :margin_start, 32)
    set_gtk_property!(outer, :margin_end, 32)
    set_gtk_property!(outer, :spacing, 16)
    push!(win_sel, outer)

    # Título
    t1 = GtkLabel("🌎  PROCESAMIENTO DE NOVEDADES PTO")
    push!(Gtk.GAccessor.style_context(t1), "sel-title")
    set_gtk_property!(t1, :halign, 1)
    push!(outer, t1)

    t2 = GtkLabel("Seleccione el país a procesar — $(Dates.today())")
    push!(Gtk.GAccessor.style_context(t2), "sel-subtitle")
    set_gtk_property!(t2, :halign, 1)
    push!(outer, t2)

    push!(outer, gtk_separator(:h))

    # Botones de país
    country_box = GtkBox(:h)
    set_gtk_property!(country_box, :spacing, 20)
    set_gtk_property!(country_box, :halign, 3)

    selected_country = Ref{Symbol}(:CO)  # default Colombia

    btn_co = GtkButton("🇨🇴  Colombia")
    btn_ar = GtkButton("🇦🇷  Argentina")

    co_available = :CO ∈ available_countries
    ar_available = :AR ∈ available_countries

    push!(Gtk.GAccessor.style_context(btn_co), co_available ? "btn-co" : "btn-disabled")
    push!(Gtk.GAccessor.style_context(btn_ar), ar_available ? "btn-ar" : "btn-disabled")
    set_gtk_property!(btn_co, :sensitive, co_available)
    set_gtk_property!(btn_ar, :sensitive, ar_available)

    push!(country_box, btn_co)
    push!(country_box, btn_ar)
    push!(outer, country_box)

    # Indicador de selección
    sel_lbl = GtkLabel(co_available ? "▶  Colombia seleccionada" : "▶  Argentina seleccionada")
    push!(Gtk.GAccessor.style_context(sel_lbl), "selected-indicator")
    set_gtk_property!(sel_lbl, :halign, 1)
    push!(outer, sel_lbl)

    # Badges de estado
    badge_box = GtkBox(:v)
    set_gtk_property!(badge_box, :spacing, 4)
    co_badge = GtkLabel(co_available ? "✓ Colombia — tiene novedades nuevas" :
                                        "✗ Colombia — sin novedades nuevas (ya procesado)")
    ar_badge = GtkLabel(ar_available ? "✓ Argentina — tiene novedades nuevas" :
                                        "✗ Argentina — sin novedades nuevas (ya procesado)")
    push!(Gtk.GAccessor.style_context(co_badge), co_available ? "badge-ok" : "badge-no")
    push!(Gtk.GAccessor.style_context(ar_badge), ar_available ? "badge-ok" : "badge-no")
    set_gtk_property!(co_badge, :halign, 1)
    set_gtk_property!(ar_badge, :halign, 1)
    push!(badge_box, co_badge)
    push!(badge_box, ar_badge)
    push!(outer, badge_box)

    push!(outer, gtk_separator(:h))

    # Botones de acción
    action_box = GtkBox(:h)
    set_gtk_property!(action_box, :spacing, 16)
    set_gtk_property!(action_box, :halign, 3)

    btn_proc  = GtkButton("▶  Procesar")
    btn_cerrar = GtkButton("Salir")
    push!(Gtk.GAccessor.style_context(btn_proc),  "btn-procesar")
    push!(Gtk.GAccessor.style_context(btn_cerrar), "btn-salir-sel")
    push!(action_box, btn_proc)
    push!(action_box, btn_cerrar)
    push!(outer, action_box)

    result_holder = Ref{CountrySelectionResult}(
        CountrySelectionResult(co_available ? :CO : :AR, false))

    signal_connect(btn_co, :clicked) do _
        selected_country[] = :CO
        GAccessor.label(sel_lbl, "▶  Colombia seleccionada")
    end
    signal_connect(btn_ar, :clicked) do _
        selected_country[] = :AR
        GAccessor.label(sel_lbl, "▶  Argentina seleccionada")
    end
    signal_connect(btn_proc, :clicked) do _
        result_holder[] = CountrySelectionResult(selected_country[], true)
        _gtk_quit!()
    end
    signal_connect(btn_cerrar, :clicked) do _
        result_holder[] = CountrySelectionResult(selected_country[], false)
        _gtk_quit!()
    end
    signal_connect(win_sel, :destroy) do _
        _gtk_quit!()
    end

    showall(win_sel)
    Gtk.gtk_main()
    destroy(win_sel)
    return result_holder[]
end

# ── Selector de país — terminal ────────────────────────────────────────────

function run_country_selector_terminal(available_countries::Vector{Symbol})::CountrySelectionResult
    clear_screen()
    println(top_border())
    println(row("$(B)$(WH)  PROCESAMIENTO DE NOVEDADES PTO — Solvo Global$(R)"))
    println(row("  $(D)$(Dates.today())$(R)"))
    println(mid_border())
    println(row("  Seleccione el país a procesar:"))
    println(empty_row())

    co_ok = :CO ∈ available_countries
    ar_ok = :AR ∈ available_countries

    println(row("  $(co_ok ? "$(GR)$(B)[1]$(R)$(GR) 🇨🇴  Colombia$(R)" : "$(D)[1] Colombia — sin novedades nuevas$(R)")"))
    println(row("  $(ar_ok ? "$(MG)$(B)[2]$(R)$(MG) 🇦🇷  Argentina$(R)" : "$(D)[2] Argentina — sin novedades nuevas$(R)")"))
    println(empty_row())
    println(row("  $(D)[S] Salir sin procesar$(R)"))
    println(mid_border())

    available_opts = Dict(
        "1" => :CO,
        "2" => :AR,
    )

    print("  Tu selección > ")
    flush(stdout)
    inp = lowercase(strip(readline()))

    inp == "s" && return CountrySelectionResult(:CO, false)

    if haskey(available_opts, inp)
        country = available_opts[inp]
        if country ∈ available_countries
            println("\n  $(GR)✓ Seleccionado: $(Config.country_name(country))$(R)")
            sleep(0.5)
            return CountrySelectionResult(country, true)
        else
            println("\n  $(RD)✗ Ese país no tiene novedades nuevas.$(R)")
            sleep(1)
            return run_country_selector_terminal(available_countries)
        end
    end

    println("\n  $(YL)Opción no reconocida. Intente de nuevo.$(R)")
    sleep(0.8)
    return run_country_selector_terminal(available_countries)
end

"""
    run_country_selector(available_countries) -> CountrySelectionResult

Muestra la pantalla de selección de país (GTK si disponible, sino terminal).
"""
function run_country_selector(available_countries::Vector{Symbol})::CountrySelectionResult
    if gtk_available()
        try
            return run_country_selector_gtk(available_countries)
        catch e
            @warn "GTK selector falló: $(sprint(showerror, e)) — usando terminal"
        end
    end
    return run_country_selector_terminal(available_countries)
end
```

---

## 7B — Cambiar los botones de finalización en el panel GTK

**Ubicación:** En `src/Panel.jl`, busque la función `run_gtk_panel`. Dentro de ella, busque el bloque donde se definen los botones, que actualmente contiene:

```julia
    btn_ok = GtkButton("▶  Finalizar y exportar archivos")
    push!(Gtk.GAccessor.style_context(btn_ok), "btn-finalize")
    set_gtk_property!(btn_ok, :sensitive, false)
    btn_no = GtkButton("Salir sin guardar")
    push!(Gtk.GAccessor.style_context(btn_no), "btn-cancel")
    set_gtk_property!(btn_no, :sensitive, false)
    push!(btn_box, btn_ok)
    push!(btn_box, btn_no)
```

**Reemplácelo** por (3 botones):

```julia
    btn_export_salir  = GtkButton("📥  Exportar y Salir")
    btn_export_volver = GtkButton("🔄  Exportar y Volver")
    btn_solo_salir    = GtkButton("Salir sin guardar")
    push!(Gtk.GAccessor.style_context(btn_export_salir),  "btn-finalize")
    push!(Gtk.GAccessor.style_context(btn_export_volver), "btn-back")
    push!(Gtk.GAccessor.style_context(btn_solo_salir),    "btn-cancel")
    set_gtk_property!(btn_export_salir,  :sensitive, false)
    set_gtk_property!(btn_export_volver, :sensitive, false)
    set_gtk_property!(btn_solo_salir,    :sensitive, false)
    push!(btn_box, btn_export_salir)
    push!(btn_box, btn_export_volver)
    push!(btn_box, btn_solo_salir)
```

Luego busque el bloque de `result_holder` y los `signal_connect`. Actualmente:

```julia
    result_holder = Ref{Bool}(false)

    signal_connect(btn_ok, :clicked) do _
        result_holder[] = true
        _gtk_quit!()
    end
    signal_connect(btn_no, :clicked) do _
        result_holder[] = false
        _gtk_quit!()
    end
    signal_connect(win, :destroy) do _
        if result_holder[] != true
            result_holder[] = false
        end
        _gtk_quit!()
    end
```

**Reemplácelo** por:

```julia
    # :export_exit = exportar y cerrar
    # :export_back = exportar y volver a selección de país
    # :just_exit   = cerrar sin exportar
    result_holder = Ref{Symbol}(:just_exit)

    signal_connect(btn_export_salir, :clicked) do _
        result_holder[] = :export_exit
        _gtk_quit!()
    end
    signal_connect(btn_export_volver, :clicked) do _
        result_holder[] = :export_back
        _gtk_quit!()
    end
    signal_connect(btn_solo_salir, :clicked) do _
        result_holder[] = :just_exit
        _gtk_quit!()
    end
    signal_connect(win, :destroy) do _
        _gtk_quit!()
    end
```

Luego busque el bloque donde se habilitan los botones al completar (dentro del timer). Actualmente:

```julia
            set_gtk_property!(btn_ok, :sensitive, true)
            set_gtk_property!(btn_no, :sensitive, true)
            return false  # detener timer
```

**Reemplácelo** por:

```julia
            set_gtk_property!(btn_export_salir,  :sensitive, true)
            set_gtk_property!(btn_export_volver, :sensitive, true)
            set_gtk_property!(btn_solo_salir,    :sensitive, true)
            return false  # detener timer
```

Finalmente, al final de `run_gtk_panel`, la función retorna `result_holder[]`. Actualmente retorna un `Bool`. Cambie la firma de la función de:

```julia
function run_gtk_panel(state::ProcessorState)::Bool
```

A:

```julia
function run_gtk_panel(state::ProcessorState)::Symbol
```

Y cambie la última línea de la función:

```julia
    Gtk.gtk_main()
    destroy(win)
    return result_holder[]
```

Queda igual (ya devuelve `result_holder[]` que ahora es `Symbol`).

---

## 7B.2 — Cambiar el panel terminal para los 3 botones

Busque la función `_run_terminal_panel`. Al final, donde pregunta al usuario, está:

```julia
    render_terminal(state, rej_window)
    print("\n  Tu respuesta [ENTER = Finalizar / S = Salir] > ")
    flush(stdout)
    return lowercase(strip(readline())) != "s"
```

**Reemplácela** por:

```julia
    render_terminal(state, rej_window)
    println()
    println(row("$(YL)$(B)  Opciones disponibles:$(R)"))
    println(row("    $(GR)[1]$(R) Exportar y Salir"))
    println(row("    $(CY)[2]$(R) Exportar y Volver a selección de país"))
    println(row("    $(D)[S]$(R) Salir sin exportar"))
    println(bot_border())
    print("\n  Tu selección [1/2/S] > ")
    flush(stdout)
    inp = lowercase(strip(readline()))
    if inp == "1"
        return :export_exit
    elseif inp == "2"
        return :export_back
    else
        return :just_exit
    end
```

Y cambie la firma de `_run_terminal_panel` de:
```julia
function _run_terminal_panel(state::ProcessorState)::Bool
```
A:
```julia
function _run_terminal_panel(state::ProcessorState)::Symbol
```

---

## 7B.3 — Actualizar `run_panel` para devolver el nuevo tipo

Busque la función `run_panel` y su llamada a los paneles. Actualmente:

```julia
    finalized = if use_gtk
        ...
        gtk_result = nothing
        try
            gtk_result = run_gtk_panel(state)
        catch e
            ...
        end
        if isnothing(gtk_result)
            _run_terminal_panel(state)
        else
            gtk_result
        end
    else
        ...
        _run_terminal_panel(state)
    end

    return PanelResult(
        finalized,
        ...
    )
```

**Reemplace** toda esa sección de `run_panel` por:

```julia
function run_panel(
    unified::DataFrame,
    new_ids::Vector{String},
    def_df::DataFrame,
)::PanelResult

    state = Processor.init_processor(new_ids, unified)

    println("\n  Clasificación de novedades:")
    for ntype in (:VAC, :INC, :AUS)
        nc  = state.nuclei[ntype]
        clr = ntype == :VAC ? GR : ntype == :INC ? CY : YL
        println("    $(clr)$(Processor.nucleus_label(ntype))$(R): " *
                "$(nc.total_ids) IDs → $(nc.n_subcores) sub-núcleo(s)")
    end
    println("\n  Iniciando procesamiento...")

    use_gtk = gtk_available()

    Threads.@spawn Processor.process_all!(state, unified)

    action = if use_gtk
        println("  Abriendo panel visual GTK...")
        sleep(0.4)
        gtk_action = nothing
        try
            gtk_action = run_gtk_panel(state)
        catch e
            @warn "GTK panel falló: $(sprint(showerror, e)) — usando terminal"
        end
        try; start_progress_drain(state); catch; end
        isnothing(gtk_action) ? _run_terminal_panel(state) : gtk_action
    else
        println("  GTK no disponible — usando panel de terminal.")
        _run_terminal_panel(state)
    end

    # action ∈ {:export_exit, :export_back, :just_exit}
    finalized = action ∈ (:export_exit, :export_back)

    return PanelResult(
        finalized,
        copy(state.valid_ids),
        copy(state.out_ids),
        copy(state.rejected_ids),
        copy(state.rejected_reasons),
        action,   # ← nuevo campo
    )
end
```

Y actualice el struct `PanelResult` para incluir el campo `action`:

Busque:
```julia
struct PanelResult
    finalized::Bool
    valid_ids::Vector{String}
    out_ids::Vector{String}
    rejected_ids::Vector{String}
    rejected_reasons::Dict{String,String}
end
```

**Reemplácelo** por:
```julia
struct PanelResult
    finalized::Bool
    valid_ids::Vector{String}
    out_ids::Vector{String}
    rejected_ids::Vector{String}
    rejected_reasons::Dict{String,String}
    action::Symbol   # :export_exit | :export_back | :just_exit
end
```

---

## 7C — Mejoras visuales al CSS del panel GTK

**Ubicación:** Dentro de `run_gtk_panel`, busque el bloque `css = """` al inicio. **Reemplace todo el contenido del CSS** (desde `css = """` hasta el cierre `"""`) por el siguiente CSS mejorado:

```julia
    css = """
    * { -gtk-icon-style: symbolic; }

    window {
        background-color: #0a0c10;
    }
    scrolledwindow {
        background-color: #0a0c10;
    }

    .panel-title {
        font-family: "JetBrains Mono","Cascadia Code","Consolas",monospace;
        font-size: 16px;
        font-weight: bold;
        color: #e6edf3;
        letter-spacing: 1px;
    }
    .panel-subtitle {
        font-family: monospace;
        font-size: 12px;
        color: #6e7681;
    }
    .panel-timer {
        font-family: monospace;
        font-size: 13px;
        color: #8b949e;
    }
    .nucleus-label-vac {
        font-family: "JetBrains Mono",monospace;
        font-size: 13px;
        font-weight: bold;
        color: #3fb950;
        letter-spacing: 0.5px;
    }
    .nucleus-label-inc {
        font-family: "JetBrains Mono",monospace;
        font-size: 13px;
        font-weight: bold;
        color: #58a6ff;
        letter-spacing: 0.5px;
    }
    .nucleus-label-aus {
        font-family: "JetBrains Mono",monospace;
        font-size: 13px;
        font-weight: bold;
        color: #e3b341;
        letter-spacing: 0.5px;
    }
    .stat-valid {
        font-family: monospace;
        font-size: 12px;
        color: #3fb950;
        font-weight: bold;
    }
    .stat-out {
        font-family: monospace;
        font-size: 12px;
        color: #f85149;
        font-weight: bold;
    }
    .mono {
        font-family: monospace;
        font-size: 12px;
        color: #c9d1d9;
    }
    .mono-dim {
        font-family: monospace;
        font-size: 11px;
        color: #484f58;
    }
    .rej-label {
        font-family: monospace;
        font-size: 11px;
        color: #f85149;
    }
    .status-processing {
        font-family: "JetBrains Mono",monospace;
        font-size: 13px;
        font-weight: bold;
        color: #e3b341;
    }
    .status-done {
        font-family: "JetBrains Mono",monospace;
        font-size: 14px;
        font-weight: bold;
        color: #3fb950;
    }
    .status-phase2 {
        font-family: "JetBrains Mono",monospace;
        font-size: 13px;
        font-weight: bold;
        color: #8957e5;
    }
    .btn-finalize {
        background-image: linear-gradient(to bottom, #2ea043, #238636);
        color: #ffffff;
        font-weight: bold;
        font-size: 13px;
        border-radius: 6px;
        padding: 9px 22px;
        border: 1px solid #2ea043;
        min-width: 160px;
    }
    .btn-finalize:hover {
        background-image: linear-gradient(to bottom, #3fb950, #2ea043);
    }
    .btn-back {
        background-image: linear-gradient(to bottom, #1a6bb5, #1158a7);
        color: #ffffff;
        font-weight: bold;
        font-size: 13px;
        border-radius: 6px;
        padding: 9px 22px;
        border: 1px solid #1a6bb5;
        min-width: 185px;
    }
    .btn-back:hover {
        background-image: linear-gradient(to bottom, #388bfd, #1a6bb5);
    }
    .btn-cancel {
        background-color: #161b22;
        color: #6e7681;
        font-size: 12px;
        border-radius: 6px;
        padding: 9px 22px;
        border: 1px solid #30363d;
    }
    .btn-cancel:hover {
        color: #c9d1d9;
        border-color: #484f58;
    }
    separator {
        background-color: #21262d;
        min-height: 1px;
    }

    /* Barras de progreso */
    progressbar trough {
        background-color: #161b22;
        border-radius: 6px;
        min-height: 16px;
        border: 1px solid #21262d;
    }
    progressbar.vac progress {
        background-image: linear-gradient(to right, #1a4731, #3fb950);
        border-radius: 6px;
        min-height: 16px;
    }
    progressbar.inc progress {
        background-image: linear-gradient(to right, #1f3a6b, #58a6ff);
        border-radius: 6px;
        min-height: 16px;
    }
    progressbar.aus progress {
        background-image: linear-gradient(to right, #5c3b00, #e3b341);
        border-radius: 6px;
        min-height: 16px;
    }
    progressbar.global progress {
        background-image: linear-gradient(to right, #3c1f6b, #8957e5);
        border-radius: 6px;
        min-height: 16px;
    }
    """
```

Además, al inicio del bloque de `run_gtk_panel`, cambie el título de la ventana:

De:
```julia
    win = GtkWindow("Procesamiento de Novedades PTO - Solvo Global", 780, 680)
    set_gtk_property!(win, :default_width,  780)
    set_gtk_property!(win, :default_height, 680)
```

A:
```julia
    win = GtkWindow("PTO Novedades — Solvo Global", 820, 720)
    set_gtk_property!(win, :default_width,  820)
    set_gtk_property!(win, :default_height, 720)
```

Y el título que aparece dentro del panel, de:
```julia
    title_lbl = GtkLabel("PROCESAMIENTO DE NOVEDADES PTO — Solvo Global")
    push!(Gtk.GAccessor.style_context(title_lbl), "title-label")
```

A:
```julia
    title_lbl = GtkLabel("⚡ PROCESAMIENTO DE NOVEDADES PTO — Solvo Global")
    push!(Gtk.GAccessor.style_context(title_lbl), "panel-title")
```

Y el subtítulo:
```julia
    info_lbl = GtkLabel("Fecha: $(Dates.today())   Total novedades nuevas: $(state.total_new)")
    push!(Gtk.GAccessor.style_context(info_lbl), "subtitle-label")
```

A:
```julia
    info_lbl = GtkLabel("$(Dates.today())   ·   $(state.total_new) novedades nuevas detectadas")
    push!(Gtk.GAccessor.style_context(info_lbl), "panel-subtitle")
```

---

# PASO 8 — Reemplazar `main.jl`

**Qué hacer:** **Reemplace TODO el contenido** de `main.jl` por el siguiente código. Este es el orquestador principal que carga datos para ambos países y maneja el ciclo completo del panel:

```julia
"""
main.jl
─────────────────────────────────────────────────────────────────────────────
Punto de entrada del sistema PTO Novedades v3.0 — Multi-País.

Flujo completo:
    1. Activar entorno Julia del proyecto
    2. Cargar módulos
    3. Descargar datos para Colombia Y Argentina (en paralelo)
    4. Construir IDs únicos para cada país
    5. Cargar Defs históricos y detectar IDs nuevos por país
    6. Si ningún país tiene novedades → terminar
    7. Mostrar selector de país
    8. Procesar el país seleccionado con los 3 núcleos
    9. Según la acción del usuario:
         • Exportar y Salir   → exportar archivos y cerrar
         • Exportar y Volver  → exportar archivos y regresar al punto 7
         • Salir              → cerrar sin exportar
─────────────────────────────────────────────────────────────────────────────
"""

# Activar entorno
using Pkg
Pkg.activate(@__DIR__)

# Cargar módulos (orden de dependencias)
include("src/Config.jl")
include("src/SynapseConnector.jl")
include("src/SharePointConnector.jl")
include("src/LocalFilesConnector.jl")
include("src/DataLoader.jl")
include("src/IDBuilder.jl")
include("src/Validator.jl")
include("src/DefManager.jl")
include("src/Processor.jl")
include("src/Exporter.jl")
include("src/Panel.jl")

using Dates
using Base: ReentrantLock
using .Config
using .DataLoader
using .IDBuilder
using .DefManager
using .Processor
using .Exporter
using .Panel

# ── Colores de consola ────────────────────────────────────────────────────

const B  = "\e[1m"
const R  = "\e[0m"
const GR = "\e[32m"
const RD = "\e[31m"
const YL = "\e[33m"
const CY = "\e[36m"
const MG = "\e[35m"

sep(c="─", n=72)  = println(c^n)
header(s) = begin sep("═", 72); println("  $s"); sep("═", 72) end
step(n, s) = println("\n$(CY)$(B)▶ [$n]$(R)  $s")

# ── Función auxiliar: preparar datos de un país ───────────────────────────

"""
    prepare_country_data(country) -> NamedTuple | nothing

Descarga, construye IDs y carga Def para el país indicado.
Retorna: (unified, def_df, new_ids) o nothing si falló la conexión.
"""
function prepare_country_data(country::Symbol)
    pais = Config.country_name(country)
    prefix = Config.country_prefix(country)

    println("\n  $(B)[$(prefix)]$(R) Cargando datos de $(B)$(pais)$(R)...")

    raw = DataLoader.load_all_sources(country)
    if isnothing(raw) || isempty(raw)
        println("  $(RD)✗ [$(prefix)] No se obtuvieron datos para $(pais).$(R)")
        return nothing
    end

    # Agregar columna _country al DataFrame para que el Validator use los festivos correctos
    raw[!, :_country] .= string(country)

    unified = IDBuilder.build_unified(raw)

    def_df  = DefManager.load_def(country)
    new_ids = DefManager.find_new(unified, def_df)

    n_new = length(new_ids)
    if n_new == 0
        println("  $(GR)✓ [$(prefix)] $(pais) ya está actualizado. Sin novedades nuevas.$(R)")
    else
        println("  $(YL)$(B)→ [$(prefix)] $(n_new) novedades nuevas en $(pais)$(R)")
    end

    return (
        country  = country,
        unified  = unified,
        def_df   = def_df,
        new_ids  = new_ids,
        has_new  = n_new > 0,
    )
end

# ── Función auxiliar: construir ProcessorState para exportar ──────────────

function _build_export_state(r::Panel.PanelResult)::Processor.ProcessorState
    nuclei = Dict{Symbol, Processor.NucleusState}()
    for ntype in (:VAC, :INC, :AUS)
        nuclei[ntype] = Processor.NucleusState(
            ntype, 0, Processor.SubcoreState[], 0, 0, 0, 0, :done)
    end
    ch = Channel{Any}(1)
    close(ch)
    return Processor.ProcessorState(
        nuclei,
        Set{String}(),
        r.valid_ids, r.out_ids,
        r.rejected_ids, r.rejected_reasons,
        length(r.valid_ids) + length(r.out_ids),
        length(r.valid_ids) + length(r.out_ids),
        now(), true, true, ch,
        Dict{String,Int}(),
        ReentrantLock(),
    )
end

# ── Función auxiliar: exportar resultados ────────────────────────────────

function do_export(results, country_data)
    step("EXP", "Exportando archivos para $(Config.country_name(country_data.country))...")
    try
        er = Exporter.export_all(
            _build_export_state(results),
            country_data.def_df,
            country_data.unified,
            country_data.country,
        )
        sep("═", 72)
        println("\n$(GR)$(B)  EXPORTACIÓN COMPLETADA — $(Config.country_name(country_data.country))$(R)\n")
        println("  📁  Carpeta:           output/$(Config.country_prefix(country_data.country))/")
        println("  📄  Def.xlsx          → $(basename(er.def_xlsx))")
        println("  📋  Snapshot día      → $(basename(er.snapshot_xlsx))  ($(er.n_valid) válidas)")
        println("  ⚠   Rechazadas        → $(basename(er.rejected_xlsx))  ($(er.n_rejected) rechazadas)")
        sep("═", 72)
        println()
    catch e
        sep("═", 72)
        println("\n$(RD)$(B)  ✗ ERROR AL EXPORTAR$(R)")
        println("  $(RD)$(sprint(showerror, e))$(R)")
        sep("═", 72)
    end
end

# ── MAIN ──────────────────────────────────────────────────────────────────

function main()
    header("SISTEMA PTO NOVEDADES v3.0 — Solvo Global  |  $(Dates.today())")

    # PASO 1-3: Descargar datos para ambos países
    step(1, "Cargando datos de COLOMBIA Y ARGENTINA...")

    # Descargar ambos en secuencia (para evitar conflictos con la autenticación SharePoint)
    data_co = prepare_country_data(:CO)
    data_ar = prepare_country_data(:AR)

    # PASO 4: Detectar países con novedades nuevas
    step(2, "Verificando novedades nuevas por país...")

    countries_with_new = Symbol[]
    data_co !== nothing && data_co.has_new && push!(countries_with_new, :CO)
    data_ar !== nothing && data_ar.has_new && push!(countries_with_new, :AR)

    if isempty(countries_with_new)
        println("\n$(GR)$(B)✅  No hay novedades nuevas para ningún país.$(R)")
        println("   Colombia: $(data_co !== nothing ? string(length(DefManager.load_def(:CO) |> nrow)) : "sin conexión") registros históricos")
        println("   Argentina: $(data_ar !== nothing ? string(length(DefManager.load_def(:AR) |> nrow)) : "sin conexión") registros históricos")
        println()
        return
    end

    println("\n  Países con novedades nuevas: $(join([Config.country_name(c) for c in countries_with_new], " + "))")

    # Mapa de datos por país (solo los que tienen novedades)
    country_data_map = Dict{Symbol, Any}()
    data_co !== nothing && data_co.has_new && (country_data_map[:CO] = data_co)
    data_ar !== nothing && data_ar.has_new && (country_data_map[:AR] = data_ar)

    # CICLO PRINCIPAL: selector de país → procesamiento → exportación
    keep_running = true
    already_processed = Set{Symbol}()  # países ya procesados en esta sesión

    while keep_running
        # Mostrar selector de país
        step(3, "Abriendo selector de país...")
        sel = Panel.run_country_selector(countries_with_new)

        if !sel.proceed
            println("\n$(YL)  Proceso cancelado por el usuario.$(R)\n")
            break
        end

        country  = sel.country
        cd       = get(country_data_map, country, nothing)

        if isnothing(cd)
            println("\n$(RD)✗ No hay datos disponibles para $(Config.country_name(country)).$(R)\n")
            continue
        end

        pais = Config.country_name(country)

        # PASO 4: Panel de procesamiento
        step(4, "Iniciando procesamiento de $(B)$(pais)$(R)...")
        results = Panel.run_panel(cd.unified, cd.new_ids, cd.def_df)

        # PASO 5: Según acción del usuario
        if results.action == :export_exit
            do_export(results, cd)
            push!(already_processed, country)
            keep_running = false   # cerrar

        elseif results.action == :export_back
            do_export(results, cd)
            push!(already_processed, country)
            # Quitar el país ya procesado de la lista para no volverlo a ofrecer
            # (a menos que aún tenga IDs sin procesar — en este caso simplificamos
            #  y lo mantenemos en la lista para que el usuario decida)
            println("\n$(CY)  Volviendo al selector de país...$(R)\n")
            # Si ya procesamos todos los países disponibles, terminar
            if all(c -> c ∈ already_processed, countries_with_new)
                println("$(GR)$(B)✅  Todos los países han sido procesados.$(R)\n")
                keep_running = false
            end

        else  # :just_exit
            println("\n$(YL)  Proceso cancelado — no se generaron archivos para $(pais).$(R)\n")
            keep_running = false
        end
    end

    println("$(D)  Sistema PTO Novedades v3.0 — Finalizado.$(R)\n")
end

# Ejecutar
main()
```

---

# PASO 9 — Verificación final

Antes de ejecutar, verifique que su `src/Config.jl` tenga estas rutas apuntando a sus archivos reales:

```julia
const ROSTER_FILE    = raw"C:\Users\SuUsuario\OneDrive - ...\Roster.xlsx"
const TYPES_PTO_FILE = raw"C:\Users\SuUsuario\OneDrive - ...\TYPES OF PTO.xlsx"
const SYNAPSE_AUTH_MODE = "AAD_INTEGRATED"    # o el modo que usa su empresa
const SYNAPSE_DATABASE_AR = "MidasoftArgentina"  # confirmar el nombre exacto de la BD
```

Verifique también que las nuevas carpetas de salida se pueden crear:

```
output/
├── CO/      ← se crea automáticamente la primera vez
└── AR/      ← se crea automáticamente la primera vez
```

Para ejecutar:

```bash
julia main.jl
```

---

# RESUMEN — Estructura de archivos de salida

Después de los cambios, los archivos de salida quedan así:

```
output/
├── CO/
│   ├── Def.xlsx               ← Histórico Colombia (se actualiza acumulativamente)
│   ├── Def.csv
│   ├── CO_Def_2025-06-18.xlsx ← Snapshot del día Colombia
│   ├── CO_Def_2025-06-18.csv
│   ├── CO_Rejected_2025-06-18.xlsx
│   └── CO_Rejected_2025-06-18.csv
└── AR/
    ├── Def.xlsx               ← Histórico Argentina
    ├── Def.csv
    ├── AR_Def_2025-06-18.xlsx ← Snapshot del día Argentina
    ├── AR_Def_2025-06-18.csv
    ├── AR_Rejected_2025-06-18.xlsx
    └── AR_Rejected_2025-06-18.csv
```

---

# FLUJO VISUAL DEL PANEL v3.0

```
┌─────────────────────────────────────────────────────────┐
│  ⚡ PROCESAMIENTO DE NOVEDADES PTO — Solvo Global        │
│  Seleccione el país a procesar — 2025-06-18             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│    [🇨🇴  Colombia]        [🇦🇷  Argentina]              │
│                                                         │
│    ▶ Colombia seleccionada                              │
│    ✓ Colombia — tiene novedades nuevas                  │
│    ✓ Argentina — tiene novedades nuevas                 │
├─────────────────────────────────────────────────────────┤
│    [▶  Procesar]    [Salir]                             │
└─────────────────────────────────────────────────────────┘

                    ↓ Al hacer clic en Procesar

┌─────────────────────────────────────────────────────────┐
│  ⚡ PROCESAMIENTO — Colombia   2025-06-18   ⏱ 00:45    │
│  1234 novedades nuevas                                  │
├─────────────────────────────────────────────────────────┤
│  ● [VAC] VACACIONES  ████████████████████  100%  ✓450  │
│  ◉ [INC] INCAPACIDADES  █████████░░░░░░░░  60%  ✓310  │
│  ○ [AUS] AUSENTISMOS  ░░░░░░░░░░░░░░░░░░  0%    ✓0   │
├─────────────────────────────────────────────────────────┤
│  ✅ COMPLETADO — Válidas: 1210   Rechazadas: 24         │
├─────────────────────────────────────────────────────────┤
│  [📥 Exportar y Salir]                                  │
│  [🔄 Exportar y Volver]    [Salir sin guardar]         │
└─────────────────────────────────────────────────────────┘
```

---

# PREGUNTAS FRECUENTES SOBRE ESTE CAMBIO

**¿Qué pasa si Colombia se conecta bien pero Argentina falla?**
El sistema continúa. En el selector de país solo aparecerá Colombia como opción disponible. Argentina mostrará el mensaje `"✗ Argentina — sin novedades nuevas"` si no pudo conectarse (y el error detallado aparecerá en la terminal antes de abrir el panel).

**¿El histórico Def de Colombia se mezcla con el de Argentina?**
No. Son archivos completamente separados: `output/CO/Def.xlsx` y `output/AR/Def.xlsx`.

**¿Qué pasa si una columna falta en las tablas de Argentina?**
El módulo `SynapseConnector.jl` valida las columnas requeridas antes de ejecutar el query. Si falta alguna, imprime un error descriptivo indicando exactamente qué columna está ausente, y esa tabla se devuelve vacía (sin abortar todo el proceso).

**¿Puedo agregar más países en el futuro?**
Sí. Basta con:
1. Agregar las constantes del nuevo país en `Config.jl` (tabla, festivos, etc.)
2. Agregar el símbolo del país en `country_tables()` y `country_name()`
3. Llamar a `prepare_country_data(:MX)` en `main.jl`
4. Agregar el botón del nuevo país en el selector de `Panel.jl`

**¿Los festivos de Argentina necesitan actualizarse cada año?**
Sí, igual que los de Colombia. Los festivos "trasladables" de Argentina cambian de fecha exacta cada año según los decretos publicados en el Boletín Oficial. Actualice `FESTIVOS_ARGENTINA` en `Config.jl` cada enero consultando https://www.argentina.gob.ar/interior/feriados

---

*Paso a paso generado para PTO Novedades v3.0 — Solvo Global*
