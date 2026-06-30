<div align="center">

# 📊 Engineering Dashboard · Data Team

**A modern, modular portfolio dashboard for engineering & data teams — with a native desktop control panel.**

![Status](https://img.shields.io/badge/status-active-2ee89a?style=flat-square)
![Version](https://img.shields.io/badge/version-4.0-5bbdff?style=flat-square)
![License](https://img.shields.io/badge/license-private-b47cff?style=flat-square)
![Made with](https://img.shields.io/badge/frontend-HTML%20%7C%20CSS%20%7C%20JS-f7b500?style=flat-square)
![Backend](https://img.shields.io/badge/backend-Python-3776AB?style=flat-square&logo=python&logoColor=white)

🇪🇸 [Español](#-es--documentación-en-español) &nbsp;·&nbsp; 🇬🇧 [English](#-en--english-documentation)

</div>

---

## 🎬 Preview

<div align="center">

<!-- Video de demostración del dashboard. Coloca el archivo en assets/data/ con el nombre indicado o ajusta la ruta. -->
https://github.com/user-attachments/assets/REEMPLAZAR_CON_TU_VIDEO

</div>

<table>
  <tr>
    <td align="center"><img src="assets/data/preview_dashboard.png" alt="Vista general del dashboard" width="100%"/><br/><sub><b>Vista general / Overview</b></sub></td>
    <td align="center"><img src="assets/data/preview_project_card.png" alt="Tarjeta de proyecto" width="100%"/><br/><sub><b>Tarjeta de proyecto / Project card</b></sub></td>
  </tr>
  <tr>
    <td align="center"><img src="assets/data/preview_panel.png" alt="Panel de gestión" width="100%"/><br/><sub><b>Panel de gestión / Management panel</b></sub></td>
    <td align="center"><img src="assets/data/preview_orgchart.png" alt="Org chart 3D" width="100%"/><br/><sub><b>Org-chart 3D / 3D org chart</b></sub></td>
  </tr>
</table>

> 💡 **Nota:** reemplaza los enlaces de video e imágenes anteriores con los archivos finales ubicados en `assets/data/` (ver sección [Multimedia](#-multimedia--es)).

---

<br/>

# 🇪🇸 ES · Documentación en Español

## Tabla de contenido

- [Acerca del proyecto](#acerca-del-proyecto)
- [Características principales](#características-principales)
- [Arquitectura y estructura](#arquitectura-y-estructura)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Modos de ejecución](#modos-de-ejecución)
- [Multimedia](#-multimedia--es)
- [Control de versiones](#control-de-versiones)
- [Notas y solución de problemas](#notas-y-solución-de-problemas)

### Acerca del proyecto

**Engineering Dashboard** es un panel de control ejecutivo construido para equipos de datos e ingeniería, pensado para dar visibilidad en tiempo real sobre **portafolio de proyectos, riesgo, capacidad del equipo y entregables críticos**. Combina un frontend ligero (sin frameworks pesados) con un **panel de edición nativo en Python/Tkinter** que permite gestionar la información directamente sobre los archivos JSON que alimentan el dashboard.

El proyecto está diseñado para ejecutarse de forma 100% local, sin dependencias de infraestructura externa, ideal para equipos que necesitan una herramienta de seguimiento rápida, visual y totalmente personalizable.

### Características principales

- 🎯 **Vista ejecutiva** con métricas de portafolio, riesgo y avance.
- 📦 **Gestión de entregables** por proyecto y por miembro del equipo.
- 📅 **Timeline** de hitos y fechas críticas.
- 🚧 **Seguimiento de blockers** para identificar cuellos de botella a tiempo.
- 💬 **Comentarios** colaborativos por proyecto.
- 📋 **Panel de SLA** para control de cumplimiento.
- 🌐 **Soporte multi-idioma** (Español / Inglés) con cambio dinámico.
- 🌓 **Tema claro / oscuro** intercambiable.
- 🧭 **Org-chart 3D interactivo** (construido con D3.js) en la pantalla de bienvenida, con selector visual de área y usuario.
- 🖥️ **Panel externo de edición** (Tkinter) para crear, editar y reorganizar proyectos sin tocar el JSON manualmente.
- 🔌 **Servidor local integrado** que conecta el dashboard web con el panel de escritorio.

### Arquitectura y estructura

```
data projects dashboard v4.0/
├── index.html                  → Punto de entrada del dashboard web
├── server.py                   → Servidor HTTP local + puente con el panel
├── panel_proyectos.py          → Punto de entrada del panel de escritorio (Tkinter)
├── migrar_proyectos.py         → Utilidad de migración de datos
├── assets/
│   ├── css/
│   │   └── styles.css          → Estilos globales y de componentes
│   ├── js/
│   │   ├── data.js             → Datos base, estado global y almacenamiento
│   │   ├── utils.js            → Funciones auxiliares reutilizables
│   │   ├── calculations.js     → Cálculo de métricas del portafolio
│   │   ├── renderers.js        → Renderizado de secciones, tarjetas y vistas
│   │   ├── sla.js              → Lógica y vista del panel de SLA
│   │   ├── dashboard.js        → Orquestación general del dashboard
│   │   ├── welcome.js          → Pantallas de bienvenida y org-chart 3D
│   │   ├── actions.js          → Acciones de usuario, persistencia y mutaciones
│   │   ├── i18n.js             → Sistema de internacionalización (ES/EN)
│   │   └── app.js              → Animación de fondo y arranque de la app
│   └── data/                   → Archivos JSON por área (fuente de datos viva)
└── panel/                      → Paquete Python del panel de escritorio
    ├── config.py                → Configuración y rutas de datos
    ├── main_panel.py            → Ventana principal del panel
    ├── editor.py                 → Editor de proyectos
    ├── widgets.py                → Componentes visuales reutilizables
    └── translator.py             → Traducción interna del panel
```

> El frontend sigue un **orden de carga explícito** en `index.html`: `data → utils → calculations → renderers → sla → dashboard → welcome → actions → i18n → app`, garantizando que cada módulo tenga sus dependencias disponibles antes de ejecutarse.

### Requisitos previos

- **Python 3.9+** (incluye `tkinter`, generalmente disponible por defecto en la mayoría de distribuciones de Python).
- Un **navegador moderno** (Chrome, Edge, Firefox).
- No se requieren paquetes adicionales de `pip` ni `npm`: las librerías de frontend (Chart.js, D3.js) se cargan vía CDN.

### Instalación

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd "data projects dashboard v4.0"

# 2. (Opcional) Verificar que Python y Tkinter estén disponibles
python --version
python -m tkinter
```

### Modos de ejecución

El proyecto ofrece **tres formas de ejecución**, según el nivel de funcionalidad que necesites:

| Modo | Comando | Descripción |
|---|---|---|
| 🟡 **Solo lectura** | Doble click en `index.html` | Abre el dashboard directamente en el navegador. El panel externo de edición **no estará disponible** en este modo. |
| 🟢 **Solo panel** | `python panel_proyectos.py` | Abre únicamente el panel de escritorio (Tkinter), funcional sobre los archivos JSON correspondientes. |
| 🔵 **Modo completo (recomendado)** | `python server.py` | Levanta un servidor local que sirve el dashboard **y** habilita la comunicación con el panel de edición, permitiendo el flujo completo. |

```bash
python server.py
```

Esto abrirá automáticamente tu navegador en `http://localhost:8000`.

### 🖼️ Multimedia (ES)

Los recursos visuales del proyecto (video de demostración e imágenes de referencia) se encuentran en:

```
assets/data/
```

Para que la sección [Preview](#-preview) de este README se muestre correctamente:

1. Coloca el video de demostración en `assets/data/` (formato `.mp4` recomendado).
2. Coloca las capturas de pantalla en `assets/data/` con los nombres usados en este documento (`preview_dashboard.png`, `preview_project_card.png`, `preview_panel.png`, `preview_orgchart.png`) o ajusta los nombres en el README según corresponda.
3. Si subes el video como *attachment* directamente en un Pull Request o Issue de GitHub, reemplaza el enlace de la sección Preview por el enlace generado automáticamente por GitHub.

### Control de versiones

Este proyecto se gestiona mediante Git. Se recomienda seguir convenciones de *commits* claros y descriptivos, documentando los cambios relevantes también en el archivo histórico de cambios incluido en el repositorio.

### Notas y solución de problemas

- 🧹 **Caché del navegador:** si has ejecutado versiones anteriores del proyecto, limpia la caché del navegador antes de probar la versión actual para evitar inconsistencias visuales o de datos.
- 📁 **Datos no encontrados:** si el panel de escritorio no encuentra el directorio de datos (`assets/data`), asegúrate de ejecutarlo desde la raíz del proyecto. Alternativamente, usa el botón **"Abrir otro JSON"** dentro del panel para cargar un archivo desde cualquier ubicación.
- 🔄 **Sincronización dashboard ↔ panel:** los cambios realizados desde el panel de escritorio se reflejan en el dashboard al recargar la página, ya que ambos leen y escriben sobre los mismos archivos JSON en `assets/data/`.

---

<br/>

# 🇬🇧 EN · English Documentation

## Table of Contents

- [About the project](#about-the-project)
- [Key features](#key-features)
- [Architecture & structure](#architecture--structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Execution modes](#execution-modes)
- [Media assets](#-media-assets--en)
- [Version control](#version-control)
- [Notes & troubleshooting](#notes--troubleshooting)

### About the project

**Engineering Dashboard** is an executive control panel built for engineering and data teams, designed to provide real-time visibility into **project portfolio status, risk, team capacity, and critical deliverables**. It pairs a lightweight, framework-free frontend with a **native Python/Tkinter editing panel** that manages the data directly on the JSON files that power the dashboard.

The project is designed to run **fully locally**, with no external infrastructure dependencies — ideal for teams that need a fast, visual, and fully customizable tracking tool.

### Key features

- 🎯 **Executive view** with portfolio metrics, risk, and progress tracking.
- 📦 **Deliverables management** per project and per team member.
- 📅 **Timeline** of milestones and critical dates.
- 🚧 **Blocker tracking** to surface bottlenecks early.
- 💬 **Collaborative comments** per project.
- 📋 **SLA panel** for compliance tracking.
- 🌐 **Multi-language support** (Spanish / English) with dynamic switching.
- 🌓 **Light / dark theme** toggle.
- 🧭 **Interactive 3D org-chart** (built with D3.js) on the welcome screen, with a visual area and user selector.
- 🖥️ **External desktop editing panel** (Tkinter) to create, edit, and reorganize projects without touching the JSON by hand.
- 🔌 **Integrated local server** that bridges the web dashboard with the desktop panel.

### Architecture & structure

```
data projects dashboard v4.0/
├── index.html                  → Web dashboard entry point
├── server.py                   → Local HTTP server + bridge to the panel
├── panel_proyectos.py          → Desktop panel entry point (Tkinter)
├── migrar_proyectos.py         → Data migration utility
├── assets/
│   ├── css/
│   │   └── styles.css          → Global and component styles
│   ├── js/
│   │   ├── data.js             → Base data, global state, and storage
│   │   ├── utils.js            → Reusable helper functions
│   │   ├── calculations.js     → Portfolio metrics calculations
│   │   ├── renderers.js        → Sections, cards, and views rendering
│   │   ├── sla.js              → SLA panel logic and view
│   │   ├── dashboard.js        → Overall dashboard orchestration
│   │   ├── welcome.js          → Welcome screens and 3D org-chart
│   │   ├── actions.js          → User actions, persistence, and mutations
│   │   ├── i18n.js             → Internationalization system (ES/EN)
│   │   └── app.js              → Background animation and app bootstrap
│   └── data/                   → Per-area JSON files (live data source)
└── panel/                      → Desktop panel Python package
    ├── config.py                → Configuration and data paths
    ├── main_panel.py            → Main panel window
    ├── editor.py                 → Project editor
    ├── widgets.py                → Reusable visual components
    └── translator.py             → Internal panel translation
```

> The frontend follows an **explicit load order** in `index.html`: `data → utils → calculations → renderers → sla → dashboard → welcome → actions → i18n → app`, ensuring every module has its dependencies available before running.

### Prerequisites

- **Python 3.9+** (includes `tkinter`, generally available by default in most Python distributions).
- A **modern browser** (Chrome, Edge, Firefox).
- No additional `pip` or `npm` packages required: frontend libraries (Chart.js, D3.js) are loaded via CDN.

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd "data projects dashboard v4.0"

# 2. (Optional) Verify Python and Tkinter are available
python --version
python -m tkinter
```

### Execution modes

The project offers **three ways to run it**, depending on the level of functionality you need:

| Mode | Command | Description |
|---|---|---|
| 🟡 **Read-only** | Double-click `index.html` | Opens the dashboard directly in the browser. The external editing panel **will not be available** in this mode. |
| 🟢 **Panel only** | `python panel_proyectos.py` | Opens only the desktop panel (Tkinter), fully functional against the corresponding JSON files. |
| 🔵 **Full mode (recommended)** | `python server.py` | Spins up a local server that serves the dashboard **and** enables communication with the editing panel, unlocking the full workflow. |

```bash
python server.py
```

This will automatically open your browser at `http://localhost:8000`.

### 🖼️ Media assets (EN)

The project's visual assets (demo video and reference images) live in:

```
assets/data/
```

For the [Preview](#-preview) section of this README to render correctly:

1. Place the demo video in `assets/data/` (`.mp4` recommended).
2. Place the screenshots in `assets/data/` using the file names referenced in this document (`preview_dashboard.png`, `preview_project_card.png`, `preview_panel.png`, `preview_orgchart.png`), or update the names in the README accordingly.
3. If you upload the video as an attachment directly to a GitHub Pull Request or Issue, replace the link in the Preview section with the one automatically generated by GitHub.

### Version control

This project is managed with Git. Clear, descriptive commit messages are recommended, and relevant changes should also be documented in the changelog file included in the repository.

### Notes & troubleshooting

- 🧹 **Browser cache:** if you've run previous versions of the project, clear your browser cache before testing the current version to avoid visual or data inconsistencies.
- 📁 **Data not found:** if the desktop panel can't find the data directory (`assets/data`), make sure you're running it from the project root. Alternatively, use the **"Open another JSON"** button inside the panel to load a file from any location.
- 🔄 **Dashboard ↔ panel sync:** changes made from the desktop panel are reflected in the dashboard upon page reload, since both read and write to the same JSON files in `assets/data/`.

---

<div align="center">

<sub>Built for the Data Team · Engineering Dashboard v4.0</sub>

</div>
