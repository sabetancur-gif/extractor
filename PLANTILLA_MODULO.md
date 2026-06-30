# 📦 [Nombre del Módulo]

> Plantilla de documentación de módulo · Copiar este archivo como `docs/[nombre-modulo].md` o `[nombre-modulo]/README.md`

## Metadata

| Campo               | Valor                                  |
|---------------------|-----------------------------------------|
| **Ruta del módulo** | `src/modulo/...`                        |
| **Autor original**  | Nombre / usuario git                    |
| **Mantenedor actual**| Nombre / usuario git                   |
| **Última actualización** | YYYY-MM-DD                         |
| **Versión / Tag**   | (si aplica, ej. v1.2.0)                 |
| **Estado**          | 🟢 Estable / 🟡 En desarrollo / 🔴 Deprecado |

---

## 1. Propósito

> ¿Qué problema resuelve este módulo? Responder en 2-4 líneas. Si no se puede explicar brevemente, el módulo probablemente debería dividirse.

(Descripción aquí)

**Responsabilidades:**
- ...
- ...

**NO es responsabilidad de este módulo:**
- ...

---

## 2. Dependencias

### 2.1 Terceros (externas)

| Paquete | Versión | Para qué se usa |
|---------|---------|------------------|
| `nombre-paquete` | `^1.0.0` | Breve razón |

### 2.2 Locales (internas del proyecto)

| Módulo | Ruta | Para qué se usa |
|--------|------|------------------|
| `otro-modulo` | `src/otro-modulo` | Breve razón |

> ⚠️ Si este módulo es importado por muchos otros, listar también **quién depende de este módulo** (consumidores conocidos), para medir el impacto de un cambio.

**Consumido por:**
- `modulo-x`
- `modulo-y`

---

## 3. Exportaciones públicas (API del módulo)

> Lo que el módulo expone hacia afuera. Esta es la sección que debe leer alguien que **consume** el módulo sin entrar a su código interno.

| Nombre | Tipo | Descripción breve |
|--------|------|---------------------|
| `NombreClase` | Clase | ... |
| `nombreFuncion()` | Función | ... |
| `CONSTANTE_X` | Constante | ... |

---

## 4. Detalle de clases

### `NombreClase`

**Descripción:** ¿Qué representa/hace esta clase?

**Constructor / inicialización:**
```
parámetro_1 (tipo) — descripción
parámetro_2 (tipo) — descripción
```

**Propiedades públicas:**

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `prop1` | string | ... |

**Métodos:**

#### `metodo(param1, param2)`
- **Descripción:** ...
- **Parámetros:**
  - `param1` (tipo): ...
  - `param2` (tipo): ...
- **Retorna:** (tipo) descripción
- **Errores/Excepciones:** ¿Qué puede fallar y cuándo?
- **Ejemplo:**
```
// ejemplo mínimo de uso
```

> 🔁 Repetir este bloque por cada método público relevante. Métodos privados/internos no necesitan este nivel de detalle, basta una línea en notas internas si son complejos.

---

## 5. Detalle de funciones (no asociadas a clase)

### `nombreFuncion(param1, param2)`
- **Descripción:** ...
- **Parámetros:**
  - `param1` (tipo): ...
- **Retorna:** (tipo) descripción
- **Efectos secundarios:** ¿modifica algo externo, hace I/O, llama APIs?
- **Ejemplo:**
```
// ejemplo mínimo de uso
```

---

## 6. Flujo / diagrama (opcional pero recomendado)

> Si el módulo tiene un flujo de datos o proceso no trivial, describirlo en pasos o pegar un diagrama.

1. Entra X →
2. Se transforma en Y →
3. Sale Z

---

## 7. Notas internas / decisiones de diseño

> Esto es lo que normalmente solo vive en la cabeza del autor. Capturarlo aquí evita reinventar la rueda o romper algo "raro a propósito".

- **Por qué se hizo así y no de otra forma:** ...
- **Trade-offs conocidos:** ...
- **Deuda técnica / cosas que se sabe que están mal pero no se han arreglado:** ...
- **Cosas que NO se deben tocar sin entender X:** ...

---

## 8. Pendientes / TODOs

- [ ] ...
- [ ] ...

---

## 9. Referencias

- Issue/ticket original: (link)
- Documentación externa relevante: (link)
- Conversaciones/decisiones importantes (Slack, PRs): (link)
