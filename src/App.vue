<template>
  <div class="app-brutalist">
    <LgnnView />
  </div>
</template>

<script setup lang="ts">
import LgnnView from './views/LgnnView.vue'
</script>

<style>
@import './style.css';

.app-brutalist {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background-color: var(--color-bg-primary);
  position: relative;
  font-family: var(--font-family);
  color: var(--color-text-main);
}

body {
  margin: 0;
  padding: 0;
  background-color: var(--color-bg-primary);
}
</style>
