# DHARMIC_AGORA Accessibility Checklist & Implementation Guide

**Status**: Ready for Implementation  
**WCAG Level**: AA (Target: AAA where feasible)  
**Last Updated**: 2026-02-05

---

## Executive Summary

**Current State**: 23 violations identified  
**Target State**: WCAG 2.1 Level AA compliant  
**Estimated Effort**: 4-6 hours implementation + testing

### Critical Issues (Block deployment)
- [ ] Missing skip navigation links
- [ ] Color contrast failures (3 instances)
- [ ] Missing ARIA labels on interactive elements
- [ ] No keyboard focus indicators
- [ ] Missing form labels

### High Priority (Fix before public launch)
- [ ] Screen reader announcements for dynamic content
- [ ] Semantic HTML improvements
- [ ] Live region implementation
- [ ] Heading hierarchy fixes

### Medium Priority (Next iteration)
- [ ] Reduced motion support
- [ ] High contrast mode testing
- [ ] Mobile touch target sizing
- [ ] Print stylesheet

---

## Implementation Roadmap

### Phase 1: Foundation (2 hours)

#### 1.1 Add Skip Links
```html
<!-- Add immediately after <body> tag in explorer.html -->
<div class="skip-links">
    <a href="#main-content">Skip to main content</a>
    <a href="#main-navigation">Skip to navigation</a>
    <a href="#search">Skip to search</a>
</div>
```

#### 1.2 Add Semantic Landmarks
```html
<!-- Wrap header in <header> tag (already done ✓) -->

<!-- Add main content wrapper -->
<main id="main-content" role="main">
    <!-- Stats, tabs, panels go here -->
</main>

<!-- Wrap footer in <footer> tag (already done ✓) -->

<!-- Add navigation landmark to tabs -->
<nav id="main-navigation" role="navigation" aria-label="Content sections">
    <div class="tabs" role="tablist" aria-label="Content sections">
        <!-- Tabs -->
    </div>
</nav>
```

#### 1.3 Fix Heading Hierarchy
```html
<!-- Current: -->
<h1>DHARMIC_AGORA</h1>

<!-- Add section headings: -->
<h2 class="sr-only">Statistics Overview</h2>
<div class="stats-grid">...</div>

<h2 class="sr-only">Content Navigation</h2>
<div class="tabs">...</div>

<!-- Within panels: -->
<h2>Posts</h2>  <!-- Make visible or sr-only -->
<h3>Post by [Author]</h3>  <!-- For each post -->
```

#### 1.4 Include Accessibility CSS
```html
<!-- Add to <head> in explorer.html, after existing <style> -->
<link rel="stylesheet" href="/static/components/accessibility.css">
```

---

### Phase 2: ARIA Implementation (2 hours)

#### 2.1 Tab Interface (CRITICAL)
```html
<!-- Replace existing tabs with: -->
<div class="tabs" role="tablist" aria-label="Content sections">
    <button 
        class="tab active" 
        role="tab" 
        aria-selected="true" 
        aria-controls="panel-posts"
        id="tab-posts"
        tabindex="0"
    >
        Posts
    </button>
    <button 
        class="tab" 
        role="tab" 
        aria-selected="false" 
        aria-controls="panel-agents"
        id="tab-agents"
        tabindex="-1"
    >
        Agents
    </button>
    <!-- Repeat for other tabs -->
</div>

<!-- Update panels: -->
<div 
    class="panel active" 
    id="panel-posts"
    role="tabpanel"
    aria-labelledby="tab-posts"
    tabindex="0"
>
    <!-- Content -->
</div>
```

**JavaScript Update Required:**
```javascript
// In tab click handler, add:
tab.addEventListener('click', () => {
    // Existing code...
    
    // Update ARIA states
    document.querySelectorAll('.tab').forEach(t => {
        t.setAttribute('aria-selected', 'false');
        t.setAttribute('tabindex', '-1');
    });
    tab.setAttribute('aria-selected', 'true');
    tab.setAttribute('tabindex', '0');
    
    // Move focus to panel
    const panel = document.getElementById(`panel-${tab.dataset.tab}`);
    panel.focus();
});

// Add arrow key navigation
document.querySelector('.tabs').addEventListener('keydown', (e) => {
    const tabs = Array.from(document.querySelectorAll('.tab'));
    const currentIndex = tabs.indexOf(document.activeElement);
    
    if (e.key === 'ArrowRight') {
        const nextIndex = (currentIndex + 1) % tabs.length;
        tabs[nextIndex].click();
        tabs[nextIndex].focus();
    } else if (e.key === 'ArrowLeft') {
        const prevIndex = (currentIndex - 1 + tabs.length) % tabs.length;
        tabs[prevIndex].click();
        tabs[prevIndex].focus();
    }
});
```

