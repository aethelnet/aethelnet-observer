# Shared Design System & Cross-View Navigation

## Implementation Summary

### Files Created

1. **`shared.css`** - Shared design system with:
   - CSS variables for colors, fonts, spacing, borders, shadows
   - Common component styles (buttons, badges, cards, tables, navigation)
   - Base styles that all views inherit

2. **`navigation.js`** - Navigation helper with:
   - Port mapping for all views (1420-1429)
   - Helper functions: `navigateToChart()`, `navigateToOpportunities()`, `navigateToProphecy()`, etc.
   - Support for URL parameters (symbol, showPredictions, showProphecy)

### Files Updated

1. **`scanner/index.html`** (Port 1429)
   - Uses `shared.css` and `navigation.js`
   - Navigation buttons (Chart, Opps, PROPHECY) use helper functions
   - Header links use absolute URLs

2. **`prophecy/index.html`** (Port 1428)
   - Uses `shared.css` and `navigation.js`
   - Chart button uses helper function with PROPHECY parameters
   - Header links use absolute URLs

3. **`opportunities/index.html`** (Port 1427)
   - Uses `shared.css` and `navigation.js`
   - Header links use absolute URLs

4. **`index.html`** (Port 1420 - Dashboard)
   - Header navigation links updated to use absolute URLs

### Shared Files Copied

- `shared.css` and `navigation.js` copied to:
  - `scanner/`
  - `prophecy/`
  - `opportunities/`

This ensures each view can load the shared files locally without cross-origin issues.

## Testing Checklist

### Navigation Testing

1. **From Scanner (1429)**:
   - Click "Chart" button → Should open ChartView (1423) with symbol
   - Click "Opps" button → Should open Opportunities (1427) with symbol
   - Click "PROPHECY" button → Should open PROPHECY (1428) with symbol
   - Click header links → Should navigate to correct views

2. **From PROPHECY (1428)**:
   - Click "Chart" button → Should open ChartView (1423) with symbol, showPredictions=true, showProphecy=true
   - Click header links → Should navigate to correct views

3. **From Opportunities (1427)**:
   - Click header links → Should navigate to correct views

4. **From Dashboard (1420)**:
   - Click header links → Should navigate to correct views

### Design System Testing

1. **Visual Consistency**:
   - All views should have consistent colors, fonts, spacing
   - Buttons, badges, cards should look similar across views
   - Status badges should use shared styles

2. **CSS Variables**:
   - Change a color in `shared.css` → Should update across all views
   - Change font size → Should update across all views

## Benefits

- ✅ **Works Across Ports**: Navigation works regardless of which port you're on
- ✅ **Consistent Design**: All views share the same design tokens
- ✅ **Easy Maintenance**: Change color in one place, updates everywhere
- ✅ **Still Independent**: Each view can have custom styles for unique features
- ✅ **Scalable**: Easy to add new views that automatically get the design system

## Future Enhancements

- Add shared component library (reusable HTML/CSS components)
- Theme switching (light/dark mode via CSS variables)
- Shared utility functions (formatting, date handling, etc.)
- Shared API client with error handling



