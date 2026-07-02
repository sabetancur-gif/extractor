# GUÍA — Forms SharePoint para OTC + Festivos países faltantes
## PTO Novedades v4.0

---

## QUÉ SE HACE EN ESTA GUÍA

1. Agregar `VALORES_FORMS_UBICACION_OTC` en `Config.jl`
2. Agregar festivos 2024–2027 para los 14 países OTC que aún no los tienen:
   Estados Unidos, Sudáfrica, Chile, Nicaragua, España, Nigeria, Armenia,
   Georgia, Ghana, Uganda, Zimbabwe, Jamaica, Bolivia, Venezuela
3. Actualizar `country_festivos` con todos los nuevos símbolos
4. Actualizar `otc_pais_to_symbol` para mapear todos los valores de
   `VALORES_FORMS_UBICACION_OTC` al símbolo de país correcto
5. Actualizar `country_ubicaciones` para que `:OTC` devuelva el nuevo set
6. Actualizar `DataLoader.jl` para descargar y filtrar Forms también en OTC

Todo se hace en **2 archivos**: `src/Config.jl` y `src/DataLoader.jl`.

---

# PASO 1 — `src/Config.jl`: agregar `VALORES_FORMS_UBICACION_OTC`

**Busque** la constante `VALORES_FORMS_UBICACION_MX` (las últimas líneas antes
de la función `country_ubicaciones`):
```julia
const VALORES_FORMS_UBICACION_MX = Set([
    "México", "Mexico"
])
```

**Justo después** de ese bloque, **antes** de la función `country_ubicaciones`,
agregue:

```julia
const VALORES_FORMS_UBICACION_OTC = Set([
    "República Dominicana", "Guatemala ", "Guatemala",
    "Honduras", "Remoto en Honduras", "Republica Dominicana",
    "Republica Dominicana ", "GUATEMALA ALLIED", "El Salvador",
    "Ciudad de guatemala", "Ciudad De Guatemala ", "Honduras ", "kenia",
    "Filipinas", "Kenya", "Rep Dominicana", "Belize", "Kenya ", "Belice",
    "Perú", "Belize ", "Brasil", "Peru", "Peru ", "India", "Philippines",
    "Brazil", "Philipines", "Philippines ", "Uruguay", "Filipinas ", "Filpinas",
    "Estados Unidos", "South Africa ",
    "Chile", "Nicaragua", "España", "Nigeria ", "Armenia", "Georgia",
    "Nigeria", "Ghana", "Uganda", "Belize City", "South Africa", "Zimbabwe",
    "Jamaica", "Africa", "Nairobi", "Sur Africa", "Bolivia", "Venezuela",
])
```

---

# PASO 2 — `src/Config.jl`: agregar festivos de los 14 países faltantes

Los siguientes países aparecen en `VALORES_FORMS_UBICACION_OTC` pero **no tienen
constante de festivos** en su `Config.jl` actual. Debe agregarlos.

**Ubíquese** justo después de la constante `FESTIVOS_EL_SALVADOR` (la última
que usted ya tiene). **Inserte los siguientes bloques en ese lugar:**