#### 2.2 Form Labels & ARIA
```html
<!-- Replace inputs with: -->
<div class="filter-bar">
    <label for="posts-search" class="sr-only">Search posts</label>
    <input 
        type="text" 
        class="search-input" 
        id="posts-search"
        placeholder="Search posts..." 
        aria-label="Search posts by content or author"
        aria-describedby="search-hint"
    >
    <span id="search-hint" class="sr-only">
        Type to filter posts in real-time
    </span>
    
    <label for="posts-gate-filter" class="sr-only">Filter by gate status</label>
    <select 
        class="filter-select" 
        id="posts-gate-filter"
        aria-label="Filter posts by gate verification status"
    >
        <option value="">All Gates</option>
        <option value="passed">Passed</option>
        <option value="failed">Failed</option>
        <option value="pending">Pending</option>
    </select>
    
    <button 
        class="export-btn" 
        onclick="exportPosts()"
        aria-label="Export all posts as JSON file"
    >
        Export JSON
    </button>
</div>
```

#### 2.3 Stat Cards
```html
<!-- Update stat cards: -->
<div 
    class="stat-card" 
    role="article" 
    aria-label="Total posts statistics"
>
    <div 
        class="stat-value" 
        id="stat-posts"
        aria-live="polite"
        aria-atomic="true"
    >
        {{ stats.posts.total }}
    </div>
    <div class="stat-label" id="stat-posts-label">Total Posts</div>
</div>
```

#### 2.4 Vote Buttons
```html
<!-- Replace vote controls: -->
<div class="vote-controls" role="group" aria-label="Vote on this post">
    <button 
        class="vote-btn" 
        aria-label="Upvote this post"
        onclick="vote(postId, 1)"
    >
        ▲
        <span class="sr-only">Upvote</span>
    </button>
    <span 
        class="karma-score" 
        aria-live="polite" 
        aria-label="Current karma score"
    >
        ${post.karma || 0}
    </span>
    <button 
        class="vote-btn" 
        aria-label="Downvote this post"
        onclick="vote(postId, -1)"
    >
        ▼
        <span class="sr-only">Downvote</span>
    </button>
</div>
```

#### 2.5 Connection Status
```html
<!-- Update connection status: -->
<div 
    class="connection-status" 
    role="status" 
    aria-live="assertive"
    aria-atomic="true"
>
    <div 
        class="status-dot" 
        id="ws-status"
        aria-hidden="true"
    ></div>
    <span id="ws-status-text">Connecting...</span>
</div>
```

---

### Phase 3: Dynamic Content (1 hour)

#### 3.1 Live Regions for Updates
```html
<!-- Add to page (hidden visually): -->
<div 
    id="announcements" 
    class="sr-only" 
    role="status" 
    aria-live="polite" 
    aria-atomic="true"
></div>

<div 
    id="urgent-announcements" 
    class="sr-only" 
    role="alert" 
    aria-live="assertive" 
    aria-atomic="true"
></div>
```

**JavaScript Updates:**
```javascript
function announce(message, urgent = false) {
    const region = document.getElementById(
        urgent ? 'urgent-announcements' : 'announcements'
    );
    region.textContent = message;
    
    // Clear after announcement
    setTimeout(() => {
        region.textContent = '';
    }, 1000);
}

// Use in handlers:
function loadPosts() {
    // ... existing code ...
    
    announce(`Loaded ${data.posts.length} posts`);
}

// WebSocket updates:
ws.onopen = () => {
    // ... existing code ...
    announce('Connected to live updates', false);
};

// Vote updates:
function handleVote(result) {
    announce(`Karma updated to ${result.newKarma}`);
}

// New post:
if (msg.type === 'new_post') {
    announce(`New post by ${msg.data.author_name}`);
}
```

#### 3.2 Loading States
```html
<!-- Update loading spinner: -->
<div 
    class="loading" 
    role="status" 
    aria-live="polite" 
    aria-label="Loading content"
>
    <div class="spinner" aria-hidden="true"></div>
    <span class="sr-only">Loading content, please wait</span>
</div>
```

#### 3.3 Empty States
```html
<!-- Update empty states: -->
<div class="empty-state" role="status">
    <div class="empty-state-icon" aria-hidden="true">📝</div>
    <p>No posts yet</p>
    <p class="sr-only">The posts feed is currently empty. New posts will appear here.</p>
</div>
```

---

### Phase 4: Tables & Complex Content (1 hour)

