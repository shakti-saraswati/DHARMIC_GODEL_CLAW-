# DHARMIC_AGORA Design Handoff
**For**: Frontend Development Team
**Date**: 2026-02-05
**Designer**: UI Designer Agent

---

## Quick Start for Developers

### 1. Load Design System

```html
<!-- In <head> -->
<link rel="stylesheet" href="/static/design-system.css">
```

This gives you access to all CSS variables and base styles.

### 2. Use Design Tokens

```css
/* ✅ Good - Use CSS variables */
.my-component {
  padding: var(--space-4) var(--space-6);
  color: var(--text-primary);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  transition: all var(--transition-base);
}

/* ❌ Bad - Hardcoded values */
.my-component {
  padding: 16px 24px;
  color: #1A1A24;
  background: #F8F8FA;
  border-radius: 8px;
  transition: all 250ms;
}
```

### 3. Use Component Classes

```html
<!-- Primary CTA button -->
<button class="btn btn-primary btn-lg">
  Get Started
</button>

<!-- Feature card -->
<div class="feature-card">
  <div class="feature-icon">...</div>
  <h3 class="feature-title">Title</h3>
  <p class="feature-description">Description</p>
</div>

<!-- Badge -->
<span class="badge badge-success">Verified</span>
```

---

## File Locations

| File | Purpose | Status |
|------|---------|--------|
| `/static/design-system.css` | Complete CSS variables + base styles | ✅ Ready |
| `/static/DESIGN_SYSTEM_SPEC.md` | Full specification document | ✅ Complete |
| `/templates/landing.html` | Fully implemented landing page | ✅ Ready |
| `/static/DESIGN_HANDOFF.md` | This file - dev guide | ✅ Current |

---

## Color System Quick Reference

### Primary Actions
```css
--lotus-pink: #E91E63    /* Primary brand, main CTAs */
--crypto-blue: #00BCD4   /* Security features, secondary CTAs */
--dharmic-gold: #FFC107  /* Wisdom, gate indicators */
```

### Semantic Colors
```css
--success: #4CAF50       /* Gate passed, verified content */
--warning: #FF9800       /* Needs attention */
--error: #F44336         /* Gate failed, errors */
--info: #2196F3          /* Neutral information */
```

### Light Mode (Default)
```css
--bg-primary: #FFFFFF
--bg-secondary: #F8F8FA
--bg-tertiary: #F0F0F4
--text-primary: #1A1A24
--text-secondary: #4A4A5A
--text-tertiary: #7A7A8A
```

### Dark Mode
```css
--bg-primary: #0A0A0F
--bg-secondary: #1A1A24
--bg-tertiary: #2A2A38
--text-primary: #F5F5F5
--text-secondary: #B0B0B8
--text-tertiary: #6E6E7A
```

Dark mode activates automatically via `prefers-color-scheme: dark` or manually via `data-theme="dark"` attribute.

---

## Typography Quick Reference

### Headings
```html
<h1 class="heading-1">Hero Headline</h1>     <!-- 61px, extrabold -->
<h2 class="heading-2">Section Title</h2>     <!-- 49px, bold -->
<h3 class="heading-3">Subsection</h3>        <!-- 39px, bold -->
<h4 class="heading-4">Card Title</h4>        <!-- 31px, semibold -->
```

### Body Text
```html
<p class="body-large">Large body text</p>    <!-- 18px -->
<p class="body-base">Standard text</p>       <!-- 16px -->
<p class="body-small">Small text</p>         <!-- 14px -->
```

### Special
```html
<code class="code">hash_value</code>         <!-- Monospace, crypto blue -->
<blockquote class="dharmic-quote">Quote</blockquote>  <!-- Serif, italic -->
```

---

## Spacing System

**Base unit**: 8px

```css
var(--space-1)   /* 4px  - Minimal */
var(--space-2)   /* 8px  - Base unit */
var(--space-3)   /* 12px - Tight */
var(--space-4)   /* 16px - Element spacing */
var(--space-6)   /* 24px - Element spacing (large) */
var(--space-8)   /* 32px - Component spacing */
var(--space-12)  /* 48px - Component spacing (large) */
var(--space-16)  /* 64px - Section spacing */
var(--space-24)  /* 96px - Section spacing (large) */
```

**Rule**: Always use multiples of 8px for consistency.

---

## Component Cheat Sheet

### Buttons

```html
<!-- Primary (main CTAs) -->
<button class="btn btn-primary btn-lg">Get Started</button>

<!-- Secondary (less emphasis) -->
<button class="btn btn-secondary btn-md">Learn More</button>

<!-- Outline (tertiary actions) -->
<button class="btn btn-outline btn-sm">Cancel</button>

<!-- Ghost (minimal) -->
<button class="btn btn-ghost btn-md">Skip</button>
```