```julia
# ── Festivos Estados Unidos 2024–2027 ─────────────────────────────────────
# Feriados federales. Los lunes sustitutos se aplican cuando el feriado
# cae en domingo (→ lunes siguiente) o sábado (→ viernes anterior).
const FESTIVOS_EEUU = Set([
    # 2024
    Date(2024,1,1),   # New Year's Day
    Date(2024,1,15),  # MLK Day (3er lunes enero)
    Date(2024,2,19),  # Presidents' Day (3er lunes febrero)
    Date(2024,5,27),  # Memorial Day (último lunes mayo)
    Date(2024,6,19),  # Juneteenth
    Date(2024,7,4),   # Independence Day
    Date(2024,9,2),   # Labor Day (1er lunes septiembre)
    Date(2024,10,14), # Columbus Day (2do lunes octubre)
    Date(2024,11,11), # Veterans Day
    Date(2024,11,28), # Thanksgiving (4to jueves noviembre)
    Date(2024,12,25), # Christmas Day
    # 2025
    Date(2025,1,1),
    Date(2025,1,20),  # MLK Day
    Date(2025,2,17),  # Presidents' Day
    Date(2025,5,26),  # Memorial Day
    Date(2025,6,19),  # Juneteenth
    Date(2025,7,4),   # Independence Day
    Date(2025,9,1),   # Labor Day
    Date(2025,10,13), # Columbus Day
    Date(2025,11,11), # Veterans Day
    Date(2025,11,27), # Thanksgiving
    Date(2025,12,25), # Christmas
    # 2026
    Date(2026,1,1),
    Date(2026,1,19),  # MLK Day
    Date(2026,2,16),  # Presidents' Day
    Date(2026,5,25),  # Memorial Day
    Date(2026,6,19),  # Juneteenth
    Date(2026,7,3),   # Independence Day (4 jul = sábado → viernes 3)
    Date(2026,9,7),   # Labor Day
    Date(2026,10,12), # Columbus Day
    Date(2026,11,11), # Veterans Day
    Date(2026,11,26), # Thanksgiving
    Date(2026,12,25), # Christmas
    # 2027
    Date(2027,1,1),
    Date(2027,1,18),  # MLK Day
    Date(2027,2,15),  # Presidents' Day
    Date(2027,5,31),  # Memorial Day
    Date(2027,6,18),  # Juneteenth (19 jun = sábado → viernes 18)
    Date(2027,7,5),   # Independence Day (4 jul = domingo → lunes 5)
    Date(2027,9,6),   # Labor Day
    Date(2027,10,11), # Columbus Day
    Date(2027,11,11), # Veterans Day
    Date(2027,11,25), # Thanksgiving
    Date(2027,12,24), # Christmas (25 dic = sábado → viernes 24)
])

# ── Festivos Sudáfrica 2024–2027 ──────────────────────────────────────────
# Fuente: Public Holidays Act 36 of 1994
# Regla: si cae en domingo → el lunes siguiente es feriado adicional.
const FESTIVOS_SUDAFRICA = Set([
    # 2024
    Date(2024,1,1),   # New Year's Day
    Date(2024,3,21),  # Human Rights Day
    Date(2024,3,29),  # Good Friday
    Date(2024,4,1),   # Family Day (Easter Monday)
    Date(2024,4,27),  # Freedom Day
    Date(2024,5,1),   # Workers' Day
    Date(2024,6,16),  # Youth Day
    Date(2024,6,17),  # Youth Day substitute (16 = domingo)
    Date(2024,8,9),   # National Women's Day
    Date(2024,9,24),  # Heritage Day
    Date(2024,12,16), # Day of Reconciliation
    Date(2024,12,25), # Christmas Day
    Date(2024,12,26), # Day of Goodwill
    # 2025
    Date(2025,1,1),
    Date(2025,3,21),
    Date(2025,4,18),  # Good Friday
    Date(2025,4,21),  # Family Day
    Date(2025,4,27),  # Freedom Day
    Date(2025,4,28),  # Freedom Day substitute (27 = domingo)
    Date(2025,5,1),
    Date(2025,6,16),
    Date(2025,8,9),
    Date(2025,8,11),  # Women's Day substitute (9 = sábado)
    Date(2025,9,24),
    Date(2025,12,16),
    Date(2025,12,25),
    Date(2025,12,26),
    # 2026
    Date(2026,1,1),
    Date(2026,3,21),
    Date(2026,3,23),  # Human Rights Day substitute (21 = sábado)
    Date(2026,4,3),   # Good Friday
    Date(2026,4,6),   # Family Day
    Date(2026,4,27),
    Date(2026,5,1),
    Date(2026,6,16),
    Date(2026,8,9),
    Date(2026,8,10),  # Women's Day substitute (9 = domingo)
    Date(2026,9,24),
    Date(2026,12,16),
    Date(2026,12,25),
    Date(2026,12,26),
    # 2027
    Date(2027,1,1),
    Date(2027,3,21),
    Date(2027,3,22),  # Human Rights Day substitute (21 = domingo)
    Date(2027,3,26),  # Good Friday
    Date(2027,3,29),  # Family Day
    Date(2027,4,27),
    Date(2027,5,1),
    Date(2027,6,16),
    Date(2027,8,9),
    Date(2027,9,24),
    Date(2027,12,16),
    Date(2027,12,25),
    Date(2027,12,26),
    Date(2027,12,27),  # Christmas substitute (25 = sábado)
])

# ── Festivos Chile 2024–2027 ──────────────────────────────────────────────
# Fuente: Ley 19.973 y modificaciones posteriores
const FESTIVOS_CHILE = Set([
    # 2024  (Easter: Mar 31)
    Date(2024,1,1),   # Año Nuevo
    Date(2024,3,29),  # Viernes Santo
    Date(2024,3,30),  # Sábado Santo
    Date(2024,5,1),   # Día del Trabajo
    Date(2024,5,21),  # Glorias Navales
    Date(2024,6,20),  # Día Nacional de los Pueblos Indígenas (3er lunes jun)
    Date(2024,6,29),  # San Pedro y San Pablo
    Date(2024,7,16),  # Virgen del Carmen
    Date(2024,8,15),  # Asunción de la Virgen
    Date(2024,9,18),  # Independencia Nacional
    Date(2024,9,19),  # Día de las Glorias del Ejército
    Date(2024,9,20),  # Feriado adicional (puente)
    Date(2024,10,12), # Día del Encuentro de Dos Mundos
    Date(2024,10,31), # Día de las Iglesias Evangélicas y Protestantes
    Date(2024,11,1),  # Día de Todos los Santos
    Date(2024,12,8),  # Inmaculada Concepción
    Date(2024,12,25), # Navidad
    # 2025  (Easter: Apr 20)
    Date(2025,1,1),
    Date(2025,4,18),  # Viernes Santo
    Date(2025,4,19),  # Sábado Santo
    Date(2025,5,1),
    Date(2025,5,21),
    Date(2025,6,20),  # Pueblos Indígenas (3er lunes junio)
    Date(2025,6,29),
    Date(2025,7,16),
    Date(2025,8,15),
    Date(2025,9,18),
    Date(2025,9,19),
    Date(2025,10,12),
    Date(2025,10,31),
    Date(2025,11,1),
    Date(2025,12,8),
    Date(2025,12,25),
    # 2026  (Easter: Apr 5)
    Date(2026,1,1),
    Date(2026,4,3),   # Viernes Santo
    Date(2026,4,4),   # Sábado Santo
    Date(2026,5,1),
    Date(2026,5,21),
    Date(2026,6,19),  # Pueblos Indígenas
    Date(2026,6,29),
    Date(2026,7,16),
    Date(2026,8,15),
    Date(2026,9,18),
    Date(2026,9,19),
    Date(2026,10,12),
    Date(2026,10,31),
    Date(2026,11,1),
    Date(2026,12,8),
    Date(2026,12,25),
    # 2027  (Easter: Mar 28)
    Date(2027,1,1),
    Date(2027,3,26),  # Viernes Santo
    Date(2027,3,27),  # Sábado Santo
    Date(2027,5,1),
    Date(2027,5,21),
    Date(2027,6,18),  # Pueblos Indígenas
    Date(2027,6,29),
    Date(2027,7,16),
    Date(2027,8,15),
    Date(2027,9,18),
    Date(2027,9,19),
    Date(2027,10,12),
    Date(2027,10,31),
    Date(2027,11,1),
    Date(2027,12,8),
    Date(2027,12,25),
])

# ── Festivos Nicaragua 2024–2027 ──────────────────────────────────────────
# Fuente: Ley No. 311 - Ley de Feriados Nacionales
const FESTIVOS_NICARAGUA = Set([
    # 2024
    Date(2024,1,1),   # Año Nuevo
    Date(2024,3,28),  # Jueves Santo
    Date(2024,3,29),  # Viernes Santo
    Date(2024,5,1),   # Día del Trabajo
    Date(2024,7,19),  # Revolución Sandinista
    Date(2024,9,14),  # Batalla de San Jacinto
    Date(2024,9,15),  # Independencia Centroamericana
    Date(2024,12,8),  # Inmaculada Concepción
    Date(2024,12,25), # Navidad
    # 2025
    Date(2025,1,1),
    Date(2025,4,17),  # Jueves Santo
    Date(2025,4,18),  # Viernes Santo
    Date(2025,5,1),
    Date(2025,7,19),
    Date(2025,9,14),
    Date(2025,9,15),
    Date(2025,12,8),
    Date(2025,12,25),
    # 2026
    Date(2026,1,1),
    Date(2026,4,2),   # Jueves Santo
    Date(2026,4,3),   # Viernes Santo
    Date(2026,5,1),
    Date(2026,7,19),
    Date(2026,9,14),
    Date(2026,9,15),
    Date(2026,12,8),
    Date(2026,12,25),
    # 2027
    Date(2027,1,1),
    Date(2027,3,25),  # Jueves Santo
    Date(2027,3,26),  # Viernes Santo
    Date(2027,5,1),
    Date(2027,7,19),
    Date(2027,9,14),
    Date(2027,9,15),
    Date(2027,12,8),
    Date(2027,12,25),
])

# ── Festivos España 2024–2027 ─────────────────────────────────────────────
# Feriados nacionales. Cada comunidad autónoma añade 2 adicionales locales;
# aquí solo se incluyen los 8 garantizados a nivel nacional.
const FESTIVOS_ESPANA = Set([
    # 2024  (Easter: Mar 31)
    Date(2024,1,1),   # Año Nuevo
    Date(2024,3,29),  # Viernes Santo
    Date(2024,5,1),   # Fiesta del Trabajo
    Date(2024,8,15),  # Asunción de la Virgen
    Date(2024,10,12), # Fiesta Nacional de España
    Date(2024,11,1),  # Todos los Santos
    Date(2024,12,6),  # Día de la Constitución
    Date(2024,12,8),  # Inmaculada Concepción
    Date(2024,12,25), # Navidad
    # 2025  (Easter: Apr 20)
    Date(2025,1,1),
    Date(2025,4,18),  # Viernes Santo
    Date(2025,5,1),
    Date(2025,8,15),
    Date(2025,10,12),
    Date(2025,10,13), # Fiesta Nacional substitute (12 = domingo)
    Date(2025,11,1),
    Date(2025,12,6),
    Date(2025,12,8),
    Date(2025,12,25),
    # 2026  (Easter: Apr 5)
    Date(2026,1,1),
    Date(2026,4,3),   # Viernes Santo
    Date(2026,5,1),
    Date(2026,8,15),
    Date(2026,10,12),
    Date(2026,11,2),  # Todos los Santos substitute (1 = domingo)
    Date(2026,12,7),  # Constitución substitute (6 = domingo)
    Date(2026,12,8),
    Date(2026,12,25),
    # 2027  (Easter: Mar 28)
    Date(2027,1,1),
    Date(2027,3,26),  # Viernes Santo
    Date(2027,5,1),
    Date(2027,8,15),
    Date(2027,8,16),  # Asunción substitute (15 = domingo)
    Date(2027,10,12),
    Date(2027,11,1),
    Date(2027,12,6),
    Date(2027,12,8),
    Date(2027,12,25),
    Date(2027,12,27), # Navidad substitute (25 = sábado)
])

# ── Festivos Nigeria 2024–2027 ────────────────────────────────────────────
# Nota: Eid al-Fitr, Eid al-Adha y Mawlid son lunares; las fechas son
# aproximadas basadas en el calendario islámico. Verifique anualmente.
const FESTIVOS_NIGERIA = Set([
    # 2024
    Date(2024,1,1),   # New Year
    Date(2024,3,29),  # Good Friday
    Date(2024,4,1),   # Easter Monday
    Date(2024,4,10),  # Eid al-Fitr (aprox)
    Date(2024,4,11),  # Eid al-Fitr (2do día)
    Date(2024,5,1),   # Workers' Day
    Date(2024,6,12),  # Democracy Day
    Date(2024,6,16),  # Eid al-Adha (aprox)
    Date(2024,6,17),  # Eid al-Adha (2do día)
    Date(2024,9,15),  # Mawlid (aprox)
    Date(2024,10,1),  # National Day
    Date(2024,12,25), # Christmas
    Date(2024,12,26), # Boxing Day
    # 2025
    Date(2025,1,1),
    Date(2025,3,30),  # Eid al-Fitr (aprox)
    Date(2025,3,31),  # Eid al-Fitr
    Date(2025,4,18),  # Good Friday
    Date(2025,4,21),  # Easter Monday
    Date(2025,5,1),
    Date(2025,6,5),   # Eid al-Adha (aprox)
    Date(2025,6,6),   # Eid al-Adha
    Date(2025,6,12),  # Democracy Day
    Date(2025,9,4),   # Mawlid (aprox)
    Date(2025,10,1),
    Date(2025,12,25),
    Date(2025,12,26),
    # 2026
    Date(2026,1,1),
    Date(2026,3,19),  # Eid al-Fitr (aprox)
    Date(2026,3,20),  # Eid al-Fitr
    Date(2026,4,3),   # Good Friday
    Date(2026,4,6),   # Easter Monday
    Date(2026,5,1),
    Date(2026,5,26),  # Eid al-Adha (aprox)
    Date(2026,5,27),  # Eid al-Adha
    Date(2026,6,12),  # Democracy Day
    Date(2026,8,24),  # Mawlid (aprox)
    Date(2026,10,1),
    Date(2026,12,25),
    Date(2026,12,26),
    # 2027
    Date(2027,1,1),
    Date(2027,3,9),   # Eid al-Fitr (aprox)
    Date(2027,3,10),  # Eid al-Fitr
    Date(2027,3,26),  # Good Friday
    Date(2027,3,29),  # Easter Monday
    Date(2027,5,1),
    Date(2027,5,15),  # Eid al-Adha (aprox)
    Date(2027,5,16),  # Eid al-Adha
    Date(2027,6,12),  # Democracy Day
    Date(2027,8,13),  # Mawlid (aprox)
    Date(2027,10,1),
    Date(2027,12,25),
    Date(2027,12,26),
])

# ── Festivos Armenia 2024–2027 ────────────────────────────────────────────
# Fuente: Ley de Feriados de la República de Armenia
const FESTIVOS_ARMENIA = Set([
    # 2024
    Date(2024,1,1),   # Año Nuevo
    Date(2024,1,2),   # Año Nuevo (2do día)
    Date(2024,1,6),   # Navidad Armenia (calendario Gregoriano)
    Date(2024,1,28),  # Día del Ejército
    Date(2024,4,7),   # Día de la Maternidad y la Belleza
    Date(2024,4,24),  # Día del Genocidio Armenio
    Date(2024,5,1),   # Día del Trabajo
    Date(2024,5,9),   # Día de la Victoria
    Date(2024,5,28),  # Día de la República
    Date(2024,7,5),   # Día de la Constitución
    Date(2024,9,21),  # Día de la Independencia
    Date(2024,12,31), # Nochevieja
    # 2025
    Date(2025,1,1),
    Date(2025,1,2),
    Date(2025,1,6),
    Date(2025,1,28),
    Date(2025,4,7),
    Date(2025,4,24),
    Date(2025,5,1),
    Date(2025,5,9),
    Date(2025,5,28),
    Date(2025,7,5),
    Date(2025,9,21),
    Date(2025,12,31),
    # 2026
    Date(2026,1,1),
    Date(2026,1,2),
    Date(2026,1,6),
    Date(2026,1,28),
    Date(2026,4,7),
    Date(2026,4,24),
    Date(2026,5,1),
    Date(2026,5,9),
    Date(2026,5,28),
    Date(2026,7,5),
    Date(2026,9,21),
    Date(2026,12,31),
    # 2027
    Date(2027,1,1),
    Date(2027,1,2),
    Date(2027,1,6),
    Date(2027,1,28),
    Date(2027,4,7),
    Date(2027,4,24),
    Date(2027,5,1),
    Date(2027,5,9),
    Date(2027,5,28),
    Date(2027,7,5),
    Date(2027,9,21),
    Date(2027,12,31),
])

# ── Festivos Georgia 2024–2027 ────────────────────────────────────────────
# Fuente: Ley de Feriados Públicos de Georgia (país en el Cáucaso)
const FESTIVOS_GEORGIA = Set([
    # 2024
    Date(2024,1,1),   # Año Nuevo
    Date(2024,1,2),   # 2do día de Año Nuevo
    Date(2024,1,7),   # Navidad Ortodoxa
    Date(2024,1,19),  # Epifanía
    Date(2024,3,3),   # Día de la Madre
    Date(2024,3,8),   # Día de la Mujer
    Date(2024,4,9),   # Día de la Unidad Nacional
    Date(2024,5,9),   # Día de la Victoria
    Date(2024,5,12),  # Día de San Andrés
    Date(2024,5,26),  # Día de la Independencia
    Date(2024,8,28),  # Mariamoba
    Date(2024,10,14), # Svetitskhovloba
    Date(2024,11,23), # Giorgoba (San Jorge)
    # 2025
    Date(2025,1,1),
    Date(2025,1,2),
    Date(2025,1,7),
    Date(2025,1,19),
    Date(2025,3,3),
    Date(2025,3,8),
    Date(2025,4,9),
    Date(2025,5,9),
    Date(2025,5,12),
    Date(2025,5,26),
    Date(2025,8,28),
    Date(2025,10,14),
    Date(2025,11,23),
    # 2026
    Date(2026,1,1),
    Date(2026,1,2),
    Date(2026,1,7),
    Date(2026,1,19),
    Date(2026,3,3),
    Date(2026,3,8),
    Date(2026,4,9),
    Date(2026,5,9),
    Date(2026,5,12),
    Date(2026,5,26),
    Date(2026,8,28),
    Date(2026,10,14),
    Date(2026,11,23),
    # 2027
    Date(2027,1,1),
    Date(2027,1,2),
    Date(2027,1,7),
    Date(2027,1,19),
    Date(2027,3,3),
    Date(2027,3,8),
    Date(2027,4,9),
    Date(2027,5,9),
    Date(2027,5,12),
    Date(2027,5,26),
    Date(2027,8,28),
    Date(2027,10,14),
    Date(2027,11,23),
])

# ── Festivos Ghana 2024–2027 ──────────────────────────────────────────────
# Fuente: Public Holidays Act 601 of Ghana
const FESTIVOS_GHANA = Set([
    # 2024
    Date(2024,1,1),   # New Year's Day
    Date(2024,3,6),   # Independence Day
    Date(2024,3,29),  # Good Friday
    Date(2024,4,1),   # Easter Monday
    Date(2024,5,1),   # Workers' Day
    Date(2024,6,4),   # Founders' Day
    Date(2024,7,1),   # Republic Day
    Date(2024,12,25), # Christmas Day
    Date(2024,12,26), # Boxing Day
    # 2025
    Date(2025,1,1),
    Date(2025,3,6),
    Date(2025,4,18),  # Good Friday
    Date(2025,4,21),  # Easter Monday
    Date(2025,5,1),
    Date(2025,6,4),
    Date(2025,7,1),
    Date(2025,12,25),
    Date(2025,12,26),
    # 2026
    Date(2026,1,1),
    Date(2026,3,6),
    Date(2026,4,3),   # Good Friday
    Date(2026,4,6),   # Easter Monday
    Date(2026,5,1),
    Date(2026,6,4),
    Date(2026,7,1),
    Date(2026,12,25),
    Date(2026,12,26),
    # 2027
    Date(2027,1,1),
    Date(2027,3,6),
    Date(2027,3,26),  # Good Friday
    Date(2027,3,29),  # Easter Monday
    Date(2027,5,1),
    Date(2027,6,4),
    Date(2027,7,1),
    Date(2027,12,25),
    Date(2027,12,26),
])

# ── Festivos Uganda 2024–2027 ─────────────────────────────────────────────
# Fuente: Public Holidays Act Uganda; Eid fechas son aproximadas (lunares)
const FESTIVOS_UGANDA = Set([
    # 2024
    Date(2024,1,1),   # New Year's Day
    Date(2024,1,26),  # Liberation Day
    Date(2024,3,8),   # Women's Day
    Date(2024,3,29),  # Good Friday
    Date(2024,4,1),   # Easter Monday
    Date(2024,5,1),   # Workers' Day
    Date(2024,6,3),   # Martyrs' Day
    Date(2024,6,9),   # Heroes' Day
    Date(2024,10,9),  # Independence Day
    Date(2024,12,25), # Christmas
    Date(2024,12,26), # Boxing Day
    # 2025
    Date(2025,1,1),
    Date(2025,1,26),
    Date(2025,3,8),
    Date(2025,4,18),
    Date(2025,4,21),
    Date(2025,5,1),
    Date(2025,6,3),
    Date(2025,6,9),
    Date(2025,10,9),
    Date(2025,12,25),
    Date(2025,12,26),
    # 2026
    Date(2026,1,1),
    Date(2026,1,26),
    Date(2026,3,8),
    Date(2026,4,3),
    Date(2026,4,6),
    Date(2026,5,1),
    Date(2026,6,3),
    Date(2026,6,9),
    Date(2026,10,9),
    Date(2026,12,25),
    Date(2026,12,26),
    # 2027
    Date(2027,1,1),
    Date(2027,1,26),
    Date(2027,3,8),
    Date(2027,3,26),
    Date(2027,3,29),
    Date(2027,5,1),
    Date(2027,6,3),
    Date(2027,6,9),
    Date(2027,10,9),
    Date(2027,12,25),
    Date(2027,12,26),
])

# ── Festivos Zimbabwe 2024–2027 ───────────────────────────────────────────
# Fuente: Public Holidays and Prohibition of Business Act Zimbabwe
const FESTIVOS_ZIMBABWE = Set([
    # 2024
    Date(2024,1,1),   # New Year's Day
    Date(2024,2,21),  # Robert Mugabe National Youth Day
    Date(2024,3,29),  # Good Friday
    Date(2024,4,1),   # Easter Monday
    Date(2024,4,18),  # Independence Day
    Date(2024,4,19),  # Independence Day Holiday
    Date(2024,5,1),   # Workers' Day
    Date(2024,5,25),  # Africa Day
    Date(2024,8,12),  # Heroes' Day (2do lunes agosto)
    Date(2024,8,13),  # Defence Forces Day (martes después de Heroes)
    Date(2024,12,22), # Unity Day
    Date(2024,12,25), # Christmas
    Date(2024,12,26), # Boxing Day
    # 2025
    Date(2025,1,1),
    Date(2025,2,21),
    Date(2025,4,18),  # Good Friday
    Date(2025,4,18),  # Independence Day
    Date(2025,4,21),  # Easter Monday
    Date(2025,5,1),
    Date(2025,5,25),
    Date(2025,8,11),  # Heroes' Day
    Date(2025,8,12),  # Defence Forces Day
    Date(2025,12,22),
    Date(2025,12,25),
    Date(2025,12,26),
    # 2026
    Date(2026,1,1),
    Date(2026,2,21),
    Date(2026,4,3),   # Good Friday
    Date(2026,4,6),   # Easter Monday
    Date(2026,4,18),  # Independence Day
    Date(2026,5,1),
    Date(2026,5,25),
    Date(2026,8,10),  # Heroes' Day
    Date(2026,8,11),  # Defence Forces Day
    Date(2026,12,22),
    Date(2026,12,25),
    Date(2026,12,26),
    # 2027
    Date(2027,1,1),
    Date(2027,2,21),
    Date(2027,3,26),  # Good Friday
    Date(2027,3,29),  # Easter Monday
    Date(2027,4,18),  # Independence Day
    Date(2027,4,19),
    Date(2027,5,1),
    Date(2027,5,25),
    Date(2027,8,9),   # Heroes' Day
    Date(2027,8,10),  # Defence Forces Day
    Date(2027,12,22),
    Date(2027,12,25),
    Date(2027,12,26),
])

# ── Festivos Jamaica 2024–2027 ────────────────────────────────────────────
# Fuente: The Holidays (Public General) Act Jamaica
const FESTIVOS_JAMAICA = Set([
    # 2024
    Date(2024,1,1),   # New Year's Day
    Date(2024,2,15),  # Bob Marley Day (unofficial; algunos empleadores)
    Date(2024,3,29),  # Good Friday
    Date(2024,4,1),   # Easter Monday
    Date(2024,5,23),  # Labour Day
    Date(2024,8,1),   # Emancipation Day
    Date(2024,8,6),   # Independence Day
    Date(2024,10,21), # National Heroes Day (3er lunes octubre)
    Date(2024,12,25), # Christmas Day
    Date(2024,12,26), # Boxing Day
    # 2025
    Date(2025,1,1),
    Date(2025,4,18),  # Good Friday
    Date(2025,4,21),  # Easter Monday
    Date(2025,5,23),  # Labour Day
    Date(2025,8,1),
    Date(2025,8,6),
    Date(2025,10,20), # National Heroes Day
    Date(2025,12,25),
    Date(2025,12,26),
    # 2026
    Date(2026,1,1),
    Date(2026,4,3),   # Good Friday
    Date(2026,4,6),   # Easter Monday
    Date(2026,5,23),
    Date(2026,8,1),
    Date(2026,8,6),
    Date(2026,10,19), # National Heroes Day
    Date(2026,12,25),
    Date(2026,12,26),
    # 2027
    Date(2027,1,1),
    Date(2027,3,26),  # Good Friday
    Date(2027,3,29),  # Easter Monday
    Date(2027,5,23),
    Date(2027,8,1),
    Date(2027,8,6),
    Date(2027,10,18), # National Heroes Day
    Date(2027,12,25),
    Date(2027,12,26),
])

# ── Festivos Bolivia 2024–2027 ────────────────────────────────────────────
# Fuente: Ley Nº 3640 (Feriados Nacionales de Bolivia)
const FESTIVOS_BOLIVIA = Set([
    # 2024  (Easter: Mar 31)
    Date(2024,1,1),   # Año Nuevo
    Date(2024,1,22),  # Día del Estado Plurinacional
    Date(2024,3,29),  # Viernes Santo
    Date(2024,5,1),   # Día del Trabajo
    Date(2024,5,30),  # Corpus Christi
    Date(2024,6,21),  # Año Nuevo Andino Amazónico (Inti Raymi)
    Date(2024,8,2),   # Día de la Revolución Agraria
    Date(2024,8,6),   # Día de la Independencia
    Date(2024,11,2),  # Día de los Difuntos
    Date(2024,12,25), # Navidad
    # 2025  (Easter: Apr 20)
    Date(2025,1,1),
    Date(2025,1,22),
    Date(2025,4,18),  # Viernes Santo
    Date(2025,5,1),
    Date(2025,6,19),  # Corpus Christi
    Date(2025,6,21),
    Date(2025,8,2),
    Date(2025,8,6),
    Date(2025,11,2),
    Date(2025,12,25),
    # 2026  (Easter: Apr 5)
    Date(2026,1,1),
    Date(2026,1,22),
    Date(2026,4,3),   # Viernes Santo
    Date(2026,5,1),
    Date(2026,6,4),   # Corpus Christi
    Date(2026,6,21),
    Date(2026,8,2),
    Date(2026,8,6),
    Date(2026,11,2),
    Date(2026,12,25),
    # 2027  (Easter: Mar 28)
    Date(2027,1,1),
    Date(2027,1,22),
    Date(2027,3,26),  # Viernes Santo
    Date(2027,5,1),
    Date(2027,5,27),  # Corpus Christi
    Date(2027,6,21),
    Date(2027,8,2),
    Date(2027,8,6),
    Date(2027,11,2),
    Date(2027,12,25),
])

# ── Festivos Venezuela 2024–2027 ──────────────────────────────────────────
# Fuente: Ley Orgánica del Trabajo, los Trabajadores y las Trabajadoras
const FESTIVOS_VENEZUELA = Set([
    # 2024  (Easter: Mar 31)
    Date(2024,1,1),   # Año Nuevo
    Date(2024,1,15),  # Natalicio de Simón Bolívar
    Date(2024,3,25),  # Lunes Santo
    Date(2024,3,28),  # Jueves Santo
    Date(2024,3,29),  # Viernes Santo
    Date(2024,4,19),  # Declaración de Independencia
    Date(2024,5,1),   # Día del Trabajador
    Date(2024,6,24),  # Batalla de Carabobo
    Date(2024,7,5),   # Día de la Independencia
    Date(2024,7,24),  # Natalicio de Simón Bolívar
    Date(2024,8,3),   # Bandera Nacional
    Date(2024,10,12), # Día de la Resistencia Indígena
    Date(2024,11,1),  # Todos los Santos
    Date(2024,12,8),  # Inmaculada Concepción
    Date(2024,12,24), # Nochebuena
    Date(2024,12,25), # Navidad
    Date(2024,12,31), # Nochevieja
    # 2025  (Easter: Apr 20)
    Date(2025,1,1),
    Date(2025,4,14),  # Lunes Santo
    Date(2025,4,17),  # Jueves Santo
    Date(2025,4,18),  # Viernes Santo
    Date(2025,4,19),
    Date(2025,5,1),
    Date(2025,6,24),
    Date(2025,7,5),
    Date(2025,7,24),
    Date(2025,10,12),
    Date(2025,11,1),
    Date(2025,12,8),
    Date(2025,12,24),
    Date(2025,12,25),
    Date(2025,12,31),
    # 2026  (Easter: Apr 5)
    Date(2026,1,1),
    Date(2026,3,30),  # Lunes Santo
    Date(2026,4,2),   # Jueves Santo
    Date(2026,4,3),   # Viernes Santo
    Date(2026,4,19),
    Date(2026,5,1),
    Date(2026,6,24),
    Date(2026,7,5),
    Date(2026,7,24),
    Date(2026,10,12),
    Date(2026,11,1),
    Date(2026,12,8),
    Date(2026,12,24),
    Date(2026,12,25),
    Date(2026,12,31),
    # 2027  (Easter: Mar 28)
    Date(2027,1,1),
    Date(2027,3,22),  # Lunes Santo
    Date(2027,3,25),  # Jueves Santo
    Date(2027,3,26),  # Viernes Santo
    Date(2027,4,19),
    Date(2027,5,1),
    Date(2027,6,24),
    Date(2027,7,5),
    Date(2027,7,24),
    Date(2027,10,12),
    Date(2027,11,1),
    Date(2027,12,8),
    Date(2027,12,24),
    Date(2027,12,25),
    Date(2027,12,31),
])
```

