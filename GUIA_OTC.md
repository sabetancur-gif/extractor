# GUÍA COMPLETA — Proceso OTC (Others Countries)
## People Management / Leaders APP
### PTO Novedades v4.0

---

## ¿QUÉ SE CONSTRUYE?

Un cuarto proceso de carga de datos llamado **OTC (Others Countries)** que:

1. Se conecta a la BD **Leaders APP** y descarga la tabla `dbo.Ausencias`
2. Hace un merge con `data/ubicacion.xlsx` para asignar el país a cada empleado (columna `Ubicación`)
3. Clasifica cada novedad en **AUS / INC / VAC** según el texto de `NomNovedad`
4. Filtra las novedades marcadas como "No reportamos"
5. Expande las filas por días hábiles usando los festivos del país de cada empleado
6. Construye la misma tabla unificada que los otros procesos
7. Usa el mismo panel, validación, exportación y Def.xlsx que CO / AR / MX
8. Guarda los archivos en `output/OTC/` con prefijo `OTC_`
9. Aparece como opción "🌍 Others Countries (OTC)" en el selector de país

**Países que puede contener OTC:**
Colombia, Argentina, México, Kenia, Perú, Guatemala, India, República Dominicana, Brasil

---

## MAPA DE CAMBIOS

| # | Archivo | Tipo |
|---|---------|------|
| 1 | `data/ubicacion.xlsx` | **CREAR** (archivo Excel manual) |
| 2 | `src/Config.jl` | **MODIFICAR** |
| 3 | `src/OTCConnector.jl` | **CREAR** (módulo nuevo) |
| 4 | `src/DataLoader.jl` | **MODIFICAR** |
| 5 | `main.jl` | **MODIFICAR** |
| 6 | `src/Panel.jl` | **MODIFICAR** |

---

---

# PASO 1 — Crear la carpeta `data/` y el archivo `data/ubicacion.xlsx`

**Qué hacer:** Dentro de la carpeta raíz del proyecto (donde está `main.jl`), cree una carpeta llamada exactamente `data`. Dentro de ella cree un archivo Excel llamado `ubicacion.xlsx`.

El archivo debe tener **exactamente dos columnas** en la primera hoja:

| SOLID      | Pais                 |
|------------|----------------------|
| SOLA12345  | Colombia             |
| SOLB99001  | Kenia                |
| SOLC44201  | Perú                 |
| SOLD71100  | India                |
| ...        | ...                  |

**Reglas:**
- Columna `SOLID`: el EmpleadoId tal como aparece en la tabla `dbo.Ausencias`
- Columna `Pais`: el nombre del país en texto libre. Los valores reconocidos son los siguientes (respete la capitalización):
  - Colombia, Argentina, México, Mexico, Kenia, Kenya, Perú, Peru, Guatemala, India, República Dominicana, Republica Dominicana, Dominican Republic, Brasil, Brazil
- Si un empleado no aparece en este archivo, se le asignará Colombia como país por defecto

---

# PASO 2 — Modificar `src/Config.jl`

**Qué hacer:** Abra `src/Config.jl`. Realice los cambios que se describen a continuación. **No reemplace todo el archivo**, haga solo las adiciones y modificaciones indicadas.

---

## 2A — Agregar base de datos OTC y tabla

**Busque** el bloque de bases de datos (después de la línea `const SYNAPSE_DATABASE_MX = "MidasoftMexico"`):
```julia
# Mexico
const SYNAPSE_DATABASE_MX = "MidasoftMexico"
```

**Justo después** de esa línea, agregue:
```julia
# Others Countries (Leaders APP - People Management)
# ← VERIFICAR el nombre exacto de la base de datos en SQL Server
const SYNAPSE_DATABASE_OTC = "LeadersAPP"
const OTC_TABLE_AUSENCIAS  = "Ausencias"

# Ruta al archivo de mapeo SOLID → País (creado en el PASO 1)
const UBICACION_FILE = joinpath(@__DIR__, "..", "data", "ubicacion.xlsx")
```

---

## 2B — Actualizar `country_tables` para OTC

**Busque** la función `country_tables` (aproximadamente línea 170):
```julia
function country_tables(country::Symbol)
    if country == :AR
        return (aus = TABLE_AUS_AR, inc = TABLE_INC_AR, vac = TABLE_VAC_AR)
    elseif country == :MX
        return (aus = TABLE_AUS_MX, inc = TABLE_INC_MX, vac = TABLE_VAC_MX)
    else
        return (aus = TABLE_AUS_CO, inc = TABLE_INC_CO, vac = TABLE_VAC_CO)
    end
end
```

**Reemplácela** por (agrega el caso :OTC):
```julia
function country_tables(country::Symbol)
    if country == :AR
        return (aus = TABLE_AUS_AR, inc = TABLE_INC_AR, vac = TABLE_VAC_AR)
    elseif country == :MX
        return (aus = TABLE_AUS_MX, inc = TABLE_INC_MX, vac = TABLE_VAC_MX)
    elseif country == :OTC
        return (aus = OTC_TABLE_AUSENCIAS, inc = "", vac = "")  # OTC usa solo una tabla
    else
        return (aus = TABLE_AUS_CO, inc = TABLE_INC_CO, vac = TABLE_VAC_CO)
    end
end
```

---

## 2C — Actualizar `country_name` y `country_prefix`

**Busque** la línea (al final del archivo):
```julia
country_name(country::Symbol) = country == :AR ? "Argentina" : country == :MX ? "Mexico" : "Colombia"
country_prefix(country::Symbol) = string(country)
```

**Reemplácela** por:
```julia
country_name(country::Symbol) =
    country == :AR  ? "Argentina" :
    country == :MX  ? "Mexico"    :
    country == :OTC ? "Others Countries" :
    "Colombia"

country_prefix(country::Symbol) = string(country)   # "CO", "AR", "MX", "OTC"
```

---

## 2D — Agregar festivos para los 6 nuevos países

**Busque** la constante `FESTIVOS_MEXICO` (termina con `])`). **Justo después** de su cierre, agregue el siguiente bloque completo:

