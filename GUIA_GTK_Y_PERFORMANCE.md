# Guía de Cambios — GTK Panel + Optimización de Rendimiento

> **Archivos que se modifican:** `src/Panel.jl`, `src/Processor.jl`, `src/Validator.jl`, `src/Config.jl`  
> Todo lo demás queda intacto.

---

## PARTE 1 — Panel GTK: diagnóstico y corrección

### ¿Por qué no abre el panel GTK?

Hay **tres bugs independientes** que actúan en cadena:

#### Bug 1 — `gtk_available()` falla silenciosamente aunque GTK esté instalado

El código actual hace esto:
```julia
Base.require(Main, :Gtk)      # ← lanza excepción si Gtk no está pre-cargado con `using`
```
`Base.require` **no carga** el paquete, solo verifica si ya está en el módulo `Main`. Como `main.jl` nunca hace `using Gtk` antes de llamar a `run_panel`, esto siempre lanza una excepción que el `try/catch` atrapa silenciosamente → devuelve `false` → va al fallback.

#### Bug 2 — El `take!(done_ch)` bloquea el event loop de GTK

GTK en Julia necesita que su event loop (`GLib.g_main_context_iteration`) se ejecute para procesar eventos (clics, refresco del timer, etc.). `take!(done_ch)` es un bloqueo de Julia que **congela el hilo** del event loop de GTK. El timer de 150 ms nunca dispara, los botones nunca responden, la ventana se cuelga inmediatamente.

La solución correcta es usar `Gtk.gtk_main()` como bloqueador principal e interactuar con el event loop via `GLib`.

#### Bug 3 — `_ensure_gtk()` usa `@eval Main using Gtk` que es problemático en módulos

Cargar paquetes con `@eval Main using Gtk` dentro de un módulo puede causar que los símbolos de Gtk (`GtkWindow`, `GtkLabel`, etc.) no estén disponibles en el scope de `Panel`. La forma correcta en Julia es declarar el `using` al inicio del módulo, condicionalmente.

---

### Solución completa para `src/Panel.jl`

#### Paso 1.1 — Reemplazar el bloque de carga condicional de GTK al inicio del módulo

Localiza y **elimina** estas líneas (están después de `module Panel` y los `using`):

```julia
# GTK (cargado condicionalmente - solo se usa si gtk_available() retorna true)
const _GTK_LOADED = Ref{Bool}(false)
function _ensure_gtk()
    if !_GTK_LOADED[]
        @eval Main using Gtk
        _GTK_LOADED[] = true
    end
end
```

**Reemplázalas por:**

```julia
# GTK — cargado al inicio del módulo.
# Si no está instalado o no hay display, gtk_available() lo detecta y usa el fallback.
const _GTK_OK = Ref{Bool}(false)
try
    @eval using Gtk
    _GTK_OK[] = true
catch
    _GTK_OK[] = false
end
```

> **Por qué funciona:** `@eval using Gtk` al nivel del módulo (no dentro de una función) pone todos los símbolos de Gtk en el scope de `Panel`. El `try/catch` captura el caso donde Gtk no esté instalado o no compiles, sin romper nada.

---

#### Paso 1.2 — Reemplazar `gtk_available()` completa

Localiza y **elimina** toda esta función:

```julia
function gtk_available()::Bool
    try
        # Verificar que Gtk está cargado y que hay display disponible
        Base.require(Main, :Gtk)
        # En sistemas din display (CI, SSH sin X), Gtk carga pero falla al crear ventanas
        get(ENV, "DISPLAY", "") == "" &&
        get(ENV, "WAYLAND_DISPLAY", "") == "" &&
        Sys.islinux() && return false
        return true
    catch
        return false
    end
end
```

**Reemplázala por:**

```julia
function gtk_available()::Bool
    _GTK_OK[] || return false
    # En Linux sin display (CI, SSH sin X11), Gtk carga pero no puede crear ventanas
    if Sys.islinux()
        has_display = !isempty(get(ENV, "DISPLAY", "")) ||
                      !isempty(get(ENV, "WAYLAND_DISPLAY", ""))
        has_display || return false
    end
    # Prueba real: intentar crear un widget mínimo
    try
        w = GtkWindow("_test_", 1, 1)
        destroy(w)
        return true
    catch
        return false
    end
end
```

