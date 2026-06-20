# Migration Guide

## Current Infrastructure Status

The Tauri infrastructure foundation is now set up. The app can run with `npm run tauri:dev` and displays a minimal Vue app.

## Directory Structure

```
Frontend/
├── src/
│   ├── main.ts              # Vue entry point
│   ├── App.vue              # Root component
│   ├── style.css            # Styles
│   ├── composables/         # Vue composables (stubs ready)
│   ├── legacy/              # For future migrated components
│   └── shared/              # For future shared utilities
├── public/
│   └── legacy/              # For future legacy HTML views
└── src-tauri/               # Tauri Rust backend
```

## How to Add Your First Component

### Example: Migrating SystemStatus Component

1. **Copy the component:**
   ```bash
   cp components/SystemStatus.js src/legacy/components/
   ```

2. **Create a Vue wrapper:**
   ```vue
   <!-- src/components/SystemStatusWrapper.vue -->
   <template>
     <div ref="container"></div>
   </template>
   
   <script setup lang="ts">
   import { onMounted, ref } from 'vue'
   import '../legacy/components/SystemStatus.js'
   
   const container = ref<HTMLElement>()
   
   onMounted(() => {
     if (container.value) {
       const element = document.createElement('component-system-status')
       container.value.appendChild(element)
     }
   })
   </script>
   ```

3. **Use in App.vue:**
   ```vue
   <template>
     <SystemStatusWrapper />
   </template>
   
   <script setup lang="ts">
   import SystemStatusWrapper from './components/SystemStatusWrapper.vue'
   </script>
   ```

## How to Add Your First View

### Example: Loading a Legacy HTML View

1. **Copy the view:**
   ```bash
   cp chartview/index.html public/legacy/chartview.html
   ```

2. **Create a Vue wrapper:**
   ```vue
   <!-- src/views/ChartView.vue -->
   <template>
     <iframe 
       src="/legacy/chartview.html" 
       style="width: 100%; height: 100vh; border: none;"
     />
   </template>
   ```

3. **Add routing (when ready):**
   - Use Vue Router or simple view switcher
   - Or open in separate Tauri window

## Step-by-Step Migration Process

1. **Test infrastructure works:**
   - Run `npm run tauri:dev`
   - Verify app opens

2. **Migrate one component:**
   - Copy to `src/legacy/components/`
   - Create Vue wrapper
   - Test in App.vue
   - Verify it works

3. **Migrate shared utilities:**
   - Copy to `src/shared/`
   - Create composable wrapper
   - Update component to use composable
   - Test

4. **Migrate one view:**
   - Copy HTML to `public/legacy/`
   - Create Vue wrapper or iframe
   - Test

5. **Repeat step by step:**
   - One component at a time
   - One view at a time
   - Test each step

## Testing Strategy

- **After each migration step:**
  - Run `npm run tauri:dev`
  - Verify functionality works
  - Check console for errors
  - Test WebSocket if applicable
  - Test API calls if applicable

- **Before moving to next step:**
  - Current step must work completely
  - No console errors
  - All functionality verified

## Notes

- Keep existing code in place until migration is complete
- Test each step independently
- Don't migrate everything at once
- Document any issues encountered
- Use git branches for each migration step



