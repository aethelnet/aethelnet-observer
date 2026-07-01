<template>
  <svg class="links-layer" aria-hidden="true" v-show="!show3D">
    <!-- Temporary FastLink Line -->
    <line
      v-if="fastLinkSource && fastLinkSource.sx !== undefined"
      :x1="fastLinkSource.sx"
      :y1="fastLinkSource.sy"
      :x2="fastLinkCurrent.x"
      :y2="fastLinkCurrent.y"
      class="synapse-link fast-link-temp"
      stroke-width="4"
      stroke="#E03C31"
    />
    <g v-for="(link, index) in projectedLinks"
       :key="'link-'+index"
       v-show="(link.source.isManual || (showAutonomous && (link.source.confidence === undefined || link.source.confidence >= minConfidence))) && (link.target.isManual || (showAutonomous && (link.target.confidence === undefined || link.target.confidence >= minConfidence)))">
      
      <!-- Fat transparent hit-area for easier clicking -->
      <line
        :x1="link.sx1"
        :y1="link.sy1"
        :x2="link.sx2"
        :y2="link.sy2"
        stroke="transparent"
        stroke-width="15"
        class="synapse-link"
        style="cursor: pointer; pointer-events: stroke;"
        @mousedown.stop
        @touchstart.stop
        @click.stop="$emit('open-edge-editor', link)"
        @contextmenu.prevent="$emit('delete-link', link)"
        title="Click to edit label, Right-Click to delete connection"
      />
      <!-- Visible line -->
      <line
        :x1="link.sx1"
        :y1="link.sy1"
        :x2="link.sx2"
        :y2="link.sy2"
        class="synapse-link base-link"
        :stroke-width="Math.max(link.weight * 2, 4)"
        :stroke="link.is_manual ? '#1A1A1A' : '#E03C31'"
        :stroke-dasharray="link.is_manual ? 'none' : '6,4'"
        style="pointer-events: none;"
      />
      
      <text
        v-if="link.label"
        :x="(link.sx1 + link.sx2)/2"
        :y="(link.sy1 + link.sy2)/2 - 12"
        font-size="10"
        fill="#1A1A1A"
        text-anchor="middle"
        font-family="'Space Mono', monospace"
        font-weight="bold"
        style="pointer-events: none; user-select: none; text-shadow: 1px 1px 0 #F4F4F0, -1px -1px 0 #F4F4F0, 1px -1px 0 #F4F4F0, -1px 1px 0 #F4F4F0;"
      >
        [{{ link.label }}]
      </text>

      <g :transform="`translate(${(link.sx1 + link.sx2)/2}, ${(link.sy1 + link.sy2)/2}) rotate(${Math.atan2(link.sy2 - link.sy1, link.sx2 - link.sx1) * 180 / Math.PI})`">
        <polygon
          points="-8,-8 10,0 -8,8"
          :fill="link.is_manual ? '#1A1A1A' : '#E03C31'"
          class="data-flow-arrow"
          @click.stop="$emit('open-edge-editor', link)"
          @contextmenu.prevent="$emit('delete-link', link)"
          style="cursor: pointer;"
        />
      </g>
    </g>
  </svg>
</template>

<script setup lang="ts">
defineProps<{
  show3D: boolean
  projectedLinks: any[]
  fastLinkSource: any
  fastLinkCurrent: any
  showAutonomous: boolean
  minConfidence: number
}>()

defineEmits(['open-edge-editor', 'delete-link'])
</script>

<style scoped>
.links-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.synapse-link {
  pointer-events: stroke;
}

.fast-link-temp {
  pointer-events: none;
  stroke-dasharray: 4,4;
  animation: dash 1s linear infinite;
}

.data-flow-arrow {
  pointer-events: all;
}
</style>