```julia
# ── Festivos Kenia 2024–2027 ──────────────────────────────────────────────
# Fuente: Kenya Holidays & Observances (Public Holidays Act)
# Viernes Santo y Lunes de Pascua son variables
const FESTIVOS_KENYA = Set([
    # 2024
    Date(2024,1,1),   # Año Nuevo
    Date(2024,3,29),  # Viernes Santo (Easter 31 Mar)
    Date(2024,4,1),   # Lunes de Pascua
    Date(2024,5,1),   # Labour Day
    Date(2024,6,1),   # Madaraka Day
    Date(2024,10,10), # Huduma Day
    Date(2024,10,20), # Mashujaa Day (domingo → se añade el lunes 21 como sustituto)
    Date(2024,10,21), # Mashujaa Day sustituto (20 oct = domingo)
    Date(2024,12,12), # Jamhuri Day
    Date(2024,12,25), # Christmas Day
    Date(2024,12,26), # Boxing Day
    # 2025
    Date(2025,1,1),
    Date(2025,4,18),  # Viernes Santo (Easter 20 Apr)
    Date(2025,4,21),  # Lunes de Pascua
    Date(2025,5,1),
    Date(2025,6,1),
    Date(2025,10,10),
    Date(2025,10,20),
    Date(2025,12,12),
    Date(2025,12,25),
    Date(2025,12,26),
    # 2026
    Date(2026,1,1),
    Date(2026,4,3),   # Viernes Santo (Easter 5 Apr)
    Date(2026,4,6),   # Lunes de Pascua
    Date(2026,5,1),
    Date(2026,6,1),
    Date(2026,10,10),
    Date(2026,10,20),
    Date(2026,12,12),
    Date(2026,12,25),
    Date(2026,12,26),
    # 2027
    Date(2027,1,1),
    Date(2027,3,26),  # Viernes Santo (Easter 28 Mar)
    Date(2027,3,29),  # Lunes de Pascua
    Date(2027,5,1),
    Date(2027,6,1),
    Date(2027,10,10),
    Date(2027,10,20),
    Date(2027,12,12),
    Date(2027,12,25),
    Date(2027,12,26),
])

# ── Festivos Perú 2024–2027 ───────────────────────────────────────────────
# Fuente: Ley 27399 y Decretos del Poder Ejecutivo
const FESTIVOS_PERU = Set([
    # 2024  (Easter: Mar 31)
    Date(2024,1,1),   # Año Nuevo
    Date(2024,3,28),  # Jueves Santo
    Date(2024,3,29),  # Viernes Santo
    Date(2024,5,1),   # Día del Trabajo
    Date(2024,6,29),  # San Pedro y San Pablo
    Date(2024,7,28),  # Fiestas Patrias
    Date(2024,7,29),  # Fiestas Patrias
    Date(2024,8,30),  # Santa Rosa de Lima
    Date(2024,10,8),  # Combate de Angamos
    Date(2024,11,1),  # Todos los Santos
    Date(2024,12,8),  # Inmaculada Concepción
    Date(2024,12,9),  # Batalla de Ayacucho
    Date(2024,12,25), # Navidad
    # 2025  (Easter: Apr 20)
    Date(2025,1,1),
    Date(2025,4,17),  # Jueves Santo
    Date(2025,4,18),  # Viernes Santo
    Date(2025,5,1),
    Date(2025,6,29),
    Date(2025,7,28),
    Date(2025,7,29),
    Date(2025,8,30),
    Date(2025,10,8),
    Date(2025,11,1),
    Date(2025,12,8),
    Date(2025,12,9),
    Date(2025,12,25),
    # 2026  (Easter: Apr 5)
    Date(2026,1,1),
    Date(2026,4,2),   # Jueves Santo
    Date(2026,4,3),   # Viernes Santo
    Date(2026,5,1),
    Date(2026,6,29),
    Date(2026,7,28),
    Date(2026,7,29),
    Date(2026,8,30),
    Date(2026,10,8),
    Date(2026,11,1),
    Date(2026,12,8),
    Date(2026,12,9),
    Date(2026,12,25),
    # 2027  (Easter: Mar 28)
    Date(2027,1,1),
    Date(2027,3,25),  # Jueves Santo
    Date(2027,3,26),  # Viernes Santo
    Date(2027,5,1),
    Date(2027,6,29),
    Date(2027,7,28),
    Date(2027,7,29),
    Date(2027,8,30),
    Date(2027,10,8),
    Date(2027,11,1),
    Date(2027,12,8),
    Date(2027,12,9),
    Date(2027,12,25),
])

# ── Festivos Guatemala 2024–2027 ──────────────────────────────────────────
# Fuente: Código de Trabajo de Guatemala
const FESTIVOS_GUATEMALA = Set([
    # 2024  (Easter: Mar 31)
    Date(2024,1,1),
    Date(2024,3,28),  # Jueves Santo
    Date(2024,3,29),  # Viernes Santo
    Date(2024,3,30),  # Sábado Santo
    Date(2024,5,1),
    Date(2024,6,30),  # Día del Ejército / Día de las Fuerzas Armadas
    Date(2024,9,15),  # Día de la Independencia
    Date(2024,10,20), # Día de la Revolución
    Date(2024,11,1),  # Día de Todos los Santos
    Date(2024,12,24), # Nochebuena
    Date(2024,12,25), # Navidad
    Date(2024,12,31), # Fin de Año
    # 2025  (Easter: Apr 20)
    Date(2025,1,1),
    Date(2025,4,17),
    Date(2025,4,18),
    Date(2025,4,19),
    Date(2025,5,1),
    Date(2025,6,30),
    Date(2025,9,15),
    Date(2025,10,20),
    Date(2025,11,1),
    Date(2025,12,24),
    Date(2025,12,25),
    Date(2025,12,31),
    # 2026  (Easter: Apr 5)
    Date(2026,1,1),
    Date(2026,4,2),
    Date(2026,4,3),
    Date(2026,4,4),
    Date(2026,5,1),
    Date(2026,6,30),
    Date(2026,9,15),
    Date(2026,10,20),
    Date(2026,11,1),
    Date(2026,12,24),
    Date(2026,12,25),
    Date(2026,12,31),
    # 2027  (Easter: Mar 28)
    Date(2027,1,1),
    Date(2027,3,25),
    Date(2027,3,26),
    Date(2027,3,27),
    Date(2027,5,1),
    Date(2027,6,30),
    Date(2027,9,15),
    Date(2027,10,20),
    Date(2027,11,1),
    Date(2027,12,24),
    Date(2027,12,25),
    Date(2027,12,31),
])

# ── Festivos India 2024–2027 ──────────────────────────────────────────────
# Solo feriados NACIONALES garantizados. Los festivos estatales/religiosos
# (Diwali, Holi, Dussehra, Eid, etc.) varían por región y año.
# Actualice según la política de su organización para India.
const FESTIVOS_INDIA = Set([
    # 2024
    Date(2024,1,26),  # Republic Day
    Date(2024,8,15),  # Independence Day
    Date(2024,10,2),  # Gandhi Jayanti
    # 2025
    Date(2025,1,26),
    Date(2025,8,15),
    Date(2025,10,2),
    # 2026
    Date(2026,1,26),
    Date(2026,8,15),
    Date(2026,10,2),
    # 2027
    Date(2027,1,26),
    Date(2027,8,15),
    Date(2027,10,2),
])

# ── Festivos República Dominicana 2024–2027 ───────────────────────────────
# Fuente: Ley 139-97 sobre días feriados
# Los días trasladables (6 Ene, 26 Ene, Corpus Christi, 6 Nov) siguen la
# regla: si cae mar/mié → lunes anterior; si cae jue/vie → lunes siguiente.
const FESTIVOS_DOMINICANA = Set([
    # 2024
    Date(2024,1,1),   # Año Nuevo
    Date(2024,1,6),   # Reyes (Sábado → se mantiene)
    Date(2024,1,21),  # Virgen de la Altagracia
    Date(2024,1,29),  # Duarte (26 ene = viernes → lunes sig 29)
    Date(2024,2,27),  # Independencia (martes → inamovible en RD)
    Date(2024,3,29),  # Viernes Santo
    Date(2024,5,1),   # Día del Trabajo
    Date(2024,5,30),  # Corpus Christi (variable, ~60 días después de Pascua)
    Date(2024,8,16),  # Restauración
    Date(2024,9,24),  # Virgen de las Mercedes
    Date(2024,11,11), # Constitución (6 nov = mié → lunes ant 4 → lunes sig 11)
    Date(2024,12,25), # Navidad
    # 2025
    Date(2025,1,1),
    Date(2025,1,6),
    Date(2025,1,21),
    Date(2025,1,27),  # Duarte (26 ene = domingo → lunes sig 27)
    Date(2025,2,27),
    Date(2025,4,18),  # Viernes Santo
    Date(2025,5,1),
    Date(2025,6,19),  # Corpus Christi
    Date(2025,8,16),
    Date(2025,9,24),
    Date(2025,11,10), # Constitución (6 nov = jue → lunes sig 10)
    Date(2025,12,25),
    # 2026
    Date(2026,1,1),
    Date(2026,1,5),   # Reyes (6 ene = martes → lunes ant 5)
    Date(2026,1,21),
    Date(2026,1,26),  # Duarte (26 ene = lunes → se mantiene)
    Date(2026,2,27),
    Date(2026,4,3),   # Viernes Santo
    Date(2026,5,1),
    Date(2026,6,4),   # Corpus Christi
    Date(2026,8,16),
    Date(2026,9,24),
    Date(2026,11,9),  # Constitución (6 nov = vie → lunes sig 9)
    Date(2026,12,25),
    # 2027
    Date(2027,1,1),
    Date(2027,1,6),
    Date(2027,1,21),
    Date(2027,1,25),  # Duarte (26 ene = martes → lunes ant 25)
    Date(2027,2,27),
    Date(2027,3,26),  # Viernes Santo
    Date(2027,5,1),
    Date(2027,5,27),  # Corpus Christi
    Date(2027,8,16),
    Date(2027,9,24),
    Date(2027,11,8),  # Constitución (6 nov = sáb → lunes sig 8)
    Date(2027,12,25),
])

# ── Festivos Brasil 2024–2027 ─────────────────────────────────────────────
# Fuente: Lei 9.093/1995 y Decreto 10.088/2019 (Dia da Consciência Negra)
# Carnaval (Seg+Ter antes del Miércoles de Ceniza) y Corpus Christi son variables
const FESTIVOS_BRASIL = Set([
    # 2024  (Easter: Mar 31 | Ash Wed: Feb 14 | Corpus Christi: May 30)
    Date(2024,1,1),   # Ano Novo
    Date(2024,2,12),  # Carnaval - 2ª feira
    Date(2024,2,13),  # Carnaval - 3ª feira
    Date(2024,3,29),  # Sexta-feira Santa
    Date(2024,4,21),  # Tiradentes
    Date(2024,5,1),   # Dia do Trabalho
    Date(2024,5,30),  # Corpus Christi
    Date(2024,9,7),   # Independência do Brasil
    Date(2024,10,12), # Nossa Senhora Aparecida
    Date(2024,11,2),  # Finados
    Date(2024,11,15), # Proclamação da República
    Date(2024,11,20), # Dia da Consciência Negra
    Date(2024,12,25), # Natal
    # 2025  (Easter: Apr 20 | Ash Wed: Mar 5 | Corpus Christi: Jun 19)
    Date(2025,1,1),
    Date(2025,3,3),   # Carnaval
    Date(2025,3,4),   # Carnaval
    Date(2025,4,18),  # Sexta-feira Santa
    Date(2025,4,21),
    Date(2025,5,1),
    Date(2025,6,19),  # Corpus Christi
    Date(2025,9,7),
    Date(2025,10,12),
    Date(2025,11,2),
    Date(2025,11,15),
    Date(2025,11,20),
    Date(2025,12,25),
    # 2026  (Easter: Apr 5 | Ash Wed: Feb 18 | Corpus Christi: Jun 4)
    Date(2026,1,1),
    Date(2026,2,16),  # Carnaval
    Date(2026,2,17),  # Carnaval
    Date(2026,4,3),   # Sexta-feira Santa
    Date(2026,4,21),
    Date(2026,5,1),
    Date(2026,6,4),   # Corpus Christi
    Date(2026,9,7),
    Date(2026,10,12),
    Date(2026,11,2),
    Date(2026,11,15),
    Date(2026,11,20),
    Date(2026,12,25),
    # 2027  (Easter: Mar 28 | Ash Wed: Feb 10 | Corpus Christi: May 27)
    Date(2027,1,1),
    Date(2027,2,8),   # Carnaval
    Date(2027,2,9),   # Carnaval
    Date(2027,3,26),  # Sexta-feira Santa
    Date(2027,4,21),
    Date(2027,5,1),
    Date(2027,5,27),  # Corpus Christi
    Date(2027,9,7),
    Date(2027,10,12),
    Date(2027,11,2),
    Date(2027,11,15),
    Date(2027,11,20),
    Date(2027,12,25),
])
```

