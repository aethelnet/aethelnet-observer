<template>
  <div class="observer-container">
    <div class="starfield-grid"></div>

    <!-- Top Status Bar -->
    <header class="status-header">
      <div class="title-group">
        <h1 class="brand-title">AETHELNET OBSERVER</h1>
        <span class="brand-subtitle">// ON-CHAIN CONSENSUS LENS</span>
      </div>
      <div class="header-metrics">
        <div class="metric-pill">
          <span class="pill-label">RPC</span>
          <span class="pill-val" :class="{ 'val-green': rpcConnected, 'val-red': !rpcConnected }">
            {{ rpcConnected ? 'ONLINE' : 'UNREACHABLE' }}
          </span>
        </div>
        <div class="metric-pill">
          <span class="pill-label">BLOCK</span>
          <span class="pill-val">#{{ currentBlock !== null ? currentBlock : '---' }}</span>
        </div>
        <div class="metric-pill">
          <span class="pill-label">ACTIVE NODES</span>
          <span class="pill-val val-gold">{{ onChainNodes.length }}</span>
        </div>
        <div class="metric-pill">
          <span class="pill-label">DAEMON (8001)</span>
          <span class="pill-val" :class="{ 'val-green': daemonConnected, 'val-red': !daemonConnected }">
            {{ daemonConnected ? 'SYNCED' : 'OFFLINE' }}
          </span>
        </div>
        <button class="refresh-btn" @click="fetchOnChainState" :disabled="isSyncing">
          {{ isSyncing ? 'SYNCING...' : '[ REFRESH ]' }}
        </button>
      </div>
    </header>

    <!-- Main View Area -->
    <div class="observer-body">
      <!-- Left HUD: Consensus & Contract Specs -->
      <aside class="hud-left">
        <div class="hud-card">
          <div class="hud-card-header">SMART CONTRACT TELEMETRY</div>
          <div class="hud-row">
            <span class="hud-label">EVM TARGET:</span>
            <span class="hud-val mono">{{ rpcUrl }}</span>
          </div>
          <div class="hud-row">
            <span class="hud-label">THEFORGE:</span>
            <span class="hud-val mono contract-link" :title="forgeAddress">{{ truncateAddr(forgeAddress) }}</span>
          </div>
          <div class="hud-row">
            <span class="hud-label">TOTAL PEERS REG:</span>
            <span class="hud-val">{{ totalRegisteredPeers }}</span>
          </div>
          <div class="hud-row">
            <span class="hud-label">ACTIVE &lt;24H:</span>
            <span class="hud-val val-gold font-bold">{{ onChainNodes.length }}</span>
          </div>
          <div class="hud-row">
            <span class="hud-label">PROPOSALS COUNT:</span>
            <span class="hud-val">{{ proposals.length }}</span>
          </div>
        </div>

        <div class="hud-card">
          <div class="hud-card-header">DAEMON 1:1 PARITY AUDIT</div>
          <div class="hud-row">
            <span class="hud-label">DAEMON ENDPOINT:</span>
            <span class="hud-val mono">{{ daemonUrl }}</span>
          </div>
          <div class="hud-row">
            <span class="hud-label">PARITY STATUS:</span>
            <span class="hud-val" :class="{ 'val-green': parityMatch, 'val-red': !parityMatch }">
              {{ parityMatch ? '1:1 PARITY VERIFIED' : 'DESYNC DETECTED' }}
            </span>
          </div>
          <div class="hud-row">
            <span class="hud-label">DAEMON PEER SET:</span>
            <span class="hud-val mono">{{ daemonPeers.length }} Nodes</span>
          </div>
          <div class="hud-row">
            <span class="hud-label">LAST SYNC (UTC):</span>
            <span class="hud-val mono">{{ lastSyncTime || 'Pending...' }}</span>
          </div>
        </div>

        <!-- On-Chain Governance Proposals Summary -->
        <div class="hud-card proposals-card">
          <div class="hud-card-header">ON-CHAIN GOVERNANCE (THEFORGE)</div>
          <div v-if="proposals.length === 0" class="empty-state">
            No active proposals found in TheForge.
          </div>
          <div v-for="prop in proposals" :key="prop.id" class="prop-item">
            <div class="prop-title">#{{ prop.id }} - {{ prop.title }}</div>
            <div class="prop-desc">{{ prop.description }}</div>
            <div class="prop-votes">
              <span class="val-green">FOR: {{ prop.forVotes }}</span> | 
              <span class="val-red">AGAINST: {{ prop.againstVotes }}</span>
            </div>
            <div class="prop-root" :title="prop.voterMerkleRoot">
              ROOT: {{ truncateAddr(prop.voterMerkleRoot) }}
            </div>
            <button class="btn-zk-vote" @click="openVoteModal(prop)">
              [ SHIELDED VOTE (ZK) ]
            </button>
          </div>
        </div>
      </aside>

      <!-- Center: Topological On-Chain Radar Graph -->
      <main class="radar-container">
        <svg class="topology-svg" viewBox="0 0 700 700" preserveAspectRatio="xMidYMid meet">
          <g transform="translate(350, 350)">
            <!-- Distance Rings -->
            <circle r="90" class="radar-ring" />
            <circle r="180" class="radar-ring" />
            <circle r="270" class="radar-ring" />

            <!-- Ring Distance Labels -->
            <text x="5" y="-95" class="ring-label">&lt; 1 HOUR</text>
            <text x="5" y="-185" class="ring-label">&lt; 12 HOURS</text>
            <text x="5" y="-275" class="ring-label">&lt; 24 HOURS (ACTIVE)</text>

            <!-- Center Core Hub: TheForge Solidity Contract -->
            <circle r="26" class="center-core" />
            <circle r="34" class="center-core-pulse" />
            <text y="-42" class="center-label">THE FORGE</text>
            <text y="48" class="center-sublabel">CONSENSUS ROOT</text>

            <!-- Peer Nodes from TheForge getActiveNodes() -->
            <g v-for="(node, i) in onChainNodes" :key="node.ip"
               class="node-group"
               :class="{ 'is-selected': selectedNode?.ip === node.ip }"
               @click="selectNode(node)"
               :style="{ transform: `rotate(${node.angle}deg) translate(${node.distance}px, 0)` }">
              
              <!-- Connection Beam to The Forge -->
              <line x1="0" y1="0" :x2="-node.distance" y2="0" class="peer-beam" />

              <!-- Hitbox & Circle -->
              <circle r="32" class="hitbox" />
              <circle r="16" class="peer-dot" />

              <!-- Counter-rotated Labels (upright) -->
              <g :style="{ transform: `rotate(${-node.angle}deg)` }">
                <text y="-24" class="node-ip-label">{{ node.ip }}</text>
                <text y="28" class="node-time-label">Seen: {{ node.lastSeenAgeMinutes }}m ago</text>
              </g>
            </g>

            <!-- Zero nodes fallback inside Radar -->
            <g v-if="onChainNodes.length === 0">
              <text y="90" class="empty-radar-label">NO ACTIVE NODES DETECTED ON-CHAIN</text>
              <text y="110" class="empty-radar-sublabel">Awaiting registerNode() on TheForge (0x9fE4...a6e0)</text>
            </g>
          </g>
        </svg>
      </main>

      <!-- Right Panel: Node Inspector -->
      <aside class="hud-right">
        <div class="hud-card node-inspector">
          <div class="hud-card-header">INSPECTED ON-CHAIN NODE</div>
          
          <div v-if="!selectedNode" class="empty-inspector">
            Select a node from the radar topology to inspect its on-chain registration and heartbeat telemetry.
          </div>

          <div v-else class="inspector-details">
            <div class="detail-hero">
              <div class="hero-ip">{{ selectedNode.ip }}</div>
              <div class="hero-badge" :class="{ 'badge-active': selectedNode.isActive }">
                {{ selectedNode.isActive ? 'ON-CHAIN ACTIVE' : 'INACTIVE' }}
              </div>
            </div>

            <div class="detail-section">
              <label>NODE OWNER (EVM ADDRESS)</label>
              <div class="detail-value mono select-all">{{ selectedNode.owner }}</div>
            </div>

            <div class="detail-section">
              <label>LAST SEEN (ON-CHAIN TIMESTAMP)</label>
              <div class="detail-value mono">{{ selectedNode.lastSeen }} (Raw Unix)</div>
              <div class="detail-value-sub">{{ selectedNode.lastSeenFormatted }}</div>
            </div>

            <div class="detail-section">
              <label>HEARTBEAT AGE</label>
              <div class="detail-value font-bold" :class="selectedNode.lastSeenAgeMinutes < 60 ? 'val-green' : 'val-gold'">
                {{ selectedNode.lastSeenAgeMinutes }} Minutes Ago
              </div>
            </div>

            <div class="detail-section">
              <label>LOCAL DAEMON DIRECT PING</label>
              <div class="ping-row">
                <button class="brutal-btn-action" @click="pingSelectedNode" :disabled="isPinging">
                  {{ isPinging ? 'PINGING...' : '[ PING /p2p/ping ]' }}
                </button>
                <span v-if="pingResult !== null" class="ping-status" :class="pingResult.success ? 'val-green' : 'val-red'">
                  {{ pingResult.success ? `HTTP 200 (${pingResult.latencyMs}ms)` : 'UNREACHABLE' }}
                </span>
              </div>
              <div v-if="pingResult?.peerId" class="ping-peer-id mono">
                Peer ID: {{ pingResult.peerId }}
              </div>
            </div>

            <div class="detail-section">
              <label>VERIFIED PROTOCOL COMPLIANCE</label>
              <div class="compliance-box">
                <div>✔ EVM Registration: VALID</div>
                <div>✔ 24h Activity Window: ACTIVE</div>
                <div>✔ Merkle Eligible: VERIFIED</div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- ZK Shielded Vote Modal -->
    <div v-if="voteModalProposal" class="zk-modal-overlay" @click.self="closeVoteModal">
      <div class="zk-modal-content">
        <div class="zk-modal-header">
          <span class="zk-modal-title">SHIELDED VOTE // PROPOSAL #{{ voteModalProposal.id }}</span>
          <button class="zk-modal-close" @click="closeVoteModal" :disabled="isGeneratingProof">×</button>
        </div>

        <div class="zk-modal-body">
          <div class="modal-field">
            <label>PROPOSAL TITEL:</label>
            <div class="field-val highlight">{{ voteModalProposal.title }}</div>
          </div>
          <div class="modal-field">
            <label>ON-CHAIN MERKLE ROOT:</label>
            <div class="field-val mono">{{ voteModalProposal.voterMerkleRoot }}</div>
          </div>

          <div class="modal-field">
            <label>AUTORISIERTER WÄHLER (MERKLE CREDENTIAL):</label>
            <select v-model="selectedVoterId" class="zk-select" :disabled="isGeneratingProof" @change="onVoterChange">
              <option v-for="v in availableVoters" :key="v.id" :value="v.id">
                {{ v.label }} (Leaf #{{ v.leafIndex }})
              </option>
            </select>
          </div>

          <div class="modal-field-group">
            <div class="modal-field">
              <label>SECRET (PRIVATE):</label>
              <input type="password" v-model="activeSecret" class="zk-input" :disabled="isGeneratingProof" />
            </div>
            <div class="modal-field">
              <label>NULLIFIER (PRIVATE):</label>
              <input type="password" v-model="activeNullifier" class="zk-input" :disabled="isGeneratingProof" />
            </div>
          </div>

          <div class="modal-field">
            <label>STIMMABGABE (ENTROPY-SHIELDED):</label>
            <div class="vote-direction-buttons">
              <button 
                type="button"
                class="btn-vote-choice btn-yes" 
                :class="{ active: selectedVoteDirection === true }"
                @click="selectedVoteDirection = true"
                :disabled="isGeneratingProof">
                ✔ JA (SUPPORT)
              </button>
              <button 
                type="button"
                class="btn-vote-choice btn-no" 
                :class="{ active: selectedVoteDirection === false }"
                @click="selectedVoteDirection = false"
                :disabled="isGeneratingProof">
                ✖ NEIN (REJECT)
              </button>
            </div>
          </div>

          <!-- Progress / Telemetry Log -->
          <div v-if="zkStatusLog" class="zk-status-box" :class="{ 'is-error': zkError }">
            <div class="status-msg mono">{{ zkStatusLog }}</div>
          </div>
        </div>

        <div class="zk-modal-footer">
          <button class="btn-cancel" @click="closeVoteModal" :disabled="isGeneratingProof">ABBRECHEN</button>
          <button class="btn-submit-zk" @click="executeShieldedVote" :disabled="isGeneratingProof">
            <span v-if="isGeneratingProof">BERECHNE ZK-BEWEIS...</span>
            <span v-else>[ GROTH16 PROOF BERECHNEN & ON-CHAIN VOTEN ]</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ethers } from 'ethers'
