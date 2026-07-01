<template>
  <div
    class="aethelnet-canvas"
    :class="{ 'is-chromatic': isChromaticMode, 'is-dragging': isDraggingFile, 'is-subconscious': isSubconscious }"
    ref="canvasContainer"
    @mousedown="onCanvasMouseDown"
    @dblclick="addNodeOnCanvas"
    @dragover.prevent="onDragOver"
    @dragleave.prevent="onDragLeave"
    @drop.prevent="onDrop"
  >
    <!-- Lasso Box Overlay -->
    <div
      v-if="lassoState.active"
      class="lasso-box"
      :style="{
        left: Math.min(lassoState.startX, lassoState.currentX) + 'px',
        top: Math.min(lassoState.startY, lassoState.currentY) + 'px',
        width: Math.abs(lassoState.currentX - lassoState.startX) + 'px',
        height: Math.abs(lassoState.currentY - lassoState.startY) + 'px',
      }"
    ></div>

    <!-- Drag & Drop Knowledge Vein Overlay -->
    <div v-if="isDraggingFile" class="knowledge-dropzone">
      <div class="dropzone-core">
        <svg
          width="48"
          height="48"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            d="M12 2v20M2 12h20M12 2a10 10 0 0 1 10 10 10 10 0 0 1-10 10 10 10 0 0 1-10-10A10 10 0 0 1 12 2z"
          ></path>
        </svg>
        <h3>DROP TO INGEST</h3>
        <p>Aethelnet will assimilate this data into the neural manifold</p>
      </div>
    </div>
    <CanvasHud
      :isChromaticMode="isChromaticMode"
      :isSubconscious="isSubconscious"
      :breadcrumbs="breadcrumbs"
      @toggle-chromatic="isChromaticMode = !isChromaticMode"
      @toggle-subconscious="toggleSubconscious"
      @enter-observer="
        playSound('warp');
        $emit('change-view', 'observer');
      "
      @navigate-up="goUp"
    />

    <!-- SVG Gooey Filter -->
    <svg width="0" height="0" style="position: absolute">
      <defs>
        <filter id="goo">
          <feGaussianBlur in="SourceGraphic" stdDeviation="25" result="blur" />
          <feColorMatrix
            in="blur"
            mode="matrix"
            values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 40 -15"
            result="goo"
          />
          <feComposite in="SourceGraphic" in2="goo" operator="atop" />
        </filter>
      </defs>
    </svg>

    <!-- Frosted panel removed in favor of Settings Node -->

    <!-- 54D Order Flow Hologram (Trading Context) -->
    <svg class="links-layer" aria-hidden="true">
      <path
        v-for="(link, i) in projectedLinks"
        :key="i"
        :d="link.d"
        class="synapse-link"
        fill="none"
        :class="{ 'is-pulsing': link.isPulsing, 'is-heavy': link.weight > 0.8 }"
        :stroke-width="link.weight * 2.5"
      />
    </svg>

    <!-- Gossip Layer (Visible only in Subgraphs) -->
    <div v-if="currentUniverseId !== 'root'" class="gossip-layer">
      <div
        v-for="(gossip, i) in gossips"
        :key="'gossip_' + i"
        class="gossip-node"
        :style="{
          left: `${Math.sin(i * 1.5) * 500 + winW / 2}px`,
          top: `${Math.cos(i * 1.5) * 300 + winH / 2}px`,
          opacity: 0.2 + Math.random() * 0.3,
        }"
        title="Public Gossip from the Matrix"
      >
        <span class="gossip-label">{{ gossip.label }}</span>
        <span class="gossip-hash">#public</span>
      </div>
    </div>

    <!-- Gooey Background Layer for Nodes -->
    <div class="gooey-layer">
      <div
        v-for="node in nodes"
        :key="'bg_' + node.id"
        class="concept-blob"
        :class="{ 'is-expanded': node.isExpanded, ghost: node.isGhost }"
        :style="{
          transform: `translate(${node.sx}px, ${node.sy}px) scale(${(node.scale || 1) * (1 + (node.depthGravity || 0) * 0.01)})`,
          zIndex:
            is3DMode || isFree3DMode
              ? Math.floor((node as any)._zDepth || 0)
              : Math.floor(node.z || 0),
          opacity: nodeMatchesSearch(node) ? (node.isDiving ? 0 : 1) : 0.15,
          backgroundColor: node.isGhost
            ? 'rgba(236, 72, 153, 0.2)'
            : getNodeColor(node),
          mixBlendMode: isChromaticMode ? 'multiply' : 'normal',
          filter: node.depthGravity
            ? `drop-shadow(0 0 ${node.depthGravity}px ${getNodeColor(node)})`
            : 'none',
        }"
      ></div>
    </div>

    <!-- HTML Foreground Layer for Nodes (Text/Inputs) -->
    <div
      v-for="node in nodes"
      :key="node.id"
      class="concept-circle"
      :class="{
        'is-dragged': node.isDragged,
        'is-diving': node.isDiving,
        'is-selected': node.isSelected,
        'is-expanded': node.isExpanded,
        ghost: node.isGhost,
      }"
      :style="{
        transform: `translate(${node.sx}px, ${node.sy}px) scale(${(node.scale || 1) * (1 + (node.depthGravity || 0) * 0.01)})`,
        zIndex:
          is3DMode || isFree3DMode
            ? Math.floor((node as any)._zDepth || 0)
            : Math.floor(node.z || 0),
        opacity: nodeMatchesSearch(node) ? (node.isDiving ? 0 : 1) : 0.15,
        pointerEvents: nodeMatchesSearch(node) ? 'auto' : 'none',
        '--node-accent': getNodeColor(node, 1.0),
        '--node-shadow-color': getNodeColor(node, 0.15),
        boxShadow: node.depthGravity ? `inset 0 0 ${node.depthGravity / 2}px var(--node-accent)` : undefined,
      }"
      @mousedown.stop="startDrag($event, node)"
      @touchstart.stop="startDrag($event, node)"
      @click.stop="toggleExpand(node)"
    >
      <!-- Nested Universe Preview (Background) -->
      <div
        v-if="
          universeMap.has(node.id) &&
          (universeMap.get(node.id)?.nodes?.length || 0) > 0
        "
        class="nested-preview"
      >
        <div
          v-for="subNode in universeMap.get(node.id)?.nodes || []"
          :key="'sn_' + subNode.id"
          class="mini-node"
          :style="{
            transform: `translate(${((subNode.x || 0) - winW / 2) * getSubgraphScale(node)}px, ${((subNode.y || 0) - winH / 2) * getSubgraphScale(node)}px)`,
          }"
        ></div>
      </div>

      <!-- Collapsed State (Just the label) -->
      <div v-if="!node.isExpanded" class="circle-label">
        <div
          class="node-title"
          :class="{ 'has-label': !!node.label }"
          :style="{ color: node.isGhost ? '#db2777' : '' }"
        >
          <span v-if="node.isPinned" class="pin-indicator">
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"
              ></path>
              <polyline points="7.5 4.21 12 6.81 16.5 4.21"></polyline>
              <polyline points="7.5 19.79 7.5 14.6 3 12"></polyline>
              <polyline points="21 12 16.5 14.6 16.5 19.79"></polyline>
              <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
              <line x1="12" y1="22.08" x2="12" y2="12"></line>
            </svg>
          </span>
          {{ node.label }}
        </div>
      </div>

      <!-- Expanded State (Input & Details) -->
      <div
        v-else
        class="circle-expanded"
        @mousedown.stop="startDrag($event, node)"
        @touchstart.stop="startDrag($event, node)"
        @click.stop
        @dblclick.stop="toggleExpand(node)"
      >
        <OmniNodeTemplate
          v-if="node.isExpanded"
          :title="node.label"
          :color="node.color || '#3b82f6'"
          :theme="'light'"
        >
          <template v-if="node.systemModule">
            <div class="embedded-node-wrapper">
              <AuraStreamView v-if="node.systemModule === 'aura'" />
              <LgnnView v-if="node.systemModule === 'lgnn'" />
              <SelfHubView v-if="node.systemModule === 'self'" />
              <OrderbookNode
                v-if="node.systemModule === 'trade'"
                :bids="orderbookData.bids"
                :asks="orderbookData.asks"
              />
            </div>

            <div
              v-if="node.systemModule === 'settings'"
              class="settings-node-content"
              @mousedown.stop
              @touchstart.stop
            >
              <h3
                style="
                  color: #d97706;
                  font-weight: 700;
                  margin-bottom: 12px;
                  font-size: 1rem;
                "
              >
                Settings (Root Parameters)
              </h3>

              <div class="setting-row">
                <span>Decay Rate (τ)</span>
                <input
                  type="range"
                  min="0.01"
                  max="0.2"
                  step="0.01"
                  value="0.08"
                  class="organic-slider"
                />
              </div>
              <div class="setting-row">
                <span>Resonance (λ)</span>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value="0.4"
                  class="organic-slider"
                />
              </div>
              <div class="setting-row">
                <span>ODE Compute Time</span>
                <input
                  type="range"
                  min="0.5"
                  max="5.0"
                  step="0.5"
                  value="2.5"
                  class="organic-slider"
                />
              </div>

              <h3
                style="
                  color: #d97706;
                  font-weight: 700;
                  margin-top: 24px;
                  margin-bottom: 12px;
                  font-size: 1rem;
                "
              >
                OmniSpider Aggression
              </h3>
              <div class="setting-row">
                <span>Confidence Threshold</span>
                <input
                  type="range"
                  min="0.5"
                  max="0.99"
                  step="0.01"
                  value="0.85"
                  class="organic-slider"
                />
              </div>
            </div>
          </template>
          <template v-else>
            <div
              v-if="node._showColorWheel"
              class="custom-color-wheel"
              @mousedown.stop="pickColorFromWheel($event, node)"
              @mousemove.stop="
                $event.buttons === 1 && pickColorFromWheel($event, node)
              "
              @mouseup.stop="closeColorWheel(node)"
              @mouseleave.stop="closeColorWheel(node)"
            ></div>
            <div class="node-drag-header"></div>
            <input
              type="text"
              v-model="node.label"
              class="node-title-input"
              placeholder="Concept Name"
              @input="updateNode(node)"
              @keydown.enter="toggleExpand(node)"
              @mousedown.stop
              @touchstart.stop
            />
            <textarea
              v-model="node.content"
              class="node-content-input"
              placeholder="Inject knowledge here..."
              @input="updateNode(node)"
              @keydown.tab.prevent="acceptSuggestion(node)"
              @mousedown.stop
              @touchstart.stop
            ></textarea>

            <div v-if="node.status" class="node-status">{{ node.status }}</div>

            <div
              class="node-controls"
              v-show="node.isSelected"
              style="
                display: flex;
                gap: 8px;
                margin-top: 8px;
                align-items: center;
                justify-content: space-between;
                width: 100%;
              "
            >
              <div
                class="aura-palette"
                style="
                  display: flex;
                  gap: 6px;
                  padding: 4px;
                  background: rgba(255, 255, 255, 0.2);
                  border-radius: 12px;
                  align-items: center;
                "
              >
                <div
                  v-for="(c, index) in customPalette"
                  :key="index"
                  @click.stop="handlePaletteClick(node, c, index, $event)"
                  :style="{
                    background: c,
                    width: '16px',
                    height: '16px',
                    borderRadius: '50%',
                    cursor: 'pointer',
                    border:
                      node.color === c
                        ? '2px solid #0f172a'
                        : '1px solid rgba(0,0,0,0.1)',
                    position: 'relative',
                    overflow: 'hidden',
                  }"
                ></div>
                <div
                  v-if="customPalette.length < 6"
                  @click.stop="addPaletteColor()"
                  style="
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    cursor: pointer;
                    border: 1px dashed rgba(0, 0, 0, 0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: rgba(0, 0, 0, 0.5);
                    font-size: 14px;
                    font-weight: bold;
                    line-height: 1;
                  "
                >
                  +
                </div>
              </div>
              <div style="display: flex; gap: 6px">
                <button
                  @click.stop="deleteNode(node)"
                  class="node-btn"
                  style="
                    background: rgba(239, 68, 68, 0.1);
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    color: #ef4444;
                    width: 30px;
                    height: 30px;
                    padding: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                  "
                  title="Delete Node"
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <path
                      d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
                    ></path>
                  </svg>
                </button>
                <button
                  v-if="node.agentType === 'spider'"
                  @click.stop="triggerSpiderPulse(node)"
                  class="node-btn"
                  style="
                    background: rgba(14, 165, 233, 0.2);
                    border-color: #0ea5e9;
                  "
                >
                  Pulse
                </button>
              </div>
            </div>

            <div
              class="suggestion-hud"
              v-if="node.suggestion"
              @click.stop="acceptSuggestion(node)"
            >
              <span class="ghost-text">{{ node.suggestion }}</span>
              <kbd class="tab-key">Tab</kbd>
            </div>
          </template>
        </OmniNodeTemplate>

        <!-- Resize Handle -->
        <div
          class="resize-handle"
          @mousedown.stop="startResize($event, node)"
          @touchstart.stop="startResize($event, node)"
        ></div>

        <!-- Fast Link Port -->
        <div
          class="link-port"
          title="Drag to connect"
          @mousedown.stop.prevent="startFastLink($event, node)"
          @touchstart.stop.prevent="startFastLink($event, node)"
        ></div>
      </div>
    </div>

    <!-- Lasso Selection Box -->
    <div
      v-if="lassoState.active"
      class="lasso-box"
      :style="{
        left: Math.min(lassoState.startX, lassoState.currentX) + 'px',
        top: Math.min(lassoState.startY, lassoState.currentY) + 'px',
        width: Math.abs(lassoState.currentX - lassoState.startX) + 'px',
        height: Math.abs(lassoState.currentY - lassoState.startY) + 'px',
      }"
    ></div>

    <!-- No Liquidations Clutter -->

    <!-- Telemetry Sidebar -->
    <transition name="slide-right">
      <div
        v-if="selectedNode"
        class="telemetry-panel"
        @mousedown.stop
        @touchstart.stop
      >
        <div class="telemetry-header">
          <div class="telemetry-title">
            <span class="telemetry-id">{{ selectedNode.id }}</span>
            <span v-if="selectedNode.isGhost" class="ghost-badge">GOSSIP</span>
          </div>
          <button @click="selectedNode.isSelected = false" class="close-btn">
            ×
          </button>
        </div>

        <div class="telemetry-body">
          <div v-if="selectedNode.isGhost" class="ghost-info">
            <p>
              <strong>Source:</strong>
              {{ selectedNode.source_peer || "Unknown Peer" }}
            </p>
            <p>
              <strong>Topic:</strong>
              {{ selectedNode.thought_topic || "Unknown" }}
            </p>
            <button
              class="assimilate-btn"
              @click="assimilateNode(selectedNode)"
            >
              Assimilate into Manifold
            </button>
          </div>
          <div v-else class="node-meta">
            <!-- Node Core Stats -->
            <div class="telemetry-stats-grid">
              <div class="stat-box">
                <span class="stat-label">Mass</span>
                <span class="stat-value">{{
                  selectedNode.scale?.toFixed(2) || "1.00"
                }}</span>
              </div>
              <div class="stat-box">
                <span class="stat-label">Links</span>
                <span class="stat-value">{{
                  getConnectedLinksCount(selectedNode.id)
                }}</span>
              </div>
              <div class="stat-box">
                <span class="stat-label">Resonance</span>
                <span class="stat-value" :style="{ color: '#ec4899' }"
                  >{{ Math.floor(Math.random() * 40 + 60) }}%</span
                >
              </div>
            </div>

            <!-- Trading Orderbook Hologram (Visible for Trade Nodes) -->
            <div
              v-if="
                selectedNode.id.includes('trade') ||
                selectedNode.systemModule === 'trade'
              "
              class="hologram-module trade-module"
            >
              <div class="module-title">LIVE ORDERBOOK [BTC/USDT]</div>
              <div
                class="orderbook-container"
                v-if="
                  orderbookData.asks.length > 0 || orderbookData.bids.length > 0
                "
              >
                <div class="orderbook-asks">
                  <div
                    class="order-row ask"
                    v-for="(ask, i) in topAsks"
                    :key="'ask' + i"
                  >
                    <span class="price">{{ ask.price }}</span>
                    <span class="size">{{ ask.size }}</span>
                    <div class="depth-bar" :style="{ width: ask.width }"></div>
                  </div>
                </div>
                <div class="orderbook-spread" v-if="orderbookSpread">
                  <span class="spread-price">{{ orderbookSpread.price }}</span>
                  <span class="spread-diff">{{ orderbookSpread.diff }}</span>
                </div>
                <div class="orderbook-bids">
                  <div
                    class="order-row bid"
                    v-for="(bid, i) in topBids"
                    :key="'bid' + i"
                  >
                    <span class="price">{{ bid.price }}</span>
                    <span class="size">{{ bid.size }}</span>
                    <div class="depth-bar" :style="{ width: bid.width }"></div>
                  </div>
                </div>
              </div>
              <div v-else class="orderbook-loading">
                Waiting for Telemetry...
              </div>

              <div class="lgnn-confidence">
                <div class="confidence-header">
                  <span>LGNN Action Propensity</span>
                  <span
                    class="buy-signal"
                    :class="{ 'sell-signal': lgnnPropensity.sell > 50 }"
                    >{{ lgnnPropensity.signal }}</span
                  >
                </div>
                <div
                  class="confidence-bar-wrap"
                  :class="{ 'is-pulsing': lgnnPropensity.isPulsing }"
                >
                  <div
                    class="confidence-bar buy"
                    :style="{ width: lgnnPropensity.buy + '%' }"
                  ></div>
                  <div
                    class="confidence-bar sell"
                    :style="{ width: lgnnPropensity.sell + '%' }"
                  ></div>
                </div>
              </div>
            </div>

            <!-- Generic Neural Telemetry -->
            <div v-else class="hologram-module neural-module">
              <div class="module-title">NEURAL ACTIVITY STREAM</div>
              <div class="neural-stream">
                <div class="pulse-line" v-for="i in 5" :key="i">
                  <span class="pulse-hex"
                    >0x{{
                      Math.floor(Math.random() * 16777215).toString(16)
                    }}</span
                  >
                  <div class="pulse-wave">
                    <div
                      class="wave-bar"
                      :style="{
                        height: Math.random() * 100 + '%',
                        animationDelay: Math.random() * 0.5 + 's',
                      }"
                    ></div>
                    <div
                      class="wave-bar"
                      :style="{
                        height: Math.random() * 100 + '%',
                        animationDelay: Math.random() * 0.5 + 's',
                      }"
                    ></div>
                    <div
                      class="wave-bar"
                      :style="{
                        height: Math.random() * 100 + '%',
                        animationDelay: Math.random() * 0.5 + 's',
                      }"
                    ></div>
                    <div
                      class="wave-bar"
                      :style="{
                        height: Math.random() * 100 + '%',
                        animationDelay: Math.random() * 0.5 + 's',
                      }"
                    ></div>
                    <div
                      class="wave-bar"
                      :style="{
                        height: Math.random() * 100 + '%',
                        animationDelay: Math.random() * 0.5 + 's',
                      }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Search, Filter & Feed HUD -->
    <div class="search-hud" @mousedown.stop @touchstart.stop>
      <input
        type="text"
        v-model="searchQuery"
        @input="updateSearch"
        @keydown.enter="ingestThoughtFromSearch"
        placeholder="Filter or feed Manifold (Enter to inject)..."
        class="search-input"
      />
      <div
        class="search-suggestion-badge"
        v-if="searchSuggestion"
        @click="
          searchQuery += searchSuggestion.replace(
            searchQuery.split(' ').pop() || '',
            '',
          )
        "
      >
        {{ searchSuggestion }} <kbd>Tab</kbd>
      </div>
      <button
        class="capture-btn"
        v-if="searchQuery"
        @click="captureAsNode"
        title="Package matching nodes into a Lens"
      >
        Lens Capture
      </button>
    </div>

    <!-- Subtle Hint -->
    <div class="canvas-hint">Double-click anywhere to add a thought</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from "vue";
