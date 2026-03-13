# Remove Legacy JWT Auth System Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all legacy JWT auth code from the frontend, leaving Clerk as the sole auth provider.

**Architecture:** Delete four dead files (AuthGuard, LoginForm, AuthLayout, login.astro), strip `auth.ts` down to just the `apiRequest` utility, update `CheckIn.jsx` to use Clerk's `useUser()` for the admin role check, and clean up a stale test mock.

**Tech Stack:** Astro 5 SSR, React islands, Clerk (`@clerk/astro/react`), Nanostores, Vitest, Material UI v7.

**Spec:** `docs/superpowers/specs/2026-03-12-remove-legacy-auth-design.md`

---

## Chunk 1: Branch + Delete Dead Files

### Task 1: Create the feature branch

- [ ] **Step 1: Create and switch to the branch**

```bash
git checkout -b feature/remove-legacy-auth
```

Expected: `Switched to a new branch 'feature/remove-legacy-auth'`

---

### Task 2: Establish a passing test baseline

Before changing anything, confirm the tests are green.

- [ ] **Step 1: Run the frontend test suite**

```bash
cd frontend && npm run test:run
```

Expected: all tests pass. If any are already failing, note them before proceeding — you are not responsible for pre-existing failures.

---

### Task 3: Delete the four dead files

These files have no live dependents. Verify after each deletion that no import of them remains in the codebase.

- [ ] **Step 1: Delete `AuthGuard.jsx`**

```bash
rm frontend/src/components/AuthGuard.jsx
```

- [ ] **Step 2: Delete `LoginForm.jsx`**

```bash
rm frontend/src/components/LoginForm.jsx
```

- [ ] **Step 3: Delete `AuthLayout.astro`**

```bash
rm frontend/src/layouts/AuthLayout.astro
```

- [ ] **Step 4: Delete `login.astro`**

```bash
rm frontend/src/pages/login.astro
```

- [ ] **Step 5: Verify no remaining imports**

```bash
grep -r "AuthGuard\|LoginForm\|AuthLayout\|login\.astro" frontend/src \
  --include="*.astro" --include="*.jsx" --include="*.tsx" --include="*.ts" --include="*.js"
```

Expected: no output.

- [ ] **Step 6: Run tests to confirm nothing broke**

```bash
cd frontend && npm run test:run
```

Expected: same result as the baseline (all passing, or same pre-existing failures only).

- [ ] **Step 7: Commit**

```bash
git rm frontend/src/components/AuthGuard.jsx \
       frontend/src/components/LoginForm.jsx \
       frontend/src/layouts/AuthLayout.astro \
       frontend/src/pages/login.astro
git commit -m "chore(frontend): delete legacy auth components and layouts"
```

---

## Chunk 2: Strip `auth.ts` + Update `CheckIn.jsx` + Fix Test Mock

### Task 4: Strip `auth.ts` to just `apiRequest`

`frontend/src/stores/auth.ts` currently exports JWT auth state and functions that are unused now that Clerk is the auth provider. Replace the entire file with only the `apiRequest` utility.

> **Note:** The existing `apiRequest` body contains several `console.debug`/`console.log` calls (production debug logging). The replacement below intentionally removes them — this is cleanup per the review doc (Issue 6). If you need to preserve them temporarily, copy them from the original before overwriting.

- [ ] **Step 1: Replace `auth.ts` with the stripped version**

Open `frontend/src/stores/auth.ts` and replace the entire contents with:

```typescript
/**
 * API request utility
 */

// API base URL
const API_BASE_URL = import.meta.env.PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Make an authenticated API request.
 * @param endpoint - API endpoint path (e.g. "/people")
 * @param options - Fetch options
 * @param getToken - Clerk session token getter (from useAuth().getToken)
 */
export async function apiRequest(
  endpoint: string,
  options: RequestInit = {},
  getToken?: () => Promise<string | null>
) {
  let token = null;
  if (getToken) {
    token = await getToken();
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers as Record<string, string>,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    if (typeof window !== 'undefined') {
      window.location.href = '/sign-in';
    }
    throw new Error('Authentication required');
  }

  return response;
}
```

- [ ] **Step 2: Verify no legacy symbols are exported**

```bash
grep -n "authStore\|authLoading\|authError\|initAuth\|^export.*login\|^export.*logout\|getAuthHeaders\|auth_token\|auth_user" frontend/src/stores/auth.ts
```

Expected: no output.

- [ ] **Step 3: Run tests**