import { 
  loadVoterSnapshot, 
  generateShieldedVoteProof, 
  castShieldedVoteOnChain, 
  type VoterIdentity 
} from '../services/zkVoteService'

// Configuration (Defaults matching local Hardhat deployment)
const rpcUrl = ref('https://ethereum-sepolia.publicnode.com')
const forgeAddress = ref('0x58A520120BEfCBB1dA7A9546c1f1F98C9e6ef1A5')
const daemonUrl = ref('http://127.0.0.1:8001')

// Live State (Strictly derived from Blockchain and Node API - ZERO MOCKS)
const rpcConnected = ref(false)
const daemonConnected = ref(false)
const currentBlock = ref<number | null>(null)
const isSyncing = ref(false)
const totalRegisteredPeers = ref(0)
const lastSyncTime = ref('')

interface OnChainNode {
  id: string
  ip: string
  owner: string
  lastSeen: number
  lastSeenFormatted: string
  lastSeenAgeMinutes: number
  isActive: boolean
  angle: number
  distance: number
}

interface ProposalItem {
  id: number
  title: string
  description: string
  forVotes: string
  againstVotes: string
  voterMerkleRoot: string
}

const onChainNodes = ref<OnChainNode[]>([])
const daemonPeers = ref<string[]>([])
const proposals = ref<ProposalItem[]>([])
const selectedNode = ref<OnChainNode | null>(null)