import * as d3 from "d3";
import AuraStreamView from "./AuraStreamView.vue";
import LgnnView from "./LgnnView.vue";
import SelfHubView from "./SelfHubView.vue";
import OrderbookNode from "../components/OrderbookNode.vue";
import CanvasHud from "@/components/CanvasHud.vue";
import OmniNodeTemplate from "@/components/OmniNodeTemplate.vue";
import { API_BASE } from "../shared/api.js";
import { setupWebSocketListener } from "../shared/websocket.js";

// --- Audio Context for Blips & Pops ---
let audioCtx: AudioContext | null = null;

function playSound(type: "blip" | "pop" | "warp") {
  if (!audioCtx) {
    audioCtx = new (
      window.AudioContext || (window as any).webkitAudioContext
    )();
  }
  if (audioCtx.state === "suspended") audioCtx.resume();

  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();

  osc.connect(gain);
  gain.connect(audioCtx.destination);

  const now = audioCtx.currentTime;

  if (type === "blip") {
    osc.type = "sine";
    osc.frequency.setValueAtTime(800, now);
    osc.frequency.exponentialRampToValueAtTime(1200, now + 0.1);
    gain.gain.setValueAtTime(0.1, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
    osc.start(now);
    osc.stop(now + 0.1);
  } else if (type === "pop") {
    osc.type = "sine";
    osc.frequency.setValueAtTime(400, now);
    osc.frequency.exponentialRampToValueAtTime(200, now + 0.15);
    gain.gain.setValueAtTime(0.2, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
    osc.start(now);
    osc.stop(now + 0.15);
  } else if (type === "warp") {
    osc.type = "triangle";
    osc.frequency.setValueAtTime(100, now);
    osc.frequency.exponentialRampToValueAtTime(300, now + 0.3);
    gain.gain.setValueAtTime(0.15, now);
    gain.gain.linearRampToValueAtTime(0.01, now + 0.3);
    osc.start(now);
    osc.stop(now + 0.3);
  }
}

// --- Theme State ---
const isChromaticMode = ref(false);
const isDraggingFile = ref(false);
const customPalette = ref<string[]>([
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
]);
const orderbookData = ref<any>({ bids: [], asks: [] });
const lgnnPropensity = ref({
  buy: 78,
  sell: 22,
  signal: "STRONG BUY",
  isPulsing: false,
});

const orderbookSpread = computed(() => {
  if (
    orderbookData.value.asks.length > 0 &&
    orderbookData.value.bids.length > 0
  ) {
    const askPrice = parseFloat(orderbookData.value.asks[0][0]);
    const bidPrice = parseFloat(orderbookData.value.bids[0][0]);
    return {
      price: ((askPrice + bidPrice) / 2).toFixed(2),
      diff: (askPrice - bidPrice).toFixed(2),
    };
  }
  return null;
});

const maxOrderSize = computed(() => {
  let max = 0.1;
  const asks = orderbookData.value.asks.slice(0, 4);
  const bids = orderbookData.value.bids.slice(0, 4);
  asks.concat(bids).forEach((level: any) => {
    const size = parseFloat(level[1]);
    if (size > max) max = size;
  });
  return max;
});

const topAsks = computed(() => {
  return orderbookData.value.asks.slice(0, 4).map((ask: any) => ({
    price: parseFloat(ask[0]).toFixed(1),
    size: parseFloat(ask[1]).toFixed(3),
    width: Math.min((parseFloat(ask[1]) / maxOrderSize.value) * 100, 100) + "%",
  }));
});

const topBids = computed(() => {
  return orderbookData.value.bids.slice(0, 4).map((bid: any) => ({
    price: parseFloat(bid[0]).toFixed(1),
    size: parseFloat(bid[1]).toFixed(3),
    width: Math.min((parseFloat(bid[1]) / maxOrderSize.value) * 100, 100) + "%",
  }));
});

const lassoState = ref({
  active: false,
  startX: 0,
  startY: 0,
  currentX: 0,
  currentY: 0,
});

let dragCounter = 0;

function onDragOver(event: DragEvent) {
  event.dataTransfer!.dropEffect = "copy";
  isDraggingFile.value = true;
}

function onDragLeave(event: DragEvent) {
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
  if (
    event.clientX <= rect.left ||
    event.clientX >= rect.right ||
    event.clientY <= rect.top ||
    event.clientY >= rect.bottom
  ) {
    isDraggingFile.value = false;
  }
}

async function onDrop(event: DragEvent) {
  isDraggingFile.value = false;
  dragCounter = 0;

  if (!event.dataTransfer) return;

  const files = event.dataTransfer.files;
  const items = event.dataTransfer.items;

  let ingestedContent = "";

  if (files && files.length > 0) {
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (
        file.type.startsWith("text/") ||
        file.type === "application/json" ||
        file.name.endsWith(".md")
      ) {
        const text = await file.text();
        ingestedContent += `[File: ${file.name}]\n${text.substring(0, 500)}...\n\n`;
      } else {
        ingestedContent += `[Ingested File: ${file.name} - ${file.type}]\n`;
      }
    }
  } else if (items && items.length > 0) {
    for (let i = 0; i < items.length; i++) {
      if (items[i].kind === "string" && items[i].type.match("^text/plain")) {
        items[i].getAsString((s) => {
          ingestText(s, event.clientX, event.clientY);
        });
        return; // handle async string later
      }
    }
  }

  if (ingestedContent) {
    ingestText(ingestedContent, event.clientX, event.clientY);
  }
}

function ingestText(text: string, clientX: number, clientY: number) {
  // Convert screen coordinates to canvas coordinates
  const canvasX =
    (clientX - width / 2 - (globalTransform?.x || 0)) /
    (globalTransform?.k || 1);
  const canvasY =
    (clientY - height / 2 - (globalTransform?.y || 0)) /
    (globalTransform?.k || 1);

  playSound("pop");

  const ingestId = `INGEST_${Date.now()}`;
  const newNode: Node = {
    id: ingestId,
    label: "Ingested Data",
    content: text,
    x: canvasX,
    y: canvasY,
    z: 0,
    vx: 0,
    vy: 0,
    vz: 0,
    color: "#60a5fa", // Aethelnet Blue
    isExpanded: true,
    scale: 1.5,
    depthGravity: 30,
    theme: "light",
  };

  nodes.value.push(newNode);
  initSimulation();

  // Connect to nearby nodes to simulate assimilation
  const nearbyNodes = nodes.value.filter((n) => n.id !== ingestId).slice(0, 3);
  nearbyNodes.forEach((target) => {
    links.value.push({
      source: ingestId,
      target: target.id,
      weight: 1.5,
    });
  });

  initSimulation();

  // Post to backend universal_ingest
  fetch(`${API_BASE}/api/lgnn/universal_ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      bot_name: "workbench_ui",
      observation: text,
      confidence: 1.0,
      context_tags: ["ingested", "workbench"],
    }),
  }).catch((err) => console.error("Ingestion failed", err));
}

function applyColorToSelected(color: string) {
  nodes.value
    .filter((n) => n.isExpanded)
    .forEach((n) => {
      n.color = color;
    });
  triggerSave();
}

function handlePaletteClick(
  node: Node,
  color: string,
  index: number,
  event: Event,
) {
  if (node.color !== color) {
    applyColorToSelected(color);
  } else {
    // Second click: open custom color wheel
    node._showColorWheel = true;
    node._activePaletteIndex = index;
  }
}

function pickColorFromWheel(event: MouseEvent, node: Node) {
  const el = event.currentTarget as HTMLElement;
  const rect = el.getBoundingClientRect();
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;
  const x = event.clientX - rect.left - centerX;
  const y = event.clientY - rect.top - centerY;

  let angle = Math.atan2(y, x) * (180 / Math.PI) + 90;
  if (angle < 0) angle += 360;

  const dist = Math.min(centerX, Math.sqrt(x * x + y * y));
  const intensity = dist / centerX;

  const lightness = 100 - intensity * 50;
  const newColor = `hsla(${Math.round(angle)}, 100%, ${Math.round(lightness)}%, 0.9)`;

  if (node._activePaletteIndex !== undefined) {
    updatePaletteColor(node, node._activePaletteIndex, newColor);
  }
}

function closeColorWheel(node: Node) {
  node._showColorWheel = false;
}

function updatePaletteColor(node: Node, index: number, newColor: string) {
  customPalette.value[index] = newColor;
  applyColorToSelected(newColor);
}

function addPaletteColor() {
  if (customPalette.value.length < 6) {
    customPalette.value.push("#0ea5e9");
  }
}

function getNodeColor(node: Node, alpha: number = 0.9): string {
  if (!isChromaticMode.value) {
    if (node.color) return node.color;
    return node.mean_activation && node.mean_activation > 0.3
      ? `rgba(217, 119, 6, ${alpha})`
      : `rgba(255, 255, 255, ${alpha})`;
  }
  // Smoothly map the node's spatial vector (x, y) to a color.
  // Because the ODE solver places semantically similar nodes close together,
  // nodes with similar meaning will automatically have similar colors!
  const cx = window.innerWidth ? window.innerWidth / 2 : 500;
  const cy = window.innerHeight ? window.innerHeight / 2 : 500;
  const dx = (node.x || 0) - cx;
  const dy = (node.y || 0) - cy;

  // Angle determines the base color (Hue)
  const angle = ((Math.atan2(dy, dx) * 180) / Math.PI + 360) % 360;

  // Distance from center determines saturation (core is softer, edges are vibrant)
  const dist = Math.sqrt(dx * dx + dy * dy);
  const saturation = Math.min(100, 60 + dist / 15);

  return `hsla(${angle}, ${saturation}%, 60%, ${alpha})`;
}

// --- Interfaces ---
interface Node {
  id: string;
  label: string;
  content: string;
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
  fx?: number | null;
  fy?: number | null;
  isDragged?: boolean;
  isExpanded?: boolean;
  sx?: number;
  sy?: number;
  scale?: number;
  mean_activation?: number;
  targetScale?: number;
  currentScale?: number;
  color?: string;
  theme?: "light" | "dark";
  preLgnnX?: number;
  preLgnnY?: number;
  suggestion?: string;
  status?: string;
  _showColorWheel?: boolean;
  _activePaletteIndex?: number;
  systemModule?: "aura" | "lgnn" | "self" | "settings" | "trade";
  manualSize?: number;
  manualWidth?: number;
  manualHeight?: number;
  isDiving?: boolean;
  isAgent?: boolean;
  agentType?: string | null;
  hasSpawnedChildren?: boolean;
  hasManualTitle?: boolean;
  inheritedFromId?: string;
  inheritedIndex?: number;
  imageUrl?: string;
  spawnedChildId?: string;
  compiledScript?: string;
  justAcceptedSuggestion?: boolean;
  isPinned?: boolean;
  pinnedX?: number;
  pinnedY?: number;
  isGhost?: boolean;
  source_peer?: string;
  thought_topic?: string;
  isSelected?: boolean;
  depthGravity?: number;
}

interface Link {
  source: string | Node;
  target: string | Node;
  weight: number;
  isPulsing?: boolean;
}

// --- State ---
const nodes = ref<Node[]>([]);
const links = ref<Link[]>([]);
const projectedLinks = ref<any[]>([]);

let simulation: any = null;
let animationFrameId = 0;
let width = window.innerWidth;
let height = window.innerHeight;
function ingestThoughtFromSearch() {
  const text = searchQuery.value.trim();
  if (!text) return;

  if (text.toLowerCase() === "/clear") {
    nodes.value = nodes.value.filter((n) => n.systemModule); // Keep only system modules
    links.value = [];
    triggerSave();
    searchQuery.value = "";
    return;
  }

  // Create a new node near the center of the screen
  const cx = width / 2 + (Math.random() - 0.5) * 100;
  const cy = height / 2 + (Math.random() - 0.5) * 100;

  const words = text.split(" ");
  let derivedLabel = "";
  if (words.length > 3) {
    derivedLabel = words.slice(0, 3).join(" ") + "...";
  } else {
    derivedLabel = text;
  }

  const newNode: Node = {
    id: "n_" + Math.random().toString(36).substr(2, 9),
    label: derivedLabel,
    content: text,
    x: cx,
    y: cy,
    z: 0,
    vx: 0,
    vy: 0,
    vz: 0,
    isExpanded: false,
    theme: "light",
  };

  nodes.value.push(newNode);
  initSimulation();
  triggerSave();

  // Clear input
  searchQuery.value = "";
}

// Track zoom/pan transform
let globalTransform = { x: 0, y: 0, k: 1 };
let zoomBehavior: any = null;

// --- Fractal Universes ---
const universeMap = new Map<string, any>();
const currentUniverseId = ref("root");
const breadcrumbs = ref<{ id: string; label: string }[]>([
  { id: "root", label: "Aethelnet" },
]);

const isPaused = ref(false);
const selectedNode = computed(() => nodes.value.find((n) => n.isSelected));

function getConnectedLinksCount(nodeId: string) {
  return links.value.filter(
    (l) =>
      (typeof l.source === "object" ? (l.source as Node).id : l.source) ===
        nodeId ||
      (typeof l.target === "object" ? (l.target as Node).id : l.target) ===
        nodeId,
  ).length;
}

function assimilateNode(node: Node) {
  node.isGhost = false;
  node.color = "#10b981"; // Green for assimilated
  triggerSave();
}

function generateId() {
  return "n_" + Math.random().toString(36).substr(2, 9);
}

let isTransitioning = false;
let wasDragged = false;

let isDrawingLink = false;
let sourceNodeForLink: Node | null = null;
const tempLink = ref<any>(null);
const fingerPos = { x: 0, y: 0 };

const winW = ref(window.innerWidth);
const winH = ref(window.innerHeight);

const isLgnnMode = ref(false);
const isSubconscious = ref(false);
const canvasContainer = ref<any>(null);

function toggleSubconscious() {
  isSubconscious.value = !isSubconscious.value;
  playSound("warp");
}

function goUp(index: number) {
  if (index < 0) return;
  if (isTransitioning) return;
  isTransitioning = true;
  const targetId = breadcrumbs.value[index].id;

  // save current
  universeMap.set(currentUniverseId.value, {
    nodes: nodes.value,
    links: links.value,
  });

  // zoom out effect
  d3.select(canvasContainer.value)
    .transition()
    .duration(800)
    .call(
      zoomBehavior.transform as any,
      d3.zoomIdentity.translate(width / 2, height / 2).scale(0.1),
    )
    .on("end", () => {
      breadcrumbs.value = breadcrumbs.value.slice(0, index + 1);
      currentUniverseId.value = targetId;
      const data = universeMap.get(targetId) || { nodes: [], links: [] };
      nodes.value = data.nodes;
      links.value = data.links;

      initSimulation();

      d3.select(canvasContainer.value)
        .transition()
        .duration(800)
        .call(
          zoomBehavior.transform as any,
          d3.zoomIdentity.translate(width / 2, height / 2).scale(1),
        )
        .on("end", () => {
          isTransitioning = false;
        });
    });
}

function diveIntoNode(node: Node) {
  if (isTransitioning) return;
  isTransitioning = true;

  universeMap.set(currentUniverseId.value, {
    nodes: nodes.value,
    links: links.value,
  });

  breadcrumbs.value.push({ id: node.id, label: node.label || "Inner Mind" });
  currentUniverseId.value = node.id;

  // zoom in effect
  d3.select(canvasContainer.value)
    .transition()
    .duration(800)
    .call(
      zoomBehavior.transform as any,
      d3.zoomIdentity
        .translate(width / 2 - node.x * 3, height / 2 - node.y * 3)
        .scale(3),
    )
    .on("end", () => {
      const data = universeMap.get(node.id) || { nodes: [], links: [] };
      nodes.value = data.nodes;
      links.value = data.links;
      initSimulation();

      d3.select(canvasContainer.value)
        .transition()
        .duration(800)
        .call(
          zoomBehavior.transform as any,
          d3.zoomIdentity.translate(width / 2, height / 2).scale(0.5),
        )
        .on("end", () => {
          d3.select(canvasContainer.value)
            .transition()
            .duration(400)
            .call(
              zoomBehavior.transform as any,
              d3.zoomIdentity.translate(width / 2, height / 2).scale(1),
            )
            .on("end", () => {
              isTransitioning = false;
            });
        });
    });
}

function updateForces() {
  if (simulation) {
    simulation.nodes(nodes.value);
    simulation.force(
      "collide",
      d3
        .forceCollide()
        .radius((d: any) => (d.isExpanded ? 220 : 60))
        .iterations(3)
        .strength(0.8),
    );
    simulation.alpha(0.3).restart();
  }
}
const is3DMode = ref(false);
const isFree3DMode = ref(false);
const orthoMode = ref<"iso" | "top" | "front" | "side">("iso");

const animState = {
  isoWeight: 1,
  orbitWeight: 0,
  zSpread: 1,
};

const cameraTheta = ref(0);
const cameraPhi = ref(Math.PI / 4);
const currentModule = ref<string | null>(null);

function navigateToModule(mod: string) {
  if (mod === "home") {
    currentModule.value = null;
    // Surface back up
    if (globalTransform.k > 1) goUp(0);
    return;
  }

  currentModule.value = mod;
  // Find node or create it
  let modNode = nodes.value.find((n) => n.systemModule === mod);
  if (!modNode) {
    const angle =
      ["aura", "lgnn", "self", "trade"].indexOf(mod) * ((Math.PI * 2) / 4);
    modNode = {
      id: "sys_" + mod,
      label:
        mod === "aura"
          ? "Aura Stream"
          : mod === "lgnn"
            ? "LGNN Core"
            : mod === "trade"
              ? "Trade Hub"
              : "Self Hub",
      content: "",
      x: Math.cos(angle) * 2000,
      y: Math.sin(angle) * 2000,
      z: 0,
      vx: 0,
      vy: 0,
      vz: 0,
      systemModule: mod as any,
      manualWidth: 1000,
      manualHeight: 800,
      isExpanded: false,
      theme: "light",
    };
    nodes.value.push(modNode);
    initSimulation();
  }

  // Dive into it!
  diveIntoNode(modNode);
}

function setViewMode(mode: "top" | "iso" | "orbit") {
  const isTop = mode === "top";
  const isIso = mode === "iso";
  const isOrbit = mode === "orbit";

  if (isTop) {
    is3DMode.value = false;
    isFree3DMode.value = false;
    orthoMode.value = "top";
  } else if (isIso) {
    is3DMode.value = true;
    isFree3DMode.value = false;
    orthoMode.value = "iso";
  } else if (isOrbit) {
    isFree3DMode.value = true;
    is3DMode.value = false;
    cameraTheta.value = 0;
    cameraPhi.value = Math.PI / 4;
  }

  // Smooth transition interpolation
  d3.transition()
    .duration(1200)
    .ease(d3.easeCubicInOut)
    .tween("viewTransition", () => {
      const iIso = d3.interpolate(animState.isoWeight, isIso ? 1 : 0);
      const iOrbit = d3.interpolate(animState.orbitWeight, isOrbit ? 1 : 0);
      const iZ = d3.interpolate(animState.zSpread, isTop ? 0.05 : 1);
      return (t) => {
        animState.isoWeight = iIso(t);
        animState.orbitWeight = iOrbit(t);
        animState.zSpread = iZ(t);
        updateProjection();
      };
    });

  if (simulation) simulation.alpha(0.1).restart(); // Agitate physics lightly
}

const activeTags = ref<Set<string>>(new Set());
const previousExpandedState = ref<Map<string, boolean> | null>(null);
const searchQuery = ref("");
const searchSuggestion = ref("");

function updateSearch() {
  if (!searchQuery.value) {
    searchSuggestion.value = "";
    return;
  }
  const queryWords = searchQuery.value.split(/\s+/);
  const lastWord = queryWords[queryWords.length - 1].toLowerCase();
  if (lastWord.startsWith("#")) {
    const match = availableTags.value.find(
      (t) =>
        t.toLowerCase().startsWith(lastWord) && t.toLowerCase() !== lastWord,
    );
    searchSuggestion.value = match || "";
  } else {
    searchSuggestion.value = "";
  }
}

function acceptSearchSuggestion() {
  if (searchSuggestion.value) {
    const words = searchQuery.value.split(/\s+/);
    words[words.length - 1] = searchSuggestion.value;
    searchQuery.value = words.join(" ") + " ";
    searchSuggestion.value = "";
  }
}

const availableTags = computed(() => {
  const tags = new Set<string>();
  nodes.value.forEach((n) => {
    const text = (n.label + " " + n.content).toLowerCase();
    const matches = text.match(/#[\w_]+/g);
    if (matches) matches.forEach((t) => tags.add(t));
  });
  return Array.from(tags).sort();
});

function toggleTagFilter(tag: string) {
  if (activeTags.value.has(tag)) {
    activeTags.value.delete(tag);
  } else {
    activeTags.value.add(tag);
  }
}

function isNodeVisible(node: Node) {
  const matchesSearch = nodeMatchesSearch(node);
  if (!matchesSearch) return false;

  if (activeTags.value.size === 0) return true;
  const text = (node.label + " " + node.content).toLowerCase();
  return Array.from(activeTags.value).some((tag) => text.includes(tag));
}

// --- Initialization ---
let wsUnsubscribe: any = null;
let executionWsUnsubscribe: any = null;

onMounted(() => {
  // Listen to the 54D Matrix & Telemetry
  wsUnsubscribe = setupWebSocketListener("BRAIN_TELEMETRY", (data: any) => {
    if (data.payload && data.payload.centrality) {
      // Apply Orderbook Depth Gravity to nodes based on their centrality in the matrix
      nodes.value.forEach((node) => {
        const symbolStr = node.id.split("@")[0] || node.id;
        if (data.payload.centrality[symbolStr]) {
          const depthScore = data.payload.centrality[symbolStr];
          // Modify node mass and visuals
          node.depthGravity = depthScore * 100;
          if (simulation) {
            // Re-apply physics slightly to simulate the gravity pull
            simulation.alpha(0.1).restart();
          }
        }
      });
    }

    // Process Orderbook Data
    if (data.payload && data.payload.orderbook) {
      const btcOb = data.payload.orderbook["BTCUSDT"];
      if (btcOb && btcOb.length > 0) {
        // btcOb is an array of size 1 (the latest depth payload)
        const latestDepth = btcOb[0];
        const bids = latestDepth.b || latestDepth.bids;
        const asks = latestDepth.a || latestDepth.asks;
        if (bids && asks) {
          orderbookData.value = {
            bids: bids,
            asks: asks,
          };

          // Calculate LGNN Signal Propensity from Orderbook Imbalance
          let bidVol = 0;
          let askVol = 0;
          bids.slice(0, 10).forEach((b: any) => (bidVol += parseFloat(b[1])));
          asks.slice(0, 10).forEach((a: any) => (askVol += parseFloat(a[1])));

          if (bidVol + askVol > 0) {
            const buyRatio = (bidVol / (bidVol + askVol)) * 100;
            lgnnPropensity.value.buy = Math.round(buyRatio);
            lgnnPropensity.value.sell = 100 - lgnnPropensity.value.buy;

            if (buyRatio > 70) lgnnPropensity.value.signal = "STRONG BUY";
            else if (buyRatio < 30) lgnnPropensity.value.signal = "STRONG SELL";
            else if (buyRatio > 55) lgnnPropensity.value.signal = "BUY";
            else if (buyRatio < 45) lgnnPropensity.value.signal = "SELL";
            else lgnnPropensity.value.signal = "NEUTRAL";

            // Trigger visual pulse on significant shift
            if (Math.abs(buyRatio - 50) > 15) {
              lgnnPropensity.value.isPulsing = true;
              setTimeout(() => {
                lgnnPropensity.value.isPulsing = false;
              }, 500);
            }
          }
        }
      }
    }
  });

  // Listen to Execution Events (Villain Arc: Autonomous Trades)
  executionWsUnsubscribe = setupWebSocketListener(
    "EXECUTION_UPDATE",
    (data: any) => {
      const trade = data.trade || data;
      if (trade && trade.symbol) {
        // Create a temporary "Strike Node" to visualize the execution
        const strikeId = `STRIKE_${Date.now()}`;
        const isLong =
          trade.side?.toUpperCase() === "LONG" ||
          trade.side?.toUpperCase() === "BUY";
        const color = isLong ? "#22c55e" : "#ef4444"; // Green for BUY, Red for SELL

        const strikeNode: Node = {
          id: strikeId,
          label: `${trade.side} ${trade.symbol}`,
          content: `Size: ${trade.quantity}`,
          color: color,
          isExpanded: true,
          x: width / 2 + (Math.random() - 0.5) * 500,
          y: height / 2 - 300,
          z: 0,
          vx: 0,
          vy: 0,
          vz: 0,
          depthGravity: 50, // Heavy node
          theme: "dark",
        };

        nodes.value.push(strikeNode);

        // Link to the target asset if it exists
        const targetSymbol = trade.symbol.replace("-USDT", "");
        const targetNode = nodes.value.find(
          (n) => n.id.includes(targetSymbol) || n.label.includes(targetSymbol),
        );
        if (targetNode) {
          links.value.push({
            source: strikeId,
            target: targetNode.id,
            weight: 5.0, // Very thick laser beam
            isPulsing: true,
          });
        }

        initSimulation();

        // Remove the strike node after 5 seconds (decay)
        setTimeout(() => {
          nodes.value = nodes.value.filter((n) => n.id !== strikeId);
          links.value = links.value.filter(
            (l) => l.source !== strikeId && l.target !== strikeId,
          );
          initSimulation();
        }, 5000);
      }
    },
  );

  // Setup infinite canvas zoom & pan
  zoomBehavior = d3
    .zoom()
    .filter(
      (e) =>
        !e.shiftKey && e.type !== "dblclick" && (!e.button || e.button === 0),
    )
    .scaleExtent([0.1, 8])
    .on("zoom", (e) => {
      globalTransform = e.transform;
      updateProjection();

      if (isTransitioning) return;

      // Auto-Dive (Zoom in)
      if (globalTransform.k > 5.5) {
        const cx = width / 2;
        const cy = height / 2;
        let closestNode = null;
        let minDist = Infinity;

        nodes.value.forEach((n) => {
          const dx = (n.sx || 0) - cx;
          const dy = (n.sy || 0) - cy;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < minDist) {
            minDist = dist;
            closestNode = n;
          }
        });

        if (closestNode && minDist < 400) {
          diveIntoNode(closestNode);
        }
      }
      // Auto-Surface (Zoom out)
      else if (
        globalTransform.k <= 0.3 &&
        breadcrumbs.value.length > 1 &&
        !isTransitioning
      ) {
        goUp(breadcrumbs.value.length - 2);
      }
    });

  if (canvasContainer.value) {
    d3.select(canvasContainer.value)
      .call(zoomBehavior)
      .on("dblclick.zoom", null);

    let isOrbiting = false;
    let lastOrbitX = 0;
    let lastOrbitY = 0;

    // Mouse orbit
    canvasContainer.value.addEventListener("mousedown", (e: MouseEvent) => {
      if (
        isFree3DMode.value &&
        (e.button === 2 || e.altKey || e.ctrlKey || e.shiftKey || e.metaKey)
      ) {
        isOrbiting = true;
        lastOrbitX = e.clientX;
        lastOrbitY = e.clientY;
        e.preventDefault();
        e.stopPropagation();
      }
    });

    // Touch orbit (3 fingers)
    canvasContainer.value.addEventListener("touchstart", (e: TouchEvent) => {
      if (isFree3DMode.value && e.touches.length === 3) {
        isOrbiting = true;
        lastOrbitX =
          (e.touches[0].clientX + e.touches[1].clientX + e.touches[2].clientX) /
          3;
        lastOrbitY =
          (e.touches[0].clientY + e.touches[1].clientY + e.touches[2].clientY) /
          3;
        e.preventDefault();
        e.stopPropagation();
      }
    });

    window.addEventListener("mousemove", (e: MouseEvent) => {
      if (isOrbiting && isFree3DMode.value) {
        const dx = e.clientX - lastOrbitX;
        const dy = e.clientY - lastOrbitY;
        cameraTheta.value -= dx * 0.005;
        cameraPhi.value -= dy * 0.005;
        cameraPhi.value = Math.max(
          -Math.PI / 2.1,
          Math.min(Math.PI / 2.1, cameraPhi.value),
        );

        lastOrbitX = e.clientX;
        lastOrbitY = e.clientY;
        updateProjection();
      }
    });

    window.addEventListener(
      "touchmove",
      (e: TouchEvent) => {
        if (isOrbiting && isFree3DMode.value && e.touches.length === 3) {
          const cx =
            (e.touches[0].clientX +
              e.touches[1].clientX +
              e.touches[2].clientX) /
            3;
          const cy =
            (e.touches[0].clientY +
              e.touches[1].clientY +
              e.touches[2].clientY) /
            3;
          const dx = cx - lastOrbitX;
          const dy = cy - lastOrbitY;
          cameraTheta.value -= dx * 0.005;
          cameraPhi.value -= dy * 0.005;
          cameraPhi.value = Math.max(
            -Math.PI / 2.1,
            Math.min(Math.PI / 2.1, cameraPhi.value),
          );

          lastOrbitX = cx;
          lastOrbitY = cy;
          updateProjection();
        }
      },
      { passive: false },
    );

    window.addEventListener("mouseup", () => {
      isOrbiting = false;
    });
    window.addEventListener("touchend", () => {
      isOrbiting = false;
    });

    // Global context menu intercept to prevent Vivaldi/Chrome mouse gestures & tabs in 3D mode
    window.addEventListener("contextmenu", (e: MouseEvent) => {
      if (isFree3DMode.value) e.preventDefault();
    });

    // Tab Navigation
    let activeTabIndex = -1;
    window.addEventListener("keydown", (e: KeyboardEvent) => {
      if (e.key === "Tab") {
        const activeTag = document.activeElement?.tagName.toLowerCase();
        // If user is editing text, let tab work natively or do nothing
        if (activeTag === "input" || activeTag === "textarea") return;

        e.preventDefault();
        if (nodes.value.length === 0) return;

        activeTabIndex = (activeTabIndex + 1) % nodes.value.length;
        const targetNode = nodes.value[activeTabIndex];
        if (targetNode) diveIntoNode(targetNode);
      } else if (e.key === "Delete" || e.key === "Backspace") {
        const activeTag = document.activeElement?.tagName.toLowerCase();
        if (activeTag === "input" || activeTag === "textarea") return;
        if (nodes.value.some((n) => n.isSelected)) {
          deleteNode();
        }
      } else if (e.key === "Escape") {
        const activeTag = document.activeElement?.tagName.toLowerCase();
        if (activeTag === "input" || activeTag === "textarea") {
          (document.activeElement as HTMLElement).blur();
        } else {
          nodes.value.forEach((n) => (n.isSelected = false));
        }
      } else if (
        ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.key)
      ) {
        const activeTag = document.activeElement?.tagName.toLowerCase();
        if (activeTag === "input" || activeTag === "textarea") return;
        e.preventDefault();
        if (nodes.value.length === 0) return;

        if (e.key === "ArrowRight" || e.key === "ArrowDown") {
          activeTabIndex = (activeTabIndex + 1) % nodes.value.length;
        } else {
          activeTabIndex =
            (activeTabIndex - 1 + nodes.value.length) % nodes.value.length;
        }

        const targetNode = nodes.value[activeTabIndex];
        if (targetNode) {
          nodes.value.forEach((n) => (n.isSelected = false));
          targetNode.isSelected = true;

          if (zoomBehavior && canvasContainer.value) {
            d3.select(canvasContainer.value)
              .transition()
              .duration(400)
              .call(
                zoomBehavior.transform as any,
                d3.zoomIdentity
                  .translate(
                    width / 2 - targetNode.x,
                    height / 2 - targetNode.y,
                  )
                  .scale(1),
              );
          }
        }
      }
    });
  }

  // Merged from duplicate onMounted
  window.addEventListener("resize", handleResize);

  // Inject a guaranteed test ghost node
  nodes.value.push({
    id: "test_ghost_01",
    label: "Test Ghost Signal",
    content: "This is a test ghost node. If you see this, CSS is working!",
    x: window.innerWidth / 2,
    y: window.innerHeight / 2,
    z: 10,
    vx: 0,
    vy: 0,
    vz: 0,
    isGhost: true,
    source_peer: "System",
    thought_topic: "Debug",
    scale: 1,
    targetScale: 1,
    theme: "dark",
  } as any);

  fetchGraphData();
  renderLoop();
});

const gossips = ref<any[]>([]);

async function fetchGossip() {
  try {
    const baseUrl = (API_BASE || "http://127.0.0.1:8001").replace(/\/api$/, "");
    const res = await fetch(`${baseUrl}/aethelnet/graph/public`);
    if (!res.ok) return;
    const rawGossips = await res.json();

    const currentIds = new Set(nodes.value.map((n) => n.id));
    let ghostsAdded = false;

    rawGossips.forEach((g) => {
      if (!currentIds.has(g.id)) {
        nodes.value.push({
          id: g.id,
          label: g.label || g.thought_topic || "Unknown Signal",
          content: g.content || `Extracted from ${g.source_peer}`,
          x: width / 2 + (Math.random() - 0.5) * 800,
          y: height / 2 + (Math.random() - 0.5) * 800,
          isGhost: true,
          source_peer: g.source_peer,
          thought_topic: g.thought_topic,
          theme: Math.random() > 0.5 ? "light" : "dark",
        } as any);
        ghostsAdded = true;
      }
    });

    if (ghostsAdded) {
      initSimulation();
    }
  } catch (err) {
    console.error("Failed to fetch gossip", err);
  }
}

let saveTimeout: any = null;
function triggerSave() {
  if (saveTimeout) clearTimeout(saveTimeout);
  saveTimeout = setTimeout(async () => {
    try {
      const url = API_BASE ? `${API_BASE}/lgnn/graph` : "/api/lgnn/graph";

      const payload = {
        nodes: nodes.value
          .filter((n) => !n.isGhost)
          .map((n) => ({
            id: n.id,
            label: n.label,
            content: n.content,
            color: n.color,
            theme: n.theme,
          })),
        links: links.value.map((l) => ({
          source: (l.source as any).id || l.source,
          target: (l.target as any).id || l.target,
          weight: (l as any).weight || 1,
        })),
      };

      await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } catch (err) {
      console.error("Failed to save graph state:", err);
    }
  }, 1000);
}

async function fetchGraphData() {
  try {
    const url = API_BASE ? `${API_BASE}/lgnn/graph` : "/api/lgnn/graph";
    const res = await fetch(url);
    if (!res.ok) return;
    const data = await res.json();

    // FILTER: User Space only shows their personal thought nodes (n_*) and explicit system modules (trade, settings, etc.)
    // We hide the massive Aethelnet network (seed_*, peer_*) to prevent overwhelming the sanctuary.
    const personalNodes = data.nodes.filter((n: any) => {
      // Keep user nodes
      if (n.id && n.id.startsWith("n_")) return true;
      const systemModules = ["self", "settings", "aura"];
      if (systemModules.includes(n.id)) return true;
      if (["self", "settings", "aura"].includes(n.systemModule))
        return true;
      return false;
    });

    // Ensure system nodes exist
    const requiredSystemNodes = [
      {
        id: "settings",
        label: "Settings",
        systemModule: "settings",
        color: "#d97706",
      },
      { id: "self", label: "Self", systemModule: "self", color: "#8b5cf6" },
      { id: "aura", label: "Aura", systemModule: "aura", color: "#ec4899" },
    ];

    requiredSystemNodes.forEach((sysNode, index) => {
      if (!personalNodes.find((n: any) => n.id === sysNode.id)) {
        personalNodes.push({
          id: sysNode.id,
          label: sysNode.label,
          content: "System Module",
          x: 100 + index * 150,
          y: 100,
          color: sysNode.color,
          scale: 1.5,
          isPinned: true,
          systemModule: sysNode.systemModule,
          status: "Online",
          isSelected: false,
          isExpanded: false,
          theme: "light",
        });
      }
    });

    const existingNodeMap = new Map(nodes.value.map((n) => [n.id, n]));
    const ghostNodes = nodes.value.filter((n) => n.isGhost);

    nodes.value = [
      ...personalNodes.map((n: any) => {
        const existing = existingNodeMap.get(n.id);
        const startX = existing?.x ?? width / 2 + (Math.random() - 0.5) * 400;
        const startY = existing?.y ?? height / 2 + (Math.random() - 0.5) * 400;
        let displayLabel = existing?.label || n.label || "";
        if (displayLabel.startsWith("n_")) {
          displayLabel = n.content
            ? n.content.substring(0, 20) + "..."
            : "Network Thought";
        }

        return {
          ...n,
          x: startX,
          y: startY,
          preLgnnX: existing?.preLgnnX ?? startX,
          preLgnnY: existing?.preLgnnY ?? startY,
          z: existing?.z ?? Math.random() * 50,
          vx: existing?.vx ?? 0,
          vy: existing?.vy ?? 0,
          vz: existing?.vz ?? 0,
          isExpanded: existing?.isExpanded ?? false,
          label: displayLabel,
          content: existing?.content || n.content || "",
          color: existing?.color || n.color,
          theme: existing?.theme || n.theme || "light",
        };
      }),
      ...ghostNodes,
    ];

    const validIds = new Set(personalNodes.map((n: any) => n.id));
    links.value = data.links
      .filter((l: any) => validIds.has(l.source) && validIds.has(l.target))
      .map((l: any) => ({
        source: l.source,
        target: l.target,
        weight: l.weight || 1,
      }));

    initSimulation();

    // Start pulsing from LGNN reservoir
    if (!(window as any)._lgnnPulseInterval) {
      (window as any)._lgnnPulseInterval = setInterval(pollLgnnPulses, 1500);
    }
  } catch (err) {
    console.error("Failed to fetch graph data", err);
  }
}

async function pollLgnnPulses() {
  if (isPaused.value) return;
  try {
    const url = API_BASE ? `${API_BASE}/lgnn/graph` : "/api/lgnn/graph";
    const res = await fetch(url);
    if (!res.ok) return;
    const data = await res.json();

    const pulseMap = new Map<string, any>(data.nodes.map((n: any) => [n.id, n]));

    // Update existing nodes
    nodes.value.forEach((node) => {
      const pulse = pulseMap.get(node.id);
      if (pulse) {
        node.mean_activation = pulse.mean_activation;
        node.targetScale = Math.max(
          0.3,
          0.8 + Math.abs(pulse.mean_activation || 0) * 1.5,
        ); // Prevent shrinking to 0
      }
    });

    // Add NEW nodes that we don't have yet!
    let addedNew = false;
    const existingIds = new Set(nodes.value.map((n) => n.id));
    for (const remoteNode of data.nodes) {
      if (!existingIds.has(remoteNode.id)) {
        // Apply the same filter as fetchGraphData
        let keep = false;
        if (remoteNode.id && remoteNode.id.startsWith("n_")) keep = true;
        const systemModules = ["trade", "self", "settings", "aura"];
        if (systemModules.includes(remoteNode.id)) keep = true;
        if (systemModules.includes(remoteNode.systemModule)) keep = true;

        if (keep) {
          nodes.value.push({
            ...remoteNode,
            x: width / 2 + (Math.random() - 0.5) * 200,
            y: height / 2 + (Math.random() - 0.5) * 200,
            z: (Math.random() - 0.5) * 50,
            vx: 0,
            vy: 0,
            vz: 0,
            targetScale: 1,
            scale: 0.1,
            isExpanded: false,
            theme: Math.random() > 0.5 ? "light" : "dark",
          });
          addedNew = true;
        }
      }
    }

    // Add NEW links
    if (addedNew) {
      const existingLinkIds = new Set(
        links.value.map((l) => {
          const s = typeof l.source === "object" ? l.source.id : l.source;
          const t = typeof l.target === "object" ? l.target.id : l.target;
          return `${s}_${t}`;
        }),
      );
      for (const rl of data.links) {
        if (!existingLinkIds.has(`${rl.source}_${rl.target}`)) {
          links.value.push({
            source: rl.source,
            target: rl.target,
            weight: rl.weight || 1,
          });
        }
      }
      initSimulation(); // Restart physics with new nodes
    } else {
      // Just agitate slightly
      if (simulation) simulation.alpha(0.05).restart();
    }
  } catch (err) {
    // silently fail pulse
  }
}

function initSimulation() {
  if (simulation) simulation.stop();

  simulation = d3
    .forceSimulation(nodes.value)
    .alphaDecay(0.02)
    .velocityDecay(0.4)
    .force("charge", d3.forceManyBody().strength(-900).distanceMax(1200))
    .force("center", d3.forceCenter(width / 2, height / 2).strength(0.02))
    .force(
      "collide",
      d3
        .forceCollide()
        .radius((d: any) => (d.isExpanded ? 260 : ((d.targetScale || 1.0) * (1.0 + getConnectedLinksCount(d.id) * 0.15) * 60)))
        .iterations(3)
        .strength(0.8),
    )
    .force(
      "link",
      d3
        .forceLink(links.value)
        .id((d: any) => d.id)
        .distance(220)
        .strength(0.025),
    )
    .on("tick", () => {
      // Inject pseudo 3D physics for Z-axis
      const n = nodes.value.length;
      for (let i = 0; i < n; i++) {
        const node = nodes.value[i];
        if (node.isPinned) continue;

        if (typeof node.z !== "number") node.z = (Math.random() - 0.5) * 200;
        if (typeof node.vz !== "number") node.vz = 0;

        // Z-axis gravity towards 0
        node.vz -= node.z * 0.005;

        // Z-axis repulsion
        for (let j = i + 1; j < n; j++) {
          const other = nodes.value[j];
          if (other.isPinned) continue;

          if (typeof other.z !== "number")
            other.z = (Math.random() - 0.5) * 200;
          if (typeof other.vz !== "number") other.vz = 0;

          const dx = node.x - other.x;
          const dy = node.y - other.y;
          const dz = node.z - other.z;
          const distSq = dx * dx + dy * dy + dz * dz;

          if (distSq < 100000) {
            // approx 300 radius
            const dist = Math.sqrt(distSq) + 0.1;
            const force = 300 / distSq;
            node.vz += (dz / dist) * force;
            other.vz -= (dz / dist) * force;
          }
        }

        node.vz *= 0.85; // Z friction
        node.z += node.vz;
      }

      updateProjection();

      // Hardware saver: Hard stop simulation quickly to save battery
      if (simulation.alpha() < 0.1) {
        simulation.stop();
      }
    });
}

// --- Projection ---
let projectionTicking = false;
function updateProjection() {
  if (projectionTicking) return;
  projectionTicking = true;
  requestAnimationFrame(() => {
    projectionTicking = false;
    performProjection();
  });
}

function performProjection() {
  const { x: tx, y: ty, k } = globalTransform;
  const rad45 = Math.PI / 4;

  nodes.value.forEach((node) => {
    if (node.isPinned) {
      node.sx = node.pinnedX ?? node.x ?? 100;
      node.sy = node.pinnedY ?? node.y ?? 100;
      node.scale = 1;
      (node as any)._zDepth = 1000; // Always on top
      return;
    }

    // Base 2D top view
    let screenX = tx + node.x * k;
    let screenY = ty + node.y * k;
    let safeZ = (node.z || 0) * animState.zSpread;
    let zDepth = safeZ;

    // Mix Iso
    if (animState.isoWeight > 0) {
      const rotX = node.x * Math.cos(rad45) - node.y * Math.sin(rad45);
      const rotY = node.x * Math.sin(rad45) + node.y * Math.cos(rad45);
      const isoX = tx + rotX * k;
      const isoY = ty + rotY * k * 0.5 - safeZ * k * 2;
      screenX =
        screenX * (1 - animState.isoWeight) + isoX * animState.isoWeight;
      screenY =
        screenY * (1 - animState.isoWeight) + isoY * animState.isoWeight;
      zDepth =
        zDepth * (1 - animState.isoWeight) +
        (-rotX - rotY + safeZ * 2) * animState.isoWeight;
    }

    // Mix Orbit
    if (animState.orbitWeight > 0) {
      const ct = Math.cos(cameraTheta.value);
      const st = Math.sin(cameraTheta.value);
      const cp = Math.cos(cameraPhi.value);
      const sp = Math.sin(cameraPhi.value);

      const dx = node.x;
      const dy = node.y;
      const dz = safeZ * 2;

      const cx = dx * ct - dy * st;
      const cy = dx * st + dy * ct;

      const px = cx;
      const py = cy * cp - dz * sp;
      const pz = cy * sp + dz * cp;

      const orbitX = tx + px * k;
      const orbitY = ty + py * k;

      screenX =
        screenX * (1 - animState.orbitWeight) + orbitX * animState.orbitWeight;
      screenY =
        screenY * (1 - animState.orbitWeight) + orbitY * animState.orbitWeight;
      zDepth =
        zDepth * (1 - animState.orbitWeight) + -pz * animState.orbitWeight;
    }

    const baseScale = node.targetScale || 1.0;
    if (!(node as any).currentScale) (node as any).currentScale = 1.0;
    (node as any).currentScale +=
      (baseScale - (node as any).currentScale) * 0.05;

    node.sx = screenX;
    node.sy = screenY;
    node.scale = Math.sqrt(k) * (node as any).currentScale * (0.9 + zDepth / 2000);
    (node as any)._zDepth = zDepth;
  });
  const nodeMap = new Map();
  nodes.value.forEach((n) => nodeMap.set(n.id, n));

  projectedLinks.value = links.value
    .map((link) => {
      const source =
        typeof link.source === "object"
          ? link.source
          : nodeMap.get(link.source);
      const target =
        typeof link.target === "object"
          ? link.target
          : nodeMap.get(link.target);

      if (
        !source ||
        !target ||
        typeof source.sx === "undefined" ||
        typeof target.sx === "undefined"
      ) {
        return {
          x1: 0,
          y1: 0,
          x2: 0,
          y2: 0,
          d: "",
          weight: 0,
          isPulsing: false,
        };
      }

      const dx = target.sx - source.sx;
      const dy = target.sy - source.sy;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      // Organic tension curve (gentle arc)
      const bend = dist * 0.15;
      const midX = (source.sx + target.sx) / 2 - (dy / dist) * bend;
      const midY = (source.sy + target.sy) / 2 + (dx / dist) * bend;

      const d = `M ${source.sx},${source.sy} Q ${midX},${midY} ${target.sx},${target.sy}`;
      return {
        x1: source.sx,
        y1: source.sy,
        x2: target.sx,
        y2: target.sy,
        d: d,
        weight: link.weight,
        isPulsing: link.isPulsing,
      };
    })
    .filter((l) => l.d);
}

function renderLoop() {
  updateProjection();
  animationFrameId = requestAnimationFrame(renderLoop);
}

function screenToGraph(clientX: number, clientY: number, nodeZ: number = 0) {
  const { x: tx, y: ty, k } = globalTransform;
  let cx = (clientX - tx) / k;
  let cy = (clientY - ty) / k;

  if (is3DMode.value) {
    const safeZ = nodeZ || 0;
    const rotX = (clientX - tx) / k;
    const rotY = (clientY - ty + safeZ * k * 2) / (k * 0.5);
    const rad45 = Math.PI / 4;
    cx = rotX * Math.cos(rad45) + rotY * Math.sin(rad45);
    cy = -rotX * Math.sin(rad45) + rotY * Math.cos(rad45);
  } else if (isFree3DMode.value) {
    // Approximate inverse rotation for smooth dragging in 3D mode
    const ct = Math.cos(-cameraTheta.value);
    const st = Math.sin(-cameraTheta.value);
    const dx = (clientX - tx) / k;
    const dy = (clientY - ty) / k;
    cx = dx * ct - dy * st;
    cy = dx * st + dy * ct;
  }
  return { x: cx, y: cy };
}

let activeDragNode: Node | null = null;
let pressTimer: number | null = null;
let isLongPress = false;
let dragOffsetX = 0;
let dragOffsetY = 0;

// For multi-select dragging
let activeDragNodes: {
  node: Node;
  offsetX: number;
  offsetY: number;
  pinnedOffsetX: number;
  pinnedOffsetY: number;
}[] = [];

function startDrag(event: MouseEvent | TouchEvent, node: Node) {
  activeDragNode = node;
  node.isDragged = true;
  isLongPress = false;
  wasDragged = false;

  const startX =
    "touches" in event
      ? (event as TouchEvent).touches[0].clientX
      : (event as MouseEvent).clientX;
  const startY =
    "touches" in event
      ? (event as TouchEvent).touches[0].clientY
      : (event as MouseEvent).clientY;

  // Select node if not selected, otherwise use existing selection
  if (
    !node.isSelected &&
    !("shiftKey" in event && event.shiftKey) &&
    !("ctrlKey" in event && event.ctrlKey) &&
    !("metaKey" in event && event.metaKey)
  ) {
    nodes.value.forEach((n) => (n.isSelected = false));
    node.isSelected = true;
  } else if (!node.isSelected) {
    node.isSelected = true;
  }

  // Populate activeDragNodes with all selected nodes
  activeDragNodes = nodes.value
    .filter((n) => n.isSelected)
    .map((n) => {
      const mouseGraphCoords = screenToGraph(startX, startY, n.z || 0);
      return {
        node: n,
        offsetX: mouseGraphCoords.x - (n.x || 0),
        offsetY: mouseGraphCoords.y - (n.y || 0),
        pinnedOffsetX: n.isPinned ? startX - (n.pinnedX || 0) : 0,
        pinnedOffsetY: n.isPinned ? startY - (n.pinnedY || 0) : 0,
      };
    });

  // Calculate mouse offset from the node's physical center so it doesn't snap/jump
  const mouseGraphCoords = screenToGraph(startX, startY, node.z || 0);
  dragOffsetX = mouseGraphCoords.x - (node.x || 0);
  dragOffsetY = mouseGraphCoords.y - (node.y || 0);

  // Start long press timer
  pressTimer = window.setTimeout(() => {
    if (wasDragged) return; // Don't spawn child if user is already dragging
    isLongPress = true;
    if (navigator.vibrate) navigator.vibrate(20); // Subtle haptic feedback

    // Spawn the child node and seamlessly transfer the drag focus
    const childNode = spawnChildNode(node);

    // Release the parents
    activeDragNodes.forEach((item) => {
      item.node.isDragged = false;
      item.node.fx = null;
      item.node.fy = null;
    });
    activeDragNodes = [];

    // Grab the new child
    activeDragNode = childNode;
    activeDragNode.isDragged = true;
    nodes.value.forEach((n) => (n.isSelected = false));
    childNode.isSelected = true;

    // Reset offset for the child since it spawns at exactly the mouse position
    dragOffsetX = 0;
    dragOffsetY = 0;
    const coords = screenToGraph(startX, startY, childNode.z);
    activeDragNode.fx = coords.x;
    activeDragNode.fy = coords.y;
    activeDragNodes.push({
      node: childNode,
      offsetX: 0,
      offsetY: 0,
      pinnedOffsetX: 0,
      pinnedOffsetY: 0,
    });
  }, 600); // 600ms long press

  if (simulation) simulation.alphaTarget(0.3).restart();

  const moveHandler = (e: MouseEvent | TouchEvent) => {
    if (!activeDragNode || activeDragNodes.length === 0) return;
    const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
    const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;

    if (Math.hypot(clientX - startX, clientY - startY) > 5) {
      wasDragged = true;
      // Cancel long press if user moves the finger BEFORE 600ms
      if (pressTimer) {
        clearTimeout(pressTimer);
        pressTimer = null;
      }
    }

    activeDragNodes.forEach((item) => {
      const n = item.node;
      n.isDragged = true;
      if (n.isPinned) {
        n.pinnedX = clientX - item.pinnedOffsetX;
        n.pinnedY = clientY - item.pinnedOffsetY;
        n.sx = n.pinnedX;
        n.sy = n.pinnedY;
      } else {
        const coords = screenToGraph(clientX, clientY, n.z || 0);
        n.fx = coords.x - item.offsetX;
        n.fy = coords.y - item.offsetY;
      }
    });
  };

  const endHandler = () => {
    if (pressTimer) {
      clearTimeout(pressTimer);
      pressTimer = null;
    }

    activeDragNodes.forEach((item) => {
      const n = item.node;
      if (!isLgnnMode.value) {
        n.preLgnnX = n.x;
        n.preLgnnY = n.y;
      }
      n.isDragged = false;
      n.fx = null;
      n.fy = null;
    });

    activeDragNode = null;
    activeDragNodes = [];

    if (simulation) simulation.alphaTarget(0);
    triggerSave();

    window.removeEventListener("mousemove", moveHandler);
    window.removeEventListener("touchmove", moveHandler);
    window.removeEventListener("mouseup", endHandler);
    window.removeEventListener("touchend", endHandler);
  };

  window.addEventListener("mousemove", moveHandler, { passive: false });
  window.addEventListener("touchmove", moveHandler, { passive: false });
  window.addEventListener("mouseup", endHandler);
  window.addEventListener("touchend", endHandler);
}

function startFastLink(e: MouseEvent | TouchEvent, node: Node) {
  isDrawingLink = true;
  sourceNodeForLink = node;
  const clientX =
    "touches" in e ? e.touches[0].clientX : (e as MouseEvent).clientX;
  const clientY =
    "touches" in e ? e.touches[0].clientY : (e as MouseEvent).clientY;
  fingerPos.x = clientX;
  fingerPos.y = clientY;
  tempLink.value = {
    x1: node.sx || 0,
    y1: node.sy || 0,
    x2: clientX,
    y2: clientY,
  };

  const moveHandler = (moveEvent: MouseEvent | TouchEvent) => {
    fingerPos.x =
      "touches" in moveEvent
        ? moveEvent.touches[0].clientX
        : (moveEvent as MouseEvent).clientX;
    fingerPos.y =
      "touches" in moveEvent
        ? moveEvent.touches[0].clientY
        : (moveEvent as MouseEvent).clientY;
  };

  const endHandler = (upEvent: MouseEvent | TouchEvent) => {
    window.removeEventListener("mousemove", moveHandler);
    window.removeEventListener("touchmove", moveHandler);
    window.removeEventListener("mouseup", endHandler);
    window.removeEventListener("touchend", endHandler);

    const clientX =
      "changedTouches" in upEvent
        ? upEvent.changedTouches[0].clientX
        : (upEvent as MouseEvent).clientX;
    const clientY =
      "changedTouches" in upEvent
        ? upEvent.changedTouches[0].clientY
        : (upEvent as MouseEvent).clientY;
    const { x: tx, y: ty, k } = globalTransform;
    const canvasX = (clientX - tx) / k;
    const canvasY = (clientY - ty) / k;

    let targetNode = null;
    for (const n of nodes.value) {
      if (n.id === sourceNodeForLink!.id) continue;
      const dx = (n.sx || 0) - clientX;
      const dy = (n.sy || 0) - clientY;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < (n.isExpanded ? 120 : 50) * k) {
        targetNode = n;
        break;
      }
    }

    if (targetNode) {
      const existingLinkIndex = links.value.findIndex(
        (l) =>
          (((l.source as Node).id || l.source) === sourceNodeForLink!.id &&
            ((l.target as Node).id || l.target) === targetNode!.id) ||
          (((l.source as Node).id || l.source) === targetNode!.id &&
            ((l.target as Node).id || l.target) === sourceNodeForLink!.id),
      );

      if (existingLinkIndex >= 0) {
        // Toggle (remove) the link if it already exists
        links.value.splice(existingLinkIndex, 1);
        initSimulation();
      } else {
        // Create new link
        links.value.push({
          source: sourceNodeForLink!.id,
          target: targetNode.id,
          weight: 1,
        });
        initSimulation();

        if (targetNode.agentType === "decoder") {
          if ((targetNode as Node).hasSpawnedChildren)
            reDecode(targetNode as Node);
          else
            triggerDecoderReaction(
              targetNode as Node,
              sourceNodeForLink as Node,
            );
        } else if (sourceNodeForLink!.agentType === "decoder") {
          if ((sourceNodeForLink as Node).hasSpawnedChildren)
            reDecode(sourceNodeForLink as Node);
          else triggerDecoderReaction(sourceNodeForLink as Node, targetNode);
        }

        if (targetNode.agentType === "evolve") {
          if ((targetNode as Node).hasSpawnedChildren)
            reEvolve(targetNode as Node);
          else triggerEvolveReaction(targetNode as Node);
        } else if (sourceNodeForLink!.agentType === "evolve") {
          if ((sourceNodeForLink as Node).hasSpawnedChildren)
            reEvolve(sourceNodeForLink as Node);
          else triggerEvolveReaction(sourceNodeForLink as Node);
        }
      }
    } else {
      spawnChildNodeAt(sourceNodeForLink!, canvasX, canvasY);
    }

    isDrawingLink = false;
    sourceNodeForLink = null;
    tempLink.value = null;
  };

  window.addEventListener("mousemove", moveHandler, { passive: false });
  window.addEventListener("touchmove", moveHandler, { passive: false });
  window.addEventListener("mouseup", endHandler);
  window.addEventListener("touchend", endHandler);
}

let lastNodeWidth = 280;
let lastNodeHeight = 180;

function spawnChildNodeAt(parentNode: Node, cx: number, cy: number): Node {
  const initialContent =
    Array.from(activeTags.value).join(" ") +
    (activeTags.value.size > 0 ? "\n\n" : "");
  const newNode: Node = {
    id: "n_" + Math.random().toString(36).substr(2, 9),
    label: "",
    content: initialContent,
    x: cx,
    y: cy,
    z: parentNode.z,
    vx: 0,
    vy: 0,
    vz: 0,
    isExpanded: true, // Auto expand
    manualWidth: lastNodeWidth,
    manualHeight: lastNodeHeight,
    theme: Math.random() > 0.5 ? "light" : "dark",
  };

  nodes.value.push(newNode);
  links.value.push({ source: parentNode.id, target: newNode.id, weight: 1 });
  initSimulation();
  triggerSave();

  return newNode;
}

function spawnChildNode(parentNode: Node): Node {
  const initialContent =
    Array.from(activeTags.value).join(" ") +
    (activeTags.value.size > 0 ? "\n\n" : "");
  const newNode: Node = {
    id: "n_" + Math.random().toString(36).substr(2, 9),
    label: "",
    content: initialContent,
    x: parentNode.x,
    y: parentNode.y, // Spawn exactly on parent to pull out smoothly
    z: parentNode.z,
    vx: 0,
    vy: 0,
    vz: 0,
    isExpanded: true, // Auto expand
    manualWidth: lastNodeWidth,
    manualHeight: lastNodeHeight,
    theme: Math.random() > 0.5 ? "light" : "dark",
  };

  nodes.value.push(newNode);
  links.value.push({ source: parentNode.id, target: newNode.id, weight: 1 });
  initSimulation();
  triggerSave();

  return newNode;
}

function startResize(e: MouseEvent | TouchEvent, node: Node) {
  const startX =
    "touches" in e ? e.touches[0].clientX : (e as MouseEvent).clientX;
  const startY =
    "touches" in e ? e.touches[0].clientY : (e as MouseEvent).clientY;

  const startWidth = node.manualWidth || 280;
  const startHeight = node.manualHeight || 180;

  const moveHandler = (moveEvent: MouseEvent | TouchEvent) => {
    const currentX =
      "touches" in moveEvent
        ? moveEvent.touches[0].clientX
        : (moveEvent as MouseEvent).clientX;
    const currentY =
      "touches" in moveEvent
        ? moveEvent.touches[0].clientY
        : (moveEvent as MouseEvent).clientY;

    // Convert screen deltas to graph scale
    const deltaX = (currentX - startX) / globalTransform.k;
    const deltaY = (currentY - startY) / globalTransform.k;

    node.manualWidth = Math.max(200, startWidth + deltaX);
    node.manualHeight = Math.max(120, startHeight + deltaY);
  };

  const endHandler = () => {
    lastNodeWidth = node.manualWidth || 280;
    lastNodeHeight = node.manualHeight || 180;
    triggerSave();
    window.removeEventListener("mousemove", moveHandler);
    window.removeEventListener("touchmove", moveHandler);
    window.removeEventListener("mouseup", endHandler);
    window.removeEventListener("touchend", endHandler);
  };

  window.addEventListener("mousemove", moveHandler);
  window.addEventListener("touchmove", moveHandler);
  window.addEventListener("mouseup", endHandler);
  window.addEventListener("touchend", endHandler);
}

function toggleExpand(node: Node) {
  if (wasDragged) {
    wasDragged = false;
    return;
  }
  if (isLongPress) {
    isLongPress = false;
    return; // Don't expand if we just triggered a long press
  }

  playSound("blip");
  node.isExpanded = !node.isExpanded;
  if (simulation) {
    simulation.force(
      "collide",
      d3
        .forceCollide()
        .radius((d: any) => (d.isExpanded ? 220 : 60))
        .strength(0.8),
    );
    simulation.alpha(0.3).restart();
  }
}

function onCanvasMouseDown(e: MouseEvent) {
  if (!e.shiftKey) {
    nodes.value.forEach((n) => {
      n.isSelected = false;
    });
  }

  if (e.shiftKey) {
    e.preventDefault();
    lassoState.value.active = true;
    lassoState.value.startX = e.clientX;
    lassoState.value.startY = e.clientY;
    lassoState.value.currentX = e.clientX;
    lassoState.value.currentY = e.clientY;

    // Clear existing selections if not holding ctrl/cmd
    if (!e.ctrlKey && !e.metaKey) {
      nodes.value.forEach((n) => (n.isSelected = false));
    }

    const moveHandler = (moveEvent: MouseEvent) => {
      lassoState.value.currentX = moveEvent.clientX;
      lassoState.value.currentY = moveEvent.clientY;
    };

    const upHandler = () => {
      lassoState.value.active = false;
      window.removeEventListener("mousemove", moveHandler);
      window.removeEventListener("mouseup", upHandler);

      const x1 = Math.min(lassoState.value.startX, lassoState.value.currentX);
      const x2 = Math.max(lassoState.value.startX, lassoState.value.currentX);
      const y1 = Math.min(lassoState.value.startY, lassoState.value.currentY);
      const y2 = Math.max(lassoState.value.startY, lassoState.value.currentY);

      // Select nodes inside the lasso
      nodes.value.forEach((node) => {
        if (node.sx !== undefined && node.sy !== undefined) {
          if (
            node.sx >= x1 &&
            node.sx <= x2 &&
            node.sy >= y1 &&
            node.sy <= y2
          ) {
            node.isSelected = true;
          }
        }
      });
    };

    window.addEventListener("mousemove", moveHandler);
    window.addEventListener("mouseup", upHandler);
  }
}

function addNodeOnCanvas(e: MouseEvent) {
  const coords = screenToGraph(e.clientX, e.clientY);
  const canvasX = coords.x;
  const canvasY = coords.y;

  const initialContent =
    Array.from(activeTags.value).join(" ") +
    (activeTags.value.size > 0 ? "\n\n" : "");

  const newNode: Node = {
    id: "n_" + Math.random().toString(36).substr(2, 9),
    label: "",
    content: initialContent,
    x: canvasX,
    y: canvasY,
    z: 0,
    vx: 0,
    vy: 0,
    vz: 0,
    isExpanded: true,
    manualWidth: lastNodeWidth,
    manualHeight: lastNodeHeight,
    theme: Math.random() > 0.5 ? "light" : "dark",
  };

  nodes.value.push(newNode);
  initSimulation();
  triggerSave();
}

function getSubgraphScale(parentNode: Node) {
  const universe = universeMap.get(parentNode.id);
  if (!universe || !universe.nodes || universe.nodes.length === 0) return 0.1;

  // Find the mathematical bounding box of the sub-graph
  let maxDist = 50; // prevent division by zero
  const cx = winW.value / 2;
  const cy = winH.value / 2;
  for (const n of universe.nodes) {
    const dx = Math.abs((n.x || cx) - cx);
    const dy = Math.abs((n.y || cy) - cy);
    if (dx > maxDist) maxDist = dx;
    if (dy > maxDist) maxDist = dy;
  }

  // Calculate the available space inside the parent node's walls
  const parentW = parentNode.isExpanded ? getExpandedWidth(parentNode) : 120;
  const parentH = parentNode.isExpanded ? getExpandedHeight(parentNode) : 120;
  const availableSpace = Math.min(parentW, parentH) - 40; // 20px padding on all sides

  // Return the ratio to scale the graph perfectly to the walls
  return availableSpace / (maxDist * 2);
}

function getExpandedWidth(node: Node) {
  if (node.manualWidth) return node.manualWidth;
  return 240;
}

function getExpandedHeight(node: Node) {
  if (node.manualHeight) return node.manualHeight;
  const baseSize = 240;
  if (!node.content) return baseSize;
  // Grow organically: +20px for every 50 characters. Cap at +160px (max 400px total).
  const extra = Math.min(160, Math.floor(node.content.length / 50) * 20);
  return baseSize + extra;
}

function onTitleInput(node: Node) {
  node.hasManualTitle = true;
  updateNode(node);
}

function deleteNode(node?: Node) {
  const nodesToDelete = node?.isSelected
    ? nodes.value.filter((n) => n.isSelected)
    : node
      ? [node]
      : nodes.value.filter((n) => n.isSelected);
  if (nodesToDelete.length === 0) return;

  const msg =
    nodesToDelete.length > 1
      ? `Are you sure you want to delete ${nodesToDelete.length} nodes?`
      : `Are you sure you want to delete "${nodesToDelete[0].label}"?`;

  if (confirm(msg)) {
    const idsToDelete = new Set(nodesToDelete.map((n) => n.id));

    // Remove from frontend state
    nodes.value = nodes.value.filter((n) => !idsToDelete.has(n.id));

    // Also remove any links connected to these nodes
    links.value = links.value.filter((l) => {
      const sourceId = typeof l.source === "object" ? l.source.id : l.source;
      const targetId = typeof l.target === "object" ? l.target.id : l.target;
      return !idsToDelete.has(sourceId) && !idsToDelete.has(targetId);
    });

    initSimulation();
    triggerSave();
  }
}

function updateNode(node: Node) {
  updateForces(); // Adapt D3 collision radius immediately
  triggerSave();

  // Continuous Fluid Flow: trigger downstream agents
  links.value.forEach((link) => {
    const sourceId = (link.source as Node).id || link.source;
    const targetId = (link.target as Node).id || link.target;
    if (sourceId === node.id) {
      const targetNode = nodes.value.find((n) => n.id === targetId);
      if (targetNode && targetNode.isAgent && targetNode.hasSpawnedChildren) {
        link.isPulsing = true;
        if (targetNode.agentType === "evolve") {
          reEvolve(targetNode);
        } else if (targetNode.agentType === "decoder") {
          reDecode(targetNode);
        }
        setTimeout(() => {
          link.isPulsing = false;
        }, 2500);
      }
    }
  });

  // Propagate title to inheriting children
  if (node.label) {
    const cleanLabel =
      node.label
        .replace(/#\w+/g, "")
        .replace(/\[\d+\]/g, "")
        .trim() || "Node";
    nodes.value.forEach((child) => {
      if (child.inheritedFromId === node.id && !child.hasManualTitle) {
        child.label = `${cleanLabel} [${child.inheritedIndex}]`;
        // We only propagate 1 level deep for now as it solves the core issue cleanly without infinite loops.
      }
    });
  }

  node.suggestion = "";
  const text = node.content || "";

  // 0. Agent & Tags Parsing
  const fullText = ((node.label || "") + " " + text).toLowerCase();
  if (!fullText.trim()) return;
  let newAgentType = null;
  if (fullText.includes("#spider")) newAgentType = "spider";
  else if (fullText.includes("#decoder")) newAgentType = "decoder";
  else if (fullText.includes("#evolve")) newAgentType = "evolve";

  if (newAgentType && !node.isAgent) {
    node.isAgent = true;
    node.agentType = newAgentType;
    spawnAgentMockup(node);
  } else if (!newAgentType && node.isAgent) {
    node.isAgent = false;
    node.agentType = null;
  }

  // Parse System Modules (#lgnn, #aura, #self)
  if (fullText.includes("#lgnn_core") || fullText.includes("#lgnn")) {
    if (node.systemModule !== "lgnn") {
      node.systemModule = "lgnn";
      node.manualWidth = 1000;
      node.manualHeight = 800;
    }
  } else if (fullText.includes("#aura") || fullText.includes("#stream")) {
    if (node.systemModule !== "aura") {
      node.systemModule = "aura";
      node.manualWidth = 1000;
      node.manualHeight = 800;
    }
  } else if (fullText.includes("#self") || fullText.includes("#hub")) {
    if (node.systemModule !== "self") {
      node.systemModule = "self";
      node.manualWidth = 1000;
      node.manualHeight = 800;
    }
  } else if (fullText.includes("#settings") || fullText.includes("#config")) {
    if (node.systemModule !== "settings") {
      node.systemModule = "settings";
      node.manualWidth = 350;
      node.manualHeight = 350;
    }
  } else {
    node.systemModule = undefined;
  }

  // 1. Tag Autocomplete
  const words = text.split(/\s+/);
  const lastWord = words[words.length - 1];

  if (lastWord.startsWith("#") && lastWord.length > 1) {
    // Gather tags from all nodes
    const allTags = new Set<string>();
    nodes.value.forEach((n) => {
      const matches = (n.label + " " + n.content).match(/#\w+/g);
      if (matches) matches.forEach((t) => allTags.add(t));
      if (matches) matches.forEach((t) => allTags.add(t));
    });

    // LGNN injected base tags
    allTags.add("#aethelnet");
    allTags.add("#lgnn_core");
    allTags.add("#aura");
    allTags.add("#self");
    allTags.add("#settings");
    allTags.add("#spider");
    allTags.add("#decoder");
    allTags.add("#evolve");

    const match = Array.from(allTags).find(
      (t) => t.startsWith(lastWord) && t !== lastWord,
    );
    if (match) {
      node.suggestion = match.substring(lastWord.length);
      return;
    }
  }

  // Predictive Neural Interface (Thought-to-Tag)
  if (text.length > 3 && !text.endsWith(" ")) {
    const txt = text.toLowerCase();
    let predictedTag = "";

    // Map natural language intents to LGNN functions
    if (txt.match(/\\b(suche|finde|crawl|recherchiere)\\b/))
      predictedTag = " #spider";
    else if (txt.match(/\\b(übersetz|entschlüssel|analysier|decode)\\b/))
      predictedTag = " #decoder";
    else if (txt.match(/\\b(verbinde|mische|evolve|kombinier)\\b/))
      predictedTag = " #evolve";
    else if (txt.match(/\\b(einstellungen|parameter|config|optionen)\\b/))
      predictedTag = " #settings";
    else if (txt.match(/\\b(bewusstsein|hub|ich|self)\\b/))
      predictedTag = " #self";
    else if (txt.match(/\\b(netzwerk|ansicht|lgnn|core)\\b/))
      predictedTag = " #lgnn_core";

    // If we predicted a tag and it's not already in the text, suggest it
    if (predictedTag && !fullText.includes(predictedTag.trim())) {
      node.suggestion = predictedTag;
      return;
    }
  }

  // 2. LGNN Auto-Compiler (Natural Language to Pseudo-Code)
  const txt = text.toLowerCase();
  const isCode =
    text.includes("#") || text.includes("def ") || text.includes("=");

  if (!isCode && text.trim().split(" ").length > 3) {
    if ((node as any).suggestionTimeout)
      clearTimeout((node as any).suggestionTimeout);
    (node as any).suggestionTimeout = setTimeout(() => {
      if (node.content === text && node.compiledScript !== "spawned") {
        let compiled = "";
        if (
          txt.includes("suche") ||
          txt.includes("finde") ||
          txt.includes("crawl")
        ) {
          compiled = `#script\n#spider\ntarget = "${node.label || "query"}"\ndepth = 3\nstart_crawl()`;
        } else if (
          txt.includes("übersetz") ||
          txt.includes("entschlüssel") ||
          txt.includes("analysier")
        ) {
          compiled = `#script\n#decoder\ninput_data = read_stream()\nreturn analyze(input_data)`;
        } else if (
          txt.includes("verbinde") ||
          txt.includes("kombinier") ||
          txt.includes("synthetisier")
        ) {
          compiled = `#script\n#evolve\nground_truth = Evolve.synthesize(inputs)\nreturn ground_truth`;
        } else {
          compiled = `#script\ndef process_thought():\n    concept = "${text.substring(0, 20)}..."\n    return LGNN.analyze(concept)`;
        }

        // Spawn it as a new code node!
        node.compiledScript = "spawned";
        node.status = "Compiled to Code";

        const childId = "n_" + Math.random().toString(36).substr(2, 9);
        nodes.value.push({
          id: childId,
          label: "Auto-Script",
          content: compiled,
          x: (node.x || width / 2) + 200,
          y: node.y || height / 2,
          z: node.z,
          vx: 0,
          vy: 0,
          vz: 0,
          isExpanded: true,
          theme: "dark",
        });
        links.value.push({ source: node.id, target: childId, weight: 1 });
        initSimulation();
        triggerSave();
      }
    }, 1200);
    return;
  }

  // Normal ghost text completion for code
  if (text.length > 5 && isCode && text.endsWith(" ")) {
    if ((node as any).suggestionTimeout)
      clearTimeout((node as any).suggestionTimeout);
    (node as any).suggestionTimeout = setTimeout(() => {
      if (node.content === text && !node.suggestion && !node.compiledScript) {
        const mockContinuations = [
          "and organically connects to the network.",
          "which generates a new meta-layer.",
          "adapting the ground truth.",
          "via dynamic Aethelnet routing.",
        ];
        node.suggestion =
          mockContinuations[
            Math.floor(Math.random() * mockContinuations.length)
          ];
      }
    }, 400);
  }
}