> **Por qué funciona:** En lugar de confiar en `Base.require` (que no carga nada), se intenta crear una ventana real. Si GTK está correctamente instalado con display disponible, esto pasa en ~1ms. Si falla por cualquier motivo (driver, Wayland quirk, headless) cae al fallback sin romper el proceso.

---

#### Paso 1.3 — Corregir `run_gtk_panel`: reemplazar `take!(done_ch)` por el event loop correcto de GTK

Esta es la corrección más crítica.

Localiza en `run_gtk_panel` la línea que dice `_ensure_gtk()` al inicio y **elimínala** (ya no existe esa función).

Luego localiza el **bloque final** de `run_gtk_panel` (las últimas ~5 líneas antes del `end`):

```julia
    # Bloquear hasta que el usuario decida
    result = take!(done_ch)
    destroy(win)
    return result
end
```

**Reemplaza ese bloque por:**

```julia
    # Bloquear usando el event loop de GTK correctamente.
    # gtk_main() procesa eventos GTK (clics, timer, refresco) sin bloquear Julia.
    # Cuando el usuario hace clic en un botón, la señal pone en done_ch y llama
    # a Gtk.gtk_main_quit() para salir del loop.
    signal_connect(btn_ok, :clicked) do _
        result_holder[] = true
        Gtk.gtk_main_quit()
    end
    signal_connect(btn_no, :clicked) do _
        result_holder[] = false
        Gtk.gtk_main_quit()
    end
    signal_connect(win, :destroy) do _
        result_holder[] = false
        Gtk.gtk_main_quit()
    end

    Gtk.gtk_main()   # ← event loop correcto; libera el hilo cuando gtk_main_quit() es llamado
    destroy(win)
    return result_holder[]
end
```

> **IMPORTANTE:** Las señales de `btn_ok`, `btn_no` y `win` destroy ya estaban conectadas más arriba en la función. Debes **eliminar las conexiones viejas** (las que usan `done_ch`) y dejar solo las nuevas. Las viejas se ven así:
> ```julia
> signal_connect(btn_ok, :clicked) do _
>     result_holder[] = true
>     isopen(done_ch) && put!(done_ch, true)
> end
> signal_connect(btn_no, :clicked) do _
>     result_holder[] = false
>     isopen(done_ch) && put!(done_ch, false)
> end
> signal_connect(win, :destroy) do _
>     isopen(done_ch) && put!(done_ch, false)
> end
> ```
> **Elimínalas completamente** y en su lugar pon solo el nuevo bloque del Paso 1.3 al final.

También **elimina** estas dos líneas que declaran `done_ch` y `result_holder` (ya no se necesita `done_ch`):

```julia
    done_ch       = Channel{Bool}(1)
    result_holder = Ref{Bool}(true)
```

Deja solo:
```julia
    result_holder = Ref{Bool}(true)
```

---

#### Paso 1.4 — Limpiar el timer: el `isopen(done_ch)` ya no existe

En el callback del timer (`GLib.g_timeout_add(150) do`), hay esta línea al inicio:

```julia
        isopen(done_ch) || return false
```

**Elimínala.** El timer ahora vive hasta que devuelve `false` (cuando el proceso termina).

---

#### Paso 1.5 — Eliminar `done_ch` del bloque de señales del timer de finalización

Dentro del `if state.finished` del timer, hay esta parte del código viejo que usa `done_ch`. Ya no hace nada. Solo asegúrate de que el bloque de finalización del timer se vea así (sin ninguna referencia a `done_ch`):

```julia
        if state.finished
            GAccessor.label(status_g,
                "✅  COMPLETADO — Válidas: $(length(state.valid_ids))   " *
                "Rechazadas: $(length(state.out_ids))")
            ctx = GtkStyleContext(status_g)
            Gtk.remove!(ctx, "status-processing")
            push!(ctx, "status-done")
            set_gtk_property!(btn_ok, :sensitive, true)
            set_gtk_property!(btn_no, :sensitive, true)
            return false   # detener timer
        end
```

---

#### Paso 1.6 — Corregir `push!(GtkStyleContext(screen), provider, 600)`

