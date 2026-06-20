<template>
  <span class="countdown-timer">{{ formattedTime }}</span>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps<{
  seconds: number
}>()

const currentSeconds = ref<number>(props.seconds)

const formattedTime = computed(() => {
  if (currentSeconds.value <= 0) return 'EXPIRED'
  
  const minutes = Math.floor(currentSeconds.value / 60)
  const seconds = currentSeconds.value % 60
  
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`
  }
  return `${seconds}s`
})

let interval: ReturnType<typeof setInterval> | null = null

function startTimer() {
  if (interval) clearInterval(interval)
  
  currentSeconds.value = props.seconds
  
  interval = setInterval(() => {
    if (currentSeconds.value > 0) {
      currentSeconds.value--
    } else {
      if (interval) clearInterval(interval)
    }
  }, 1000)
}

// Watch for prop changes - only reset if the new value is significantly different
// This prevents resetting on every data refresh when the value is just recalculated
watch(() => props.seconds, (newSeconds, oldSeconds) => {
  // Only update if:
  // 1. This is the first value (oldSeconds is undefined)
  // 2. The difference is significant (more than 2 seconds) - indicates a real change, not just recalculation
  // 3. The new value is much larger than current (opportunity was refreshed/renewed)
  if (oldSeconds === undefined || 
      Math.abs(newSeconds - oldSeconds) > 2 || 
      (newSeconds > currentSeconds.value + 5)) {
    currentSeconds.value = newSeconds
    startTimer()
  }
  // Otherwise, let the timer continue counting down naturally
})

onMounted(() => {
  startTimer()
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
})
</script>

<style scoped>
.countdown-timer {
  font-family: var(--font-family-mono, monospace);
  font-weight: 600;
}
</style>