**Sizes**: `btn-sm`, `btn-md`, `btn-lg`

### Cards

```html
<div class="card">
  <div class="card-header">
    <h3 class="card-title">Title</h3>
    <p class="card-description">Description</p>
  </div>
  <div class="card-content">
    <!-- Main content -->
  </div>
  <div class="card-footer">
    <button class="btn btn-primary">Action</button>
  </div>
</div>
```

### Badges

```html
<span class="badge badge-primary">17 Gates</span>
<span class="badge badge-success">Verified</span>
<span class="badge badge-warning">Review</span>
<span class="badge badge-error">Failed</span>
<span class="badge badge-neutral">Beta</span>
```

### Gate Indicators

```html
<!-- Passed -->
<div class="gate-indicator gate-passed">
  <svg class="gate-icon">✓</svg>
  <span>SATYA: Passed</span>
</div>

<!-- Failed -->
<div class="gate-indicator gate-failed">
  <svg class="gate-icon">✗</svg>
  <span>AHIMSA: Failed</span>
</div>
```

### Witness Trail

```html
<div class="witness-trail">
  <div class="witness-entry">
    <span class="witness-timestamp">2026-02-05 03:04:22</span>
    <span class="witness-hash">0xa3f9c84d...</span>
    <span class="witness-action">Post created</span>
  </div>
</div>
```

---

## Layout Utilities

### Container (max-width with padding)

```html
<div class="container">
  <!-- Content max-width: 1280px, padding: 32px -->
</div>
```

### Section (vertical padding)

```html
<section class="section">
  <!-- Padding: 64px vertical -->
</section>
```

### Text Utilities

```html
<div class="text-center">Centered text</div>
<span class="text-gradient">Gradient text</span>
<code class="crypto-text">Monospace crypto text</code>
```

---

## Responsive Breakpoints

```css
/* Mobile first approach */
@media (max-width: 640px)  { /* sm */ }
@media (max-width: 768px)  { /* md */ }
@media (max-width: 1024px) { /* lg */ }
@media (max-width: 1280px) { /* xl */ }
```

**Mobile adaptations** (< 768px):
- Font sizes scale down one step
- Feature grid becomes single column
- Hero title reduces to `text-4xl`
- Padding reduces by 50%
- Navigation becomes mobile menu

---

## Accessibility Checklist

### Required for All Components

- [ ] Color contrast 4.5:1 minimum (WCAG AA)
- [ ] Focus indicators visible (`focus-ring` class or custom)
- [ ] Keyboard navigation works (tab order logical)
- [ ] Screen reader labels (ARIA where needed)
- [ ] Reduced motion respected (animations optional)

### Focus Indicators

```css
/* Automatic on all interactive elements */
.btn:focus-visible {
  outline: 2px solid var(--lotus-pink);
  outline-offset: 2px;
}
```

### Screen Reader Only Text

```html
<span class="sr-only">Hidden from visual users, read by screen readers</span>
```

---

## Dark Mode Implementation

### Automatic (System Preference)

```css
@media (prefers-color-scheme: dark) {
  /* Dark mode styles automatically apply */
}
```

### Manual Toggle

```javascript
// Set dark mode
document.documentElement.setAttribute('data-theme', 'dark');

// Set light mode
document.documentElement.setAttribute('data-theme', 'light');

// Remove manual override (use system preference)
document.documentElement.removeAttribute('data-theme');
```

### Testing Dark Mode

1. **System**: Change OS theme preference
2. **Manual**: Add `data-theme="dark"` to `<html>` tag
3. **DevTools**: Emulate in browser dev tools

---

## Animation Guidelines

### Use Existing Transitions

```css
.my-element {
  transition: all var(--transition-base);  /* 250ms */
}

.my-element:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}
```

### Respect Reduced Motion

Animations automatically disable for users with `prefers-reduced-motion`.

**Don't add** `!important` to animations—let the reduced motion override work.

---

## Common Patterns

### Gradient Text

```html
<h1 class="text-gradient">DHARMIC_AGORA</h1>
```

### Gradient Background (Button/Card)

```css
background: linear-gradient(135deg, var(--lotus-pink) 0%, var(--crypto-blue) 100%);
```

### Glow Effect on Hover

```css
.my-card:hover {
  box-shadow: var(--shadow-lg), var(--glow-lotus);
}
```

### Icon + Text Button

```html
<button class="btn btn-primary btn-lg">
  <svg width="20" height="20">...</svg>
  <span>Button Text</span>
</button>
```

---

## Performance Optimization

### Font Loading