Esta llamada tiene la API incorrecta en Gtk.jl v1. Localiza esta línea:

```julia
    push!(GtkStyleContext(screen), provider, 600)
```

**Reemplázala por:**

```julia
    Gtk.GAccessor.add_provider_for_screen(screen, provider, 600)
```

> En Gtk.jl 1.x el método correcto para añadir un CSS provider al screen es `add_provider_for_screen`.

---

### Resumen de cambios en `Panel.jl` — solo Problema 1

| # | Qué | Acción |
|---|-----|--------|
| 1.1 | Bloque `_GTK_LOADED` + `_ensure_gtk()` | Eliminar y reemplazar por `const _GTK_OK` con `@eval using Gtk` |
| 1.2 | Función `gtk_available()` | Eliminar y reemplazar por versión con prueba real de ventana |
| 1.3 | `done_ch`, señales viejas, `take!(done_ch)` | Eliminar `done_ch`; reemplazar señales; usar `Gtk.gtk_main()` |
| 1.4 | `isopen(done_ch)` al inicio del timer | Eliminar esa línea |
| 1.5 | Bloque `if state.finished` del timer | Quitar cualquier referencia residual a `done_ch` |
| 1.6 | `push!(GtkStyleContext(screen), provider, 600)` | Reemplazar por `Gtk.GAccessor.add_provider_for_screen(...)` |

---

## PARTE 2 — Optimización de rendimiento

### Diagnóstico: ¿por qué tarda ~1 hora sin Def?

Hay **cuatro cuellos de botella** identificados:

#### Cuello 1 — `@async` no es paralelismo real en Julia

`@async` en Julia crea una *coroutine cooperativa* en un solo hilo. Los tres núcleos (VAC, INC, AUS) en `process_all!` se lanzan con `@async` pero se ejecutan **uno a la vez**, cooperando solo en los `yield()`. No hay paralelismo real. Para paralelismo real en Julia se necesita `Threads.@spawn`.

#### Cuello 2 — `filter(r -> r.X == val, df)` dentro de loops es O(n²)

En `validate_vac`, `validate_inc` y `resolve_conflicts` hay llamadas como:
```julia
sub = filter(r -> r.Numero_novedad == num_nov, rows)
```
Esto itera el DataFrame completo por cada `num_nov` único. Con miles de filas y docenas de novedades, esto es cuadrático. La solución es un índice con `groupby` previo.

#### Cuello 3 — `filter(r -> r.ID ∈ id_set, unified)` en `validate_group` escanea `unified` completo por cada sub-núcleo

`unified` puede tener decenas de miles de filas. Cada sub-núcleo de 200 IDs hace este filtro completo. Con 30 sub-núcleos son 30 escaneos completos.

#### Cuello 4 — `SUBCORE_SIZE = 200` produce demasiados sub-núcleos

Con 5000 novedades nuevas y `SUBCORE_SIZE = 200` se crean 25 sub-núcleos solo para VAC. Cada sub-núcleo tiene overhead de channel puts, estado, etc. Con `@async` cooperativo, estos sub-núcleos no corren en paralelo de todas formas.

---

### Cambios de rendimiento

#### Cambio 2.1 — `src/Config.jl`: ajustar `SUBCORE_SIZE`

Localiza:
```julia
const SUBCORE_SIZE  = 200
```

**Reemplaza por:**
```julia
const SUBCORE_SIZE  = 500
```

> Con sub-núcleos más grandes hay menos overhead de canal y de scheduling cooperativo. El panel sigue mostrando progreso, solo con menos granularidad (que es perfectamente aceptable).

---

#### Cambio 2.2 — `src/Processor.jl`: usar `Threads.@spawn` en lugar de `@async`

Esto es el cambio más impactante. Los tres núcleos pasan a correr en paralelo real si Julia tiene múltiples threads.

> **Prerequisito:** Julia debe lanzarse con múltiples threads:
> ```
> julia --threads auto main.jl
> ```
> O establecer la variable de entorno: `JULIA_NUM_THREADS=auto`  
> Añade esta línea al archivo `.bat` o script con el que ejecutas el proyecto.

**En `process_all!`, localiza el loop de núcleos:**

