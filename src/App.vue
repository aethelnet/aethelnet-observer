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
  background-image: 
    linear-gradient(rgba(17, 17, 17, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(17, 17, 17, 0.05) 1px, transparent 1px);
  background-size: 20px 20px;
}
</style>
