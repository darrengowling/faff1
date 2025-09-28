# Link Linter

## Purpose
Automatically detects placeholder links and empty navigation arrays to prevent incomplete implementations from reaching production.

## Usage

### Standalone
```bash
npm run lint:links
```

### As part of E2E test pipeline
```bash
npm run test:e2e  # Automatically runs lint:links first
```

## What it detects

### 1. Placeholder href links
- `href="#"` - Empty hash links
- `href="/TODO"` - TODO placeholder links

### 2. Empty navigation arrays
- `const navigationItems = []`
- `const menuItems = []`
- `const dropdownItems = []`

### 3. TODO navigation comments
- `/* TODO navigation */`
- `/* FIXME navigation */`

## Example Output

### Success
```
✅ No placeholder links or empty navigation arrays found!
🚀 All navigation appears to be properly implemented.
```

### Failure
```
❌ Found 2 placeholder/navigation issue(s):

🔴 Placeholder href (1 occurrence(s)):
   frontend/src/components/Header.jsx:45:16
   └─ Found placeholder href="#" link
   └─ Code: <a href="#" className="nav-link">
   └─ Match: "href="#""

💡 How to fix:
   • Replace href="#" with proper URLs or onClick handlers
   • Populate empty navigation arrays with actual menu items
```

## CI Integration

The linter runs automatically before E2E tests:
- ❌ **CI fails fast** if placeholders are detected
- ✅ **CI continues** only when all navigation is properly implemented

## Files Scanned
- `frontend/src/**/*.{js,jsx,ts,tsx}`
- `frontend/public/**/*.html`

## Files Excluded
- `**/node_modules/**`
- `**/build/**` 
- `**/test-results/**`
- `**/*.test.{js,jsx,ts,tsx}`
- `**/*.spec.{js,jsx,ts,tsx}`