function togglePin(node: Node) {
  node.isPinned = !node.isPinned;
  if (node.isPinned) {
    if (node.systemModule) {
      // Huge UI panels (Aura, LGNN) dock perfectly to the right side
      const panelWidth = node.manualWidth || 1000;
      node.pinnedX = window.innerWidth - panelWidth / 2 - 20 + 60;
      node.pinnedY = window.innerHeight / 2 + 60;
    } else {
      // Small pinned thoughts dock to the top-left area neatly
      const existingPinned = nodes.value.filter(
        (n) => n.isPinned && !n.systemModule,
      );
      const stackIndex = existingPinned.length - 1;
      node.pinnedX = 150 + 60;
      node.pinnedY = 150 + stackIndex * 80 + 60;
    }
    // Force immediate update
    node.sx = node.pinnedX;
    node.sy = node.pinnedY;
  } else {
    // Unpin: Convert current screen coords back to world coords
    const coords = screenToGraph(
      node.pinnedX || 100,
      node.pinnedY || 100,
      node.z || 0,
    );
    node.x = node.x || Math.random() * width;
    node.y = node.y || Math.random() * height;
    node.vx = node.vx || 0;
    node.vy = node.vy || 0;
    if (!node.theme) {
      node.theme = "light";
    }
    node.fx = null;
    node.fy = null;
  }
  updateProjection();
  triggerSave();
}

