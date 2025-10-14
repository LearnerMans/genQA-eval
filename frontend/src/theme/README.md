# Theme Color Schemes

This directory contains multiple color scheme options for the RAG Eval Core application. Each theme has been carefully designed for optimal UI/UX, readability, and accessibility.

## Available Themes

### 1. Current Theme (Earth Tones)
**File:** `colors.css`

Your original earth-tone palette with muted olive greens and soft grays. Professional and research-focused.

**Best for:** Academic, research-oriented applications

---

### 2. Modern Blue (Recommended)
**File:** `colors-modern-blue.css`

A clean, professional palette with blue accents optimized for readability and accessibility.

**Key Features:**
- Pure white background with high contrast
- Blue (#2563eb) primary for trust and professionalism
- WCAG AAA compliant contrast ratios
- Clear visual hierarchy with three text weights

**Best for:** Professional dashboards, business applications, general-purpose use

---

### 3. Dark Mode
**File:** `colors-dark.css`

Modern dark theme that's easy on the eyes during extended use.

**Key Features:**
- Dark slate background (#0f172a)
- Reduced eye strain for night usage
- Maintained contrast ratios for accessibility
- Elevated surfaces for depth perception

**Best for:** Night-time use, reduced eye strain, developer tools

---

### 4. Purple/Violet
**File:** `colors-purple.css`

Creative and innovative feel with purple primary colors.

**Key Features:**
- Purple (#8b5cf6) primary for creativity
- Pink accent (#ec4899) for highlights
- Light purple surface tints
- Modern and energetic

**Best for:** Creative tools, design applications, modern SaaS products

---

### 5. Teal/Cyan
**File:** `colors-teal.css`

Modern SaaS feel with teal/cyan primary colors.

**Key Features:**
- Teal (#14b8a6) primary for modernity
- Cyan accent for freshness
- Clean and contemporary
- Popular in tech/SaaS products

**Best for:** SaaS platforms, data analytics, modern web applications

---

### 6. Minimal Monochrome
**File:** `colors-monochrome.css`

Ultra-clean Scandinavian design with pure black and white.

**Key Features:**
- Pure monochrome palette
- Maximum focus on content
- Timeless and elegant
- Minimal distractions

**Best for:** Content-focused apps, minimalist interfaces, documentation

---

## How to Switch Themes

### Method 1: Using the Theme Switcher (Recommended)

A floating theme switcher button (🎨) appears in the bottom-right corner of the app. Click it to:
1. See all available themes
2. Preview them instantly
3. Switch between themes with one click

### Method 2: Manual Import

Edit `frontend/src/index.css`:

```css
/* Change this line to use a different theme */
@import "./theme/colors.css";                /* Current */
@import "./theme/colors-modern-blue.css";    /* Modern Blue */
@import "./theme/colors-dark.css";           /* Dark Mode */
@import "./theme/colors-purple.css";         /* Purple */
@import "./theme/colors-teal.css";           /* Teal */
@import "./theme/colors-monochrome.css";     /* Monochrome */
```

---

## Color Variable Reference

All themes use the same CSS variable names for consistency. Here are the key variables:

### Primary Colors
- `--color-text` - Main text color
- `--color-background` - Page background
- `--color-primary` - Primary brand/action color
- `--color-primary-hover` - Hover state for primary
- `--color-secondary` - Secondary elements
- `--color-accent` - Accent/highlight color

### Surfaces
- `--color-surface` - Card/container backgrounds
- `--color-surface-elevated` - Elevated surfaces (modals, dropdowns)
- `--color-surface-hover` - Hover states

### Text Hierarchy
- `--color-text-primary` - Primary text (headings, important)
- `--color-text-secondary` - Secondary text (body, descriptions)
- `--color-text-tertiary` - Tertiary text (labels, captions)
- `--color-muted-text` - Muted text (disabled, placeholders)

### Semantic Colors
- `--color-danger` - Errors, destructive actions
- `--color-success` - Success states, confirmations
- `--color-warning` - Warnings, cautions
- `--color-info` - Information, neutral alerts

### Borders
- `--color-border` - Default borders
- `--color-border-strong` - Emphasized borders
- `--color-ring` - Focus rings

---

## Design Principles

All themes follow these UI/UX best practices:

1. **Accessibility First**
   - WCAG AA or better contrast ratios
   - Color is not the only differentiator
   - Focus states with 3:1 contrast

2. **Visual Hierarchy**
   - Clear distinction between text weights
   - Proper use of surface elevations
   - Consistent spacing and sizing

3. **Semantic Clarity**
   - Red for danger/errors
   - Green for success
   - Amber for warnings
   - Blue for information

4. **Performance**
   - CSS variables for instant theme switching
   - No runtime JavaScript color calculations
   - Optimized for browser rendering

---

## Customizing Themes

To create your own theme:

1. Copy an existing theme file (e.g., `colors-modern-blue.css`)
2. Rename it (e.g., `colors-custom.css`)
3. Modify the CSS variable values
4. Add it to the theme switcher in `ThemeSwitcher.jsx`

### Tips for Custom Themes
- Maintain consistent variable names
- Test contrast ratios with tools like [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- Use semantic color conventions (red=danger, green=success)
- Test with actual content, not just design mockups

---

## Recommendations by Use Case

| Use Case | Recommended Theme | Why |
|----------|------------------|-----|
| General Purpose | Modern Blue | Professional, accessible, familiar |
| Night Usage | Dark Mode | Reduced eye strain, battery saving |
| Creative Work | Purple/Violet | Inspiring, modern, energetic |
| Data Analytics | Teal/Cyan | Clean, tech-focused, modern |
| Documentation | Monochrome | Distraction-free, timeless |
| Research | Current (Earth) | Academic, professional |

---

## Browser Support

All themes use modern CSS features:

- CSS Custom Properties (CSS Variables)
- `@theme` directive (via CSS framework)
- Works in all modern browsers (Chrome, Firefox, Safari, Edge)

---

## Contributing

To propose a new theme:

1. Create a new CSS file following the naming convention
2. Ensure all required CSS variables are defined
3. Test for accessibility (contrast ratios)
4. Add documentation describing the theme's purpose
5. Update the theme switcher component

---

**Last Updated:** 2025-10-14