```julia
    tasks = Task[]

    for ntype in (:VAC, :INC, :AUS)
        nucleus = state.nuclei[ntype]
        nucleus.status = :running
        put!(state.progress_channel,
            (:nucleus_start, ntype, nucleus.total_ids, nucleus.n_subcores))

        t = @async begin
            for sc in nucleus.subcores
                process_subcore!(sc, nucleus, unified, state)
                yield()
            end
        end
        push!(tasks, t)
    end

    @async begin
        for t in tasks
            wait(t)
        end
        state.finished = true
        put!(state.progress_channel,
            (:all_done, length(state.valid_ids), length(state.out_ids)))
        close(state.progress_channel)
    end
```

**Reemplaza todo ese bloque por:**

```julia
    tasks = Task[]

    for ntype in (:VAC, :INC, :AUS)
        nucleus = state.nuclei[ntype]
        nucleus.status = :running
        put!(state.progress_channel,
            (:nucleus_start, ntype, nucleus.total_ids, nucleus.n_subcores))

        # Threads.@spawn usa un thread real del pool de Julia (vs @async cooperativo)
        t = Threads.@spawn begin
            for sc in nucleus.subcores
                process_subcore!(sc, nucleus, unified, state)
            end
        end
        push!(tasks, t)
    end

    # Watcher en @async (no necesita thread real, solo espera)
    @async begin
        for t in tasks
            wait(t)
        end
        state.finished = true
        put!(state.progress_channel,
            (:all_done, length(state.valid_ids), length(state.out_ids)))
        close(state.progress_channel)
    end
```

> **Nota sobre thread-safety:** `push!` a `Vector` y `Dict` no es thread-safe. Los tres núcleos escriben concurrentemente a `state.valid_ids`, `state.out_ids`, `state.rejected_ids` y `state.rejected_reasons`. Necesitas protegerlos con un lock.

**Agrega un lock al `ProcessorState`.** En `src/Processor.jl`, localiza la definición de `ProcessorState`:

```julia
mutable struct ProcessorState
    nuclei::Dict{Symbol, NucleusState}
    valid_ids::Vector{String}
    out_ids::Vector{String}
    rejected_ids::Vector{String}
    rejected_reasons::Dict{String, String}
    total_new::Int
    processed::Int
    started_at::DateTime
    finished::Bool
    finalized::Bool
    progress_channel::Channel{Any}
end
```

**Reemplaza por:**

```julia
mutable struct ProcessorState
    nuclei::Dict{Symbol, NucleusState}
    valid_ids::Vector{String}
    out_ids::Vector{String}
    rejected_ids::Vector{String}
    rejected_reasons::Dict{String, String}
    total_new::Int
    processed::Int
    started_at::DateTime
    finished::Bool
    finalized::Bool
    progress_channel::Channel{Any}
    _lock::ReentrantLock        # ← nuevo campo para thread-safety
end
```

En la función `init_processor`, localiza el `return ProcessorState(...)` al final y **agrega `ReentrantLock()`** como último argumento:

```julia
    return ProcessorState(
        nuclei,
        String[], String[], String[],
        Dict{String,String}(),
        length(unique(new_ids)),
        0,
        now(), false, false,
        Channel{Any}(2048),
        ReentrantLock(),        # ← agregar esta línea
    )
```

Luego en `process_subcore!`, localiza el loop que escribe al estado compartido:

```julia
    for vr in results
        if vr.status == Validator.valid
            sc.valid_count += 1
            push!(state.valid_ids, vr.id)
        else
            sc.out_count += 1
            push!(state.out_ids, vr.id)
            push!(state.rejected_ids, vr.id)
            state.rejected_reasons[vr.id] = vr.reason
        end
        sc.done     += 1
        state.processed += 1
        put!(state.progress_channel,
            (:progress, sc.nucleus, sc.id, vr.id, vr.status, vr.reason))
    end
```

**Reemplaza por:**