function spawnAgentMockup(node: Node) {
  if (node.hasSpawnedChildren) return;

  if (node.agentType === "decoder") {
    node.status = "Awaiting data stream...";
    return;
  }
  if (node.agentType === "evolve") {
    node.status = "Awaiting inputs...";
    return;
  }

  // Only set to true for agents that spawn immediately (e.g. Spider)
  node.hasSpawnedChildren = true;

  // Simulate LGNN thinking delay
  setTimeout(() => {
    let childCount = 4; // Spiders fetch 4 results

    for (let i = 0; i < childCount; i++) {
      const angle = (i / childCount) * Math.PI * 2;
      const dist = 180;
      const childX = (node.x || width / 2) + Math.cos(angle) * dist;
      const childY = (node.y || height / 2) + Math.sin(angle) * dist;

      let newLabel = "";
      if (node.label && node.label !== "#spider" && node.label !== "#decoder") {
        const cleanLabel = node.label.replace(/#\w+/g, "").trim() || "Agent";
        newLabel = `${cleanLabel} [${i + 1}]`;
      } else {
        newLabel =
          node.agentType === "spider" ? `Result ${i + 1}` : `Decoded ${i + 1}`;
      }

      const childId = "agent_spawn_" + Date.now() + "_" + i;
      nodes.value.push({
        id: childId,
        label: newLabel,
        content:
          node.agentType === "spider"
            ? `Extracted semantic fragment from web spider...`
            : `Translated meaning from LGNN context...`,
        x: childX,
        y: childY,
        sx: childX,
        sy: childY,
        z: node.z,
        vx: 0,
        vy: 0,
        vz: 0,
        isExpanded: false,
        theme: Math.random() > 0.5 ? "light" : "dark",
      });

      links.value.push({
        source: node.id,
        target: childId,
        weight: 1,
      });
    }
    initSimulation(); // Restart physics to integrate new nodes seamlessly
  }, 1200);
}

function triggerDecoderReaction(decoder: Node, sourceNode: Node) {
  if (decoder.hasSpawnedChildren) return;
  decoder.hasSpawnedChildren = true;

  const hasImage = !!sourceNode.imageUrl;

  // Make the decoder node physically grow and expand to show it's working!
  decoder.isExpanded = true;
  decoder.manualWidth = 300;
  decoder.manualHeight = 280;

  decoder.status = hasImage
    ? "Analyzing pixel matrix..."
    : "Decryption in progress...";

  setTimeout(() => {
    decoder.status = "";

    const childId = "decoder_spawn_" + Date.now();
    decoder.spawnedChildId = childId;

    const newNode = {
      id: "node_" + Date.now(),
      label: "New Concept",
      content: "",
      x: width / 2,
      y: height / 2,
      vx: 0,
      vy: 0,
      isExpanded: true,
      color: null,
      theme: Math.random() > 0.5 ? "light" : "dark",
    };

    nodes.value.push({
      id: childId,
      label: hasImage ? "Image Analysis" : "Decoded Output",
      content: hasImage
        ? 'The GNN analyzed the image matrix: "An abstract visual pattern resonating strongly with the current ground truth."'
        : "The GNN decoded the semantics and provides the structured output as a new node.",
      imageUrl: hasImage ? sourceNode.imageUrl : undefined,
      x: (decoder.x || width / 2) + 150,
      y: decoder.y || height / 2,
      sx: (decoder.x || width / 2) + 150,
      sy: decoder.y || height / 2,
      z: decoder.z,
      vx: 0,
      vy: 0,
      vz: 0,
      isExpanded: true,
      manualWidth: hasImage ? 260 : undefined,
      manualHeight: hasImage ? 340 : undefined,
      theme: Math.random() > 0.5 ? "light" : "dark",
    });

    links.value.push({ source: decoder.id, target: childId, weight: 1 });
    initSimulation();
  }, 1800);
}

function triggerEvolveReaction(evolveNode: Node) {
  if (evolveNode.hasSpawnedChildren) return;
  evolveNode.hasSpawnedChildren = true;

  evolveNode.isExpanded = true;
  evolveNode.manualWidth = 320;
  evolveNode.manualHeight = 280;
  evolveNode.status = "Synthesizing converging concepts...";
  evolveNode.content = "[LGNN Evolve]: Analyzing converging semantic fields...";

  setTimeout(() => {
    evolveNode.status = "";
    evolveNode.content =
      "[LGNN Evolve]: Synthesis complete. Ground truth convergence successful.";

    const childId = "evolve_spawn_" + Date.now();
    evolveNode.spawnedChildId = childId;
    nodes.value.push({
      id: childId,
      label: "Evolutionary Synthesis",
      content:
        "The GNN synthesized the divergent sources to extract this meta-structure. The concept successfully evolved.",
      x: (evolveNode.x || width / 2) + 200,
      y: evolveNode.y || height / 2,
      sx: (evolveNode.x || width / 2) + 200,
      sy: evolveNode.y || height / 2,
      z: evolveNode.z,
      vx: 0,
      vy: 0,
      vz: 0,
      isExpanded: true,
      manualWidth: 300,
      manualHeight: 300,
      inheritedFromId: evolveNode.id,
      inheritedIndex: 1,
      hasManualTitle: false,
      theme: Math.random() > 0.5 ? "light" : "dark",
    });

    links.value.push({ source: evolveNode.id, target: childId, weight: 3 });
    initSimulation();
  }, 3500);
}

function acceptSuggestion(node: Node) {
  if (node.suggestion) {
    node.content += node.suggestion;
    node.suggestion = "";
    node.justAcceptedSuggestion = true;
    updateNode(node);
  }
}

async function triggerSpiderPulse(node: Node) {
  node.content +=
    "\n\n[Spider]: Fetched live data streams. Extracting anomaly... Pulse emitted.";
  node.status = "Transmitting data...";

  // Flash screen to indicate trans-universe data flow
  if (currentUniverseId.value !== "root") {
    const flash = document.createElement("div");
    flash.style.position = "fixed";
    flash.style.top = "0";
    flash.style.left = "0";
    flash.style.width = "100vw";
    flash.style.height = "100vh";
    flash.style.backgroundColor = "rgba(14, 165, 233, 0.2)";
    flash.style.pointerEvents = "none";
    flash.style.zIndex = "9999";
    flash.style.transition = "opacity 0.8s ease-out";
    document.body.appendChild(flash);

    // Force reflow
    void flash.offsetWidth;
    flash.style.opacity = "0";
    setTimeout(() => flash.remove(), 800);
  }

  try {
    const baseUrl = (API_BASE || "http://127.0.0.1:8001").replace(/\/api$/, "");
    const res = await fetch(`${baseUrl}/aethelnet/graph/public`);
    if (res.ok) {
      const data = await res.json();
      const rawGossips = Array.isArray(data) ? data : data.gossip || [];
      const currentIds = new Set(nodes.value.map((n) => n.id));

      const newGossips = rawGossips
        .filter((g: any) => !currentIds.has(g.id))
        .sort(() => 0.5 - Math.random())
        .slice(0, 3);

      if (newGossips.length > 0) {
        newGossips.forEach((g: any, i: number) => {
          const angle = (i / newGossips.length) * Math.PI * 2;
          const dist = 180;
          const childX = (node.x || width / 2) + Math.cos(angle) * dist;
          const childY = (node.y || height / 2) + Math.sin(angle) * dist;

          const childNode = {
            id: g.id,
            label: g.label || g.thought_topic || "Unknown Signal",
            content: g.content || `Extracted from ${g.source_peer}`,
            x: childX,
            y: childY,
            sx: childX,
            sy: childY,
            z: node.z,
            vx: 0,
            vy: 0,
            vz: 0,
            isGhost: true,
            source_peer: g.source_peer,
            thought_topic: g.thought_topic,
            theme: Math.random() > 0.5 ? "light" : "dark",
          } as any;

          nodes.value.push(childNode);
          links.value.push({
            source: node,
            target: childNode,
            weight: 0.8,
            isPulsing: true,
          } as any);
        });
        initSimulation();
      } else {
        node.content += "\n\n[Spider]: No new anomalies found on the network.";
      }
    }
  } catch (err) {
    console.error("Spider failed to fetch network data", err);
  }

  // Animate local links
  links.value.forEach((l) => {
    const sId = (l.source as Node).id || l.source;
    const tId = (l.target as Node).id || l.target;

    if (sId === node.id || tId === node.id) {
      l.isPulsing = true;

      const targetId = sId === node.id ? tId : sId;
      const targetNode = nodes.value.find((n) => n.id === targetId);

      if (targetNode) {
        if (
          targetNode.content.includes("#evolve") ||
          targetNode.label === "Evolutionary Synthesis"
        ) {
          setTimeout(() => reEvolve(targetNode), 600);
        } else if (targetNode.agentType === "decoder") {
          setTimeout(() => reDecode(targetNode), 600);
        } else {
          targetNode.status = "Receiving spider pulse...";
          setTimeout(() => {
            targetNode.status = "";
          }, 1500);
        }
      }

      setTimeout(() => {
        l.isPulsing = false;
      }, 1000);
    }
  });

  setTimeout(() => {
    node.status = "";
  }, 1000);
  updateNode(node);
  triggerSave();
}

function reEvolve(evolveNode: Node) {
  // If it's already synthesizing, skip
  if (evolveNode.status === "Synthesizing update...") return;

  // Find the child synthesis node if it exists, or update the evolve node itself
  let targetToUpdate = evolveNode;
  if (evolveNode.spawnedChildId) {
    const child = nodes.value.find((n) => n.id === evolveNode.spawnedChildId);
    if (child) targetToUpdate = child;
  }

  evolveNode.status = "Synthesizing update...";
  setTimeout(() => {
    evolveNode.status = "";
    targetToUpdate.content +=
      "\n\n[LGNN Evolve]: Re-evaluating ground truth based on incoming pulse. Paradigm shifted (Iteration " +
      Math.floor(Math.random() * 1000) +
      ").";
    triggerSave();
  }, 1800);
}

function reDecode(decoderNode: Node) {
  if (decoderNode.status === "Decoding stream...") return;

  let targetToUpdate = decoderNode;
  if (decoderNode.spawnedChildId) {
    const child = nodes.value.find((n) => n.id === decoderNode.spawnedChildId);
    if (child) targetToUpdate = child;
  }

  decoderNode.status = "Decoding stream...";
  setTimeout(() => {
    decoderNode.status = "";
    targetToUpdate.content +=
      "\n\n[Decoder]: New data intercepted. Semantic payload injected into output node.";
    triggerSave();
  }, 1200);
}

// --- Search & Lens Capture ---
function nodeMatchesSearch(node: Node) {
  if (!searchQuery.value.trim()) return true;
  const terms = searchQuery.value.toLowerCase().split(/\s+/);
  const content = (node.label + " " + node.content).toLowerCase();

  // Fedora-style fuzzy search: every term must match
  return terms.every((term) => {
    let pIdx = 0;
    for (let i = 0; i < content.length && pIdx < term.length; i++) {
      if (content[i] === term[pIdx]) pIdx++;
    }
    return pIdx === term.length;
  });
}

function captureAsNode() {
  if (!searchQuery.value.trim()) return;

  const matchingNodes = nodes.value.filter((n) => nodeMatchesSearch(n));
  if (matchingNodes.length === 0) return;

  // Move them out of the current universe
  const remainingNodes = nodes.value.filter((n) => !nodeMatchesSearch(n));

  // Create the new Parent Lens Node
  const { x: tx, y: ty, k } = globalTransform;
  const canvasX = (window.innerWidth / 2 - tx) / k;
  const canvasY = (window.innerHeight / 2 - ty) / k;

  const lensNode: Node = {
    id: "n_" + Math.random().toString(36).substr(2, 9),
    label: `Lens: ${searchQuery.value}`,
    content: `Captured nodes filtered by: ${searchQuery.value}`,
    x: canvasX,
    y: canvasY,
    preLgnnX: canvasX,
    preLgnnY: canvasY,
    z: 50,
    vx: 0,
    vy: 0,
    vz: 0,
    isExpanded: false,
    theme: Math.random() > 0.5 ? "light" : "dark",
  };

  // Create the new inner universe with the matching nodes
  const innerLinks = links.value.filter(
    (l) =>
      matchingNodes.some((m) => m.id === ((l.source as Node).id || l.source)) &&
      matchingNodes.some((m) => m.id === ((l.target as Node).id || l.target)),
  );

  universeMap.set(lensNode.id, {
    nodes: matchingNodes.map((n: any) => ({ ...n })),
    links: innerLinks.map((l: any) => ({
      ...l,
      source: (l.source as Node).id || l.source,
      target: (l.target as Node).id || l.target,
    })),
  });

  // Update current universe to remove the clustered nodes and add the Lens Node
  remainingNodes.push(lensNode);
  nodes.value = remainingNodes;

  links.value = links.value.filter(
    (l) =>
      remainingNodes.some(
        (m) => m.id === ((l.source as Node).id || l.source),
      ) &&
      remainingNodes.some((m) => m.id === ((l.target as Node).id || l.target)),
  );

  searchQuery.value = "";
  initSimulation();
}

function handleResize() {
  width = window.innerWidth;
  height = window.innerHeight;
  winW.value = width;
  winH.value = height;
  if (simulation) {
    simulation.force(
      "center",
      d3.forceCenter(width / 2, height / 2).strength(0.02),
    );
    simulation.alpha(0.1).restart();
  }
}

// --- Setup/Teardown ---
// onMounted merged above

onUnmounted(() => {
  if (wsUnsubscribe) wsUnsubscribe();
  if (executionWsUnsubscribe) executionWsUnsubscribe();
  window.removeEventListener("resize", handleResize);
  if (animationFrameId) cancelAnimationFrame(animationFrameId);
  if (simulation) simulation.stop();
});
</script>

<style scoped>
.lasso-box {
  position: fixed;
  border: 1px solid rgba(59, 130, 246, 0.8);
  background: rgba(59, 130, 246, 0.1);
  pointer-events: none;
  z-index: 9999;
}

.concept-circle.is-selected {
  box-shadow: 0 0 0 3px #3b82f6, 0 0 20px rgba(59, 130, 246, 0.5) !important;
}
* {
  box-sizing: border-box;
}

.aethelnet-canvas {
  width: 100vw;
  height: 100vh;
  background-color: #fcfbf9; /* Warm architecture studio white */
  background-image: radial-gradient(circle at 50% 50%, rgba(217, 119, 6, 0.03) 0%, transparent 60%);
  position: relative;
  overflow: hidden;
  font-family: 'Inter', -apple-system, sans-serif;
  user-select: none;
  perspective: 1600px;
}

.aethelnet-canvas.is-chromatic {
  background-color: #ffffff;
  background-image: none;
}

/* The Subconscious Depth Fusion */
.aethelnet-canvas {
  transition: background-color 0.8s ease, color 0.8s ease;
}

.aethelnet-canvas.is-subconscious {
  background-color: #020617; /* Deep radar slate */
  background-image:
    linear-gradient(rgba(16, 185, 129, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(16, 185, 129, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  --text-color: #94a3b8;
}

.aethelnet-canvas.is-subconscious .synapse-node {
  /* Dim the conscious thoughts slightly to reveal the network */
  opacity: 0.4;
  mix-blend-mode: luminosity;
  transition: opacity 0.8s ease, mix-blend-mode 0.8s ease;
}

.aethelnet-canvas.is-subconscious .synapse-link {
  /* Make the pipelines glow brightly */
  stroke: rgba(16, 185, 129, 0.9) !important;
  filter: drop-shadow(0 0 5px rgba(16, 185, 129, 0.8));
  transition: all 0.8s ease;
}

.aethelnet-canvas.is-subconscious .concept-circle {
  background: transparent !important;
  border-color: transparent !important;
  box-shadow: none !important;
  backdrop-filter: none !important;
}



.links-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.synapse-link {
  stroke: rgba(148, 163, 184, 0.5);
  stroke-linecap: round;
  transition: all 0.4s ease;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.05));
}

.synapse-link.is-heavy {
  stroke: rgba(14, 165, 233, 0.6);
  filter: drop-shadow(0 4px 10px rgba(14, 165, 233, 0.3));
}

.synapse-link.is-pulsing {
  animation: data-pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes data-pulse {
  0%, 100% {
    stroke-opacity: 1;
    filter: drop-shadow(0 0 15px rgba(56, 189, 248, 0.6));
    stroke: rgba(56, 189, 248, 0.9);
  }
  50% {
    stroke-opacity: 0.5;
    filter: drop-shadow(0 0 5px rgba(56, 189, 248, 0.2));
    stroke: rgba(14, 165, 233, 0.5);
  }
}

.gooey-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  filter: url('#goo');
  will-change: filter;
  transform: translateZ(0);
  display: none;
}

.aethelnet-canvas.is-subconscious .gooey-layer {
  display: block;
}

.concept-blob {
  position: absolute;
  top: 0;
  left: 0;
  border-radius: 50%;
  transform-origin: center center;
  transition: border-radius 0.4s cubic-bezier(0.16, 1, 0.3, 1), background-color 0.5s ease;
  width: 100px;
  height: 100px;
  margin-left: -50px;
  margin-top: -50px;
  will-change: transform, background-color;
}

.concept-blob.is-expanded {
  width: 240px;
  height: 240px;
  margin-left: -120px;
  margin-top: -120px;
  border-radius: 40px;
}

/* Frosted Glass Control Panel */
.frosted-panel {
  position: absolute;
  top: 40px;
  left: 40px;
  width: 280px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(24px) saturate(150%);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 24px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.05), inset 0 0 0 1px rgba(255, 255, 255, 0.8);
  padding: 24px;
  z-index: 1000;
  color: #334155;
  font-family: 'Inter', sans-serif;
}

.panel-header h2 {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 24px;
  letter-spacing: -0.5px;
  color: #0f172a;
}

.version {
  font-size: 0.75rem;
  color: #94a3b8;
  font-weight: 500;
}

.panel-section {
  margin-bottom: 24px;
}

.panel-section h3 {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #64748b;
  margin-bottom: 12px;
  font-weight: 700;
}

.setting-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
  margin-bottom: 8px;
  color: #475569;
}