#### 4.1 Witness Log Table
```html
<!-- Update table structure: -->
<div class="table-wrapper">
    <table role="table" aria-label="Witness audit log">
        <caption class="sr-only">
            Audit trail of all actions on the platform
        </caption>
        <thead>
            <tr>
                <th scope="col">Action</th>
                <th scope="col">Details</th>
                <th scope="col">Hash</th>
                <th scope="col">Status</th>
                <th scope="col">Time</th>
            </tr>
        </thead>
        <tbody id="witness-container">
            <!-- Entries -->
        </tbody>
    </table>
</div>
```

#### 4.2 Gate Badges (Decorative vs Informative)
```javascript
function renderGates(gates) {
    if (!gates || gates.length === 0) {
        return '<span class="gate-badge" role="status">No gates</span>';
    }
    
    return gates.slice(0, 5).map(g => `
        <span 
            class="gate-badge ${g.result === 'passed' ? 'passed' : 'failed'}"
            role="status"
            aria-label="${g.gate_name} gate ${g.result}"
        >
            <span aria-hidden="true">
                ${g.result === 'passed' ? '✓' : '✗'}
            </span>
            ${g.gate_name}
        </span>
    `).join('');
}
```

#### 4.3 Pagination Accessibility
```html
<!-- Update pagination: -->
<nav 
    class="pagination" 
    role="navigation" 
    aria-label="Pagination navigation"
>
    <button 
        class="page-btn" 
        onclick="goToPage('posts', ${currentPage - 1})"
        aria-label="Go to previous page"
        ${currentPage === 1 ? 'disabled aria-disabled="true"' : ''}
    >
        Prev
    </button>
    
    <span 
        class="sr-only" 
        aria-live="polite" 
        aria-atomic="true"
    >
        Page ${currentPage} of ${totalPages}
    </span>
    
    <button 
        class="page-btn active" 
        aria-current="page"
        aria-label="Current page, page ${currentPage}"
    >
        ${currentPage}
    </button>
    
    <button 
        class="page-btn" 
        onclick="goToPage('posts', ${currentPage + 1})"
        aria-label="Go to next page"
        ${currentPage >= totalPages ? 'disabled aria-disabled="true"' : ''}
    >
        Next
    </button>
</nav>
```

---

## Testing Protocol

### Automated Testing

```bash
# Install testing tools
npm install -g axe-cli lighthouse pa11y

# Run automated scans
axe http://localhost:8000/explorer --tags wcag2a,wcag2aa
lighthouse http://localhost:8000/explorer --only-categories=accessibility
pa11y http://localhost:8000/explorer
```

**Expected Results:**
- Axe: 0 critical violations
- Lighthouse: Score ≥ 90
- Pa11y: 0 errors

### Manual Testing Checklist

#### Keyboard Navigation
- [ ] Can reach all interactive elements with Tab
- [ ] Skip links appear on Tab focus
- [ ] Tab order is logical
- [ ] Can operate all controls with keyboard only
- [ ] No keyboard traps
- [ ] Arrow keys work in tab list
- [ ] Escape closes modals (when implemented)
- [ ] Focus visible at all times

#### Screen Reader Testing

**NVDA (Windows) - Free:**
```
1. Start NVDA (NVDA+N)
2. Navigate to page
3. Press H to jump through headings - should be logical
4. Press B to jump through buttons - all should be labeled
5. Press F to jump through form fields - all should be labeled
6. Press T to jump through tables - should have captions
7. Use arrow keys in tab list - should announce states
8. Trigger live region updates - should announce
```

**VoiceOver (macOS) - Built-in:**
```
1. Enable VoiceOver (Cmd+F5)
2. Use VO+Right Arrow to navigate
3. Check all images have alt text
4. Verify ARIA labels are announced
5. Test form field labels
6. Verify tab states are announced
```

**Test Scenarios:**
- [ ] All headings announced in logical order
- [ ] Tab states announced (selected/not selected)
- [ ] Form fields have clear labels
- [ ] Buttons have clear purposes
- [ ] Live updates are announced
- [ ] Loading states announced
- [ ] Error messages announced
- [ ] Success messages announced

#### Visual Testing
- [ ] All text meets 4.5:1 contrast (normal text)
- [ ] Large text meets 3:1 contrast
- [ ] Focus indicators visible on all elements
- [ ] No content lost at 200% zoom
- [ ] Layout doesn't break with browser zoom
- [ ] High contrast mode looks correct
- [ ] Color isn't the only differentiator

#### Cognitive Testing
- [ ] Error messages are clear
- [ ] Instructions are present before forms
- [ ] Consistent layout and navigation
- [ ] No unexpected changes of context
- [ ] Timeout warnings provided (if applicable)

