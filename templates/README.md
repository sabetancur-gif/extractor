<div align="center">

<!-- Replace with your project banner. Recommended size: 1200×300px -->
<img src="docs/assets/banner.png" alt="Code Documentation Guides" width="100%" />

# 📖 Code Documentation Guides

**Standardized module documentation templates for multi-language, multi-stack codebases.**  
**Plantillas estandarizadas de documentación de módulos para proyectos multi-lenguaje.**

---

![Status](https://img.shields.io/badge/status-active-2ee89a?style=flat-square)
![Version](https://img.shields.io/badge/version-1.0-5bbdff?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-b47cff?style=flat-square)
![Languages](https://img.shields.io/badge/templates-Python%20%7C%20JS%20%7C%20CSS%20%7C%20HTML%20%7C%20JSON-f7b500?style=flat-square)
![Lang](https://img.shields.io/badge/lang-EN%20%7C%20ES-3776AB?style=flat-square)

🇬🇧 [English](#-en--english-documentation) &nbsp;·&nbsp; 🇪🇸 [Español](#-es--documentación-en-español) &nbsp;·&nbsp; [Templates](#templates) &nbsp;·&nbsp; [Contributing](CONTRIBUTING.md)

</div>

---

## 🖼️ Preview

<table>
  <tr>
    <td align="center"><img src="docs/assets/preview_python.png" alt="Python template" width="100%"/><br/><sub><b>Python module template</b></sub></td>
    <td align="center"><img src="docs/assets/preview_js.png" alt="JavaScript template" width="100%"/><br/><sub><b>JavaScript / TypeScript template</b></sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/assets/preview_css.png" alt="CSS template" width="100%"/><br/><sub><b>CSS / SCSS template</b></sub></td>
    <td align="center"><img src="docs/assets/preview_json.png" alt="JSON template" width="100%"/><br/><sub><b>JSON config template</b></sub></td>
  </tr>
</table>

> 💡 Replace placeholder images above with real screenshots of your filled templates. Place them in `docs/assets/` using the filenames referenced here, or update the paths in the README accordingly.

---

<br/>

# 🇬🇧 EN · English Documentation

## Table of Contents

- [About the project](#about-the-project)
- [Why this exists](#why-this-exists)
- [Who is this for](#who-is-this-for)
- [Templates](#templates)
- [Repository structure](#repository-structure)
- [How to use](#how-to-use)
- [Adoption tips](#adoption-tips)
- [Contributing](#contributing)

---

### About the project

**Code Documentation Guides** is a curated set of module documentation templates — one per file type — designed to bring consistency to codebases where files are written by different people at different times.

Each template covers the full anatomy of a module: its purpose, dependencies, public exports, internal classes and functions, design decisions, and known gotchas. Filling one out takes **10–15 minutes per module** and saves hours of future reverse-engineering.

Every template is available in both **English** and **Spanish** and lives as a Markdown file that can be committed directly alongside the code it documents.

---

### Why this exists

> *"The hardest code to maintain isn't the complex code — it's the undocumented one."*

These guides were created after repeatedly spending time figuring out what a module does, why it was written the way it was, and which parts were safe to change. This repo is the fix: a concrete, opinionated starting point that any team can adopt without a documentation toolchain.

---

### Who is this for

- **Individual contributors** who want a clear format for documenting their own work before handing it off.
- **Tech leads** looking for a lightweight standard to enforce across a team — without writing one from scratch.
- **Onboarding developers** who need a fast way to navigate an unfamiliar codebase.

---

### Templates

| Template | File type | 🇬🇧 English | 🇪🇸 Español |
|----------|-----------|-------------|-------------|
| 🐍 Python module | `.py` | [EN →](docs/en/TEMPLATE_PYTHON.md) | [ES →](docs/es/TEMPLATE_PYTHON.md) |
| ⚡ JavaScript / TypeScript | `.js` / `.ts` | [EN →](docs/en/TEMPLATE_JS.md) | [ES →](docs/es/TEMPLATE_JS.md) |
| 🎨 Stylesheet | `.css` / `.scss` | [EN →](docs/en/TEMPLATE_CSS.md) | [ES →](docs/es/TEMPLATE_CSS.md) |
| 🌐 HTML document | `.html` | [EN →](docs/en/TEMPLATE_HTML.md) | [ES →](docs/es/TEMPLATE_HTML.md) |
| 🗂️ JSON file | `.json` | [EN →](docs/en/TEMPLATE_JSON.md) | [ES →](docs/es/TEMPLATE_JSON.md) |

---

### Repository structure

```
code-documentation-guides/
├── docs/
│   ├── en/                          → All templates in English
│   │   ├── TEMPLATE_PYTHON.md       → Python module template
│   │   ├── TEMPLATE_JS.md           → JavaScript / TypeScript template
│   │   ├── TEMPLATE_CSS.md          → CSS / SCSS stylesheet template
│   │   ├── TEMPLATE_HTML.md         → HTML document template
│   │   └── TEMPLATE_JSON.md         → JSON config / data file template
│   ├── es/                          → All templates in Spanish
│   │   ├── TEMPLATE_PYTHON.md
│   │   ├── TEMPLATE_JS.md
│   │   ├── TEMPLATE_CSS.md
│   │   ├── TEMPLATE_HTML.md
│   │   └── TEMPLATE_JSON.md
│   └── assets/                      → Banner, preview screenshots
├── CONTRIBUTING.md                  → How to contribute
├── LICENSE                          → MIT license
└── README.md                        → This file
```

---

### How to use

**Three ways to adopt these templates, from lightest to deepest:**

| Mode | How | When to use |
|------|-----|-------------|
| 🟡 **Copy & fill** | Copy the template into your project as `docs/[module-name].md`, replace every `[ ]` placeholder with real content, delete sections that don't apply, commit. | Starting a new module or documenting an existing one. |
| 🟢 **Checklist only** | Keep your current doc format and use the template as a review checklist to catch missing sections. | Teams with an existing doc convention. |
| 🔵 **Full adoption (recommended)** | Add the template to your PR template as a required checklist item, enforce via code review. | Teams that want consistent docs across the whole codebase. |

```bash
# Suggested placement inside your project
docs/
└── modules/
    ├── auth-service.md      ← filled from TEMPLATE_PYTHON.md
    ├── dashboard.md         ← filled from TEMPLATE_JS.md
    └── global-styles.md     ← filled from TEMPLATE_CSS.md
```

---

### Adoption tips

- **Start with your 5 most-imported modules.** Those are the ones doing the most work and causing the most confusion when someone new joins.
- **Trim aggressively.** A one-page doc that's accurate beats a five-page doc that's stale. Delete every section that genuinely doesn't apply.
- **Automate the "last updated" field.** Instead of maintaining it manually, derive it from git: `git log -1 --format="%ad" --date=short -- path/to/module`.
- **Make it a PR gate.** The most effective enforcement is a single PR checklist question: *"Does this module have or update a doc file?"*

---

<br/>

# 🇪🇸 ES · Documentación en Español

## Tabla de contenido

- [Acerca del proyecto](#acerca-del-proyecto)
- [Por qué existe esto](#por-qué-existe-esto)
- [Para quién es esto](#para-quién-es-esto)
- [Plantillas](#plantillas)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Cómo usar](#cómo-usar)
- [Consejos de adopción](#consejos-de-adopción)
- [Contribuir](#contribuir)

---

### Acerca del proyecto

**Code Documentation Guides** es un conjunto de plantillas de documentación de módulos — una por tipo de archivo — diseñadas para dar consistencia a codebases donde los archivos son escritos por distintas personas en distintos momentos.

Cada plantilla cubre la anatomía completa de un módulo: su propósito, dependencias, exportaciones públicas, clases y funciones internas, decisiones de diseño, y advertencias conocidas. Completar una toma **10–15 minutos por módulo** y ahorra horas de ingeniería inversa futura.

Cada plantilla está disponible en **inglés y español** y vive como un archivo Markdown que puede commitearse directamente junto al código que documenta.

---

### Por qué existe esto

> *"El código más difícil de mantener no es el complejo — es el que no tiene documentación."*

Estas guías surgieron tras pasar tiempo repetidamente tratando de entender qué hace un módulo, por qué fue escrito de esa manera, y qué partes son seguras de modificar. Este repositorio es la solución: un punto de partida concreto y con criterio que cualquier equipo puede adoptar sin necesitar herramientas de documentación adicionales.

---

### Para quién es esto

- **Desarrolladores** que quieren un formato claro para documentar su propio trabajo antes de entregarlo.
- **Tech leads** que buscan un estándar ligero para aplicar en equipo sin tener que escribirlo desde cero.
- **Desarrolladores en onboarding** que necesitan una forma rápida de navegar un codebase desconocido.

---

### Plantillas

| Plantilla | Tipo de archivo | 🇬🇧 English | 🇪🇸 Español |
|-----------|-----------------|-------------|-------------|
| 🐍 Módulo Python | `.py` | [EN →](docs/en/TEMPLATE_PYTHON.md) | [ES →](docs/es/TEMPLATE_PYTHON.md) |
| ⚡ JavaScript / TypeScript | `.js` / `.ts` | [EN →](docs/en/TEMPLATE_JS.md) | [ES →](docs/es/TEMPLATE_JS.md) |
| 🎨 Hoja de estilos | `.css` / `.scss` | [EN →](docs/en/TEMPLATE_CSS.md) | [ES →](docs/es/TEMPLATE_CSS.md) |
| 🌐 Documento HTML | `.html` | [EN →](docs/en/TEMPLATE_HTML.md) | [ES →](docs/es/TEMPLATE_HTML.md) |
| 🗂️ Archivo JSON | `.json` | [EN →](docs/en/TEMPLATE_JSON.md) | [ES →](docs/es/TEMPLATE_JSON.md) |

---

### Estructura del repositorio

```
code-documentation-guides/
├── docs/
│   ├── en/                          → Todas las plantillas en inglés
│   │   ├── TEMPLATE_PYTHON.md       → Plantilla módulo Python
│   │   ├── TEMPLATE_JS.md           → Plantilla JavaScript / TypeScript
│   │   ├── TEMPLATE_CSS.md          → Plantilla hoja de estilos CSS / SCSS
│   │   ├── TEMPLATE_HTML.md         → Plantilla documento HTML
│   │   └── TEMPLATE_JSON.md         → Plantilla archivo JSON
│   ├── es/                          → Todas las plantillas en español
│   │   ├── TEMPLATE_PYTHON.md
│   │   ├── TEMPLATE_JS.md
│   │   ├── TEMPLATE_CSS.md
│   │   ├── TEMPLATE_HTML.md
│   │   └── TEMPLATE_JSON.md
│   └── assets/                      → Banner e imágenes de preview
├── CONTRIBUTING.md                  → Cómo contribuir
├── LICENSE                          → Licencia MIT
└── README.md                        → Este archivo
```

---

### Cómo usar

**Tres formas de adoptar estas plantillas, de más ligera a más profunda:**

| Modo | Cómo | Cuándo usarlo |
|------|------|---------------|
| 🟡 **Copiar y completar** | Copia la plantilla en tu proyecto como `docs/[nombre-modulo].md`, reemplaza cada marcador `[ ]` con contenido real, elimina las secciones que no apliquen, haz commit. | Al crear un módulo nuevo o documentar uno existente. |
| 🟢 **Solo como checklist** | Mantén tu formato actual y usa la plantilla como lista de verificación para detectar secciones faltantes. | Equipos con una convención de documentación existente. |
| 🔵 **Adopción completa (recomendado)** | Agrega la plantilla al PR template como ítem de checklist requerido, refuerza en code review. | Equipos que quieren documentación consistente en todo el codebase. |

```bash
# Ubicación sugerida dentro de tu proyecto
docs/
└── modules/
    ├── auth-service.md      ← completado desde TEMPLATE_PYTHON.md
    ├── dashboard.md         ← completado desde TEMPLATE_JS.md
    └── global-styles.md     ← completado desde TEMPLATE_CSS.md
```

---

### Consejos de adopción

- **Empieza con tus 5 módulos más importados.** Son los que más trabajo hacen y los que más confusión generan cuando alguien nuevo se incorpora.
- **Elimina sin miedo.** Una documentación de una página precisa vale más que una de cinco páginas desactualizada. Borra cada sección que genuinamente no aplique.
- **Automatiza el campo "última actualización".** En lugar de mantenerlo manualmente, derívalo de git: `git log -1 --format="%ad" --date=short -- ruta/al/modulo`.
- **Hazlo un requisito del PR.** El refuerzo más efectivo es una sola pregunta en el checklist del PR: *"¿Este módulo tiene o actualiza un archivo de documentación?"*

---

### Contribuir / Contributing

Contributions are welcome — new templates, improvements to existing ones, translations to other languages, or fixes.  
Las contribuciones son bienvenidas — nuevas plantillas, mejoras, traducciones a otros idiomas o correcciones.

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

<div align="center">

<sub>Built for teams who believe readable code is kind code · Code Documentation Guides v1.0</sub>

</div>
