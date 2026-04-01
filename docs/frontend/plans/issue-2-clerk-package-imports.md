# Issue 2: Standardize Clerk Package Imports Implementation Plan
Status: Complete

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all `@clerk/clerk-react` usage and delete two dead files that were its only consumers, leaving `@clerk/astro/react` as the sole Clerk React package.

**Architecture:** `AuthenticatedContent.jsx` and `ClerkProviderWrapper.jsx` are dead files (never imported by any live code) that happen to be the only remaining callers of `@clerk/clerk-react`. Deleting them and removing the package dependency is all that's needed. `CheckIn.jsx` previously used `useUser` from `@clerk/clerk-react` — this was already fixed (uses `window.Clerk` now). No code changes to live components are required.

**Tech Stack:** Astro 5 SSR, React, `@clerk/astro`, `@clerk/astro/react`, npm

**Spec:** `docs/frontend/review.md` — Issue 2

---

## Chunk 1: Verify dead files are truly unused, then delete them

### Task 1: Confirm no live code imports the two dead files

Before deleting, verify nothing imports them.

- [ ] **Step 1: Search for imports of `AuthenticatedContent`**

```bash
grep -rn "AuthenticatedContent" frontend/src \
  --include="*.astro" --include="*.jsx" --include="*.tsx" --include="*.ts" --include="*.js"
```

Expected: no output (file exists but is not imported anywhere).

- [ ] **Step 2: Search for imports of `ClerkProviderWrapper`**

```bash
grep -rn "ClerkProviderWrapper" frontend/src \
  --include="*.astro" --include="*.jsx" --include="*.tsx" --include="*.ts" --include="*.js"
```

Expected: no output.

- [ ] **Step 3: Search for any remaining `@clerk/clerk-react` imports**

```bash
grep -rn "@clerk/clerk-react" frontend/src \
  --include="*.astro" --include="*.jsx" --include="*.tsx" --include="*.ts" --include="*.js"
```

Expected: exactly 2 results — the dead files (`AuthenticatedContent.jsx` and `ClerkProviderWrapper.jsx`). If any other file shows up, stop and investigate before proceeding.

---

### Task 2: Delete the two dead files

- [ ] **Step 1: Delete `AuthenticatedContent.jsx`**

```bash
git rm frontend/src/components/AuthenticatedContent.jsx
```

- [ ] **Step 2: Delete `ClerkProviderWrapper.jsx`**

```bash
git rm frontend/src/components/ClerkProviderWrapper.jsx
```

- [ ] **Step 3: Verify `@clerk/clerk-react` is now completely unused**

```bash
grep -rn "@clerk/clerk-react" frontend/src \
  --include="*.astro" --include="*.jsx" --include="*.tsx" --include="*.ts" --include="*.js"
```

Expected: no output.

- [ ] **Step 4: Run tests**

```bash
cd frontend && npm run test:run
```

Expected: no new failures beyond the pre-existing 37 failures in `GroupList`, `GroupMemberManager`, `MessageHistory`, and `MessageForm` tests.

- [ ] **Step 5: Commit**

```bash
git commit -m "chore(frontend): delete dead AuthenticatedContent and ClerkProviderWrapper components"
```

---

## Chunk 2: Remove the unused package dependency

### Task 3: Uninstall `@clerk/clerk-react`

- [ ] **Step 1: Remove the package**

```bash
cd frontend && npm uninstall @clerk/clerk-react
```

- [ ] **Step 2: Verify it is gone from `package.json`**

```bash
grep "clerk-react" frontend/package.json
```

Expected: no output.

- [ ] **Step 3: Run the production build to confirm nothing breaks**

```bash
cd frontend && npm run build
```

Expected: build completes with no errors.

- [ ] **Step 4: Run tests**

```bash
cd frontend && npm run test:run
```

Expected: same result as after Task 2 (no new failures).

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore(frontend): remove unused @clerk/clerk-react dependency"
```

---

## Verification Checklist

After both chunks are complete:

```bash
# 1. No @clerk/clerk-react in source — expected: no output
grep -rn "@clerk/clerk-react" frontend/src

# 2. Not in package.json — expected: no output
grep "clerk-react" frontend/package.json

# 3. Dead files are gone — expected: errors (files not found)
ls frontend/src/components/AuthenticatedContent.jsx 2>&1
ls frontend/src/components/ClerkProviderWrapper.jsx 2>&1

# 4. Build passes
cd frontend && npm run build
```
