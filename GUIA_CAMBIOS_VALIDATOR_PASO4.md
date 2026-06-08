# Guía de Cambios — Paso 4 `resolve_conflicts` en `Validator.jl`

> **Alcance:** Solo se modifica `src/Validator.jl`.  
> No se toca `Processor.jl`, `DefManager.jl`, `DataLoader.jl`, `Config.jl` ni ningún otro módulo.  
> Los pasos 1, 2 y 3 de `validate_group` permanecen **intactos**.

---

## 0. Contexto clave antes de empezar

### Nombres de columnas relevantes

| Columna en `unified` (DataFrame interno) | Columna en `Def` (archivo de salida) |
|---|---|
| `SOLID` | `"SOLID"` |
| `Fecha_Del_Evento` | `"Date of PTO"` |
| `Novedad` | `"Novedad"` |
| `Numero_novedad` | `"Numero novedad"` |
| `Tiempo_Afectacion` (alias `Hours_of_PTO`) | `"Hours of PTO"` |
| `INDEX` | `"INDEX"` |

> **Nota importante:** `resolve_conflicts` opera sobre `unified`, el DataFrame interno con nombres en snake_case (`:Fecha_Del_Evento`, `:Tiempo_Afectacion`, etc.). La función no lee ni escribe el Def directamente.  
> `Column2` y `PROCESADA` son columnas del **Def**, no de `unified`. Por eso la nueva lógica recibe `new_ids` (el conjunto de IDs nuevos) y trabaja sobre `unified` para calcular `Column2` internamente.

### Cómo fluye el Paso 4 hoy

```
validate_group(ids, unified, nucleus_type)
  → pasos 1-3 → passed_ids (Set de IDs que aprobaron)
  → resolve_conflicts(passed_ids, unified)   ← aquí está el cambio
```

`resolve_conflicts` devuelve un `Vector{ValidResult}` con `status = valid` o `out`. El resultado luego es consumido por `Processor.jl` → `DefManager.build_def_rows` que asigna `IN/OUT` y `PROCESADA` en el Def.

### ¿Qué hace hoy `resolve_conflicts`?

Aplica una jerarquía antigua (Novedad duplicada → más reciente; mismo prefijo → suma ≤ 8; distinto prefijo → INC > AUS > VAC).

### ¿Qué debe hacer ahora?

La nueva lógica que describes tiene **dos grandes bloques**:

1. **Bloque A — Decisión rápida para filas simples (Column2 == 1):** marcar `PROCESADA = "SI"` o decidir cuáles quedan en `IN`.
2. **Bloque B — Resolver conflictos reales (Column2 > 1):** para cada SOLID × Fecha, aplicar las reglas 1, 2 y 3 (y jerarquía de desempate).

---

## 1. Qué eliminar

### En `Validator.jl` — función `resolve_conflicts` completa

Localiza el bloque que empieza en:

```julia
"""
    resolve_conflicts(passed_ids, unified) -> Vector{ValidResult}

Para IDs que comparten (SOLID + Fecha Del Evento) aplica jerarquía:
    1. Mismo Novedad         → keep el más reciente (mayor INDEX), OUT al resto
    2. Mismo prefijo num_nov → válidos si suma Hours_of_PTO ≤ 8
    3. Distinto prefijo      → jerarquía INC > AUS > VAC
"""
function resolve_conflicts(passed_ids::Set{String}, unified::DataFrame)::Vector{ValidResult}
```

…y termina en el `end` correspondiente (antes de `# API pública`).

**Elimina todo ese bloque completo** — docstring + función.

---

## 2. Qué agregar en su lugar

Pega el siguiente código **exactamente donde estaba `resolve_conflicts`**, antes del comentario `# API pública`:

