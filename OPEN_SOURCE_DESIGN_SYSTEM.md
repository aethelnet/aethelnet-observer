# Open Source Design System

## Overview
This design system has been updated to be fully open-source friendly, removing all proprietary font references (Apple, Google) and adding support for both light and dark modes.

## Font Stack
The design system now uses open-source fonts that are widely available on Linux systems:

```css
--font-family: 'Liberation Sans', 'DejaVu Sans', 'Bitstream Vera Sans', 'Nimbus Sans L', sans-serif;
--font-family-mono: 'Liberation Mono', 'DejaVu Sans Mono', 'Bitstream Vera Sans Mono', 'Nimbus Mono L', 'Courier New', monospace;
```

### Font Availability
- **Liberation Sans**: Included in most Linux distributions (Fedora, Ubuntu, etc.)
- **DejaVu Sans**: Widely available on Linux systems
- **Bitstream Vera Sans**: Open-source font family
- **Nimbus Sans L**: Ghostscript fonts, commonly available

These fonts are free, open-source, and align with the philosophy of open-source operating systems like Fedora Silverblue.

## Color System

### Dark Mode (Default)
- Background: `#0a0a0a` (near black)
- Cards: `rgba(20, 20, 30, 0.9)` (dark with transparency)
- Text: `#e8e8e8` (light gray)
- Accent: `#4ade80` (bright green)
- Danger: `#f87171` (bright red)
- Warning: `#fbbf24` (gold/yellow)

### Light Mode
- Background: `#f8f9fa` (light gray)
- Cards: `rgba(255, 255, 255, 0.95)` (white with transparency)
- Text: `#1a1a1a` (near black)
- Accent: `#059669` (darker green for better contrast)
- Danger: `#dc2626` (darker red for better contrast)
- Warning: `#d97706` (darker orange for better contrast)

## Theme Support

### Automatic Theme Detection
The design system automatically detects the user's system preference using CSS media queries:

```css
@media (prefers-color-scheme: light) {
    /* Light mode styles */
}
```

### Manual Theme Toggle
You can manually set a theme by adding a class to the `<html>` or `<body>` element:

```html
<html class="light-theme">
<!-- or -->
<html class="dark-theme">
```

## Usage

### Using the Design System
All components and views should use CSS custom properties (variables) from the design system:

```css
.my-component {
    background: var(--color-bg-card);
    color: var(--color-text);
    border: 1px solid var(--color-accent-border);
    font-family: var(--font-family);
}
```

### Component Colors
- Use `var(--color-accent)` for primary actions and highlights
- Use `var(--color-danger)` for errors and destructive actions
- Use `var(--color-warning)` for warnings
- Use `var(--color-positive)` for positive indicators (green)
- Use `var(--color-negative)` for negative indicators (red)

## Files Updated

1. **shared/styles.css** - Main design system with light/dark mode support
2. **index.html** - Updated inline styles to use open-source fonts
3. **styles.css** - Updated font stack
4. **shared.css** - Updated font stack

## Browser Compatibility

The design system works in all modern browsers:
- Firefox (Linux default)
- Chromium (open-source Chrome alternative)
- WebKit-based browsers

All fonts fall back gracefully to system sans-serif if specific fonts aren't available.

## Philosophy

This design system aligns with:
- **Open Source**: No proprietary dependencies
- **Freedom**: Works on any operating system
- **Accessibility**: High contrast in both light and dark modes
- **Flexibility**: Automatic theme detection with manual override option