.settings-node-content {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 10px;
}

.organic-slider {
  -webkit-appearance: none;
  width: 120px;
  height: 6px;
  background: rgba(203, 213, 225, 0.5);
  border-radius: 4px;
  outline: none;
}
.organic-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #d97706;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(217, 119, 6, 0.3);
}

/* Base Node - Foreground */
.concept-circle {
  position: absolute;
  top: 0;
  left: 0;
  border-radius: 50%;
  transform-origin: center center;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  transition: all 0.3s ease;

  /* Size when collapsed */
  width: 100px;
  height: 100px;
  margin-left: -50px;
  margin-top: -50px;

  /* Clinical Frosted Glass style */
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border: 1.5px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
}

.concept-circle:hover + .concept-blob, .concept-circle:hover {
  /* Delegate hover effect to blob if needed, but foreground handles interactions */
}

.concept-circle:hover {
  border-color: var(--node-accent);
  box-shadow: 0 10px 30px var(--node-shadow-color);
  background: rgba(255, 255, 255, 0.95);
}

.concept-circle.is-dragged {
  cursor: grabbing;
  border-color: var(--node-accent);
  box-shadow: 0 15px 45px var(--node-shadow-color);
  background: rgba(255, 255, 255, 1);
  z-index: 9999 !important;
}