---

## 2E — Actualizar `country_festivos` para incluir los 6 nuevos países

**Busque** la función `country_festivos`:
```julia
function country_festivos(country::Symbol)::Set{Date}
    country == :AR ? FESTIVOS_ARGENTINA :
    country == :MX ? FESTIVOS_MEXICO :
                    FESTIVOS_COLOMBIA
end
```

**Reemplácela** por:
```julia
function country_festivos(country::Symbol)::Set{Date}
    country == :AR  ? FESTIVOS_ARGENTINA   :
    country == :MX  ? FESTIVOS_MEXICO      :
    country == :KE  ? FESTIVOS_KENYA       :
    country == :PE  ? FESTIVOS_PERU        :
    country == :GT  ? FESTIVOS_GUATEMALA   :
    country == :IND ? FESTIVOS_INDIA       :
    country == :DOM ? FESTIVOS_DOMINICANA  :
    country == :BR  ? FESTIVOS_BRASIL      :
                     FESTIVOS_COLOMBIA     # default: CO y fallback OTC sin match
end
```

---

## 2F — Agregar función de mapeo Ubicación → símbolo de país

**Al final del archivo**, justo antes de `end # module Config`, agregue:

```julia
# Mapeo del valor de la columna 'Pais' en ubicacion.xlsx → símbolo de festivos
function otc_pais_to_symbol(pais::String)::Symbol
    p = strip(pais)
    p ∈ ("Colombia", "Columbia", "Colmbia", "Col")          && return :CO
    p ∈ ("Argentina", "Buenos Aires")                        && return :AR
    p ∈ ("México", "Mexico", "MEXICO")                       && return :MX
    p ∈ ("Kenya", "Kenia", "KENYA", "KENIA")                && return :KE
    p ∈ ("Perú", "Peru", "PERU", "PERÚ")                    && return :PE
    p ∈ ("Guatemala", "GUATEMALA")                           && return :GT
    p ∈ ("India", "INDIA")                                   && return :IND
    p ∈ ("República Dominicana", "Republica Dominicana",
         "Dominican Republic", "RD", "Dom. Rep.", "DOMINICANA") && return :DOM
    p ∈ ("Brasil", "Brazil", "BRASIL", "BRAZIL")            && return :BR
    @warn "Ubicación OTC no reconocida: '$pais'. Se usarán festivos de Colombia."
    return :CO
end
```

---

# PASO 3 — Crear el archivo `src/OTCConnector.jl`

**Qué hacer:** En la carpeta `src/`, cree un archivo nuevo llamado exactamente `OTCConnector.jl`. Copie y pegue el siguiente contenido completo:

```julia
"""
src/OTCConnector.jl
─────────────────────────────────────────────────────────────────────────────
Conecta a Azure Synapse (Leaders APP) y descarga la tabla dbo.Ausencias
para el proceso OTC (Others Countries / People Management).

La tabla Ausencias tiene una estructura diferente a las tablas Midasoft:
    • Una sola tabla (no tres separadas)
    • La clasificación AUS/INC/VAC se hace por NomNovedad
    • Las fechas están en columnas F1, F3, F4 (no Finir/Ffinr/FSalR)
    • EmpleadoId = SOLID
    • El país del empleado se determina externamente (data/ubicacion.xlsx)
─────────────────────────────────────────────────────────────────────────────
"""
module OTCConnector

using DataFrames, ODBC, Dates, Logging
using ..Config

export fetch_from_leaders_app

# ── Helpers ────────────────────────────────────────────────────────────────

safe_str(v) = ismissing(v) ? "" : strip(string(v))

safe_date(v) = begin
    ismissing(v) && return missing
    v isa Date     && return v
    v isa DateTime && return Date(v)
    tryparse(Date, string(v))
end

safe_num(v) = begin
    ismissing(v) && return missing
    v isa Number  && return Float64(v)
    r = tryparse(Float64, string(v))
    isnothing(r) ? missing : r
end

# ── String de conexión ─────────────────────────────────────────────────────

function build_connection_string_otc()::String
    base =  "Driver={$(Config.ODBC_DRIVER)};" *
            "Server=$(Config.SYNAPSE_SERVER),$(Config.SYNAPSE_PORT);" *
            "Database=$(Config.SYNAPSE_DATABASE_OTC);" *
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

# ── Query SQL ──────────────────────────────────────────────────────────────

function build_sql_ausencias()::String
    fecha = string(Config.FECHA_MINIMA)
    """
    SELECT
        LTRIM(RTRIM(CAST(EmpleadoId AS NVARCHAR(50))))  AS EmpleadoId,
        LTRIM(RTRIM(CAST(Persona_ID AS NVARCHAR(50))))  AS Persona_ID,
        LTRIM(RTRIM(Empleado))                          AS Empleado,
        LTRIM(RTRIM(Company))                           AS Company,
        LTRIM(RTRIM(Operation))                         AS Operation,
        Clase_Id,
        LTRIM(RTRIM(Clase))                             AS Clase,
        LTRIM(RTRIM(CAST(CodNovedad AS NVARCHAR(20)))) AS CodNovedad,
        LTRIM(RTRIM(NomNovedad))                        AS NomNovedad,
        CAST(Numero AS NVARCHAR(30))                    AS Numero,
        CAST(F1 AS DATE)                                AS F1,
        CAST(F2 AS DATE)                                AS F2,
        CAST(F3 AS DATE)                                AS F3,
        CAST(F4 AS DATE)                                AS F4,
        CAST(ISNULL(Dias,  0) AS FLOAT)                AS Dias,
        CAST(ISNULL(Horas, 0) AS FLOAT)                AS Horas,
        Codigo_Anterior, Codigo_Nuevo, Salario_Nuevo,
        Dia, Ano, Mes, FGenera, AnoGenera, MesGenera, DiaGenera,
        Idsolicitante, Usrsolicitante, Observacion,
        Facturable, Valor_Facturable
    FROM dbo.$(Config.OTC_TABLE_AUSENCIAS)
    WHERE (
        (F3 IS NOT NULL AND CAST(F3 AS DATE) >= '$(fecha)')
        OR
        (F3 IS NULL AND F1 IS NOT NULL AND CAST(F1 AS DATE) >= '$(fecha)')
    )
    ORDER BY COALESCE(F3, F1) ASC
    """
end

# ── API pública ────────────────────────────────────────────────────────────

"""
    fetch_from_leaders_app() -> DataFrame | nothing

Conecta a la base de datos Leaders APP y descarga la tabla Ausencias.
No aplica filtro de SOLID (el proceso OTC incluye todos los empleados).
Los registros anteriores a Config.FECHA_MINIMA se excluyen.
"""
function fetch_from_leaders_app()::Union{DataFrame, Nothing}
    println("   Conectando a Leaders APP (OTC)...")
    println("   Servidor:     $(Config.SYNAPSE_SERVER)")
    println("   Base de datos: $(Config.SYNAPSE_DATABASE_OTC)")
    println("   Tabla:        dbo.$(Config.OTC_TABLE_AUSENCIAS)")
    println("   Fecha mínima: $(Config.FECHA_MINIMA)")

    conn = try
        ODBC.Connection(build_connection_string_otc())
    catch e
        @error """
        No se pudo conectar a Leaders APP (OTC).
        Error: $e

        Verifique en src/Config.jl:
            • SYNAPSE_DATABASE_OTC  (nombre exacto de la BD en SQL Server)
            • SYNAPSE_AUTH_MODE     (AAD_INTEGRATED / AAD_PASSWORD / SQL)
            • ODBC_DRIVER           (driver ODBC instalado)
        """
        return nothing
    end

    println("   ✓ Conexión establecida. Descargando Ausencias...")

    df = try
        raw = DBInterface.execute(conn, build_sql_ausencias()) |> DataFrame
        println("   ✓ Ausencias [OTC]: $(nrow(raw)) filas descargadas.")
        raw
    catch e
        @error "Error ejecutando query en Leaders APP: $e"
        DBInterface.close!(conn)
        return nothing
    end

    DBInterface.close!(conn)
    println("   Conexión cerrada (OTC Leaders APP).")
    return df
end

end # module OTCConnector
```