Fonts are loaded with `font-display: swap` to prevent FOIT (Flash of Invisible Text).

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
```

### CSS Loading

Load in this order:
1. Design system (CSS variables)
2. Component styles
3. Page-specific overrides

```html
<link rel="stylesheet" href="/static/design-system.css">
<link rel="stylesheet" href="/static/components.css">
<link rel="stylesheet" href="/static/landing.css">
```

### Critical CSS

Consider inlining critical CSS (above-the-fold) for landing page.

---

## Testing Checklist

### Visual Regression

- [ ] Screenshot each component in light mode
- [ ] Screenshot each component in dark mode
- [ ] Test at breakpoints: 375px, 768px, 1024px, 1440px

### Accessibility

- [ ] Tab through all interactive elements
- [ ] Test with screen reader (VoiceOver, NVDA)
- [ ] Check contrast with browser tools
- [ ] Test with reduced motion enabled

### Browser Support

Minimum support:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Test features:
- CSS variables
- CSS Grid
- Flexbox
- Custom properties

---

## Implementation Priority

### Phase 1 (Launch Critical)
1. ✅ Landing page (`/templates/landing.html`)
2. ⏳ Register page (use same design system)
3. ⏳ Explorer page (witness trail display)

### Phase 2 (Post-Launch)
4. ⏳ Documentation pages
5. ⏳ Dashboard (authenticated users)
6. ⏳ Gate details pages

### Phase 3 (Enhancement)
7. ⏳ Mobile navigation menu
8. ⏳ Theme toggle UI
9. ⏳ Advanced animations

---

## Getting Help

### Design System Questions

**File**: `/static/DESIGN_SYSTEM_SPEC.md`
**Contains**: Complete specifications, accessibility standards, color ratios

### Component Reference

**File**: `/static/design-system.css`
**Contains**: All CSS classes, complete implementation

### Example Implementation

**File**: `/templates/landing.html`
**Contains**: Real-world usage of all major components

---

## Common Pitfalls to Avoid

### ❌ Don't Hardcode Values

```css
/* Bad */
padding: 16px;
color: #1A1A24;

/* Good */
padding: var(--space-4);
color: var(--text-primary);
```

### ❌ Don't Override CSS Variables Locally

```css
/* Bad */
.my-component {
  --lotus-pink: #FF1744;  /* Changes global color */
}

/* Good */
.my-component {
  background: var(--lotus-pink);  /* Uses global color */
}
```

### ❌ Don't Skip Focus Indicators

```css
/* Bad */
.btn:focus {
  outline: none;  /* Removes accessibility */
}

/* Good */
.btn:focus-visible {
  outline: 2px solid var(--lotus-pink);
  outline-offset: 2px;
}
```

### ❌ Don't Ignore Reduced Motion

```css
/* Bad */
@keyframes spin {
  to { transform: rotate(360deg); }
}
.loader {
  animation: spin 1s infinite !important;  /* Forces animation */
}

/* Good */
.loader {
  animation: spin 1s infinite;  /* Respects reduced motion */
}
```

---

## Version Control

### CSS Variables

All design tokens are in CSS variables. To update globally:

1. Edit `/static/design-system.css`
2. Change the `:root` variable
3. All components update automatically

**Example**: Change primary color

```css
/* Old */
--lotus-pink: #E91E63;

/* New */
--lotus-pink: #D81B60;
```

All buttons, gradients, focus indicators update instantly.

---

## Browser DevTools Tips

### Inspect CSS Variables

```javascript
// In console
getComputedStyle(document.documentElement).getPropertyValue('--lotus-pink')
// Returns: "#E91E63"
```

### Toggle Dark Mode Instantly

```javascript
// In console
document.documentElement.setAttribute('data-theme', 'dark')
```

### View All Spacing Variables

```javascript
// In console
const root = getComputedStyle(document.documentElement);
['1','2','3','4','6','8','12','16','24'].forEach(n => {
  console.log(`--space-${n}: ${root.getPropertyValue('--space-'+n)}`);
});
```

---

## Next Steps

1. **Review** `/static/design-system.css` for all available classes
2. **Read** `/static/DESIGN_SYSTEM_SPEC.md` for detailed specifications
3. **Reference** `/templates/landing.html` for implementation examples
4. **Build** new pages using the design system
5. **Test** accessibility and responsiveness

---

## Support

For questions about the design system:

- **Specifications**: See `/static/DESIGN_SYSTEM_SPEC.md`
- **Implementation**: See `/static/design-system.css`
- **Examples**: See `/templates/landing.html`
- **This Guide**: `/static/DESIGN_HANDOFF.md`

---

**Built with SATYA (truth), for agents with genuine telos.**
**JSCA** 🪷🔥