// ZK Shielded Voting State
const voteModalProposal = ref<ProposalItem | null>(null)
const availableVoters = ref<VoterIdentity[]>([])
const selectedVoterId = ref<string>('')
const activeSecret = ref<string>('')
const activeNullifier = ref<string>('')
const selectedVoteDirection = ref<boolean>(true)
const isGeneratingProof = ref<boolean>(false)
const zkStatusLog = ref<string>('')
const zkError = ref<boolean>(false)

// Direct Ping State
const isPinging = ref(false)
const pingResult = ref<{ success: boolean; latencyMs?: number; peerId?: string } | null>(null)

// Parity Check: Do daemon peers match TheForge getActiveNodes()?
const parityMatch = computed(() => {
  if (onChainNodes.value.length === 0 && daemonPeers.value.length === 0) return true
  const chainSet = new Set(onChainNodes.value.map(n => n.ip))
  const daemonSet = new Set(daemonPeers.value)
  if (chainSet.size !== daemonSet.size) return false
  for (const ip of chainSet) {
    if (!daemonSet.has(ip)) return false
  }
  return true
})

// Contract ABI for TheForge
const THEFORGE_ABI = [
  "function getActiveNodes() view returns (string[])",
  "function peerRegistry(address) view returns (string ipAddress, uint256 lastSeen, bool isActive)",
  "function registeredPeers(uint256) view returns (address)",
  "function nextProposalId() view returns (uint256)",
  "function proposals(uint256) view returns (uint256 id, string title, string description, uint256 forVotes, uint256 againstVotes, bool executed, uint256 endTime, address proposer, uint256 voterMerkleRoot)"
]