---

# PASO 4 — Modificar `src/DataLoader.jl`

Este paso agrega, en 4 sub-pasos, lo necesario para el proceso OTC **dentro del módulo DataLoader existente**. No se modifica ninguna función ya existente, solo se agregan nuevas.

---

## 4A — Agregar `using ..OTCConnector` a las dependencias

**Busque** el bloque `using` al principio del módulo (antes de `export`):
```julia
using ..Config
using ..SynapseConnector
using ..SharePointConnector
using ..LocalFilesConnector
```

**Reemplácelo** por (agrega la última línea):
```julia
using ..Config
using ..SynapseConnector
using ..SharePointConnector
using ..LocalFilesConnector
using ..OTCConnector
```

---

## 4B — Agregar `load_all_sources_otc` al `export`

**Busque** la línea:
```julia
export load_all_sources
```

**Reemplácela** por:
```julia
export load_all_sources, load_all_sources_otc
```

---

## 4C — Agregar las constantes y helpers de OTC

**Busque** el comentario de sección que dice:
```julia
# API pública
```
(Es el que está justo antes de la función `load_all_sources`.)

**Justo ANTES de ese comentario**, inserte el siguiente bloque completo:

```julia
# ── OTC: tablas de clasificación de novedades ──────────────────────────────

# Novedades que se procesan como AUS
const OTC_NOVEDAD_AUS = Set([
    "Licencia no remunerada",
    "Licencia remunerada",
    "Permiso por asuntos externos con licencia pagada",
    "FlexiSolvo",
    "Permiso personal con licencia pagada",
    "Permiso por problemas técnicos con licencia pagada",
    "Ausencia no justificada",
    "Permiso por cumpleaños con licencia pagada",
    "Licencia por luto",
    "Licencia por calamidad",
    "Licencia por Mudanza",
    "votación",
    "Permiso por capacitación con licencia pagada",
    "Suspensión por sanción",
])

# Novedades que se procesan como INC
const OTC_NOVEDAD_INC = Set([
    "Enfermedad general",
    "Cita médica con licencia pagada",
    "Paternidad",
    "Maternidad",
])

# Novedades que se procesan como VAC
const OTC_NOVEDAD_VAC = Set([
    "Vacaciones laborables",
    "VA",
    "Vacaciones no laborables",
])

# Novedades que se IGNORAN (No reportamos)
const OTC_NOVEDAD_SKIP = Set([
    "OFICIO", "DEPTO", "AREA", "UBICACION", "SECCIÓN", "SUBDIVISION",
])

"""
    otc_classify_novedad(nom_novedad) -> Symbol | nothing

Clasifica el texto de NomNovedad en :AUS, :INC, :VAC o nothing (ignorar).
"""
function otc_classify_novedad(nom_novedad::String)::Union{Symbol, Nothing}
    nom = strip(nom_novedad)
    nom ∈ OTC_NOVEDAD_AUS  && return :AUS
    nom ∈ OTC_NOVEDAD_INC  && return :INC
    nom ∈ OTC_NOVEDAD_VAC  && return :VAC
    nom ∈ OTC_NOVEDAD_SKIP && return nothing
    # Novedad desconocida: advertir y omitir
    @debug "OTC: NomNovedad no reconocida, se omite: '$nom'"
    return nothing
end

"""
    otc_resolve_dates(row) -> (fs, fl)

Determina Fecha_Salida (fs) y Fecha_Llegada (fl) para un registro OTC.

Reglas:
    • Si F3 no es missing → fs = F3, fl = F4 (o F3 si F4 es missing)
    • Si F3 es missing y F1 no es missing → fs = fl = F1 (un solo día)
    • De lo contrario → (missing, missing) → la fila se descarta
"""
function otc_resolve_dates(row)
    f1 = get(row, :F1, missing)
    f3 = get(row, :F3, missing)
    f4 = get(row, :F4, missing)

    if !ismissing(f3)
        fl = ismissing(f4) ? f3 : f4
        return (f3, fl)
    elseif !ismissing(f1)
        return (f1, f1)
    else
        return (missing, missing)
    end
end

"""
    build_otc_normalized(raw_df, ubicacion_map) -> DataFrame

Transforma la tabla cruda de Ausencias al formato normalizado:
    1. Resuelve fechas (F1/F3/F4 → Fecha_Salida/Fecha_Llegada)
    2. Clasifica NomNovedad → tipo (:AUS/:INC/:VAC) y prefijo de Numero_novedad
    3. Asigna Ubicación y _country desde ubicacion_map
    4. Descarta novedades no clasificadas ("No reportamos" + desconocidas)
Retorna DataFrame con columnas en formato unificado, listo para expand_rows.
"""
function build_otc_normalized(
    raw_df::DataFrame,
    ubicacion_map::Dict{String,String},
)::DataFrame

    isempty(raw_df) && return DataFrame()
    rows_out = []

    for r in eachrow(raw_df)
        nom_nov = string(coalesce(get(r, :NomNovedad, ""), ""))
        tipo = otc_classify_novedad(nom_nov)
        isnothing(tipo) && continue   # "No reportamos" o desconocida → saltar

        fs, fl = otc_resolve_dates(r)
        (ismissing(fs) || ismissing(fl)) && continue  # sin fechas → saltar

        solid   = string(coalesce(get(r, :EmpleadoId, ""), ""))
        numero  = string(coalesce(get(r, :Numero, ""), ""))
        dias    = safe_f64(get(r, :Dias,  missing))
        horas   = safe_f64(get(r, :Horas, missing))
        nombre  = string(coalesce(get(r, :Empleado, ""), ""))

        # Prefijo del Numero_novedad según tipo
        prefix = tipo == :VAC ? "VAC" : tipo == :INC ? "INC" : "AUS"
        num_nov_built = isempty(numero) ? "$(prefix)-?" : "$(prefix)-$(numero)"

        # País del empleado desde el mapa de ubicación
        pais_str    = get(ubicacion_map, solid, "Colombia")
        country_sym = Config.otc_pais_to_symbol(pais_str)

        push!(rows_out, (
            SOLID             = solid,
            Fecha_Salida      = fs,
            Fecha_Llegada     = fl,
            Nombre_y_Apellido = nombre,
            Novedad           = nom_nov,
            Numero_novedad    = num_nov_built,
            Dias_Numeros      = dias > 0 ? dias : missing,
            Horas_Numeros     = horas > 0 ? horas : missing,
            _tipo             = tipo,
            _country_sym      = country_sym,
            # Columnas extras de trazabilidad OTC
            _otc_company   = string(coalesce(get(r, :Company,   ""), "")),
            _otc_operation = string(coalesce(get(r, :Operation, ""), "")),
            _otc_ubicacion = pais_str,
        ))
    end

    isempty(rows_out) && return DataFrame()
    return DataFrame(rows_out)
end

"""
    expand_otc_rows(norm_df) -> DataFrame

Expande el DataFrame normalizado OTC igual que expand_rows pero:
    • Usa _tipo para la lógica de fechas
    • Usa _country_sym (por fila) para festivos correctos
    • Agrega _country (String) = string(_country_sym) para el Validator
"""
function expand_otc_rows(norm_df::DataFrame)::DataFrame
    isempty(norm_df) && return DataFrame()
    expanded = []

    for r in eachrow(norm_df)
        fs   = get(r, :Fecha_Salida,  missing)
        fl   = get(r, :Fecha_Llegada, missing)
        ismissing(fs) && continue
        ismissing(fl) && (fl = fs)

        novedad   = string(coalesce(get(r, :Novedad, ""), ""))
        dias_num  = safe_f64(get(r, :Dias_Numeros, missing))
        horas_num = safe_f64(get(r, :Horas_Numeros, missing))
        num_nov   = string(coalesce(get(r, :Numero_novedad, ""), ""))
        tipo      = get(r, :_tipo, :AUS)
        ctry_sym  = get(r, :_country_sym, :CO)

        horas_total = dias_num * 8.0 + horas_num

        # Obtener rango de fechas del evento (misma lógica que expand_rows)
        fechas = fecha_evento_range(tipo, novedad, fs, fl, horas_total, :otc)

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
                _source           = :otc,
                _tipo             = tipo,
                _country          = string(ctry_sym),   # ← para Validator
                _otc_ubicacion    = string(coalesce(get(r, :_otc_ubicacion, ""), "")),
                _otc_company      = string(coalesce(get(r, :_otc_company,   ""), "")),
                _otc_operation    = string(coalesce(get(r, :_otc_operation, ""), "")),
            ))
        end
    end

    isempty(expanded) && return DataFrame()
    return DataFrame(expanded)
end
```