.concept-circle.is-selected {
  border-color: var(--node-accent);
  border-width: 2.5px;
  box-shadow: 0 0 25px var(--node-shadow-color);
  background: rgba(255, 255, 255, 1);
}

.concept-circle.ghost {
  border-style: dashed !important;
  border-width: 2px !important;
  border-color: rgba(236, 72, 153, 0.8) !important;
  background: rgba(255, 255, 255, 0.9) !important;
  box-shadow: 0 0 20px rgba(236, 72, 153, 0.4) !important;
}

/* Agent States */
.concept-circle.is-spider {
  box-shadow: 0 0 30px rgba(239, 68, 68, 0.4), inset 0 0 0 2px rgba(239, 68, 68, 0.8) !important;
  animation: pulse-spider 2s infinite alternate;
}
@keyframes pulse-spider {
  0% { box-shadow: 0 0 20px rgba(239, 68, 68, 0.3), inset 0 0 0 2px rgba(239, 68, 68, 0.6) !important; }
  100% { box-shadow: 0 0 40px rgba(239, 68, 68, 0.6), inset 0 0 0 2px rgba(239, 68, 68, 1) !important; }
}

.concept-circle.is-decoder {
  box-shadow: 0 0 30px rgba(56, 189, 248, 0.4), inset 0 0 0 2px rgba(56, 189, 248, 0.8) !important;
  animation: pulse-decoder 2s infinite alternate;
}
@keyframes pulse-decoder {
  0% { box-shadow: 0 0 20px rgba(56, 189, 248, 0.3), inset 0 0 0 2px rgba(56, 189, 248, 0.6) !important; }
  100% { box-shadow: 0 0 40px rgba(56, 189, 248, 0.6), inset 0 0 0 2px rgba(56, 189, 248, 1) !important; }
}