---

# PASO 3 — `src/Config.jl`: actualizar `country_festivos`

**Busque** la función `country_festivos` actual:
```julia
function country_festivos(country::Symbol)::Set{Date}
    country == :AR ? FESTIVOS_ARGENTINA   :
    country == :MX ? FESTIVOS_MEXICO      :
    country == :KE ? FESTIVOS_KENIA       :
    country == :PE ? FESTIVOS_PERU        :
    country == :GT ? FESTIVOS_GUATEMALA   :
    country == :IND ? FESTIVOS_INDIA       :
    country == :DOM ? FESTIVOS_DOMINICANA  :
    country == :BR ? FESTIVOS_BRASIL      :
    country == :PH ? FESTIVOS_PHILIPPINES :
    country == :HN ? FESTIVOS_HONDURAS    :
    country == :BZ ? FESTIVOS_BELICE      :
    country == :UY ? FESTIVOS_URUGUAY     :
    country == :SV ? FESTIVOS_EL_SALVADOR :
                    FESTIVOS_COLOMBIA  # default: CO y fallback OTC sin match
end
```

**Reemplácela** por:
```julia
function country_festivos(country::Symbol)::Set{Date}
    country == :AR  ? FESTIVOS_ARGENTINA   :
    country == :MX  ? FESTIVOS_MEXICO      :
    country == :KE  ? FESTIVOS_KENIA       :
    country == :PE  ? FESTIVOS_PERU        :
    country == :GT  ? FESTIVOS_GUATEMALA   :
    country == :IND ? FESTIVOS_INDIA       :
    country == :DOM ? FESTIVOS_DOMINICANA  :
    country == :BR  ? FESTIVOS_BRASIL      :
    country == :PH  ? FESTIVOS_PHILIPPINES :
    country == :HN  ? FESTIVOS_HONDURAS    :
    country == :BZ  ? FESTIVOS_BELICE      :
    country == :UY  ? FESTIVOS_URUGUAY     :
    country == :SV  ? FESTIVOS_EL_SALVADOR :
    country == :US  ? FESTIVOS_EEUU        :
    country == :ZA  ? FESTIVOS_SUDAFRICA   :
    country == :CL  ? FESTIVOS_CHILE       :
    country == :NI  ? FESTIVOS_NICARAGUA   :
    country == :ES  ? FESTIVOS_ESPANA      :
    country == :NG  ? FESTIVOS_NIGERIA     :
    country == :AM  ? FESTIVOS_ARMENIA     :
    country == :GE  ? FESTIVOS_GEORGIA     :
    country == :GH  ? FESTIVOS_GHANA       :
    country == :UG  ? FESTIVOS_UGANDA      :
    country == :ZW  ? FESTIVOS_ZIMBABWE    :
    country == :JM  ? FESTIVOS_JAMAICA     :
    country == :BO  ? FESTIVOS_BOLIVIA     :
    country == :VE  ? FESTIVOS_VENEZUELA   :
                     FESTIVOS_COLOMBIA     # default para CO y cualquier país sin match
end
```