```julia
    for vr in results
        if vr.status == Validator.valid
            sc.valid_count += 1
        else
            sc.out_count += 1
        end
        sc.done += 1

        # Escrituras compartidas protegidas por lock
        lock(state._lock) do
            if vr.status == Validator.valid
                push!(state.valid_ids, vr.id)
            else
                push!(state.out_ids, vr.id)
                push!(state.rejected_ids, vr.id)
                state.rejected_reasons[vr.id] = vr.reason
            end
            state.processed += 1
        end

        put!(state.progress_channel,
            (:progress, sc.nucleus, sc.id, vr.id, vr.status, vr.reason))
    end
```

También las escrituras sobre `nucleus` al final de `process_subcore!`:

```julia
    sc.status             = :done
    nucleus.valid_total  += sc.valid_count
    nucleus.out_total    += sc.out_count
    nucleus.done_subcores += 1
```

**Reemplaza por:**

```julia
    sc.status = :done
    lock(state._lock) do
        nucleus.valid_total   += sc.valid_count
        nucleus.out_total     += sc.out_count
        nucleus.done_subcores += 1
    end
```

Y el bloque de `nucleus.status = :done`:

```julia
    if nucleus.done_subcores == nucleus.n_subcores
        nucleus.status = :done
        put!(state.progress_channel,
            (:nucleus_done, sc.nucleus, nucleus.valid_total, nucleus.out_total))
    end
```

**Reemplaza por:**

```julia
    local nucleus_done = false
    lock(state._lock) do
        nucleus_done = (nucleus.done_subcores == nucleus.n_subcores)
        nucleus_done && (nucleus.status = :done)
    end
    if nucleus_done
        put!(state.progress_channel,
            (:nucleus_done, sc.nucleus, nucleus.valid_total, nucleus.out_total))
    end
```

---

#### Cambio 2.3 — `src/Validator.jl`: pre-indexar por `Numero_novedad` en lugar de `filter` por fila

En `validate_vac` y `validate_inc`, el loop actual hace:
```julia
for num_nov in unique(rows.Numero_novedad)
    sub = filter(r -> r.Numero_novedad == num_nov, rows)
```

Esto es O(n × m) donde n = filas, m = novedades únicas.

**En `validate_vac`**, reemplaza el inicio de la función después de `isempty(rows) && return results`:

```julia
    # ANTES (lento):
    for num_nov in unique(rows.Numero_novedad)
        sub = filter(r -> r.Numero_novedad == num_nov, rows)
```

**Por:**

```julia
    # DESPUÉS (índice previo O(n) total):
    # Agrupar por Numero_novedad una sola vez
    groups = Dict{String, Vector{Int}}()
    for (i, r) in enumerate(eachrow(rows))
        k = string(coalesce(get(r, :Numero_novedad, ""), ""))
        push!(get!(groups, k, Int[]), i)
    end

    for (num_nov, idxs) in groups
        sub = rows[idxs, :]
```

Aplica el **mismo cambio** en `validate_inc` (es estructuralmente idéntico).

---

#### Cambio 2.4 — `src/Validator.jl`: pre-indexar `unified` por ID en `validate_group`

En `validate_group`, la línea:
```julia
    rows   = filter(r -> r.ID ∈ id_set, unified)
```
escanea `unified` completo. Si `unified` tiene 20.000 filas y hay 30 sub-núcleos, esto sucede 30 veces.

La solución: construir el índice `ID → índice de fila` **una sola vez** en `init_processor` y pasarlo a `validate_group`.

Esto requiere un cambio en la firma de `validate_group`. Sigue estos pasos:

**Paso A — en `src/Processor.jl`, agrega un campo al `ProcessorState`:**

En la struct `ProcessorState`, después de `progress_channel::Channel{Any}`, agrega:

```julia
    unified_index::Dict{String, Int}    # ID → índice de fila en unified
```

**Paso B — en `init_processor`, construir el índice:**

Antes del `return ProcessorState(...)`, agrega:

```julia
    # Índice rápido ID → fila de unified (construido una sola vez)
    unified_index = Dict{String,Int}()
    for (i, row) in enumerate(eachrow(unified))
        haskey(unified_index, row.ID) || (unified_index[row.ID] = i)
    end
```

Y agrégalo al constructor de `ProcessorState`:

```julia
    return ProcessorState(
        nuclei,
        String[], String[], String[],
        Dict{String,String}(),
        length(unique(new_ids)),
        0,
        now(), false, false,
        Channel{Any}(2048),
        unified_index,          # ← nuevo
        ReentrantLock(),
    )
```