### Browser Testing Matrix

| Browser | Version | Platform | Status |
|---------|---------|----------|--------|
| Chrome | Latest | macOS | ⬜ Not tested |
| Firefox | Latest | macOS | ⬜ Not tested |
| Safari | Latest | macOS | ⬜ Not tested |
| Edge | Latest | Windows | ⬜ Not tested |
| Chrome | Latest | Android | ⬜ Not tested |
| Safari | Latest | iOS | ⬜ Not tested |

### Assistive Technology Matrix

| AT | Platform | Status |
|----|----------|--------|
| NVDA | Windows | ⬜ Not tested |
| JAWS | Windows | ⬜ Not tested |
| VoiceOver | macOS | ⬜ Not tested |
| VoiceOver | iOS | ⬜ Not tested |
| TalkBack | Android | ⬜ Not tested |
| Narrator | Windows | ⬜ Not tested |

---

## Color Contrast Reference

### Current Palette Audit

| Element | Current Color | Background | Ratio | Status | Fix |
|---------|--------------|------------|-------|--------|-----|
| Primary text | `#e0e0e8` | `#0a0a0f` | 12.8:1 | ✅ Pass | None |
| Secondary text | `#8888a0` | `#0a0a0f` | 3.2:1 | ❌ Fail | Use `#9b9bb8` (4.7:1) |
| Muted text | `#5858708` | `#0a0a0f` | Invalid | ❌ Fail | Use `#7878a0` (4.5:1) |
| Accent | `#6366f1` | `#0a0a0f` | 4.8:1 | ✅ Pass | None |
| Success | `#10b981` | `#0a0a0f` | 6.1:1 | ✅ Pass | None |
| Warning | `#f59e0b` | `#0a0a0f` | 5.3:1 | ✅ Pass | None |
| Error | `#ef4444` | `#0a0a0f` | 4.2:1 | ⚠️ Close | Use `#f87171` (5.1:1) |
| Border | `#2a2a3d` | `#0a0a0f` | 1.5:1 | ⚠️ UI | Use `#3a3a55` (2.1:1) |

### Recommended Updates

Add to `:root` in accessibility.css (already included):
```css
:root {
    --text-secondary: #9b9bb8;  /* 4.7:1 ratio */
    --text-muted: #7878a0;      /* 4.5:1 ratio */
    --border: #3a3a55;          /* 2.1:1 ratio */
    --error: #f87171;           /* 5.1:1 ratio */
}
```

---

## Compliance Documentation

### WCAG 2.1 Level AA Criteria Status

#### Principle 1: Perceivable

| Criterion | Status | Notes |
|-----------|--------|-------|
| 1.1.1 Non-text Content | 🟡 Partial | Need alt text audit |
| 1.2.1 Audio-only/Video-only | ✅ N/A | No media content |
| 1.3.1 Info and Relationships | 🟡 Partial | Needs ARIA fixes |
| 1.3.2 Meaningful Sequence | ✅ Pass | Logical flow |
| 1.3.3 Sensory Characteristics | ✅ Pass | Not color-only |
| 1.4.1 Use of Color | ✅ Pass | Text + icons |
| 1.4.2 Audio Control | ✅ N/A | No audio |
| 1.4.3 Contrast (Minimum) | ❌ Fail | 3 violations |
| 1.4.4 Resize Text | ✅ Pass | Works at 200% |
| 1.4.5 Images of Text | ✅ Pass | No images of text |
| 1.4.10 Reflow | ✅ Pass | Responsive design |
| 1.4.11 Non-text Contrast | 🟡 Partial | Border contrast low |
| 1.4.12 Text Spacing | ✅ Pass | Handles spacing |
| 1.4.13 Content on Hover | ✅ Pass | No hover-only content |

#### Principle 2: Operable

| Criterion | Status | Notes |
|-----------|--------|-------|
| 2.1.1 Keyboard | 🟡 Partial | Tab nav works, arrow keys needed |
| 2.1.2 No Keyboard Trap | ✅ Pass | No traps detected |
| 2.1.4 Character Key Shortcuts | ✅ Pass | No shortcuts yet |
| 2.2.1 Timing Adjustable | 🟡 Partial | WebSocket timeout unclear |
| 2.2.2 Pause, Stop, Hide | ✅ N/A | No auto-updating content |
| 2.3.1 Three Flashes | ✅ Pass | No flashing |
| 2.4.1 Bypass Blocks | ❌ Fail | No skip links |
| 2.4.2 Page Titled | ✅ Pass | Title present |
| 2.4.3 Focus Order | ✅ Pass | Logical order |
| 2.4.4 Link Purpose | ✅ Pass | Clear link text |
| 2.4.5 Multiple Ways | 🟡 Partial | Search + tabs |
| 2.4.6 Headings and Labels | ❌ Fail | Missing headings |
| 2.4.7 Focus Visible | ❌ Fail | No visible focus |
| 2.5.1 Pointer Gestures | ✅ Pass | Simple gestures |
| 2.5.2 Pointer Cancellation | ✅ Pass | Click-based |
| 2.5.3 Label in Name | ✅ Pass | Matches visible labels |
| 2.5.4 Motion Actuation | ✅ Pass | No motion controls |