---

## 4D — Agregar la función pública `load_all_sources_otc`

**Busque** el comentario `# API pública` seguido de la función `load_all_sources`. **Justo DESPUÉS** del cierre de esa función (`end` final de `load_all_sources`), agregue la siguiente función:

```julia
"""
    load_all_sources_otc() -> DataFrame | nothing

Carga y procesa la fuente OTC (People Management / Leaders APP).

Flujo:
    1. Descarga dbo.Ausencias desde Leaders APP (OTCConnector)
    2. Carga data/ubicacion.xlsx → mapa SOLID → País
    3. Merge: asigna Ubicación (país) a cada fila por EmpleadoId
    4. Normaliza columnas al formato unificado
    5. Clasifica novedades: AUS / INC / VAC (filtra "No reportamos")
    6. Expande filas por días hábiles usando festivos del país de cada fila
    7. Enriquece con Roster y Types_of_PTO
    8. Retorna tabla unificada lista para IDBuilder
"""
function load_all_sources_otc()::Union{DataFrame, Nothing}

    println("\n  [1/5] Conectando a Leaders APP (OTC)...")
    raw_df = OTCConnector.fetch_from_leaders_app()
    if isnothing(raw_df) || nrow(raw_df) == 0
        @error "No se obtuvieron datos de Leaders APP para el proceso OTC."
        return nothing
    end

    println("\n  [2/5] Cargando mapa de ubicaciones (data/ubicacion.xlsx)...")
    ubicacion_map = Dict{String,String}()
    if isfile(Config.UBICACION_FILE)
        try
            using_xlsx = begin
                import XLSX
                xf = XLSX.readxlsx(Config.UBICACION_FILE)
                sh = xf[XLSX.sheetnames(xf)[1]]
                df_ub = XLSX.eachtablerow(sh) |> DataFrame
                if "SOLID" ∈ names(df_ub) && "Pais" ∈ names(df_ub)
                    for row in eachrow(df_ub)
                        k = string(coalesce(row.SOLID, ""))
                        v = string(coalesce(row.Pais,  "Colombia"))
                        !isempty(k) && (ubicacion_map[k] = v)
                    end
                    println("  ✓ ubicacion.xlsx: $(length(ubicacion_map)) empleados mapeados.")
                else
                    @warn "ubicacion.xlsx no tiene columnas 'SOLID' y 'Pais'. Se usará Colombia por defecto."
                end
                true
            end
        catch e
            @warn "No se pudo leer data/ubicacion.xlsx: $e — Se usará Colombia por defecto."
        end
    else
        @warn "No existe data/ubicacion.xlsx. Se asignará Colombia a todos los empleados OTC."
        println("  ⚠ Cree el archivo data/ubicacion.xlsx con columnas SOLID y Pais.")
    end

    println("\n  [3/5] Normalizando y clasificando novedades OTC...")
    norm_df = build_otc_normalized(raw_df, ubicacion_map)
    if isempty(norm_df)
        @error "Tras clasificar NomNovedad, no quedaron filas OTC a procesar."
        return nothing
    end
    n_aus = count(r -> r._tipo == :AUS, eachrow(norm_df))
    n_inc = count(r -> r._tipo == :INC, eachrow(norm_df))
    n_vac = count(r -> r._tipo == :VAC, eachrow(norm_df))
    println("  ✓ Clasificadas: AUS=$(n_aus) | INC=$(n_inc) | VAC=$(n_vac)")

    println("\n  [4/5] Expandiendo filas OTC por días hábiles...")
    expanded = expand_otc_rows(norm_df)
    if isempty(expanded)
        @error "La expansión OTC resultó en 0 filas."
        return nothing
    end
    println("  ✓ OTC expandido: $(nrow(expanded)) filas.")

    println("\n  [5/5] Cargando archivos locales (Roster, Types of PTO)...")
    roster_df    = LocalFilesConnector.load_roster()
    types_pto_df = LocalFilesConnector.load_types_of_pto()

    unified = enrich_with_lookups(expanded, types_pto_df, roster_df)
    sort!(unified, :Fecha_Salida)

    println("\n  ✓ [OTC] Tabla unificada: $(nrow(unified)) filas, $(ncol(unified)) columnas.")
    return unified
end
```

---

## 4E — Agregar `:otc` al `fecha_evento_range` (para que no falle con la fuente `:otc`)

**Busque** dentro de `fecha_evento_range` esta línea:
```julia
    single_day_set = source == :midasoft ? SINGLE_DAY_MIDASOFT : SINGLE_DAY_FORMS
```

**Reemplácela** por:
```julia
    # Para :otc la clasificación AUS/INC/VAC ya se hizo en OTC loader;
    # la expansión single_day la maneja _tipo directamente.
    single_day_set = source == :midasoft ? SINGLE_DAY_MIDASOFT :
                     source == :otc      ? Set{String}() :   # OTC no tiene singles por nombre
                                          SINGLE_DAY_FORMS
```

---

# PASO 5 — Modificar `main.jl`

---

## 5A — Agregar `include` del nuevo módulo

**Busque** el bloque de `include` al principio:
```julia
include("src/Config.jl")
include("src/SynapseConnector.jl")
include("src/SharePointConnector.jl")
include("src/LocalFilesConnector.jl")
include("src/DataLoader.jl")
```

**Reemplácelo** por (agrega OTCConnector entre LocalFilesConnector y DataLoader):
```julia
include("src/Config.jl")
include("src/SynapseConnector.jl")
include("src/SharePointConnector.jl")
include("src/LocalFilesConnector.jl")
include("src/OTCConnector.jl")
include("src/DataLoader.jl")
```

---