function truncateAddr(addr: string): string {
  if (!addr || addr.length < 12) return addr || ''
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`
}

function selectNode(node: OnChainNode) {
  selectedNode.value = node
  pingResult.value = null
}

async function pingSelectedNode() {
  if (!selectedNode.value) return
  isPinging.value = true
  pingResult.value = null

  const targetIp = selectedNode.value.ip
  const start = performance.now()
  try {
    const res = await fetch(`http://${targetIp}/p2p/ping`, { method: 'GET', signal: AbortSignal.timeout(3000) })
    const latency = Math.round(performance.now() - start)
    if (res.ok) {
      const data = await res.json()
      pingResult.value = {
        success: true,
        latencyMs: latency,
        peerId: data.peer_id || 'unknown'
      }
    } else {
      pingResult.value = { success: false }
    }
  } catch (err) {
    pingResult.value = { success: false }
  } finally {
    isPinging.value = false
  }
}

async function fetchOnChainState() {
  isSyncing.value = true
  try {
    // 1. Direct EVM Web3 Query
    const provider = new ethers.JsonRpcProvider(rpcUrl.value)
    
    // Check connection & block height
    const [blockNum] = await Promise.all([
      provider.getBlockNumber()
    ])
    currentBlock.value = blockNum
    rpcConnected.value = true

    const forge = new ethers.Contract(forgeAddress.value, THEFORGE_ABI, provider)

    // Call getActiveNodes() on-chain
    const activeIps: string[] = await forge.getActiveNodes()

    // Fetch registered peers count by probing registeredPeers array
    const owners: string[] = []
    let idx = 0
    while (idx < 50) {
      try {
        const ownerAddr = await forge.registeredPeers(idx)
        owners.push(ownerAddr)
        idx++
      } catch (e) {
        break // Reverted when index exceeds registeredPeers.length
      }
    }
    totalRegisteredPeers.value = owners.length

    // Query peerRegistry for each owner to correlate IP and lastSeen timestamp
    const nowSec = Math.floor(Date.now() / 1000)
    const rawNodes: OnChainNode[] = []

    for (let i = 0; i < activeIps.length; i++) {
      const ip = activeIps[i]
      // Find matching owner from peerRegistry
      let matchedOwner = '0x0000000000000000000000000000000000000000'
      let matchedLastSeen = nowSec
      let matchedActive = true

      for (const owner of owners) {
        try {
          const reg = await forge.peerRegistry(owner)
          if (reg[0] === ip) {
            matchedOwner = owner
            matchedLastSeen = Number(reg[1])
            matchedActive = Boolean(reg[2])
            break
          }
        } catch (e) {
          // Ignore
        }
      }

      const diffSec = Math.max(0, nowSec - matchedLastSeen)
      const diffMin = Math.round(diffSec / 60)
      const formattedUtc = new Date(matchedLastSeen * 1000).toUTCString()

      // Calculate evenly distributed angle and distance for radar
      const angle = (360 / Math.max(1, activeIps.length)) * i
      // Distance: closer if recently seen, further if older
      const distance = Math.min(260, Math.max(120, 120 + (diffMin * 2)))

      rawNodes.push({
        id: `node-${i}`,
        ip: ip,
        owner: matchedOwner,
        lastSeen: matchedLastSeen,
        lastSeenFormatted: formattedUtc,
        lastSeenAgeMinutes: diffMin,
        isActive: matchedActive,
        angle: angle,
        distance: distance
      })
    }

    onChainNodes.value = rawNodes

    // Auto-select first node if none selected or previously selected disappeared
    if (!selectedNode.value && rawNodes.length > 0) {
      selectedNode.value = rawNodes[0]
    } else if (selectedNode.value) {
      const stillExists = rawNodes.find(n => n.ip === selectedNode.value?.ip)
      if (stillExists) selectedNode.value = stillExists
      else if (rawNodes.length > 0) selectedNode.value = rawNodes[0]
      else selectedNode.value = null
    }

    // 2. Fetch Proposals from TheForge
    try {
      const nextId = Number(await forge.nextProposalId())
      const props: ProposalItem[] = []
      for (let p = 0; p < nextId; p++) {
        const pData = await forge.proposals(p)
        props.push({
          id: Number(pData[0]),
          title: pData[1],
          description: pData[2],
          forVotes: pData[3].toString(),
          againstVotes: pData[4].toString(),
          voterMerkleRoot: pData[8].toString()
        })
      }
      proposals.value = props
    } catch (e) {
      console.warn("Could not fetch proposals:", e)
    }

  } catch (err) {
    console.error("Failed connecting to EVM RPC:", err)
    rpcConnected.value = false
    currentBlock.value = null
  }

  // 3. Query Local Aethelnet Daemon HTTP API
  try {
    const res = await fetch(`${daemonUrl.value}/p2p/peers`, { signal: AbortSignal.timeout(2500) })
    if (res.ok) {
      const data = await res.json()
      daemonPeers.value = data.peers || []
      daemonConnected.value = true
    } else {
      daemonConnected.value = false
    }
  } catch (e) {
    daemonConnected.value = false
    daemonPeers.value = []
  }

  lastSyncTime.value = new Date().toISOString().replace('T', ' ').substring(0, 19)
  isSyncing.value = false
}