```bash
cd frontend && npm run test:run
```

Expected: all tests still pass.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/stores/auth.ts
git commit -m "refactor(frontend): strip auth.ts to apiRequest utility only"
```

---

### Task 5: Update `CheckIn.jsx` to use Clerk's `useUser()`

`CheckIn.jsx` uses `authStore` solely for an admin role check. Replace it with Clerk's `useUser()` hook.

- [ ] **Step 1: Confirm `useStore` has no other callers in `CheckIn.jsx`**

```bash
grep -n "useStore" frontend/src/components/CheckIn.jsx
```

Expected: exactly 2 lines — the import (line 46) and `const auth = useStore(authStore)` (line ~207). If any other `useStore(...)` calls exist, do not remove the `useStore` import in the next step.

- [ ] **Step 2: Update the import lines in `CheckIn.jsx`**

Find and replace in `frontend/src/components/CheckIn.jsx`:

**Remove** (line 45–46):
```js
import { apiRequest, authStore } from '../stores/auth';
import { useStore } from '@nanostores/react';
```

**Replace with:**
```js
import { apiRequest } from '../stores/auth';
import { useUser } from '@clerk/astro/react';
```

- [ ] **Step 3: Replace the auth state usage in the component body**

Find and remove (line ~207):
```js
  const auth = useStore(authStore);
```

Add in its place (inside the component, near other hook calls at the top):
```js
  const { user } = useUser();
```

- [ ] **Step 4: Replace the `isAdmin` function**

Find (lines ~514–516):
```js
  const isAdmin = () => {
    return auth.user?.role === 'admin';
  };
```

Replace with:
```js
  const isAdmin = () => {
    return user?.publicMetadata?.role === 'admin';
  };
```

- [ ] **Step 5: Verify no remaining `authStore` or `useStore` references in CheckIn.jsx**

```bash
grep -n "authStore\|useStore\|auth\.user" frontend/src/components/CheckIn.jsx
```

Expected: no output.

- [ ] **Step 6: Verify no file in the codebase still imports legacy auth symbols**

```bash
grep -rn "authStore\|initAuth\|authLoading\|authError\|getAuthHeaders" frontend/src \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" --include="*.astro"
```

Expected: no output.

- [ ] **Step 7: Run tests**

```bash
cd frontend && npm run test:run
```

Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/CheckIn.jsx
git commit -m "refactor(frontend): replace authStore admin check with Clerk useUser()"
```

---

### Task 6: Remove stale `authStore` mock from `EventForm.test.jsx`

`EventForm.test.jsx` mocks `authStore` in its `vi.mock` factory. That export no longer exists in `auth.ts`, so the mock key should be removed.

- [ ] **Step 1: Update the mock in `frontend/src/test/components/EventForm.test.jsx`**

Find (lines 6–11):
```js
vi.mock('../../stores/auth', () => ({
  apiRequest: vi.fn(),
  authStore: {
    get: () => ({ isAuthenticated: true, user: { role: 'admin' } })
  }
}));
```

Replace with:
```js
vi.mock('../../stores/auth', () => ({
  apiRequest: vi.fn(),
}));
```

- [ ] **Step 2: Run tests**

```bash
cd frontend && npm run test:run
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/test/components/EventForm.test.jsx
git commit -m "test(frontend): remove stale authStore mock from EventForm tests"
```

---

## Chunk 3: Build Verification

### Task 7: Verify the full build

- [ ] **Step 1: Run the production build**

```bash
cd frontend && npm run build
```

Expected: build completes with no errors. TypeScript type errors count as failures.

- [ ] **Step 2: Confirm spec verification checklist**

```bash
# 1. auth.ts exports only apiRequest — expected: one line containing "export async function apiRequest"
grep -n "^export" frontend/src/stores/auth.ts

# 2. No file imports legacy auth symbols — expected: no output
grep -rn "authStore\|initAuth\|authLoading\|authError\|getAuthHeaders\|auth_token\|auth_user" \
  frontend/src \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" --include="*.astro"

# 3. CheckIn.jsx uses useUser — expected: two lines (the import and the useUser() call)
grep -n "useUser" frontend/src/components/CheckIn.jsx
```

- [ ] **Step 3: If build passes, the branch is ready for PR**

```bash
git log --oneline feature/remove-legacy-auth ^main
```

Expected: 4 commits listed (Tasks 3, 4, 5, 6 — assumes Chunk 1 was already executed on this branch).