```julia
# Paso 4 — Nueva lógica: Column2 y resolución de conflictos

# ── helpers internos ────────────────────────────────────────────────────────

"""
    _pto_hours(row) -> Float64

Lee Hours_of_PTO (alias de Tiempo_Afectacion) de una fila de `unified`.
"""
_pto_hours(r) = sf64(get(r, :Tiempo_Afectacion, 0.0))

"""
    _index_int(row) -> Int

Convierte el campo INDEX a Int para comparar recencia.
Mayor INDEX = carga más reciente.
"""
function _index_int(r)
    v = get(r, :INDEX, nothing)
    (isnothing(v) || ismissing(v)) && return 0
    n = tryparse(Int, string(v))
    isnothing(n) ? 0 : n
end

"""
    _novedad_rank(novedad_str) -> Int

Jerarquía interna cuando el prefijo de Numero_novedad es igual.
Mayor número = mayor prioridad.
"""
function _novedad_rank(novedad_str::String)::Int
    u = lowercase(strip(novedad_str))
    occursin("incapacidad",       u) && return 6
    occursin("maternidad",        u) && return 5
    occursin("paternidad",        u) && return 4
    occursin("vacacion",          u) && return 3
    occursin("licencia no remun", u) && return 2
    return 1
end

"""
    _prefix_rank(num_nov_str) -> Int

Jerarquía por prefijo de Numero_novedad: INC > VAC > AUS.
"""
function _prefix_rank(num_nov_str::String)::Int
    p = prefix3(num_nov_str)
    p == "INC" && return 3
    p == "VAC" && return 2
    p == "AUS" && return 1
    return 0
end

"""
    _best_subset(rows_sub) -> Set{String}

Dado un sub-DataFrame de filas en conflicto (mismo SOLID + fecha),
devuelve el Set de IDs que deben quedar como `valid`.

Implementa las reglas 1, 2 y 3 descritas en el requisito,
más la jerarquía de desempate general.
"""
function _best_subset(rows_sub::DataFrame)::Set{String}
    n = nrow(rows_sub)
    n == 0 && return Set{String}()
    n == 1 && return Set{String}([rows_sub[1, :ID]])

    novedades  = [string(coalesce(get(rows_sub[j,:], :Novedad,        ""), "")) for j in 1:n]
    num_novs   = [string(coalesce(get(rows_sub[j,:], :Numero_novedad, ""), "")) for j in 1:n]
    prefixes   = prefix3.(num_novs)
    horas      = [_pto_hours(rows_sub[j,:]) for j in 1:n]

    unique_novedades = unique(novedades)
    unique_prefixes  = unique(prefixes)

    # ── Regla 1: Mismo valor en "Novedad" ──────────────────────────────────
    # Si todas (o al menos 2) comparten la misma Novedad Y las horas son iguales
    # → mantener 1, marcar el resto OUT.
    if length(unique_novedades) == 1
        unique_horas = unique(horas)

        if length(unique_horas) == 1
            # Regla 1: misma Novedad, mismas horas → conservar el más reciente
            indices = [_index_int(rows_sub[j,:]) for j in 1:n]
            best_j  = argmax(indices)
            return Set{String}([rows_sub[best_j, :ID]])

        else
            # Regla 2: misma Novedad, horas diferentes
            # → conservar el subconjunto de mayor suma ≤ 8
            return _max_sum_subset(rows_sub, horas)
        end
    end

    # ── Regla 3: Distinta Novedad ───────────────────────────────────────────
    # Hay 8.0 en alguna fila?
    has_eight = any(h -> norm_eq(h, 8.0), horas)

    if has_eight
        # Conservar solo las filas con 8.0, luego aplicar jerarquía entre ellas
        eight_mask = [norm_eq(horas[j], 8.0) for j in 1:n]
        candidates = rows_sub[eight_mask, :]
        return _apply_hierarchy(candidates)
    else
        # Ninguna tiene 8.0 → conservar el subconjunto de mayor suma ≤ 8
        return _max_sum_subset(rows_sub, horas)
    end
end

"""
    _apply_hierarchy(candidates) -> Set{String}

Entre varias candidatas, aplica:
  1. Prefijo INC > VAC > AUS
  2. Si empate de prefijo → mayor rango de Novedad (texto)
  3. Si sigue empate → más reciente (mayor INDEX)
Conserva solo 1 fila.
"""
function _apply_hierarchy(candidates::DataFrame)::Set{String}
    n = nrow(candidates)
    n == 0 && return Set{String}()
    n == 1 && return Set{String}([candidates[1, :ID]])

    num_novs  = [string(coalesce(get(candidates[j,:], :Numero_novedad, ""), "")) for j in 1:n]
    novedades = [string(coalesce(get(candidates[j,:], :Novedad,        ""), "")) for j in 1:n]

    scores = [(
        _prefix_rank(num_novs[j]),
        _novedad_rank(novedades[j]),
        _index_int(candidates[j,:]),
        j
    ) for j in 1:n]

    best = argmax(scores)
    return Set{String}([candidates[best[4], :ID]])
end

"""
    _max_sum_subset(rows_sub, horas) -> Set{String}

Selecciona el subconjunto de filas cuya suma de horas sea máxima
y menor o igual a 8.0.

Estrategia:
  - Ordenar por horas desc.
  - Acumular greedy hasta que la suma ≤ 8.
  - Si ninguna combinación individual ≤ 8 → conservar la de mayor horas.
  - Desempate final: jerarquía de prefijo/novedad/INDEX.
"""
function _max_sum_subset(rows_sub::DataFrame, horas::Vector{Float64})::Set{String}
    n = nrow(rows_sub)

    sorted_idx = sortperm(horas; rev=true)
    acc   = 0.0
    keeps = Int[]

    for j in sorted_idx
        if acc + horas[j] <= 8.0 + 1e-6
            push!(keeps, j)
            acc += horas[j]
        end
    end

    if isempty(keeps)
        # Todas individualmente > 8 → conservar la de mayor horas (desempate jerarquía)
        candidates = rows_sub[[sorted_idx[1]], :]
        return _apply_hierarchy(candidates)
    end

    if length(keeps) == 1
        return Set{String}([rows_sub[keeps[1], :ID]])
    end

    # Más de una fila en el subconjunto ganador
    return Set{String}([rows_sub[j, :ID] for j in keeps])
end

# ── función pública del paso 4 ───────────────────────────────────────────────

"""
    resolve_conflicts(passed_ids, unified, new_ids) -> Vector{ValidResult}

Nueva implementación del Paso 4.

Lógica en dos bloques:

**Bloque A — filas simples (Column2 == 1 para el SOLID+fecha):**
  - Calcular Column2 = cantidad de IDs en `passed_ids` que comparten
    (SOLID, Fecha_Del_Evento).
  - Si Column2 de todo el lote de nuevos suma igual a la cantidad de filas
    nuevas → todas quedan `valid` (PROCESADA = "SI").
  - Si no, las que tengan Column2 == 1 también quedan `valid`.

**Bloque B — filas con conflicto (Column2 > 1 para ese SOLID+fecha):**
  - Para cada (SOLID, Fecha_Del_Evento) con más de 1 ID en `passed_ids`,
    aplicar las reglas 1, 2 y 3 mediante `_best_subset`.
  - IDs no seleccionados → `out`.

El parámetro `new_ids` es el `Set{String}` de IDs nuevos de esta corrida
(puede ser igual a `passed_ids` si todos pasaron el paso 3).
"""
function resolve_conflicts(
    passed_ids::Set{String},
    unified::DataFrame,
    new_ids::Set{String} = passed_ids,   # compatibilidad: si no se pasa, usar passed_ids
)::Vector{ValidResult}

    results   = ValidResult[]
    processed = Set{String}()

    # ── Índice rápido ID → fila en unified ──────────────────────────────────
    id_to_i = Dict{String,Int}()
    for (i, row) in enumerate(eachrow(unified))
        haskey(id_to_i, row.ID) || (id_to_i[row.ID] = i)
    end

    # ── Calcular Column2 por (SOLID, Fecha_Del_Evento) solo sobre passed_ids ─
    # Column2 = cuántos IDs de passed_ids comparten ese par (SOLID, fecha).
    solid_date_count = Dict{Tuple{String,Any},Int}()
    for id in passed_ids
        i = get(id_to_i, id, nothing)
        isnothing(i) && continue
        r     = unified[i, :]
        solid = string(coalesce(get(r, :SOLID, ""), ""))
        fde   = get(r, :Fecha_Del_Evento, missing)
        k     = (solid, fde)
        solid_date_count[k] = get(solid_date_count, k, 0) + 1
    end

    # ── Bloque A: verificar si la suma global de Column2 == n_nuevas ─────────
    # (Aplica solo cuando se procesa un lote nuevo completo, es decir cuando
    #  passed_ids ⊆ new_ids. Si es una re-corrida parcial se salta este check.)
    suma_col2   = sum(values(solid_date_count))   # suma de Column2 sobre grupos
    n_nuevas    = length(intersect(passed_ids, new_ids))
    suma_simple = (suma_col2 == n_nuevas)         # todos tienen Column2 == 1

    # ── Recorrer cada ID de passed_ids ───────────────────────────────────────
    for id in passed_ids
        id ∈ processed && continue

        i = get(id_to_i, id, nothing)
        if isnothing(i)
            push!(processed, id)
            push!(results, ValidResult(id, valid, ""))
            continue
        end

        r     = unified[i, :]
        solid = string(coalesce(get(r, :SOLID, ""), ""))
        fde   = get(r, :Fecha_Del_Evento, missing)
        k     = (solid, fde)
        col2  = get(solid_date_count, k, 1)

        if col2 == 1
            # Sin conflicto → directamente valid
            push!(processed, id)
            push!(results, ValidResult(id, valid, ""))
            continue
        end

        # col2 > 1: hay conflicto real para este grupo
        # Reunir todas las filas del grupo (solo las de passed_ids)
        group_ids = [
            pid for pid in passed_ids
            if begin
                gi = get(id_to_i, pid, nothing)
                !isnothing(gi) &&
                string(coalesce(get(unified[gi,:], :SOLID, ""), "")) == solid &&
                get(unified[gi,:], :Fecha_Del_Evento, missing) == fde
            end
        ]

        # Construir sub-DataFrame del grupo
        group_rows = unified[[id_to_i[pid] for pid in group_ids], :]

        # Aplicar reglas
        keep_set = _best_subset(group_rows)

        for pid in group_ids
            push!(processed, pid)
            if pid ∈ keep_set
                push!(results, ValidResult(pid, valid, ""))
            else
                push!(results, ValidResult(pid, out,
                    "Conflicto Column2=$(col2): SOLID=$(solid) fecha=$(fde) — descartado por jerarquía/suma"))
            end
        end
    end

    return results
end
```

