# 🎨 [module-name].css / [module-name].scss

<!-- Ruta: styles/[module-name].css -->
<!-- Guía completa en: docs/guides/CSS_GUIDE.md -->

## Metadata

| Field                  | Value                                              |
|------------------------|----------------------------------------------------|
| **File path**          | `styles/[module-name].css`                         |
| **Preprocessor**       | Plain CSS / SCSS / Less / PostCSS                  |
| **Scope**              | Global / Component / Layout / Theme / Utility      |
| **Author**             | Name / git user                                    |
| **Maintainer**         | Name / git user                                    |
| **Last updated**       | YYYY-MM-DD                                         |
| **Status**             | 🟢 Stable / 🟡 In progress / 🔴 Deprecated         |

---

## 1. Purpose

> What visual problem or responsibility does this file own? 2–4 lines max.

(Description here)

**This file IS responsible for:**
- ...
- ...

**This file is NOT responsible for:**
- ...

---

## 2. Dependencies

### 2.1 External (CDN / npm packages)

| Package | Version | Purpose |
|---------|---------|---------|
| `normalize.css` | `^8.0.1` | Cross-browser baseline reset |

### 2.2 Internal imports / cascading order

> List files this stylesheet depends on, in the order they must be loaded. Order matters in CSS.

```
1. variables.css       ← must load first (custom properties)
2. reset.css           ← base resets
3. typography.css      ← font rules
4. [module-name].css   ← this file
```

---

## 3. Custom Properties (CSS Variables)

> Variables defined IN this file. Variables consumed but defined elsewhere go in section 2.

| Variable | Default value | Description |
|----------|---------------|-------------|
| `--color-primary` | `#1A73E8` | Main brand color |
| `--spacing-unit` | `8px` | Base spacing unit |
| `--border-radius` | `4px` | Standard corner radius |

---

## 4. Exported selectors / classes

> Public surface of this stylesheet: classes, IDs, or custom elements other files should use.

| Selector | Type | Description |
|----------|------|-------------|
| `.btn` | class | Base button style |
| `.btn--primary` | modifier (BEM) | Primary action button |
| `.card` | class | Container card component |
| `#main-nav` | id | Main navigation wrapper |

### 4.1 Class naming convention

- [ ] BEM (Block__Element--Modifier)
- [ ] Utility-first (Tailwind-style)
- [ ] SMACSS
- [ ] Custom — *(explain here)*

---

## 5. Responsive breakpoints used

| Breakpoint name | Min-width | Target device |
|-----------------|-----------|---------------|
| `sm` | `480px` | Large phones |
| `md` | `768px` | Tablets |
| `lg` | `1024px` | Laptops |
| `xl` | `1280px` | Desktop |

---

## 6. Animations / transitions defined

| Name (`@keyframes` or class) | Duration | Trigger | Description |
|------------------------------|----------|---------|-------------|
| `fadeIn` | `200ms` | class add | Element entrance |
| `.is-loading` | `1s infinite` | JS toggle | Loading spinner |

---

## 7. Known overrides / specificity issues

> Document any `!important`, high-specificity selectors, or third-party overrides. These are the traps.

```css
/* ⚠️ Override for [Library X] default button — do not remove */
.lib-btn.btn--primary {
  background: var(--color-primary) !important;
}
```

**Reason:** [Library X] uses inline styles that can't be overridden otherwise. Ticket: #000

---

## 8. Usage examples

### Basic
```html
<button class="btn btn--primary">Submit</button>
```

### With modifier
```html
<div class="card card--featured">
  <p class="card__body">Content</p>
</div>
```

---

## 9. Internal notes / design decisions

- **Why this approach over X:** ...
- **Known technical debt:** ...
- **Do NOT modify without understanding:** ...

---

## 10. TODO

- [ ] ...
- [ ] ...

---

## 11. References

- Design system / Figma: (link)
- Related ticket / issue: (link)
- Browser compatibility notes: (link)