---

# PASO 4 — `src/Config.jl`: actualizar `otc_pais_to_symbol`

**Busque** la función `otc_pais_to_symbol` actual:
```julia
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

**Reemplácela completamente** por esta versión ampliada que cubre **todos** los valores de `VALORES_FORMS_UBICACION_OTC`, incluidos los espacios al final que tiene el Set original:

```julia
function otc_pais_to_symbol(pais::String)::Symbol
    p = strip(pais)   # strip() elimina espacios al inicio y al final

    # Colombia
    p ∈ ("Colombia", "Columbia", "Colmbia", "Col") && return :CO

    # Argentina
    p ∈ ("Argentina", "Buenos Aires", "BUENOS AIRES") && return :AR

    # México
    p ∈ ("México", "Mexico", "MEXICO") && return :MX

    # Kenia / Kenya
    p ∈ ("Kenya", "Kenia", "KENYA", "KENIA", "kenia", "Nairobi") && return :KE

    # Perú
    p ∈ ("Perú", "Peru", "PERU", "PERÚ") && return :PE

    # Guatemala
    p ∈ ("Guatemala", "GUATEMALA", "GUATEMALA ALLIED",
         "Ciudad de guatemala", "Ciudad De Guatemala") && return :GT

    # India
    p ∈ ("India", "INDIA") && return :IND

    # República Dominicana
    p ∈ ("República Dominicana", "Republica Dominicana",
         "Rep Dominicana", "Dominican Republic",
         "RD", "Dom. Rep.", "DOMINICANA") && return :DOM

    # Brasil
    p ∈ ("Brasil", "Brazil", "BRASIL", "BRAZIL") && return :BR

    # Filipinas
    p ∈ ("Filipinas", "Philippines", "Philipines",
         "Filpinas") && return :PH

    # Honduras
    p ∈ ("Honduras", "Remoto en Honduras") && return :HN

    # Belize / Belice
    p ∈ ("Belize", "Belice", "Belize City") && return :BZ

    # Uruguay
    p == "Uruguay" && return :UY

    # El Salvador
    p == "El Salvador" && return :SV

    # Estados Unidos
    p ∈ ("Estados Unidos", "USA", "US", "United States") && return :US

    # Sudáfrica
    p ∈ ("South Africa", "Sur Africa", "Africa",
         "Nairobi") && return :ZA
    # Nota: "Africa" y "Nairobi" se mapean a Sudáfrica como fallback regional.
    # Si su empresa tiene empleados en otros países africanos específicos,
    # cree símbolos adicionales para ellos.

    # Chile
    p == "Chile" && return :CL

    # Nicaragua
    p == "Nicaragua" && return :NI

    # España
    p ∈ ("España", "Espana", "Spain") && return :ES

    # Nigeria
    p ∈ ("Nigeria", "NIGERIA") && return :NG

    # Armenia
    p == "Armenia" && return :AM

    # Georgia
    p == "Georgia" && return :GE

    # Ghana
    p == "Ghana" && return :GH

    # Uganda
    p == "Uganda" && return :UG

    # Zimbabwe
    p == "Zimbabwe" && return :ZW

    # Jamaica
    p == "Jamaica" && return :JM

    # Bolivia
    p == "Bolivia" && return :BO

    # Venezuela
    p == "Venezuela" && return :VE

    @warn "Ubicación OTC no reconocida: '$pais'. Se usarán festivos de Colombia."
    return :CO