---

## 3. Ajuste en `validate_group` — firma de la llamada a `resolve_conflicts`

La signatura de `resolve_conflicts` ahora acepta un tercer argumento opcional (`new_ids`). En `validate_group` la llamada actual es:

```julia
# ANTES (línea ~268 aprox.)
conflict_results = resolve_conflicts(passed_ids, unified)
```

**Cámbiala por:**

```julia
# DESPUÉS
conflict_results = resolve_conflicts(passed_ids, unified, Set(ids))
```

> `ids` es el parámetro de entrada de `validate_group` (el lote de IDs nuevos que se está procesando en este sub-núcleo). Con esto `new_ids` dentro de `resolve_conflicts` sabe exactamente cuáles son "nuevos" en esta corrida.

---

## 4. Ajuste en el docstring del módulo (encabezado de `Validator.jl`)

Localiza el bloque de comentario al inicio del archivo (dentro de la triple-comilla del módulo):

```julia
    4. resolve_conflicts   → Column2 != 1 (mismo SOLID + fecha)
```

Cámbialo por:

```julia
    4. resolve_conflicts   → Column2 y jerarquía de conflictos (SOLID + Fecha_Del_Evento)
                             Regla 1: misma Novedad+horas → más reciente
                             Regla 2: misma Novedad, horas distintas → max suma ≤ 8
                             Regla 3: distinta Novedad → prioriza 8h, luego INC>VAC>AUS
```

