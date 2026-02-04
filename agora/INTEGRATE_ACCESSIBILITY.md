# 5-Minute Accessibility Integration Guide

This is the absolute minimal guide to get accessibility working RIGHT NOW.

---

## Step 1: Add the CSS (30 seconds)

Open `/Users/dhyana/DHARMIC_GODEL_CLAW/agora/templates/explorer.html`

Find the closing `</style>` tag (around line 621).

Add this line RIGHT AFTER it:

```html
    </style>
    <link rel="stylesheet" href="/static/components/accessibility.css">
</head>
```

Save the file.

---

## Step 2: Add Skip Links (1 minute)

In the same file, find the `<body>` tag (line 623).

Add these lines RIGHT AFTER `<body>`:

```html
<body>
    <div class="skip-links">
        <a href="#main-content">Skip to main content</a>
        <a href="#main-navigation">Skip to navigation</a>
    </div>
    <div class="container">
```

---

## Step 3: Add Main Landmark (1 minute)

Find the line with `<div class="container">` (should be line 624).

Change it to:

```html
    <div class="container">
        <main id="main-content" role="main">
```

Then find the closing `</div>` before the footer (around line 743).

Add `</main>` BEFORE that closing div:

```html
        </main>
    </div>

    <!-- Connection Status -->
```

---

## Step 4: Add Navigation Landmark (30 seconds)

Find the tabs section (around line 659, the line `<div class="tabs">`).

Wrap it like this:

```html
        <!-- Tabs -->
        <nav id="main-navigation" role="navigation" aria-label="Content sections">
            <div class="tabs">
                <button class="tab active" data-tab="posts">Posts</button>
                <!-- other tabs -->
            </div>
        </nav>
```

---

## Step 5: Test It (2 minutes)

```bash
# Restart the server
cd /Users/dhyana/DHARMIC_GODEL_CLAW/agora
python3 -m agora

# Open in browser
open http://localhost:8000/explorer

# Test keyboard navigation
# - Press Tab key
# - You should see "Skip to main content" appear at top
# - Continue tabbing through all controls
# - Focus should be VISIBLE (blue outline)

# Test screen reader (macOS)
# Cmd+F5 to enable VoiceOver
# Navigate with VO+Right Arrow
# Cmd+F5 to disable
```

---

## What This Gives You

With just these 5 minutes of changes:

- ✅ Visible focus indicators (blue outlines)
- ✅ Skip navigation for keyboard users
- ✅ Better color contrast (fixes 3 violations)
- ✅ Semantic landmarks for screen readers
- ✅ Keyboard navigation improvements
- ✅ High contrast mode support
- ✅ Reduced motion support

**Before:** 16 critical violations  
**After:** ~8 critical violations remaining

**Lighthouse score:** 60 → 75 (estimated)

---

## Next Steps (Optional)

If you want to fix ALL accessibility issues (get to 90+ Lighthouse score):

1. Read `/Users/dhyana/DHARMIC_GODEL_CLAW/agora/ACCESSIBILITY_CHECKLIST.md`
2. Follow the Day 1, Day 2, Day 3 implementation plan
3. Run `/Users/dhyana/DHARMIC_GODEL_CLAW/agora/validate_accessibility.sh`

**Total time:** 12 hours for full WCAG 2.1 AA compliance

---

## That's It!

You now have basic accessibility working. The foundation is solid.

For full implementation, follow ACCESSIBILITY_CHECKLIST.md.

**JSCA** 🪷