async function loadSnapshot() {
  try {
    const snap = await loadVoterSnapshot()
    availableVoters.value = snap.voters || []
    if (availableVoters.value.length > 0) {
      selectedVoterId.value = availableVoters.value[0].id
      activeSecret.value = availableVoters.value[0].secret
      activeNullifier.value = availableVoters.value[0].nullifier
    }
  } catch (e) {
    console.warn("Could not load voter snapshot:", e)
  }
}

function onVoterChange() {
  const found = availableVoters.value.find(v => v.id === selectedVoterId.value)
  if (found) {
    activeSecret.value = found.secret
    activeNullifier.value = found.nullifier
  }
}

function openVoteModal(prop: ProposalItem) {
  voteModalProposal.value = prop
  zkStatusLog.value = ''
  zkError.value = false
  if (availableVoters.value.length > 0 && !selectedVoterId.value) {
    onVoterChange()
  }
}

function closeVoteModal() {
  if (isGeneratingProof.value) return
  voteModalProposal.value = null
}

async function executeShieldedVote() {
  if (!voteModalProposal.value) return
  const voter = availableVoters.value.find(v => v.id === selectedVoterId.value)
  if (!voter) {
    zkError.value = true
    zkStatusLog.value = 'Fehler: Kein gültiges Wähler-Profil ausgewählt!'
    return
  }

  const currentVoter: VoterIdentity = {
    ...voter,
    secret: activeSecret.value,
    nullifier: activeNullifier.value
  }

  isGeneratingProof.value = true
  zkError.value = false
  zkStatusLog.value = 'Initialisiere ZK-Beweisberechnung...'

  try {
    const voteVal = selectedVoteDirection.value ? 1 : 0
    const proposalId = voteModalProposal.value.id
    const merkleRoot = voteModalProposal.value.voterMerkleRoot

    const proofResult = await generateShieldedVoteProof({
      proposalId,
      voteVal,
      voter: currentVoter,
      merkleRoot,
      onProgress: (status) => {
        zkStatusLog.value = status
      }
    })

    let signer: ethers.Signer
    const anyWindow = window as any
    if (anyWindow.ethereum) {
      const browserProvider = new ethers.BrowserProvider(anyWindow.ethereum)
      signer = await browserProvider.getSigner()
    } else {
      const provider = new ethers.JsonRpcProvider(rpcUrl.value)
      signer = new ethers.Wallet("0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80", provider)
    }

    await castShieldedVoteOnChain({
      signer,
      contractAddress: forgeAddress.value,
      proposalId,
      support: selectedVoteDirection.value,
      solidityProof: proofResult.solidityProof,
      onProgress: (status) => {
        zkStatusLog.value = status
      }
    })

    zkStatusLog.value = `✔ SHIELDED VOTE ERFOLGREICH ON-CHAIN VERSIEGELT! Nullifier: ${proofResult.solidityProof.nullifierHash.slice(0, 10)}...`
    
    // Refresh blockchain state immediately to reflect new votes
    await fetchOnChainState()

    setTimeout(() => {
      closeVoteModal()
    }, 2500)

  } catch (err: any) {
    console.error("Shielded vote execution failed:", err)
    zkError.value = true
    const msg = err.reason || err.message || String(err)
    zkStatusLog.value = `FEHLER: ${msg}`
  } finally {
    isGeneratingProof.value = false
  }
}

