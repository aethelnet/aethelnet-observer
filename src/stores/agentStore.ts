import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface AgentBlueprint {
  id: string
  name: string
  icon: string
  description: string
  category: string
  version: string
  installed: boolean
}

export const useAgentStore = defineStore('agentStore', () => {
  const agents = ref<AgentBlueprint[]>([
    {
      id: 'omni-decoder',
      name: 'Omni Decoder',
      icon: '👁',
      description: 'Decodes latent vectors from any node into human-readable text using LLMs.',
      category: 'Analytics',
      version: '1.2.0',
      installed: false
    },
    {
      id: 'lgnn-bridge',
      name: 'LGNN P2P Bridge',
      icon: '🌉',
      description: 'Creates a WebRTC bridge to synchronize graph state with remote peers.',
      category: 'System',
      version: '2.0.1',
      installed: false
    },
    {
      id: 'z-score-trader',
      name: 'Z-Score Sniper',
      icon: '🎯',
      description: 'Executes high-frequency trades based on statistical deviations (Z-Scores).',
      category: 'Trading',
      version: '3.1.0',
      installed: true
    },
    {
      id: 'fusion-reactor',
      name: 'Fusion Reactor',
      icon: '⚛',
      description: 'Combines two concepts (nodes) and uses Llama 3 to synthesize a new hybrid concept.',
      category: 'Analytics',
      version: '1.0.0',
      installed: true
    },
    {
      id: 'discord-webhook',
      name: 'Discord Sink',
      icon: '💬',
      description: 'Pipes high-confidence LGNN anomalies directly into a Discord channel.',
      category: 'Data Collection',
      version: '1.5.2',
      installed: false
    },
    {
      id: 'PatternMatcher',
      name: 'Pattern Matcher',
      icon: '🦂',
      description: 'Episode Pattern Matcher',
      category: 'Analytics',
      version: '1.0.0',
      installed: true
    },
    {
      id: 'Prisma',
      name: 'Prisma',
      icon: 'PR',
      description: 'Research Commenter Node',
      category: 'Analytics',
      version: '1.0.0',
      installed: true
    },
    {
      id: 'Repulsor',
      name: 'Repulsor',
      icon: 'RP',
      description: 'Noise Filter Shield',
      category: 'System',
      version: '1.0.0',
      installed: true
    },
    {
      id: 'Graviton',
      name: 'Graviton',
      icon: 'GR',
      description: 'Concept Attractor',
      category: 'System',
      version: '1.0.0',
      installed: true
    },
    {
      id: 'EntropyChamber',
      name: 'Entropy Chamber',
      icon: 'EN',
      description: 'Concept Decay Engine',
      category: 'System',
      version: '1.0.0',
      installed: true
    },
    {
      id: 'Incubator',
      name: 'Incubator',
      icon: 'IN',
      description: 'Concept Greenhouse',
      category: 'System',
      version: '1.0.0',
      installed: true
    },
    {
      id: 'Chronosphere',
      name: 'Chronosphere',
      icon: 'CH',
      description: 'Predictive Extrapolation',
      category: 'Analytics',
      version: '1.0.0',
      installed: true
    }
  ])

  const installedAgents = computed(() => {
    return agents.value.filter(a => a.installed).map(a => a.id)
  })

  const fetchInstalledAgents = async () => {
    try {
      const res = await fetch('/api/dashboard/agents/installed')
      if (res.ok) {
        const ids: string[] = await res.json()
        agents.value.forEach(a => {
          if (ids.includes(a.id)) {
            a.installed = true
          } else {
            a.installed = false
          }
        })
      }
    } catch (e) {
      console.warn("Could not fetch installed agents", e)
    }
  }

  const saveInstalledAgents = async () => {
    try {
      await fetch('/api/dashboard/agents/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ installed: installedAgents.value })
      })
    } catch (e) {
      console.warn("Could not save installed agents", e)
    }
  }

  const installAgent = (agentId: string) => {
    const agent = agents.value.find(a => a.id === agentId)
    if (agent && !agent.installed) {
      agent.installed = true
      saveInstalledAgents()
    }
  }

  const isInstalled = (agentId: string) => {
    const agent = agents.value.find(a => a.id === agentId)
    return agent ? agent.installed : false
  }

  // Fetch immediately on store creation
  fetchInstalledAgents()

  return {
    agents,
    installedAgents,
    installAgent,
    isInstalled,
    fetchInstalledAgents
  }
})