## 5B — Agregar función `prepare_otc_data`

**Busque** la función `prepare_country_data` y su cierre `end`. **Justo DESPUÉS** de ese `end`, agregue:

```julia
# Función auxiliar: preparar datos del proceso OTC
"""
    prepare_otc_data() -> NamedTuple | nothing

Descarga y prepara los datos del proceso OTC (Leaders APP).
Retorna: (country, unified, def_df, new_ids, has_new) o nothing si falló.
"""
function prepare_otc_data()
    prefix = "OTC"
    println("\n $(B)[$(prefix)]$(R) Cargando datos de $(B)Others Countries (People Management)$(R)...")

    raw = DataLoader.load_all_sources_otc()
    if isnothing(raw) || isempty(raw)
        println("  $(RD)✗ [OTC] No se obtuvieron datos de Leaders APP.$(R)")
        return nothing
    end

    # _country ya está asignado por fila en OTCLoader (no sobreescribir aquí)
    # Solo verificar que la columna existe; si no, asignar Colombia por defecto
    if :_country ∉ names(raw)
        raw[!, :_country] .= "CO"
    end

    unified = IDBuilder.build_unified(raw)
    def_df  = DefManager.load_def(:OTC)
    new_ids = DefManager.find_new(unified, def_df)

    n_new = length(new_ids)
    if n_new == 0
        println("  $(GR)✓ [OTC] Ya está actualizado. Sin novedades nuevas.$(R)")
    else
        println("  $(YL)$(B)→ [OTC] $(n_new) novedades nuevas en Others Countries$(R)")
    end

    return (
        country = :OTC,
        unified = unified,
        def_df  = def_df,
        new_ids = new_ids,
        has_new = n_new > 0,
    )
end
```

---

## 5C — Actualizar la función `main()` para cargar OTC

**Busque** dentro de `main()` el bloque de carga de países:
```julia
    # PASO 1-3: Descargar datos para todos los países
    step(1, "Cargando datos de COLOMBIA, ARGENTINA, MEXICO...")

    # Descargar en secuencia (para evitar conflictos con la autenticación SharePoint)
    data_co = prepare_country_data(:CO)
    data_ar = prepare_country_data(:AR)
    data_mx = prepare_country_data(:MX)
```

**Reemplácelo** por:
```julia
    # PASO 1-3: Descargar datos para todos los procesos
    step(1, "Cargando datos de COLOMBIA, ARGENTINA, MEXICO y OTC...")

    # Descargar en secuencia (evita conflictos de autenticación SharePoint)
    data_co  = prepare_country_data(:CO)
    data_ar  = prepare_country_data(:AR)
    data_mx  = prepare_country_data(:MX)
    data_otc = prepare_otc_data()
```

---

## 5D — Agregar OTC a la detección de novedades nuevas

**Busque** el bloque:
```julia
    countries_with_new = Symbol[]
    data_co !== nothing && data_co.has_new && push!(countries_with_new, :CO)
    data_ar !== nothing && data_ar.has_new && push!(countries_with_new, :AR)
    data_mx !== nothing && data_mx.has_new && push!(countries_with_new, :MX)
```

**Reemplácelo** por:
```julia
    countries_with_new = Symbol[]
    data_co  !== nothing && data_co.has_new  && push!(countries_with_new, :CO)
    data_ar  !== nothing && data_ar.has_new  && push!(countries_with_new, :AR)
    data_mx  !== nothing && data_mx.has_new  && push!(countries_with_new, :MX)
    data_otc !== nothing && data_otc.has_new && push!(countries_with_new, :OTC)
```

---

## 5E — Actualizar el mensaje cuando no hay novedades

**Busque** el bloque que imprime el estado cuando no hay novedades:
```julia
    if isempty(countries_with_new)
        println("\n$(GR)$(B)✅  No hay novedades nuevas para ningún país.$(R)")
        println("   Colombia: $(data_co !== nothing ? string(length(DefManager.load_def(:CO) |> nrow)) : "sin conexión") registros históricos")
        println("   Argentina: $(data_ar !== nothing ? string(length(DefManager.load_def(:AR) |> nrow)) : "sin conexión") registros históricos")
        println("   Mexico: $(data_mx !== nothing ? string(length(DefManager.load_def(:MX) |> nrow)) : "sin conexión") registros históricos")
        println()
        return
    end
```

**Reemplácelo** por:
```julia
    if isempty(countries_with_new)
        println("\n$(GR)$(B)✅  No hay novedades nuevas para ningún proceso.$(R)")
        println("   Colombia:         $(data_co  !== nothing ? string(nrow(DefManager.load_def(:CO)))  : "sin conexión") registros históricos")
        println("   Argentina:        $(data_ar  !== nothing ? string(nrow(DefManager.load_def(:AR)))  : "sin conexión") registros históricos")
        println("   Mexico:           $(data_mx  !== nothing ? string(nrow(DefManager.load_def(:MX)))  : "sin conexión") registros históricos")
        println("   Others Countries: $(data_otc !== nothing ? string(nrow(DefManager.load_def(:OTC))) : "sin conexión") registros históricos")
        println()
        return
    end
```

---

## 5F — Agregar OTC al mapa de datos por proceso

**Busque** el bloque:
```julia
    country_data_map = Dict{Symbol, Any}()
    data_co !== nothing && data_co.has_new && (country_data_map[:CO] = data_co)
    data_ar !== nothing && data_ar.has_new && (country_data_map[:AR] = data_ar)
    data_mx !== nothing && data_mx.has_new && (country_data_map[:MX] = data_mx)
```

**Reemplácelo** por:
```julia
    country_data_map = Dict{Symbol, Any}()
    data_co  !== nothing && data_co.has_new  && (country_data_map[:CO]  = data_co)
    data_ar  !== nothing && data_ar.has_new  && (country_data_map[:AR]  = data_ar)
    data_mx  !== nothing && data_mx.has_new  && (country_data_map[:MX]  = data_mx)
    data_otc !== nothing && data_otc.has_new && (country_data_map[:OTC] = data_otc)
```

---

## 5G — Actualizar el título principal

**Busque**:
```julia
    header("SISTEMA PTO NOVEDADES v3.0 — Solvo Global  |  $(Dates.today())")
```

**Reemplácelo** por:
```julia
    header("SISTEMA PTO NOVEDADES v4.0 — Solvo Global  |  $(Dates.today())")
```

---

# PASO 6 — Modificar `src/Panel.jl`

Se hacen cambios en dos funciones: `run_country_selector_gtk` y `run_country_selector_terminal`.

---

## 6A — Agregar la clase CSS `.btn-otc` en `run_country_selector_gtk`

**Busque** la clase `.btn-mx` dentro de `css_sel` en `run_country_selector_gtk`:
```julia
    .btn-mx {
        background-color: #b54a1a; color: #ffffff;
        font-weight: bold; font-size: 14px;
        border-radius: 8px; padding: 12px 32px; border: none;
        min-width: 200px;
    }
    .btn-disabled {
```

**Reemplácelo** por (inserta `.btn-otc` entre `.btn-mx` y `.btn-disabled`):
```julia
    .btn-mx {
        background-color: #b54a1a; color: #ffffff;
        font-weight: bold; font-size: 14px;
        border-radius: 8px; padding: 12px 32px; border: none;
        min-width: 200px;
    }
    .btn-otc {
        background-color: #1a5b7a; color: #ffffff;
        font-weight: bold; font-size: 14px;
        border-radius: 8px; padding: 12px 32px; border: none;
        min-width: 200px;
    }
    .btn-disabled {
```

---

## 6B — Ampliar el tamaño de la ventana del selector

El selector ahora tiene 4 botones y necesita más espacio.

**Busque**:
```julia
    win_sel = GtkWindow("Selección de País - PTO Novedades", 520, 380)
    set_gtk_property!(win_sel, :default_width, 520)
    set_gtk_property!(win_sel, :default_height, 380)
```

**Reemplácelo** por:
```julia
    win_sel = GtkWindow("Selección de Proceso - PTO Novedades", 680, 430)
    set_gtk_property!(win_sel, :default_width, 680)
    set_gtk_property!(win_sel, :default_height, 430)
```

---

## 6C — Actualizar el título del selector

**Busque**:
```julia
    t1 = GtkLabel("🌎 PROCESAMIENTO DE NOVEDADES PTO")
```