end
```

---

# PASO 5 — `src/Config.jl`: actualizar `country_ubicaciones`

**Busque** la función `country_ubicaciones`:
```julia
function country_ubicaciones(country::Symbol)::Set{String}
    # Forms solo aplica a Colombia. Esta función existe por compatibilidad.
    # DataLoader ya guarda que solo llama Forms cuando country == :CO.
    country == :AR  ? VALORES_FORMS_UBICACION_AR :
    country == :MX  ? VALORES_FORMS_UBICACION_MX :
    country == :OTC ? Set{String}() :   # OTC nunca usa Forms
                     VALORES_FORMS_UBICACION_CO
end
```

**Reemplácela** por:
```julia
function country_ubicaciones(country::Symbol)::Set{String}
    country == :AR  ? VALORES_FORMS_UBICACION_AR  :
    country == :MX  ? VALORES_FORMS_UBICACION_MX  :
    country == :OTC ? VALORES_FORMS_UBICACION_OTC :
                     VALORES_FORMS_UBICACION_CO
end
```

---

# PASO 6 — `src/DataLoader.jl`: incluir Forms en OTC

En el PASO anterior de la guía habíamos reemplazado el bloque de Forms para
que solo corriera cuando `country == :CO`. Ahora hay que ampliarlo para que
también corra cuando `country == :OTC`.

**Busque** el bloque que quedó así en `load_all_sources`:
```julia
    println("\n  [2/4] Descargando Novedades.xlsx desde SharePoint...")
    forms_df = DataFrame()   # default vacío para todos los países excepto CO

    if country != :CO
        # Forms (Novedades.xlsx) solo aplica al proceso de Colombia.
        # Para Argentina, México y OTC se omite completamente.
        println("  ℹ Forms SharePoint omitido para $(pais) — solo aplica a Colombia.")
    else
        forms_df_raw = SharePointConnector.fetch_novedades_from_sharepoint()
        if isnothing(forms_df_raw)
            @warn "No se pudo obtener Forms de SharePoint. Se procesará solo Midasoft."
        else
            if "Ubicación" ∈ names(forms_df_raw)
                forms_df = filter(
                    r -> string(coalesce(r[Symbol("Ubicación")], "")) ∈
                         Config.VALORES_FORMS_UBICACION_CO,
                    forms_df_raw
                )
            else
                forms_df = forms_df_raw
            end
            println("  ✓ Forms Colombia: $(nrow(forms_df)) filas válidas.")
        end
    end