**Paso C — pasar el índice desde `process_subcore!` a `validate_group`:**

En `process_subcore!`, la llamada actual es:
```julia
    results = validate_group(sc.ids, unified, sc.nucleus)
```

**Reemplaza por:**
```julia
    results = validate_group(sc.ids, unified, sc.nucleus, state.unified_index)
```

**Paso D — actualizar la firma y el cuerpo de `validate_group` en `Validator.jl`:**

Localiza:
```julia
function validate_group(
    ids::Vector{String},
    unified::DataFrame,
    nucleus_type::Symbol,
)::Vector{ValidResult}

    isempty(ids) && return ValidResult[]

    id_set = Set(ids)
    rows   = filter(r -> r.ID ∈ id_set, unified)
```

**Reemplaza por:**

```julia
function validate_group(
    ids::Vector{String},
    unified::DataFrame,
    nucleus_type::Symbol,
    id_index::Dict{String,Int} = Dict{String,Int}(),   # opcional para compatibilidad
)::Vector{ValidResult}

    isempty(ids) && return ValidResult[]

    id_set = Set(ids)

    # Usar índice pre-construido si está disponible; sino filtro completo como fallback
    rows = if !isempty(id_index)
        idxs = [id_index[id] for id in ids if haskey(id_index, id)]
        isempty(idxs) ? filter(r -> r.ID ∈ id_set, unified) : unified[idxs, :]
    else
        filter(r -> r.ID ∈ id_set, unified)
    end
```

> El valor por defecto `Dict{String,Int}()` mantiene la compatibilidad: si alguien llama `validate_group` con 3 argumentos (como en los tests) sigue funcionando.

---

### Resumen de cambios de rendimiento

| # | Archivo | Qué | Impacto estimado |
|---|---------|-----|-----------------|
| 2.1 | `Config.jl` | `SUBCORE_SIZE`: 200 → 500 | Reduce overhead de canal ×2.5 |
| 2.2 | `Processor.jl` | `@async` → `Threads.@spawn` + `ReentrantLock` | ×3 con 4 cores, ×6 con 8 cores |
| 2.3 | `Validator.jl` | `filter` por novedad → Dict de grupos previo | O(n²) → O(n) por núcleo |
| 2.4 | `Processor.jl` + `Validator.jl` | Índice de `unified` pre-construido | Elimina 30 escaneos completos |

Con 5000 novedades y 4 threads físicos, la combinación de 2.2 + 2.3 + 2.4 debería bajar de ~60 min a **menos de 15 minutos**. Con 8 threads, menos de 8 minutos.

---

## Orden recomendado para aplicar los cambios

1. `src/Config.jl` → Cambio 2.1 (5 segundos, no rompe nada)
2. `src/Panel.jl` → Cambios 1.1 a 1.6 (GTK)
3. `src/Processor.jl` → Cambio 2.2 (struct + lock + `Threads.@spawn`)
4. `src/Processor.jl` → Cambio 2.4 Pasos A y B (agregar `unified_index` a struct e `init_processor`)
5. `src/Processor.jl` → Cambio 2.4 Paso C (actualizar llamada a `validate_group`)
6. `src/Validator.jl` → Cambio 2.3 (grupos por dict en `validate_vac` e `validate_inc`)
7. `src/Validator.jl` → Cambio 2.4 Paso D (actualizar firma de `validate_group`)
8. Ajustar el comando de lanzamiento: `julia --threads auto main.jl`

---

## Verificación rápida post-cambio

Después de aplicar todos los cambios, prueba con:

```julia
# Desde la terminal, en el directorio del proyecto:
julia --threads auto -e "
using Pkg; Pkg.activate(\".\")
include(\"src/Config.jl\")
include(\"src/Panel.jl\")
using .Panel
println(\"GTK disponible: \", Panel.gtk_available())
"
```

Debe imprimir `GTK disponible: true` si GTK está instalado con display activo.

Para verificar threads:
```julia
julia --threads auto -e "println(Threads.nthreads())"
```
Debe imprimir un número mayor a 1 (idealmente 4, 8 o el número de cores lógicos del equipo).