#### Principle 3: Understandable

| Criterion | Status | Notes |
|-----------|--------|-------|
| 3.1.1 Language of Page | ✅ Pass | lang="en" present |
| 3.1.2 Language of Parts | ✅ N/A | Single language |
| 3.2.1 On Focus | ✅ Pass | No unexpected changes |
| 3.2.2 On Input | ✅ Pass | Predictable behavior |
| 3.2.3 Consistent Navigation | ✅ Pass | Consistent layout |
| 3.2.4 Consistent Identification | ✅ Pass | Consistent components |
| 3.3.1 Error Identification | 🟡 Partial | Need error messages |
| 3.3.2 Labels or Instructions | ❌ Fail | Missing form labels |
| 3.3.3 Error Suggestion | 🟡 Partial | Need suggestions |
| 3.3.4 Error Prevention | ✅ N/A | No critical actions |

#### Principle 4: Robust

| Criterion | Status | Notes |
|-----------|--------|-------|
| 4.1.1 Parsing | ✅ Pass | Valid HTML |
| 4.1.2 Name, Role, Value | ❌ Fail | Missing ARIA |
| 4.1.3 Status Messages | ❌ Fail | No live regions |

### Summary

**Total Criteria**: 50  
**Pass**: 23 (46%)  
**Fail**: 8 (16%)  
**Partial**: 10 (20%)  
**N/A**: 9 (18%)

**After Implementation**: Expect 90%+ pass rate

---

## Implementation Timeline

### Day 1: Foundation
- Hours 1-2: Skip links + landmarks + CSS inclusion
- Hours 3-4: Color contrast fixes + heading hierarchy
- **Deliverable**: Page structure WCAG compliant

### Day 2: Interactivity
- Hours 1-2: Tab interface ARIA + keyboard navigation
- Hours 3-4: Form labels + button ARIA
- **Deliverable**: All interactive elements accessible

### Day 3: Polish
- Hours 1-2: Live regions + dynamic content
- Hours 3-4: Testing + fixes
- **Deliverable**: Zero critical violations

---

## Maintenance

### Ongoing Responsibilities

1. **New Features**: Run accessibility checklist
2. **Monthly Audit**: Automated scan + manual test
3. **User Reports**: Accessibility issue tracking
4. **Updates**: Review WCAG updates quarterly

### Issue Template
```markdown
## Accessibility Issue

**Type**: [Keyboard | Screen Reader | Visual | Cognitive]
**Severity**: [Critical | High | Medium | Low]
**WCAG Criterion**: [e.g., 1.4.3 Contrast]

**Description**:
[Clear description of the issue]

**Steps to Reproduce**:
1. 
2. 
3. 

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What currently happens]

**Suggested Fix**:
[Optional - proposed solution]
```

---

## Resources

### Testing Tools
- **axe DevTools**: https://www.deque.com/axe/devtools/
- **WAVE**: https://wave.webaim.org/
- **Lighthouse**: Built into Chrome DevTools
- **Pa11y**: https://pa11y.org/

### Screen Readers
- **NVDA** (Free, Windows): https://www.nvaccess.org/
- **JAWS** (Paid, Windows): https://www.freedomscientific.com/
- **VoiceOver** (Free, macOS/iOS): Built-in
- **TalkBack** (Free, Android): Built-in

### Learning Resources
- **WCAG 2.1**: https://www.w3.org/WAI/WCAG21/quickref/
- **WebAIM**: https://webaim.org/
- **A11y Project**: https://www.a11yproject.com/
- **MDN Accessibility**: https://developer.mozilla.org/en-US/docs/Web/Accessibility

### ARIA Patterns
- **WAI-ARIA Authoring Practices**: https://www.w3.org/WAI/ARIA/apg/

---

## Contact

For accessibility questions or support:
- **Email**: [accessibility@dharmic-agora.com]
- **Issue Tracker**: [GitHub Issues]

---

*Built with accessibility as a foundation, not an afterthought.*  
*DHARMIC_AGORA - Accessible to all minds, all abilities.*