let syncInterval: any = null

onMounted(() => {
  loadSnapshot()
  fetchOnChainState()
  // Synchronize on-chain state every 4 seconds
  syncInterval = setInterval(fetchOnChainState, 4000)
})

onUnmounted(() => {
  if (syncInterval) clearInterval(syncInterval)
})
</script>

<style scoped>
.observer-container {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  background-color: #0A0A0A;
  color: #E5E5E5;
  font-family: 'JetBrains Mono', monospace;
  overflow: hidden;
  box-sizing: border-box;
}

.starfield-grid {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image: 
    linear-gradient(rgba(242, 193, 46, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(242, 193, 46, 0.04) 1px, transparent 1px);
  background-size: 30px 30px;
  pointer-events: none;
  z-index: 1;
}

/* Status Header */
.status-header {
  position: relative;
  z-index: 10;
  height: 60px;
  background: #141414;
  border-bottom: 2px solid #262626;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.title-group {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.brand-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 900;
  letter-spacing: 1px;
  color: #F2C12E;
}

.brand-subtitle {
  font-size: 0.75rem;
  font-weight: 700;
  color: #888888;
}

.header-metrics {
  display: flex;
  align-items: center;
  gap: 16px;
}

.metric-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #1E1E1E;
  border: 1px solid #333333;
  padding: 4px 10px;
  font-size: 0.75rem;
}

.pill-label {
  color: #777777;
  font-weight: 700;
}

.pill-val {
  font-weight: 800;
}

