# Remove Legacy JWT Auth System

**Date:** 2026-03-12
**Scope:** Frontend only
**Branch:** feature/remove-legacy-auth

---

## Problem

The legacy JWT auth system coexists with Clerk, creating auth state confusion and dead code. `authStore` is never populated in production (Clerk is the active auth provider), so any legacy checks silently fail. The goal is to remove all legacy JWT code entirely.

---

## Files to Delete

| File | Reason |
|---|---|
| `src/components/AuthGuard.jsx` | JWT-based auth guard; no longer referenced by any page layout |
| `src/components/LoginForm.jsx` | JWT login form; superseded by Clerk's `<SignIn />` page |
| `src/layouts/AuthLayout.astro` | Wraps `AuthGuard`; no pages use it (all use `ClerkAuthLayout`) |
| `src/pages/login.astro` | Meta-redirect to `/sign-in`; dead file |

---

## Files to Modify

### `src/stores/auth.ts`

**Remove:**
- `User` and `AuthState` type definitions
- `authStore` (nanostore map)
- `authLoading` atom
- `authError` atom
- `initAuth()` — reads JWT from localStorage
- `login()` — POST to `/users/login`, stores JWT
- `logout()` — clears localStorage JWT
- `getAuthHeaders()` — builds `Authorization: Bearer` header from JWT store
- All `localStorage.getItem/setItem/removeItem('auth_token' | 'auth_user')` calls

**Keep:**
- `API_BASE_URL` (module-private constant — not exported, used only by `apiRequest`)
- `apiRequest()` function and its `getToken` parameter (Clerk token injection point)

Result: `auth.ts` becomes a thin API request utility with no auth state.

### `src/components/CheckIn.jsx`

**Remove:**
- `authStore` from the `stores/auth` import line
- `useStore` import from `@nanostores/react` (becomes unused once `authStore` is removed; line 46)
- `const auth = useStore(authStore)` declaration (line 207)

**Add import:**
```ts
import { useUser } from '@clerk/astro/react';
```

**Replace `isAdmin()`:**
```ts
// Before
const auth = useStore(authStore);
const isAdmin = () => auth.user?.role === 'admin';

// After
const { user } = useUser();
const isAdmin = () => user?.publicMetadata?.role === 'admin';
```

This matches how Clerk stores user roles (as `publicMetadata.role`) and is consistent with the Clerk package already used elsewhere in the codebase (`@clerk/astro/react`).

---

### `src/test/components/EventForm.test.jsx`

Remove the `authStore` key from the `vi.mock('../../stores/auth', ...)` factory (line 8). After `authStore` is deleted from `auth.ts`, this mock references a non-existent export.

---

## What Is Not Changed

- `apiRequest()` signature is unchanged — all 10+ call sites work as-is
- All test files that mock `apiRequest` are unaffected
- `AuthenticatedApp.jsx` is untouched (already Clerk-only)
- `ClerkAuthLayout.astro` is untouched
- `middleware.ts` is untouched

---

## Verification

After the change:
1. `auth.ts` exports only `apiRequest`
2. No file imports `authStore`, `initAuth`, `login`, `logout`, `authLoading`, `authError`, or `getAuthHeaders`
3. `CheckIn.jsx` uses `useUser()` from `@clerk/astro/react` for the admin check
4. Frontend builds without errors (`npm run build` in `frontend/`)
5. Frontend tests pass (`npm run test:run` in `frontend/`)
