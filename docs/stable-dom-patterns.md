# Stable DOM Patterns for Critical TestIDs

This document describes the implementation of stable DOM patterns that ensure critical testids are never hidden or removed, making E2E testing more reliable.

## Overview

Critical testids should remain in the DOM even during loading states, disabled states, or conditional rendering. Instead of unmounting elements, we use stable visibility patterns that keep elements accessible to testing tools.

## Implementation Patterns

### 1. Keep Elements Mounted with Disabled States

Instead of:
```jsx
{!loading && (
  <input data-testid="authEmailInput" />
)}
```

Do this:
```jsx
<TestableInput 
  data-testid="authEmailInput"
  loading={loading}  // Adds disabled + aria-disabled
/>
```

### 2. Use Stable Hiding Instead of display:none

Instead of:
```jsx
<div style={{display: hidden ? 'none' : 'block'}}>
  <input data-testid="criticalInput" />
</div>
```

Do this:
```jsx
<TestableInput
  data-testid="criticalInput"
  stableHidden={hidden}  // Uses visibility:hidden + aria-hidden
/>
```

### 3. CSS Classes for Stable Visibility

```css
/* Explicit hidden state - never accidental */
[data-testid][hidden] {
  display: none !important;
}

/* Stable visibility - keeps layout, prevents DOM shifts */
[data-testid].visually-hidden {
  visibility: hidden !important;
  pointer-events: none !important;
  position: relative !important;
}

/* Disabled state styling */
[data-testid][aria-disabled="true"] {
  opacity: 0.6;
  pointer-events: none;
  cursor: not-allowed;
}

/* Loading state styling */
[data-testid].loading {
  opacity: 0.7;
  pointer-events: none;
  position: relative;
}
```

## Testable Components

Enhanced testable components support stable DOM patterns:

### TestableInput
```jsx
<TestableInput
  data-testid="emailInput"
  loading={isSubmitting}      // Disables input, adds loading class
  stableHidden={shouldHide}   // Uses visibility:hidden + aria-hidden
/>
```

### TestableButton  
```jsx
<TestableButton
  data-testid="submitButton"
  loading={isSubmitting}      // Shows disabled state
  disabled={!canSubmit}       // Additional disabled logic
/>
```

## Visibility Detection Rules

The DOM verifier now uses enhanced visibility detection:

### Not Counted as "Present"
- `[hidden]` attribute
- `aria-hidden="true"`
- `.visually-hidden` class
- `display: none`
- `visibility: hidden`
- `opacity: 0`
- Zero dimensions (width=0, height=0)

### Counted as "Present"
- `aria-disabled="true"` (disabled but visible)
- `.loading` class (loading but visible)
- Normal visible elements

## Benefits

### 1. Reliable E2E Testing
- TestIDs always present in DOM
- No timing issues with element mounting
- Consistent selectors across states

### 2. Better User Experience
- Smooth transitions between states
- No layout shifts when elements hide/show
- Clear visual feedback for disabled states

### 3. Accessibility
- Proper ARIA attributes
- Screen reader compatibility
- Keyboard navigation consistency

## Migration Guide

### Step 1: Replace Conditional Rendering
```jsx
// Before
{isLoggedIn && <Button data-testid="logout">Logout</Button>}

// After  
<TestableButton 
  data-testid="logout" 
  stableHidden={!isLoggedIn}
>
  Logout
</TestableButton>
```

### Step 2: Replace Loading States
```jsx
// Before
<input 
  data-testid="emailInput"
  disabled={loading}
/>

// After
<TestableInput 
  data-testid="emailInput" 
  loading={loading}
/>
```

### Step 3: Replace Hidden States
```jsx
// Before
<div style={{display: showAdvanced ? 'block' : 'none'}}>
  <input data-testid="advancedOption" />
</div>

// After
<TestableInput
  data-testid="advancedOption"
  stableHidden={!showAdvanced}
/>
```

## Testing

### Contract Tests
Run `npm run test:contract` to verify testid structure and visibility patterns.

### Stable DOM Tests  
Run `npm run test:stable-dom` to verify elements remain in DOM during state changes.

### E2E Tests
The audit script now properly detects stable hidden elements:
```bash
npm run audit:testids
```

## Examples

### Authentication Form
```jsx
function LoginForm() {
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState('');
  
  return (
    <TestableForm data-testid="loginForm" loading={loading}>
      <TestableInput
        data-testid="authEmailInput"
        value={email}
        onChange={setEmail}
        loading={loading}        // Disabled during submit
        type="email"
        placeholder="Email"
      />
      
      <TestableButton
        data-testid="authSubmitBtn"
        type="submit"
        loading={loading}        // Shows loading state
        disabled={!email}       // Disabled when empty
      >
        {loading ? 'Signing In...' : 'Sign In'}
      </TestableButton>
    </TestableForm>
  );
}
```

### Create League Form
```jsx
function CreateLeagueForm() {
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({});
  
  return (
    <form>
      <TestableInput
        data-testid="createName"
        value={formData.name}
        loading={submitting}    // Keeps input mounted but disabled
        onChange={handleNameChange}
      />
      
      <TestableButton
        data-testid="createSubmit" 
        type="submit"
        loading={submitting}    // Shows creating... state
      >
        {submitting ? 'Creating...' : 'Create League'}
      </TestableButton>
    </form>
  );
}
```

This stable DOM approach ensures that critical UI elements remain testable and accessible throughout all application states.