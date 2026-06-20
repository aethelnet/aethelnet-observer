<template>
  <div class="micro-vision">
    <div class="decoder-header">
      <span class="title">MICRO VISION [SUBGRAPH]</span>
      <span class="status" :class="{ active: inputNodes.length > 0 }">{{ inputNodes.length > 0 ? 'FOCUSED' : 'IDLE' }}</span>
    </div>
    <div class="content-panel">
      <div v-if="inputNodes.length === 0" class="idle-text">
        Connect a node to visualize its local ego-network.
      </div>
      <div ref="chartContainer" class="chart-container" v-show="inputNodes.length > 0"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineProps, ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  inputs: Record<string, any>
  globalNodes: any[]
  globalLinks: any[]
}>()

const chartContainer = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

const inputNodes = computed(() => {
  return Object.values(props.inputs || {}).filter(v => v && v.node).map(v => v.node);
})

const subgraph = computed(() => {
  const nodesMap = new Map<string, any>()
  const linksSet = new Set<any>()

  const sourceIds = new Set(inputNodes.value.map(n => n.id))

  // Find all links connected to the source nodes
  props.globalLinks?.forEach(link => {
    const sId = typeof link.source === 'string' ? link.source : link.source.id
    const tId = typeof link.target === 'string' ? link.target : link.target.id
    
    if (sourceIds.has(sId) || sourceIds.has(tId)) {
      linksSet.add({ source: sId, target: tId, weight: link.weight })
      
      // We must extract the actual node objects from globalNodes
      if (!nodesMap.has(sId)) {
        const sn = props.globalNodes?.find(n => n.id === sId)
        if (sn) nodesMap.set(sId, sn)
      }
      if (!nodesMap.has(tId)) {
        const tn = props.globalNodes?.find(n => n.id === tId)
        if (tn) nodesMap.set(tId, tn)
      }
    }
  })

  // If no links but there is an input node, just show the node itself
  if (linksSet.size === 0) {
    inputNodes.value.forEach(n => nodesMap.set(n.id, n))
  }

  return {
    nodes: Array.from(nodesMap.values()),
    links: Array.from(linksSet)
  }
})

function updateChart() {
  if (!chart || !chartContainer.value) return

  const data = subgraph.value
  
  const option = {
    backgroundColor: 'transparent',
    tooltip: {},
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: data.nodes.map(n => {
          let color = '#005096' // spider
          if (n.node_type === 'app') color = '#F2C12E'
          else if (n.isManual) color = '#00FF41' // seed
          
          const isSource = inputNodes.value.some(src => src.id === n.id)
          
          return {
            id: n.id,
            name: n.label || n.id,
            symbolSize: isSource ? 25 : 15,
            itemStyle: {
              color: isSource ? '#E03C31' : color,
              borderColor: '#1A1A1A',
              borderWidth: 2,
            },
            label: {
              show: true,
              position: 'right',
              color: '#F4F4F0',
              fontSize: 10,
              formatter: '{b}'
            }
          }
        }),
        links: data.links.map(l => ({
          source: l.source,
          target: l.target,
          lineStyle: {
            width: Math.max(1, (l.weight || 1) * 2),
            color: '#333'
          }
        })),
        roam: true,
        force: {
          repulsion: 200,
          edgeLength: 60,
          layoutAnimation: true
        }
      }
    ]
  }

  chart.setOption(option)
}

watch(subgraph, () => {
  nextTick(() => {
    updateChart()
  })
}, { deep: true })

let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  if (chartContainer.value) {
    chart = echarts.init(chartContainer.value)
    updateChart()
    
    resizeObserver = new ResizeObserver(() => {
      chart?.resize()
    })
    resizeObserver.observe(chartContainer.value)
    
    window.addEventListener('resize', () => {
      chart?.resize()
    })
  }
})

onUnmounted(() => {
  if (resizeObserver && chartContainer.value) {
    resizeObserver.unobserve(chartContainer.value)
  }
  chart?.dispose()
})
</script>

<style scoped>
.micro-vision {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #050505;
  color: #F4F4F0;
  font-family: 'Space Mono', monospace;
  border: 1px solid #E03C31;
}

.decoder-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #E03C31;
  color: #FFF;
}

.title {
  font-weight: bold;
  font-size: 14px;
  letter-spacing: 1px;
}

.status {
  font-size: 10px;
  padding: 2px 6px;
  background: #1A1A1A;
  color: #888;
  border-radius: 2px;
}

.status.active {
  background: #FFF;
  color: #E03C31;
  font-weight: bold;
}

.content-panel {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.idle-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #666;
  font-size: 12px;
  line-height: 1.6;
}

.chart-container {
  width: 100%;
  height: 100%;
}
</style>
