<script setup lang="ts">
import AethelnetObserverView from './views/AethelnetObserverView.vue'
</script>

<template>
  <div class="app-layout">
    <main class="main-content">
      <AethelnetObserverView />
    </main>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&display=swap');

body, html {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  background-color: #FFFFFF;
  color: #111111;
  font-family: 'JetBrains Mono', monospace;
  overflow: hidden;
}

.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  background-color: #FFFFFF;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #FFFFFF;
  position: relative;
}
</style>

#app {
  width: 100vw;
  height: 100vh;
}

.app-layout {
  display: flex;
  width: 100%;
  height: 100vh;
  position: relative;
}

.sidebar {
  width: 280px;
  background: #FFFFFF;
  border-right: 4px solid #111111;
  display: flex;
  flex-direction: column;
  transition: width 0.2s cubic-bezier(0.25, 1, 0.5, 1);
  z-index: 100;
  flex-shrink: 0;
  box-shadow: 4px 0 0 rgba(0, 0, 0, 0.05); /* subtle depth, but mostly flat */
}

.sidebar.collapsed {
  width: 70px;
}

.sidebar-header {
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1rem;
  border-bottom: 4px solid #111111;
  background-color: #F8F8F8;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #111111;
  font-weight: 800;
  font-size: 1.1rem;
  letter-spacing: -0.5px;
  text-transform: uppercase;
}

.logo-icon {
  font-size: 1.5rem;
  font-weight: 800;
}

.toggle-btn {
  background: #111111;
  border: 2px solid #111111;
  color: #FFFFFF;
  cursor: pointer;
  padding: 0.4rem 0.6rem;
  font-size: 0.9rem;
  font-weight: bold;
  box-shadow: 2px 2px 0px #FF3366;
  transition: transform 0.1s, box-shadow 0.1s;
}

.toggle-btn:hover {
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0px #FF3366;
}

.toggle-btn:active {
  transform: translate(2px, 2px);
  box-shadow: 0px 0px 0px #FF3366;
}

.main-nav {
  flex: 1;
  padding: 1.5rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  background-color: #FFFFFF;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.8rem 1rem;
  background: #FFFFFF;
  border: 2px solid #111111;
  color: #111111;
  font-weight: 700;
  cursor: pointer;
  text-transform: uppercase;
  font-size: 0.85rem;
  box-shadow: 4px 4px 0px #111111;
  transition: all 0.1s ease;
  width: 100%;
}

.nav-item:hover {
  transform: translate(-2px, -2px);
  box-shadow: 6px 6px 0px #111111;
  background-color: #F0F0F0;
}

.nav-item:active {
  transform: translate(4px, 4px);
  box-shadow: 0px 0px 0px #111111;
}

.nav-item.active {
  background: #111111;
  color: #FFFFFF;
  border-color: #111111;
  box-shadow: 4px 4px 0px #FF3366;
}

.nav-icon {
  font-size: 1.2rem;
  min-width: 24px;
  text-align: center;
}

.nav-label {
  white-space: nowrap;
}

.sidebar-footer {
  padding: 1.5rem;
  border-top: 4px solid #111111;
  background-color: #F8F8F8;
}

.system-metrics {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.metric-label {
  font-size: 0.75rem;
  color: #111111;
  font-weight: 800;
  margin-bottom: 2px;
  display: block;
}

.metric-bar {
  height: 12px;
  background: #FFFFFF;
  border: 2px solid #111111;
  overflow: hidden;
  box-shadow: inset 2px 2px 0 rgba(0,0,0,0.1);
}

.metric-bar .fill {
  height: 100%;
  background: #111111;
  transition: width 0.3s ease;
}

/* Alert state for CPU */
.metric-bar .fill.alert {
  background: #FF3366;
}

.main-content {
  flex: 1;
  position: relative;
  overflow: hidden;
  background-image: 
    linear-gradient(rgba(17, 17, 17, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(17, 17, 17, 0.05) 1px, transparent 1px);
  background-size: 20px 20px;
}
</style>
