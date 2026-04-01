# Issue 3: Fix Route Protection Gaps Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tighten the Clerk middleware so it skips static assets, and give `index.astro` and `Messaging.astro` a consistent layout by switching them to `ClerkAuthLayout`.

**Architecture:** Two independent fixes. (1) The middleware currently runs Clerk auth on every request including `/_astro/` bundles and static files — add an early-return guard before the route check. (2) `index.astro` and `Messaging.astro` inline the same HTML boilerplate that `ClerkAuthLayout.astro` already provides — replace that duplication with the layout component, matching the pattern used by `Events.astro`, `People.astro`, and `checkin.astro`.

**Tech Stack:** Astro 5 SSR, `@clerk/astro/server` middleware, Astro layouts

**Spec:** `docs/frontend/review.md` — Issue 3

---

## Chunk 1: Fix the middleware static-asset guard

### Task 1: Add early return for static asset requests in `middleware.ts`

**Files:**
- Modify: `frontend/src/middleware.ts`

The current middleware passes every request — including `/_astro/*.js`, `/favicon.svg`, etc. — through Clerk's auth check. Add a guard before the route matcher.

- [ ] **Step 1: Open `frontend/src/middleware.ts` and replace the entire file**

Current contents:
```ts
import { clerkMiddleware, createRouteMatcher } from '@clerk/astro/server';

const isProtectedRoute = createRouteMatcher([
  '/',
  '/Events(.*)',
  '/People(.*)',
  '/Messaging(.*)',
  '/checkin(.*)',
]);

export const onRequest = clerkMiddleware((auth, context) => {
  const { redirectToSignIn, userId } = auth();

  if (!userId && isProtectedRoute(context.request)) {
    return redirectToSignIn();
  }
});
```

Replace with:
```ts
import { clerkMiddleware, createRouteMatcher } from '@clerk/astro/server';

const isProtectedRoute = createRouteMatcher([
  '/',
  '/Events(.*)',
  '/People(.*)',
  '/Messaging(.*)',
  '/checkin(.*)',
]);

const STATIC_ASSET_RE = /\.(?:js|css|svg|ico|png|jpg|jpeg|gif|webp|woff|woff2|ttf|eot|map)$/i;

export const onRequest = clerkMiddleware((auth, context) => {
  const { pathname } = new URL(context.request.url);

  if (pathname.startsWith('/_astro/') || STATIC_ASSET_RE.test(pathname)) {
    return;
  }

  const { redirectToSignIn, userId } = auth();

  if (!userId && isProtectedRoute(context.request)) {
    return redirectToSignIn();
  }
});
```

- [ ] **Step 2: Run the build to confirm no TypeScript errors**

```bash
cd frontend && npm run build
```

Expected: build completes with no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/middleware.ts
git commit -m "fix(frontend): skip static assets in Clerk middleware"
```

---

## Chunk 2: Standardize page layouts

### Task 2: Switch `index.astro` to `ClerkAuthLayout`

**Files:**
- Modify: `frontend/src/pages/index.astro`

`index.astro` currently inlines the same HTML structure (`<html>`, `<head>`, global styles, `NavigationIsland`) that `ClerkAuthLayout.astro` already provides.

- [ ] **Step 1: Replace `frontend/src/pages/index.astro`**

Current file:
```astro
---
import { ViewTransitions } from 'astro:transitions';
import NavigationIsland from '../components/NavigationIsland.jsx';
import IndexWrapper from "../components/IndexWrapper.jsx";
---

<html lang="en">
<head>
  <meta charset="utf-8" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Home - Youtharoot</title>
  <ViewTransitions />
</head>
<body>
  <style is:global>
    html, body {
      background: #181818 !important;
      color: #f5f5f5 !important;
      margin: 0;
      padding: 0;
    }
    html {
      overflow-y: scroll;
    }
    body {
      padding-bottom: 70px;
    }
    @media (min-width: 600px) {
      body {
        padding-bottom: 0;
      }
    }
  </style>

  <NavigationIsland client:only="react" transition:persist="global-nav" />
  <IndexWrapper client:only="react" />
</body>
</html>
```

Replace with:
```astro
---
import ClerkAuthLayout from '../layouts/ClerkAuthLayout.astro';
import IndexWrapper from "../components/IndexWrapper.jsx";
---

<ClerkAuthLayout title="Home - Youtharoot">
  <IndexWrapper client:only="react" />
</ClerkAuthLayout>
```

- [ ] **Step 2: Run the build**

```bash
cd frontend && npm run build
```

Expected: build completes with no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/index.astro
git commit -m "refactor(frontend): use ClerkAuthLayout in index page"
```

---

### Task 3: Switch `Messaging.astro` to `ClerkAuthLayout`

**Files:**
- Modify: `frontend/src/pages/Messaging.astro`

`Messaging.astro` has the same duplicated boilerplate as `index.astro` did.

- [ ] **Step 1: Replace `frontend/src/pages/Messaging.astro`**

Current file:
```astro
---
import { ViewTransitions } from 'astro:transitions';
import NavigationIsland from '../components/NavigationIsland.jsx';
import MessagingPageWrapper from "../components/MessagingPageWrapper.jsx";

const title = 'SMS Messaging - Youtharoot';
---

<html lang="en">
<head>
  <meta charset="utf-8" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <ViewTransitions />
</head>
<body>
  <style is:global>
    html, body {
      background: #181818 !important;
      color: #f5f5f5 !important;
      margin: 0;
      padding: 0;
    }
    html {
      overflow-y: scroll;
    }
    body {
      padding-bottom: 70px;
    }
    @media (min-width: 600px) {
      body {
        padding-bottom: 0;
      }
    }
  </style>

  <NavigationIsland client:only="react" transition:persist="global-nav" />
  <MessagingPageWrapper client:only="react" />
</body>
</html>
```

Replace with:
```astro
---
import ClerkAuthLayout from '../layouts/ClerkAuthLayout.astro';
import MessagingPageWrapper from "../components/MessagingPageWrapper.jsx";
---

<ClerkAuthLayout title="SMS Messaging - Youtharoot">
  <MessagingPageWrapper client:only="react" />
</ClerkAuthLayout>
```

- [ ] **Step 2: Run the build**

```bash
cd frontend && npm run build
```

Expected: build completes with no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Messaging.astro
git commit -m "refactor(frontend): use ClerkAuthLayout in Messaging page"
```

---

## Verification Checklist

After all tasks complete:

```bash
# 1. Middleware has the static asset guard
grep "STATIC_ASSET_RE\|_astro" frontend/src/middleware.ts

# 2. All protected pages use ClerkAuthLayout — expected: 5 results
grep -l "ClerkAuthLayout" frontend/src/pages/*.astro

# 3. No page inlines the global dark-theme styles anymore
grep -l "background: #181818" frontend/src/pages/*.astro

# 4. Build passes
cd frontend && npm run build
```

Expected state after completion:
- `middleware.ts` skips static assets before running auth
- All 5 protected pages (`index`, `Events`, `People`, `Messaging`, `checkin`) use `ClerkAuthLayout`
- No duplicated layout HTML in page files
