# 🌐 [page-or-component-name].html

<!-- Ruta: src/[page-or-component-name].html -->
<!-- Guía completa en: docs/guides/HTML_GUIDE.md -->

## Metadata

| Field               | Value                                              |
|---------------------|----------------------------------------------------|
| **File path**       | `src/[page-or-component-name].html`                |
| **Type**            | Page / Layout / Partial / Component / Email        |
| **Template engine** | None / Jinja2 / Handlebars / Nunjucks / EJS / Pug  |
| **Author**          | Name / git user                                    |
| **Maintainer**      | Name / git user                                    |
| **Last updated**    | YYYY-MM-DD                                         |
| **Status**          | 🟢 Stable / 🟡 In progress / 🔴 Deprecated         |

---

## 1. Purpose

> What page, view, or UI structure does this file define? 2–4 lines max.

(Description here)

**This file IS responsible for:**
- ...

**This file is NOT responsible for:**
- ...

---

## 2. Dependencies

### 2.1 Scripts loaded

> List all `<script>` tags, in load order. Separate blocking from deferred.

| File / CDN | Load strategy | Purpose |
|------------|---------------|---------|
| `vendor/alpine.min.js` | `defer` | Reactivity layer |
| `src/main.js` | `defer` | App entrypoint |
| `https://cdn.example.com/lib.js` | `async` | Third-party widget |

### 2.2 Stylesheets linked

| File / CDN | Purpose |
|------------|---------|
| `styles/reset.css` | Base reset |
| `styles/[module].css` | Page styles |

### 2.3 Partials / includes / components

| Partial | Path | Description |
|---------|------|-------------|
| `_header.html` | `partials/_header.html` | Site navigation |
| `_footer.html` | `partials/_footer.html` | Site footer |

---

## 3. Page / document structure

> High-level DOM structure. Use indentation to show nesting.

```
<html>
 └── <head>          ← SEO, meta, fonts, CSS
 └── <body>
      ├── <header>   ← Site navigation (#main-nav)
      ├── <main>
      │    ├── .hero          ← Hero section
      │    ├── .content-grid  ← Main content area
      │    └── .sidebar       ← Optional sidebar
      └── <footer>   ← Links, copyright
```

---

## 4. Key elements & IDs

> Important IDs or landmark elements that JS or CSS hooks into. These are the "public API" of the HTML structure.

| Selector | Tag | Purpose |
|----------|-----|---------|
| `#app` | `<div>` | JS mount point |
| `#main-nav` | `<nav>` | Main navigation |
| `.js-modal-trigger` | `<button>` | Triggers modal (used by `modal.js`) |
| `[data-user-id]` | `<div>` | Data attribute read by `UserCard.js` |

---

## 5. Template variables / slots

> If using a template engine, list all variables this template expects.

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `{{ title }}` | `string` | ✅ | Page `<title>` and `<h1>` |
| `{{ user.name }}` | `string` | ✅ | Displayed in greeting |
| `{{ items }}` | `array` | ❌ | List of items to render |
| `{% block content %}` | block | ✅ | Main content injection point |

---

## 6. SEO / `<head>` contents

| Tag | Content | Notes |
|-----|---------|-------|
| `<title>` | `Page Name — Site Name` | Max 60 chars |
| `meta description` | ... | Max 155 chars |
| `og:title` | ... | Open Graph for sharing |
| `canonical` | `https://...` | Canonical URL |
| `lang` attribute | `es` / `en` | Set on `<html>` |

---

## 7. Accessibility (a11y) notes

- [ ] All images have meaningful `alt` text (or `alt=""` if decorative)
- [ ] Heading hierarchy is sequential (`h1` → `h2` → `h3`)
- [ ] All interactive elements are keyboard-navigable
- [ ] Color contrast meets WCAG 2.1 AA minimum
- [ ] Form fields have associated `<label>` elements
- [ ] ARIA roles / attributes used: *(list them here)*

---

## 8. Forms (if applicable)

### `#form-name`

| Field | `name` attr | Type | Required | Validation |
|-------|-------------|------|----------|------------|
| Email | `email` | `email` | ✅ | Valid email format |
| Message | `message` | `textarea` | ✅ | Max 500 chars |

- **Submits to:** `POST /api/contact`
- **Handled by:** `src/forms/contactForm.js`

---

## 9. Internal notes / design decisions

- **Why this structure:** ...
- **Known quirks:** ...
- **Do NOT change without understanding:** ...

---

## 10. TODO

- [ ] ...
- [ ] ...

---

## 11. References

- Figma design: (link)
- Related ticket / issue: (link)
- CMS template docs (if applicable): (link)
