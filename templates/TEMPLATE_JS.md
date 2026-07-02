# ⚡ [module-name].js / [module-name].ts

<!-- Ruta: src/[module-name].js -->
<!-- Guía completa en: docs/guides/JS_GUIDE.md -->

## Metadata

| Field               | Value                                              |
|---------------------|----------------------------------------------------|
| **File path**       | `src/[module-name].js`                             |
| **Module system**   | ESM (`import/export`) / CJS (`require`) / IIFE     |
| **Runtime**         | Browser / Node.js / Both                           |
| **Framework**       | None / React / Vue / Angular / other               |
| **Author**          | Name / git user                                    |
| **Maintainer**      | Name / git user                                    |
| **Last updated**    | YYYY-MM-DD                                         |
| **Status**          | 🟢 Stable / 🟡 In progress / 🔴 Deprecated         |

---

## 1. Purpose

> What single problem does this module solve? 2–4 lines max. If it can't be described briefly, it likely does too much.

(Description here)

**This module IS responsible for:**
- ...

**This module is NOT responsible for:**
- ...

---

## 2. Dependencies

### 2.1 Third-party (npm / CDN)

| Package | Version | Used for |
|---------|---------|----------|
| `axios` | `^1.6.0` | HTTP requests |
| `dayjs` | `^1.11.0` | Date formatting |

### 2.2 Internal (local modules)

| Module | Path | Used for |
|--------|------|----------|
| `authService` | `src/services/auth.js` | Token management |
| `logger` | `src/utils/logger.js` | Error logging |

### 2.3 Consumed by (reverse dependencies)

> Files that import this module. Useful to assess the blast radius of a change.

- `src/pages/dashboard.js`
- `src/components/UserCard.js`

---

## 3. Public exports

> The contract of this module. What other files can import.

| Export name | Type | Description |
|-------------|------|-------------|
| `UserService` | `class` (default) | Main user management class |
| `formatUser()` | `function` (named) | Transforms raw API user object |
| `USER_ROLES` | `const` (named) | Enum-like object of valid roles |

```js
// Import examples
import UserService from './userService.js';
import { formatUser, USER_ROLES } from './userService.js';
```

---

## 4. Constants & configuration

| Name | Value | Description |
|------|-------|-------------|
| `MAX_RETRIES` | `3` | HTTP retry attempts before failing |
| `CACHE_TTL` | `300000` | Cache time-to-live in ms (5 min) |

---

## 5. Classes

### `ClassName`

**Description:** What does this class represent?

**Constructor**

```js
new ClassName(param1, param2)
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `param1` | `string` | ✅ | — | ... |
| `param2` | `object` | ❌ | `{}` | ... |

**Public properties**

| Property | Type | Description |
|----------|------|-------------|
| `this.id` | `string` | Unique identifier |
| `this.isReady` | `boolean` | Initialization state |

---

#### Methods

##### `methodName(param1, param2)`

- **Description:** ...
- **Parameters:**
  | Param | Type | Required | Description |
  |-------|------|----------|-------------|
  | `param1` | `string` | ✅ | ... |
  | `param2` | `number` | ❌ | ... |
- **Returns:** `Promise<Object>` — description of resolved value
- **Throws:**
  - `TypeError` — when `param1` is not a string
  - `NetworkError` — when the API call fails after `MAX_RETRIES`
- **Side effects:** Mutates `this.cache`, triggers `onUpdate` callback
- **Example:**
  ```js
  const result = await instance.methodName('value', 3);
  console.log(result.data);
  ```

> 🔁 Repeat the method block above for each public method.  
> Private/internal methods don't need this level of detail — a one-liner in section 9 is enough.

---

## 6. Functions (not bound to a class)

### `functionName(param1, param2)`

- **Description:** ...
- **Parameters:**
  | Param | Type | Required | Description |
  |-------|------|----------|-------------|
  | `param1` | `string` | ✅ | ... |
- **Returns:** `string` — description
- **Throws:** `ValidationError` — if param1 is empty
- **Side effects:** None / (describe if any)
- **Example:**
  ```js
  const label = functionName('raw-value');
  // → 'Formatted Value'
  ```

---

## 7. Events / callbacks

> If the module emits events (EventEmitter, CustomEvent, callbacks) list them here.

| Event / callback | When it fires | Payload |
|------------------|---------------|---------|
| `onSuccess(data)` | After successful API call | `{ id, name, status }` |
| `'data:updated'` (EventEmitter) | After cache refresh | `updatedRecords[]` |

---

## 8. Error handling strategy

> How does this module handle and propagate errors?

- All async methods use `try/catch` internally and re-throw as `AppError` with a `code` property.
- Validation errors are thrown synchronously as `ValidationError`.
- Network errors trigger the retry logic (up to `MAX_RETRIES`) before throwing.

**Custom error types used:**

| Error class | Thrown when |
|-------------|-------------|
| `ValidationError` | Input doesn't pass schema check |
| `NetworkError` | Fetch fails after all retries |

---

## 9. Internal notes / design decisions

- **Why this pattern over X:** ...
- **Known trade-offs:** ...
- **Technical debt:** ...
- **Do NOT change without understanding:** ...

---

## 10. TODO

- [ ] ...
- [ ] ...

---

## 11. References

- Related ticket / issue: (link)
- API docs (if this wraps an external API): (link)
- Architecture decision record (ADR): (link)