**Reemplácelo** por:
```julia
    t1 = GtkLabel("🌎  PROCESAMIENTO DE NOVEDADES PTO — v4.0")
```

**Busque** (la línea justo abajo):
```julia
    t2 = GtkLabel("Seleccione el país a procesar - $(Dates.today())")
```

**Reemplácelo** por:
```julia
    t2 = GtkLabel("Seleccione el proceso a ejecutar — $(Dates.today())")
```

---

## 6D — Agregar botón OTC y su disponibilidad

**Busque** el bloque de creación de botones de país:
```julia
    selected_country = Ref{Symbol}(:CO)  # default Colombia

    btn_co = GtkButton("🇨🇴 Colombia")
    btn_ar = GtkButton("🇦🇷 Argentina")
    btn_mx = GtkButton("🇲🇽 Mexico")

    co_available = :CO ∈ available_countries
    ar_available = :AR ∈ available_countries
    mx_available = :MX ∈ available_countries

    push!(Gtk.GAccessor.style_context(btn_co), co_available ? "btn-co" : "btn-disabled")
    push!(Gtk.GAccessor.style_context(btn_ar),  ar_available ? "btn-ar" : "btn-disabled")
    push!(Gtk.GAccessor.style_context(btn_mx),  mx_available ? "btn-mx" : "btn-disabled")
    set_gtk_property!(btn_co, :sensitive, co_available)
    set_gtk_property!(btn_ar, :sensitive, ar_available)
    set_gtk_property!(btn_mx, :sensitive, mx_available)

    push!(country_box, btn_co)
    push!(country_box, btn_ar)
    push!(country_box, btn_mx)
    push!(outer, country_box)
```

**Reemplácelo** por:
```julia
    selected_country = Ref{Symbol}(:CO)  # default Colombia

    btn_co  = GtkButton("🇨🇴  Colombia")
    btn_ar  = GtkButton("🇦🇷  Argentina")
    btn_mx  = GtkButton("🇲🇽  Mexico")
    btn_otc = GtkButton("🌍  Others Countries")

    co_available  = :CO  ∈ available_countries
    ar_available  = :AR  ∈ available_countries
    mx_available  = :MX  ∈ available_countries
    otc_available = :OTC ∈ available_countries

    push!(Gtk.GAccessor.style_context(btn_co),  co_available  ? "btn-co"  : "btn-disabled")
    push!(Gtk.GAccessor.style_context(btn_ar),  ar_available  ? "btn-ar"  : "btn-disabled")
    push!(Gtk.GAccessor.style_context(btn_mx),  mx_available  ? "btn-mx"  : "btn-disabled")
    push!(Gtk.GAccessor.style_context(btn_otc), otc_available ? "btn-otc" : "btn-disabled")
    set_gtk_property!(btn_co,  :sensitive, co_available)
    set_gtk_property!(btn_ar,  :sensitive, ar_available)
    set_gtk_property!(btn_mx,  :sensitive, mx_available)
    set_gtk_property!(btn_otc, :sensitive, otc_available)

    # Primera fila: CO, AR, MX
    push!(country_box, btn_co)
    push!(country_box, btn_ar)
    push!(country_box, btn_mx)
    push!(outer, country_box)

    # Segunda fila: OTC (centrado)
    otc_box = GtkBox(:h)
    set_gtk_property!(otc_box, :halign, 3)
    push!(otc_box, btn_otc)
    push!(outer, otc_box)
```

---

## 6E — Actualizar el indicador de selección inicial

**Busque**:
```julia
    # Indicador de selección
    sel_lbl = GtkLabel(
        co_available ? "▶ Colombia seleccionada"  :
        ar_available ? "▶ Argentina seleccionada" : 
                    "▶ Mexico seleccionado"
    )
```

**Reemplácelo** por:
```julia
    # Indicador de selección
    sel_lbl = GtkLabel(
        co_available  ? "▶  Colombia seleccionada"          :
        ar_available  ? "▶  Argentina seleccionada"         :
        mx_available  ? "▶  Mexico seleccionado"            :
        otc_available ? "▶  Others Countries seleccionado"  :
                        "▶  (ningún proceso disponible)"
    )
```

---

## 6F — Agregar el badge de estado para OTC

**Busque** el bloque de badges:
```julia
    co_badge = GtkLabel(co_available ? "✓ Colombia - tiene novedades nuevas" :
                                        "✗ Colombia - sin novedades nuevas (ya procesado)")
    ar_badge = GtkLabel(ar_available ? "✓ Argentina - tiene novedades nuevas" :
                                        "✗ Argentina - sin novedades nuevas (ya procesado)")
    mx_badge = GtkLabel(mx_available ? "✓ Mexico - tiene novedades nuevas" : 
                                        "✗ Mexico - sin novedades nuevas (ya procesado)")
    push!(Gtk.GAccessor.style_context(co_badge), co_available ? "badge-ok" : "badge-no")
    push!(Gtk.GAccessor.style_context(ar_badge), ar_available ? "badge-ok" : "badge-no")
    push!(Gtk.GAccessor.style_context(mx_badge), mx_available ? "badge-ok" : "badge-no")
    set_gtk_property!(co_badge, :halign, 1)
    set_gtk_property!(ar_badge, :halign, 1)
    set_gtk_property!(mx_badge, :halign, 1)
    push!(badge_box, co_badge)
    push!(badge_box, ar_badge)
    push!(badge_box, mx_badge)
```

**Reemplácelo** por:
```julia
    co_badge  = GtkLabel(co_available  ? "✓ Colombia — novedades nuevas"          : "✗ Colombia — sin novedades nuevas")
    ar_badge  = GtkLabel(ar_available  ? "✓ Argentina — novedades nuevas"         : "✗ Argentina — sin novedades nuevas")
    mx_badge  = GtkLabel(mx_available  ? "✓ Mexico — novedades nuevas"            : "✗ Mexico — sin novedades nuevas")
    otc_badge = GtkLabel(otc_available ? "✓ Others Countries (OTC) — novedades nuevas" : "✗ Others Countries (OTC) — sin novedades nuevas")
    push!(Gtk.GAccessor.style_context(co_badge),  co_available  ? "badge-ok" : "badge-no")
    push!(Gtk.GAccessor.style_context(ar_badge),  ar_available  ? "badge-ok" : "badge-no")
    push!(Gtk.GAccessor.style_context(mx_badge),  mx_available  ? "badge-ok" : "badge-no")
    push!(Gtk.GAccessor.style_context(otc_badge), otc_available ? "badge-ok" : "badge-no")
    for lbl in (co_badge, ar_badge, mx_badge, otc_badge)
        set_gtk_property!(lbl, :halign, 1)
    end
    push!(badge_box, co_badge)
    push!(badge_box, ar_badge)
    push!(badge_box, mx_badge)
    push!(badge_box, otc_badge)
```

---

## 6G — Actualizar el valor por defecto del `result_holder`

**Busque**:
```julia
    result_holder = Ref{CountrySelectionResult}(
        CountrySelectionResult(
            co_available ? :CO :
            ar_available ? :AR :
            :MX, false
        ))
```

**Reemplácelo** por:
```julia
    result_holder = Ref{CountrySelectionResult}(
        CountrySelectionResult(
            co_available  ? :CO  :
            ar_available  ? :AR  :
            mx_available  ? :MX  :
            otc_available ? :OTC :
            :CO, false
        ))
```

---

## 6H — Agregar el signal_connect del botón OTC

**Busque** el bloque de `signal_connect` de los botones de país:
```julia
    signal_connect(btn_co, :clicked) do _
        selected_country[] = :CO
        GAccessor.label(sel_lbl, "▶ Colombia seleccionada")
    end
    signal_connect(btn_ar, :clicked) do _
        selected_country[] = :AR
        GAccessor.label(sel_lbl, "▶ Argentina seleccionada")
    end
    signal_connect(btn_mx, :clicked) do _
        selected_country[] = :MX
        GAccessor.label(sel_lbl, "▶ Mexico seleccionado")
    end
```