```

**Reemplácelo** por:
```julia
    println("\n  [2/4] Descargando Novedades.xlsx desde SharePoint...")
    forms_df = DataFrame()   # default vacío

    if country ∉ (:CO, :OTC)
        # Forms solo aplica a Colombia y OTC.
        println("  ℹ Forms SharePoint omitido para $(pais) — solo aplica a CO y OTC.")
    else
        forms_df_raw = SharePointConnector.fetch_novedades_from_sharepoint()
        if isnothing(forms_df_raw)
            @warn "No se pudo obtener Forms de SharePoint. Se procesará solo Midasoft/LeadersAPP."
        else
            ubicaciones_pais = Config.country_ubicaciones(country)
            if "Ubicación" ∈ names(forms_df_raw)
                forms_df = filter(
                    r -> string(coalesce(r[Symbol("Ubicación")], "")) ∈ ubicaciones_pais,
                    forms_df_raw
                )
                println("  ✓ Forms $(pais): $(nrow(forms_df)) filas con Ubicación válida.")
            else
                # Sin columna Ubicación: Colombia toma todo, OTC no toma nada
                if country == :CO
                    forms_df = forms_df_raw
                    println("  ✓ Forms Colombia (sin col. Ubicación): $(nrow(forms_df)) filas.")
                else
                    @warn "Forms no tiene columna 'Ubicación'. No se puede filtrar para OTC."
                end
            end
        end
    end