.circle-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #475569;
  text-align: center;
  padding: 10px;
  word-wrap: break-word;
  max-width: 90%;
  line-height: 1.2;
}

/* Expanded Node */
.concept-circle.is-expanded {
  width: 400px;
  height: 400px;
  margin-left: -200px;
  margin-top: -200px;
  border-radius: 50%;
  padding: 0;
  align-items: center;
  justify-content: center;
  background: transparent !important;
  box-shadow: none !important;
  border: none !important;
  backdrop-filter: none !important;
  transition: all 0.5s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.circle-expanded {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.custom-color-wheel {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: conic-gradient(red, yellow, lime, aqua, blue, magenta, red);
  z-index: 200;
  cursor: crosshair;
  box-shadow: 0 10px 30px rgba(0,0,0,0.3), inset 0 0 0 2px rgba(255,255,255,0.8);
  display: flex;
  align-items: center;
  justify-content: center;
}

.custom-color-wheel::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: radial-gradient(circle, white, transparent);
  pointer-events: none;
}

/* Force embedded node views to be transparent and fit the container */
.embedded-node-wrapper :deep(> div) {
  height: auto !important;
  min-height: 0 !important;
  background: transparent !important;
  padding: 0 !important;
}

.embedded-node-wrapper :deep(.lgnn-container),
.embedded-node-wrapper :deep(.self-hub-view),
.embedded-node-wrapper :deep(.aura-stream-view) {
  height: auto !important;
  background: transparent !important;
}

.embedded-node-wrapper :deep(.hub-container) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}

