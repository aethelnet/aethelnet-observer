import { ref } from 'vue'

// 0 = Max AI / Low Graphics
// 100 = Max Graphics / Low AI
export const resourceAllocation = ref(50)

export const engineSettings = {
  get physicsDecay() {
    // If Max Graphics (100), decay is low (0.01), physics takes long to settle, looks cool but uses CPU.
    // If Max AI (0), decay is high (0.1), physics settles instantly, saving CPU.
    return 0.1 - (resourceAllocation.value / 100) * 0.09
  },
  get particleCount() {
    // Max Graphics = 50 particles, Max AI = 0 particles
    return Math.floor((resourceAllocation.value / 100) * 50)
  },
  get aiPriority() {
    // If Max AI (0), priority is 1.0. If Max Graphics (100), priority is 0.1.
    return 1.0 - (resourceAllocation.value / 100) * 0.9
  }
}