```

---

# PASO 7 — `src/DataLoader.jl`: asignar `_country` correcto a las filas de Forms OTC

Cuando Forms se procesa para OTC, cada fila tiene una "Ubicación" (texto del
país) que debe convertirse al símbolo de país correcto para que el `Validator`
use los festivos adecuados.

**Busque** la función `build_forms_table`:
```julia
function build_forms_table(forms_df::DataFrame)::DataFrame
    isempty(forms_df) && return DataFrame()
    expanded = expand_rows(forms_df, :forms)
    sort!(expanded, :Fecha_Salida)
    println("   Nov Forms: $(nrow(expanded)) filas expandidas.")
    return expanded
end
```

**Reemplácela** por:
```julia
function build_forms_table(forms_df::DataFrame, country::Symbol = :CO)::DataFrame
    isempty(forms_df) && return DataFrame()
    expanded = expand_rows(forms_df, :forms)

    # Para OTC: asignar _country por fila según la columna Ubicación
    if country == :OTC && "_country" ∉ names(expanded)
        if "Ubicación" ∈ names(expanded)
            expanded[!, :_country] = [
                string(Config.otc_pais_to_symbol(
                    string(coalesce(r[Symbol("Ubicación")], ""))
                ))
                for r in eachrow(expanded)
            ]
        else
            expanded[!, :_country] .= "CO"  # fallback
        end
    elseif "_country" ∉ names(expanded)
        # Para Colombia: todos son :CO
        expanded[!, :_country] .= string(country)
    end

    sort!(expanded, :Fecha_Salida)
    println("   Nov Forms $(country): $(nrow(expanded)) filas expandidas.")
    return expanded