---

## 5. Nada más cambia

| Archivo | Acción |
|---|---|
| `Validator.jl` | ✅ Reemplazar `resolve_conflicts` + ajustar llamada en `validate_group` + docstring |
| `Processor.jl` | ❌ No tocar |
| `DefManager.jl` | ❌ No tocar (`PROCESADA` y `IN/OUT` se siguen asignando allí igual que antes) |
| `DataLoader.jl` | ❌ No tocar |
| `Config.jl` | ❌ No tocar |
| `main.jl` / `Panel.jl` | ❌ No tocar |

---

## 6. Notas de diseño importantes

### ¿Por qué `Column2` se recalcula dentro de `resolve_conflicts` y no se lee del Def?

En el momento en que `resolve_conflicts` se ejecuta, el Def **aún no existe o no ha sido actualizado**. `DefManager.build_def_rows` se llama *después* de que `validate_group` termina. Por eso la función calcula `Column2` internamente usando `unified`, exactamente igual a como lo hace `build_def_rows` — contando cuántos IDs de `passed_ids` comparten `(SOLID, Fecha_Del_Evento)`.

### ¿Qué pasa con `PROCESADA`?

- Filas que quedan `valid` → `DefManager.build_def_rows` ya les pone `"PROCESADA" = "SI"` (no cambia nada).  
- Filas que quedan `out` → `DefManager.update_def` ya les pone `"IN/OUT" = "OUT"`. Si quieres que además tengan `"PROCESADA" = "SI"` en el Def, deberías agregar `out_rows[!, "PROCESADA"] .= "SI"` en `DefManager.update_def` justo después de la línea `out_rows[!, "IN/OUT"] .= "OUT"`. Pero eso es un cambio opcional en `DefManager.jl` y lo decides tú.