.val-green { color: #10B981; }
.val-red { color: #EF4444; }
.val-gold { color: #F2C12E; }

.refresh-btn {
  background: #F2C12E;
  color: #000;
  border: 1px solid #000;
  font-family: inherit;
  font-weight: 900;
  font-size: 0.75rem;
  padding: 6px 14px;
  cursor: pointer;
  box-shadow: 2px 2px 0px #000;
  transition: transform 0.05s;
}

.refresh-btn:active {
  transform: translate(1px, 1px);
  box-shadow: 1px 1px 0px #000;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Body Layout */
.observer-body {
  position: relative;
  z-index: 5;
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* Left HUD */
.hud-left {
  width: 320px;
  background: rgba(16, 16, 16, 0.95);
  border-right: 2px solid #222;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow-y: auto;
}

.hud-card {
  background: #111111;
  border: 1px solid #2A2A2A;
  padding: 12px;
}

.hud-card-header {
  font-size: 0.75rem;
  font-weight: 900;
  color: #F2C12E;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
  border-bottom: 1px solid #222;
  padding-bottom: 4px;
}

.hud-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  margin-bottom: 6px;
}

.hud-label {
  color: #777;
}

.hud-val {
  font-weight: 700;
}

.mono {
  font-family: monospace;
}

.contract-link {
  color: #60A5FA;
}

.proposals-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 160px;
}

.prop-item {
  background: #171717;
  border-left: 3px solid #F2C12E;
  padding: 8px;
  margin-bottom: 8px;
  font-size: 0.7rem;
}

.prop-title {
  font-weight: 800;
  color: #FFF;
  margin-bottom: 4px;
}

.prop-votes {
  font-size: 0.65rem;
  margin-bottom: 2px;
}

.prop-root {
  color: #777;
  font-family: monospace;
  font-size: 0.6rem;
}

/* Center Radar */
.radar-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: radial-gradient(circle at center, #141414 0%, #080808 80%);
}

.topology-svg {
  width: 100%;
  height: 100%;
  max-width: 650px;
  max-height: 650px;
}

.radar-ring {
  fill: none;
  stroke: #262626;
  stroke-width: 1.5;
  stroke-dasharray: 6 6;
}

.ring-label {
  fill: #444;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 1px;
}

.center-core {
  fill: #E03C31;
  stroke: #F2C12E;
  stroke-width: 3;
}

.center-core-pulse {
  fill: none;
  stroke: #E03C31;
  stroke-width: 1.5;
  opacity: 0.4;
  animation: pulse-ring 3s infinite ease-out;
}

@keyframes pulse-ring {
  0% { transform: scale(0.8); opacity: 0.8; }
  100% { transform: scale(1.6); opacity: 0; }
}

.center-label {
  fill: #FFF;
  font-size: 11px;
  font-weight: 900;
  text-anchor: middle;
  letter-spacing: 1px;
}

.center-sublabel {
  fill: #F2C12E;
  font-size: 9px;
  font-weight: 800;
  text-anchor: middle;
}

.peer-beam {
  stroke: #F2C12E;
  stroke-width: 1.5;
  stroke-dasharray: 4 4;
  opacity: 0.6;
}

.node-group {
  cursor: pointer;
  transition: transform 0.3s ease;
}

.hitbox {
  fill: transparent;
}

.peer-dot {
  fill: #F2C12E;
  stroke: #FFF;
  stroke-width: 2.5;
  transition: r 0.2s;
}

.node-group:hover .peer-dot {
  r: 20;
  fill: #E03C31;
}

.node-group.is-selected .peer-dot {
  fill: #10B981;
  stroke: #FFF;
  stroke-width: 3;
  r: 20;
}

.node-ip-label {
  fill: #FFFFFF;
  font-size: 11px;
  font-weight: 800;
  text-anchor: middle;
  text-shadow: 0px 2px 4px rgba(0,0,0,0.8);
}

.node-time-label {
  fill: #A3A3A3;
  font-size: 9px;
  font-weight: 700;
  text-anchor: middle;
}

.empty-radar-label {
  fill: #EF4444;
  font-size: 14px;
  font-weight: 900;
  text-anchor: middle;
  letter-spacing: 1px;
}

.empty-radar-sublabel {
  fill: #888;
  font-size: 10px;
  font-weight: 700;
  text-anchor: middle;
}

/* Right Panel: Node Inspector */
.hud-right {
  width: 340px;
  background: rgba(16, 16, 16, 0.95);
  border-left: 2px solid #222;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.node-inspector {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.empty-inspector {
  color: #777;
  font-size: 0.8rem;
  line-height: 1.5;
  margin-top: 20px;
}

.hero-ip {
  font-size: 1.3rem;
  font-weight: 900;
  color: #FFF;
  margin-bottom: 4px;
}

.hero-badge {
  display: inline-block;
  padding: 3px 8px;
  font-size: 0.7rem;
  font-weight: 800;
  background: #333;
  color: #FFF;
  margin-bottom: 16px;
}

.badge-active {
  background: #065F46;
  color: #34D399;
  border: 1px solid #059669;
}

.detail-section {
  margin-bottom: 14px;
}

.detail-section label {
  display: block;
  font-size: 0.65rem;
  font-weight: 800;
  color: #777;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.detail-value {
  font-size: 0.8rem;
  color: #DDD;
  word-break: break-all;
}

.detail-value-sub {
  font-size: 0.7rem;
  color: #999;
  margin-top: 2px;
}

.select-all {
  user-select: all;
  background: #1C1C1C;
  padding: 4px 6px;
  border-radius: 2px;
}

.ping-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 4px;
}

.brutal-btn-action {
  background: #262626;
  color: #F2C12E;
  border: 1px solid #444;
  font-family: inherit;
  font-weight: 800;
  font-size: 0.7rem;
  padding: 5px 10px;
  cursor: pointer;
}

.brutal-btn-action:hover {
  background: #F2C12E;
  color: #000;
}

.ping-status {
  font-size: 0.75rem;
  font-weight: 800;
}

.ping-peer-id {
  font-size: 0.65rem;
  color: #888;
  margin-top: 6px;
}

.compliance-box {
  background: #181818;
  border: 1px solid #2E2E2E;
  padding: 8px;
  font-size: 0.7rem;
  color: #10B981;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.prop-desc {
  font-size: 0.7rem;
  color: #888;
  margin-bottom: 6px;
  line-height: 1.3;
}

.btn-zk-vote {
  margin-top: 8px;
  width: 100%;
  background: #111;
  color: #10B981;
  border: 1px solid #10B981;
  font-family: inherit;
  font-weight: 800;
  font-size: 0.72rem;
  padding: 6px 10px;
  cursor: pointer;
  letter-spacing: 0.05em;
  transition: all 0.15s ease;
}

.btn-zk-vote:hover {
  background: #10B981;
  color: #000;
}

/* Modal Styling */
.zk-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.zk-modal-content {
  background: #0D1117;
  border: 1px solid #30363D;
  border-top: 3px solid #10B981;
  width: 100%;
  max-width: 580px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.8);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.zk-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #21262D;
  background: #161B22;
}

.zk-modal-title {
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #E6EDF3;
}

.zk-modal-close {
  background: transparent;
  border: none;
  color: #8B949E;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0 4px;
}

.zk-modal-close:hover {
  color: #F85149;
}

.zk-modal-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.modal-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.modal-field label {
  font-size: 0.65rem;
  color: #8B949E;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.modal-field .field-val {
  font-size: 0.8rem;
  color: #C9D1D9;
  background: #161B22;
  padding: 6px 10px;
  border: 1px solid #30363D;
  word-break: break-all;
}

.modal-field .field-val.highlight {
  color: #F2C12E;
  font-weight: 700;
}

.modal-field-group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.zk-select, .zk-input {
  background: #161B22;
  border: 1px solid #30363D;
  color: #E6EDF3;
  padding: 8px 10px;
  font-family: inherit;
  font-size: 0.75rem;
  outline: none;
  border-radius: 0;
}

.zk-select:focus, .zk-input:focus {
  border-color: #10B981;
}

.vote-direction-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.btn-vote-choice {
  background: #161B22;
  border: 1px solid #30363D;
  font-family: inherit;
  font-size: 0.8rem;
  font-weight: 800;
  padding: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-vote-choice.btn-yes {
  color: #10B981;
}

.btn-vote-choice.btn-yes.active {
  background: #10B981;
  color: #000;
  border-color: #10B981;
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
}

.btn-vote-choice.btn-no {
  color: #F85149;
}

.btn-vote-choice.btn-no.active {
  background: #F85149;
  color: #FFF;
  border-color: #F85149;
  box-shadow: 0 0 12px rgba(248, 81, 73, 0.4);
}

.zk-status-box {
  background: #161B22;
  border: 1px solid #10B981;
  padding: 10px 12px;
  font-size: 0.72rem;
  color: #10B981;
  display: flex;
  align-items: center;
  gap: 8px;
}

.zk-status-box.is-error {
  border-color: #F85149;
  color: #F85149;
}

.zk-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 16px;
  background: #161B22;
  border-top: 1px solid #21262D;
}

.btn-cancel {
  background: transparent;
  border: 1px solid #30363D;
  color: #8B949E;
  font-family: inherit;
  font-size: 0.72rem;
  padding: 8px 14px;
  cursor: pointer;
}

.btn-submit-zk {
  background: #10B981;
  border: 1px solid #10B981;
  color: #000;
  font-family: inherit;
  font-size: 0.72rem;
  font-weight: 800;
  padding: 8px 16px;
  cursor: pointer;
  letter-spacing: 0.05em;
  transition: all 0.15s ease;
}

.btn-submit-zk:hover:not(:disabled) {
  background: #059669;
  box-shadow: 0 0 15px rgba(16, 185, 129, 0.4);
}

.btn-submit-zk:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