.node-title-input {
  width: 100%;
  border: none;
  background: transparent;
  font-family: var(--font-family-header);
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text);
  text-align: center;
  outline: none;
  margin-bottom: 12px;
  padding: 4px;
}

.node-title-input::placeholder {
  color: var(--color-text-muted);
}

.node-image {
  width: 100%;
  max-height: 180px;
  object-fit: cover;
  border-radius: 6px;
  box-shadow: var(--shadow-sm);
  margin-bottom: 12px;
}

.node-content-input {
  width: 100%;
  flex: 1;
  min-height: 80px;
  border: 1px solid var(--border-color);
  background: rgba(0, 0, 0, 0.2);
  font-family: var(--font-family);
  font-size: 0.95rem;
  color: var(--color-text);
  font-weight: 400;
  resize: vertical;
  outline: none;
  line-height: 1.5;
  text-align: left;
  padding: 12px;
  border-radius: 6px;
  transition: var(--transition-fast);
}

.node-content-input:focus {
  background: rgba(0, 0, 0, 0.4);
  border-color: var(--color-accent);
}

.node-content-input::placeholder {
  color: var(--color-text-muted);
}

.node-btn {
  background: var(--color-accent);
  color: var(--color-text-inverse);
  border: none;
  padding: 10px 16px;
  border-radius: 6px;
  font-family: var(--font-family);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition-fast);
  width: 100%;
  margin-top: 12px;
}

.node-btn:hover {
  background: var(--color-accent-hover);
}

.canvas-hint {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.85rem;
  color: #94a3b8;
  font-weight: 500;
  pointer-events: none;
  opacity: 0.7;
}

/* LGNN Toggle */
.lgnn-toggle-wrapper {
  position: absolute;
  top: 30px;
  right: 30px;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 100;
}

.toggle-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #64748b;
  letter-spacing: -0.2px;
}

.lgnn-toggle {
  width: 44px;
  height: 24px;
  background: #e2e8f0;
  border-radius: 12px;
  border: none;
  position: relative;
  cursor: pointer;
  transition: background 0.3s ease;
  padding: 0;
}

.lgnn-toggle.active {
  background: #0f172a;
}

.toggle-knob {
  width: 20px;
  height: 20px;
  background: #ffffff;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.lgnn-toggle.active .toggle-knob {
  transform: translateX(20px);
}

/* LGNN Bridges (AI calculated) */
.lgnn-bridge-link {
  stroke: #0ea5e9; /* Subtle cyan */
  stroke-width: 1.5px;
  stroke-dasharray: 4 6; /* Dotted line effect */
  transition: stroke-opacity 0.2s ease;
}

/* Temporary drawn cable */
.temp-link {
  stroke: #94a3b8;
  stroke-width: 2px;
  stroke-linecap: round;
  stroke-dasharray: 6 6;
  pointer-events: none;
}

/* Breadcrumbs HUD */
.breadcrumbs-hud {
  position: absolute;
  top: 30px;
  left: 30px;
  display: flex;
  gap: 8px;
  z-index: 100;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  padding: 8px 16px;
  border-radius: 20px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
  color: #cbd5e1;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  letter-spacing: 0.05em;
}

.crumb {
  cursor: pointer;
  transition: color 0.2s;
}

.crumb:hover {
  color: #06b6d4;
  text-shadow: 0 0 8px rgba(6, 182, 212, 0.5);
}

.crumb-separator {
  color: rgba(203, 213, 225, 0.3);
}



/* Search HUD */
.search-hud {
  position: absolute;
  top: 30px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 100;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  padding: 10px 20px;
  border-radius: 24px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06), inset 0 0 0 1px rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(226, 232, 240, 0.6);
  transition: all 0.3s ease;
}

.search-hud:focus-within {
  box-shadow: 0 8px 30px rgba(14, 165, 233, 0.15), inset 0 0 0 1px rgba(255, 255, 255, 1);
  border-color: rgba(14, 165, 233, 0.3);
}

.search-input {
  border: none;
  background: transparent;
  outline: none;
  font-family: inherit;
  font-size: 1rem;
  color: #0f172a;
  width: 300px;
  font-weight: 500;
}

.search-input::placeholder {
  color: #94a3b8;
  font-weight: 400;
}

.search-suggestion-badge {
  font-size: 0.8rem;
  color: #0ea5e9;
  background: rgba(14, 165, 233, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  white-space: nowrap;
}

.search-suggestion-badge kbd {
  font-size: 0.65rem;
  font-family: monospace;
  background: #0ea5e9;
  color: white;
  padding: 2px 4px;
  border-radius: 4px;
}

.capture-btn {
  background: #0ea5e9;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.capture-btn:hover {
  background: #0284c7;
}

/* AI Suggestion HUD */
.suggestion-hud {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding: 6px 10px;
  background: rgba(14, 165, 233, 0.05);
  border: 1px solid rgba(14, 165, 233, 0.2);
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.suggestion-hud:hover {
  background: rgba(14, 165, 233, 0.1);
}

.ghost-text {
  font-size: 0.85rem;
  color: #0ea5e9;
  font-style: italic;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}

.tab-key {
  font-size: 0.7rem;
  font-family: monospace;
  background: #e2e8f0;
  color: #64748b;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: bold;
}

/* Fast Link Port */
.link-port {
  position: absolute;
  right: -10px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  background: #cbd5e1;
  border-radius: 50%;
  cursor: crosshair;
  z-index: 10;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: transform 0.2s, background 0.2s;
}

.link-port:hover {
  background: #3b82f6;
  transform: translateY(-50%) scale(1.3);
}

/* Global Actions HUD */
.global-actions-hud {
  position: absolute;
  bottom: 30px;
  left: 30px;
  display: flex;
  gap: 10px;
  z-index: 100;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  padding: 10px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06), inset 0 0 0 1px rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(226, 232, 240, 0.6);
}

.global-actions-hud button {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(226, 232, 240, 0.8);
  color: #64748b;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}

.global-actions-hud button:hover:not(.disabled) {
  background: #ffffff;
  color: #0ea5e9;
  border-color: #0ea5e9;
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(14, 165, 233, 0.15);
}

.global-actions-hud button.active {
  background: #0ea5e9;
  color: white;
  border-color: #0ea5e9;
  box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3);
}

.global-actions-hud button.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Layers HUD */
.layers-hud {
  position: absolute;
  top: 90px;
  right: 30px;
  z-index: 100;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.hud-title {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #94a3b8;
  font-weight: 700;
  margin-bottom: 4px;
}

.layer-pills {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-end;
}

.layer-pill {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(226, 232, 240, 0.6);
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 0.85rem;
  color: #475569;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04), inset 0 0 0 1px rgba(255, 255, 255, 0.8);
}

.layer-pill:hover {
  background: #ffffff;
  transform: translateX(-4px);
  box-shadow: 0 6px 20px rgba(14, 165, 233, 0.1), inset 0 0 0 1px rgba(255, 255, 255, 1);
  color: #0ea5e9;
}

.layer-pill.active {
  background: #0f172a;
  color: white;
  border-color: #0f172a;
  box-shadow: 0 8px 25px rgba(15, 23, 42, 0.2);
}

.node-drag-header {
  width: 100%;
  height: 14px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px 6px 0 0;
  cursor: grab;
  margin-bottom: 8px;
  flex-shrink: 0;
}

.node-drag-header:active {
  cursor: grabbing;
}

@media (prefers-color-scheme: dark) {
  .node-drag-header {
    background: rgba(255, 255, 255, 0.05);
  }
}

.telemetry-panel {
  position: absolute;
  top: 80px;
  bottom: 20px;
  right: 20px;
  width: 380px;
  background: rgba(20, 0, 0, 0.85); /* Villain Glass */
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(239, 68, 68, 0.4);
  border-radius: 16px;
  color: #f87171;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 0 30px rgba(239, 68, 68, 0.2), inset 0 0 10px rgba(239, 68, 68, 0.1);
}

.slide-right-enter-active, .slide-right-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-right-enter-from, .slide-right-leave-to {
  opacity: 0;
  transform: translateX(50px);
}

.telemetry-header {
  padding: 16px;
  border-bottom: 1px solid rgba(239, 68, 68, 0.5);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: rgba(239, 68, 68, 0.1);
}

.telemetry-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.telemetry-id {
  font-family: 'Berkeley Mono', monospace;
  font-size: 0.75rem;
  color: #fca5a5;
  text-shadow: 0 0 5px rgba(239, 68, 68, 0.5);
  word-break: break-all;
}

.ghost-badge {
  display: inline-block;
  padding: 2px 6px;
  background: rgba(236, 72, 153, 0.1);
  color: #db2777;
  border: 1px solid rgba(236, 72, 153, 0.3);
  border-radius: 4px;
  font-size: 0.65rem;
  font-weight: bold;
  letter-spacing: 1px;
}

.close-btn {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}
.close-btn:hover {
  color: #475569;
}

.telemetry-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  font-size: 0.85rem;
}

.ghost-info p, .meta-row {
  margin: 0 0 8px 0;
  display: flex;
  justify-content: space-between;
}

.meta-label {
  color: #64748b;
}

.assimilate-btn {
  width: 100%;
  padding: 10px;
  margin-top: 8px;
  background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(236, 72, 153, 0.2);
}
.assimilate-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(236, 72, 153, 0.3);
}

.telemetry-stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 16px;
}

.stat-box {
  background: rgba(69, 10, 10, 0.4);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 0 10px rgba(239, 68, 68, 0.1);
}

.stat-label {
  font-size: 0.65rem;
  color: #fca5a5;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 1.1rem;
  font-family: 'Berkeley Mono', monospace;
  font-weight: bold;
  color: #ef4444;
  text-shadow: 0 0 8px rgba(239, 68, 68, 0.6);
}

.hologram-module {
  background: rgba(69, 10, 10, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  padding: 16px;
  position: relative;
  overflow: hidden;
}

.module-title {
  font-size: 0.7rem;
  color: #ef4444;
  font-family: 'Berkeley Mono', monospace;
  margin-bottom: 16px;
  letter-spacing: 1px;
  border-bottom: 1px solid rgba(239, 68, 68, 0.4);
  padding-bottom: 8px;
  text-shadow: 0 0 5px rgba(239, 68, 68, 0.5);
}

.orderbook-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-family: 'Berkeley Mono', monospace;
  font-size: 0.75rem;
  margin-bottom: 20px;
}

.order-row {
  display: flex;
  justify-content: space-between;
  padding: 2px 0;
  position: relative;
  z-index: 1;
}

.order-row .price { font-weight: bold; }
.order-row.ask .price { color: #f87171; }
.order-row.bid .price { color: #4ade80; }
.order-row .size { color: #94a3b8; }

.depth-bar {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: -1;
  opacity: 0.15;
}
.order-row.ask .depth-bar { background: #f87171; }
.order-row.bid .depth-bar { background: #4ade80; }

.orderbook-spread {
  text-align: center;
  padding: 8px 0;
  color: #f1f5f9;
  font-size: 0.85rem;
  font-weight: bold;
  border-top: 1px dashed rgba(255,255,255,0.1);
  border-bottom: 1px dashed rgba(255,255,255,0.1);
  margin: 4px 0;
  display: flex;
  justify-content: center;
  gap: 12px;
}

.spread-diff { color: #64748b; font-size: 0.7rem; align-self: center; }

.lgnn-confidence {
  margin-top: 16px;
}

.confidence-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.7rem;
  color: #94a3b8;
  margin-bottom: 8px;
}
.buy-signal { color: #4ade80; font-weight: bold; }

.confidence-bar-wrap {
  display: flex;
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  background: rgba(255,255,255,0.1);
}

.confidence-bar.buy { background: #4ade80; }
.confidence-bar.sell { background: #f87171; }

.neural-stream {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pulse-line {
  display: flex;
  align-items: center;
  gap: 16px;
}

.pulse-hex {
  font-family: 'Berkeley Mono', monospace;
  font-size: 0.7rem;
  color: #ec4899;
}

.pulse-wave {
  display: flex;
  align-items: center;
  gap: 2px;
  height: 20px;
  flex: 1;
}

.wave-bar {
  width: 4px;
  background: #38bdf8;
  border-radius: 2px;
  animation: pulseHeight 1s ease-in-out infinite alternate;
}

@keyframes pulseHeight {
  0% { transform: scaleY(0.2); opacity: 0.5; }
  100% { transform: scaleY(1); opacity: 1; }
}

.concept-circle.ghost {
  border: 2px dashed rgba(236, 72, 153, 0.6) !important;
  background: rgba(255, 255, 255, 0.9) !important;
  box-shadow: 0 0 20px rgba(236, 72, 153, 0.2) !important;
}
.concept-blob.ghost {
  background-color: rgba(236, 72, 153, 0.2) !important;
}
.concept-circle.ghost .node-title-input {
  color: #db2777 !important;
}
</style>