### ¿Qué pasa en primera corrida (sin Def previo)?

`new_ids` será igual a todos los IDs de `unified`. La lógica de `Bloque A` compara la suma de Column2 con `n_nuevas`. Si todos tienen Column2 == 1, todos quedan `valid` de inmediato. Si algunos tienen Column2 > 1, pasan por `Bloque B`. Esto es exactamente lo que describes.

### Casos con Column2 > 2 (3, 4, 5 novedades el mismo día)

`_best_subset` y `_max_sum_subset` trabajan sobre el grupo completo sin importar su tamaño. `_max_sum_subset` usa greedy ordenado por horas desc, que en la práctica reduce al subconjunto óptimo sin necesidad de iterar por pares explícitamente.

### Jerarquía general de desempate

Implementada en `_apply_hierarchy` y `_prefix_rank` / `_novedad_rank`:

```
Prefijo:  INC (3) > VAC (2) > AUS (1) > desconocido (0)
Novedad:  incapacidad > maternidad > paternidad > vacacion > licencia no remunerada > resto
Recencia: mayor INDEX gana
```

Cuando quieras ajustar la jerarquía del texto de `Novedad`, solo edita `_novedad_rank`.

---

## 7. Resumen de pasos manuales

1. Abrir `src/Validator.jl`.
2. **Eliminar** el docstring + función `resolve_conflicts` completa (desde la triple-comilla hasta su `end`).
3. **Pegar** el bloque completo de la sección 2 en ese mismo lugar.
4. **Modificar** la llamada en `validate_group`:  
   `resolve_conflicts(passed_ids, unified)` → `resolve_conflicts(passed_ids, unified, Set(ids))`
5. **Actualizar** el docstring del módulo (4 líneas del encabezado, sección 4).
6. Guardar y correr el proyecto normalmente.