end
```

Luego, **busque** la línea donde se llama a `build_forms_table`:
```julia
    forms_expanded    = isempty(forms_df) ? DataFrame() :
                        build_forms_table(forms_df)
```

**Reemplácela** por (pasa `country` a la función):
```julia
    forms_expanded    = isempty(forms_df) ? DataFrame() :
                        build_forms_table(forms_df, country)
```

---

# VERIFICACIÓN FINAL

**`src/Config.jl`** — verifique que existan:
- [ ] `VALORES_FORMS_UBICACION_OTC` con los valores del Set dado
- [ ] `FESTIVOS_EEUU`, `FESTIVOS_SUDAFRICA`, `FESTIVOS_CHILE`, `FESTIVOS_NICARAGUA`
- [ ] `FESTIVOS_ESPANA`, `FESTIVOS_NIGERIA`, `FESTIVOS_ARMENIA`, `FESTIVOS_GEORGIA`
- [ ] `FESTIVOS_GHANA`, `FESTIVOS_UGANDA`, `FESTIVOS_ZIMBABWE`, `FESTIVOS_JAMAICA`
- [ ] `FESTIVOS_BOLIVIA`, `FESTIVOS_VENEZUELA`
- [ ] `country_festivos` tiene los 14 nuevos símbolos: `:US`, `:ZA`, `:CL`, `:NI`, `:ES`, `:NG`, `:AM`, `:GE`, `:GH`, `:UG`, `:ZW`, `:JM`, `:BO`, `:VE`
- [ ] `otc_pais_to_symbol` cubre todos los valores de `VALORES_FORMS_UBICACION_OTC`
- [ ] `country_ubicaciones(:OTC)` devuelve `VALORES_FORMS_UBICACION_OTC`

**`src/DataLoader.jl`** — verifique:
- [ ] El bloque de Forms descarga cuando `country ∈ (:CO, :OTC)`
- [ ] Filtra con `Config.country_ubicaciones(country)` en ambos casos
- [ ] `build_forms_table` acepta el parámetro `country`
- [ ] Las filas OTC de Forms reciben `_country` según `otc_pais_to_symbol`
- [ ] La llamada a `build_forms_table` pasa `country`

---

## Resultado final por proceso

| Proceso | Fuente Midasoft/LeadersAPP | Fuente Forms SharePoint |
|---------|---------------------------|------------------------|
| `:CO` Colombia | ✅ tablas midasoft | ✅ filtrado por `VALORES_FORMS_UBICACION_CO` |
| `:AR` Argentina | ✅ tablas midasoft AR | ⏭ omitido |
| `:MX` México | ✅ tablas midasoft MX | ⏭ omitido |
| `:OTC` Others | ✅ tabla Leaders APP | ✅ filtrado por `VALORES_FORMS_UBICACION_OTC` |

*Guía generada para PTO Novedades v4.0*