**Reemplácelo** por:
```julia
    signal_connect(btn_co, :clicked) do _
        selected_country[] = :CO
        GAccessor.label(sel_lbl, "▶  Colombia seleccionada")
    end
    signal_connect(btn_ar, :clicked) do _
        selected_country[] = :AR
        GAccessor.label(sel_lbl, "▶  Argentina seleccionada")
    end
    signal_connect(btn_mx, :clicked) do _
        selected_country[] = :MX
        GAccessor.label(sel_lbl, "▶  Mexico seleccionado")
    end
    signal_connect(btn_otc, :clicked) do _
        selected_country[] = :OTC
        GAccessor.label(sel_lbl, "▶  Others Countries (OTC) seleccionado")
    end
```

---

## 6I — Actualizar `run_country_selector_terminal` para OTC

**Busque** la función `run_country_selector_terminal`. Dentro de ella, busque el bloque que verifica disponibilidades:
```julia
    co_ok = :CO ∈ available_countries
    ar_ok = :AR ∈ available_countries
    mx_ok = :MX ∈ available_countries
```

**Reemplácelo** por:
```julia
    co_ok  = :CO  ∈ available_countries
    ar_ok  = :AR  ∈ available_countries
    mx_ok  = :MX  ∈ available_countries
    otc_ok = :OTC ∈ available_countries
```

Luego, **busque** las líneas que imprimen las opciones:
```julia
    println(row("  $(co_ok ? "$(GR)$(B)[1]$(R)$(GR) 🇨🇴  Colombia$(R)" : "$(D)[1] Colombia - sin novedades nuevas$(R)")"))
    println(row("  $(ar_ok ? "$(MG)$(B)[2]$(R)$(MG) 🇦🇷  Argentina$(R)" : "$(D)[2] Argentina - sin novedades nuevas$(R)")"))
    println(row("  $(mx_ok ? "$(MG)$(B)[3]$(R)$(MG) 🇲🇽  Mexico$(R)" : "$(D)[3] Mexico - sin novedades nuevas$(R)")"))
```

**Reemplácelas** por:
```julia
    println(row("  $(co_ok  ? "$(GR)$(B)[1]$(R)$(GR) 🇨🇴  Colombia$(R)"               : "$(D)[1] Colombia — sin novedades nuevas$(R)")"))
    println(row("  $(ar_ok  ? "$(MG)$(B)[2]$(R)$(MG) 🇦🇷  Argentina$(R)"              : "$(D)[2] Argentina — sin novedades nuevas$(R)")"))
    println(row("  $(mx_ok  ? "$(MG)$(B)[3]$(R)$(MG) 🇲🇽  Mexico$(R)"                 : "$(D)[3] Mexico — sin novedades nuevas$(R)")"))
    println(row("  $(otc_ok ? "$(CY)$(B)[4]$(R)$(CY) 🌍  Others Countries (OTC)$(R)"  : "$(D)[4] Others Countries — sin novedades nuevas$(R)")"))
```

Finalmente, **busque** el `Dict` de opciones disponibles:
```julia
    available_opts = Dict(
        "1" => :CO,
        "2" => :AR,
    )
```

**Reemplácelo** por:
```julia
    available_opts = Dict(
        "1" => :CO,
        "2" => :AR,
        "3" => :MX,
        "4" => :OTC,
    )
```

(Si ya tiene "3" => :MX, solo agregue "4" => :OTC)

---

---

# VERIFICACIÓN FINAL — Checklist antes de ejecutar

Antes de correr `include("main.jl")`, verifique:

**Archivos y carpetas:**
- [ ] Existe `data/ubicacion.xlsx` con columnas `SOLID` y `Pais`
- [ ] Existe `src/OTCConnector.jl` (creado en el PASO 3)

**`src/Config.jl`:**
- [ ] `SYNAPSE_DATABASE_OTC = "LeadersAPP"` (cambiar al nombre real de la BD)
- [ ] `OTC_TABLE_AUSENCIAS = "Ausencias"` (cambiar si la tabla tiene otro nombre)
- [ ] `UBICACION_FILE` apunta a `data/ubicacion.xlsx`
- [ ] Existen `FESTIVOS_KENYA`, `FESTIVOS_PERU`, `FESTIVOS_GUATEMALA`, `FESTIVOS_INDIA`, `FESTIVOS_DOMINICANA`, `FESTIVOS_BRASIL`
- [ ] `country_festivos(:KE)`, `:PE`, `:GT`, `:IND`, `:DOM`, `:BR` están en el switch
- [ ] `country_name(:OTC)` = "Others Countries"
- [ ] `otc_pais_to_symbol(...)` existe al final del módulo

**`src/OTCConnector.jl`:**
- [ ] El archivo existe y el módulo se llama `module OTCConnector`

**`src/DataLoader.jl`:**
- [ ] `using ..OTCConnector` está en las dependencias
- [ ] `load_all_sources_otc` está en el `export`
- [ ] Existen `OTC_NOVEDAD_AUS`, `OTC_NOVEDAD_INC`, `OTC_NOVEDAD_VAC`, `OTC_NOVEDAD_SKIP`
- [ ] Existe `build_otc_normalized`, `expand_otc_rows`, `load_all_sources_otc`
- [ ] `fecha_evento_range` maneja `source == :otc` sin error

**`main.jl`:**
- [ ] `include("src/OTCConnector.jl")` está ANTES de `include("src/DataLoader.jl")`
- [ ] Existe la función `prepare_otc_data()`
- [ ] `data_otc = prepare_otc_data()` está en `main()`
- [ ] `:OTC` se agrega a `countries_with_new`
- [ ] `country_data_map[:OTC] = data_otc` está en el mapa

**`src/Panel.jl`:**
- [ ] CSS tiene clase `.btn-otc { background-color: #1a5b7a; ... }`
- [ ] `btn_otc = GtkButton("🌍  Others Countries")`
- [ ] `otc_available = :OTC ∈ available_countries`
- [ ] `signal_connect(btn_otc, ...)` existe
- [ ] Terminal muestra `[4] 🌍 Others Countries (OTC)`
- [ ] `"4" => :OTC` en `available_opts`

---

# SALIDA ESPERADA al ejecutar

```
════════════════════════════════════════════════════════════════════════
  SISTEMA PTO NOVEDADES v4.0 — Solvo Global  |  2025-06-29
════════════════════════════════════════════════════════════════════════

▶ [1]  Cargando datos de COLOMBIA, ARGENTINA, MEXICO y OTC...

 [CO] Cargando datos de Colombia...
   ✓ ausentismos [Colombia]: 1234 filas
   ✓ incapacidades [Colombia]: 456 filas
   ✓ vacaciones [Colombia]: 789 filas

 [AR] Cargando datos de Argentina...
   ✓ AusentismosArgentina [Argentina]: ...

 [MX] Cargando datos de Mexico...
   ✓ AusentismoMexico [Mexico]: ...

 [OTC] Cargando datos de Others Countries (People Management)...
   Conectando a Leaders APP (OTC)...
   ✓ Ausencias [OTC]: 2891 filas descargadas.
   ✓ ubicacion.xlsx: 847 empleados mapeados.
   ✓ Clasificadas: AUS=1203 | INC=445 | VAC=1243
   ✓ OTC expandido: 4892 filas.
   → [OTC] 612 novedades nuevas en Others Countries

▶ [2]  Verificando novedades nuevas por país...
  Procesos con novedades nuevas: Colombia + OTC

▶ [3]  Abriendo selector de país...
  ┌─────────────────────────────────────────────────────┐
  │  🌎 PROCESAMIENTO DE NOVEDADES PTO — v4.0           │
  │  [🇨🇴 Colombia] [🇦🇷 Argentina] [🇲🇽 Mexico]        │
  │           [🌍 Others Countries]                     │
  │  ▶ Colombia seleccionada                            │
  └─────────────────────────────────────────────────────┘

[Usuario selecciona OTC y presiona Procesar]

▶ [4]  Iniciando procesamiento de Others Countries...
  INCAPACIDADES:  445 IDs → 1 sub-núcleo
  AUSENTISMOS:   1203 IDs → 3 sub-núcleos
  VACACIONES:    1243 IDs → 3 sub-núcleos

  ✅ COMPLETADO
  📥 Exportar y Salir
  🔄 Exportar y Volver

[Al exportar:]
  📁  Carpeta:  output/OTC/
  📄  Def.xlsx          → OTC_Def_2025-06-29.xlsx
  ⚠   Rechazadas        → OTC_Rejected_2025-06-29.xlsx
```

---

*Guía generada para PTO Novedades v4.0 — OTC (People Management)*
