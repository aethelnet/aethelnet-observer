<template>
  <div class="forge-container">
    <div class="forge-header">
      <h2>THE FORGE <span>// DAO GOVERNANCE</span></h2>
      <ShieldedGovernance class="mb-8" @proof-generated="handleZkVote" />
      <div class="stats-bar">
        <div class="stat">
          <label>TREASURY BALANCE</label>
          <span class="value">10,000,000 AETHEL</span>
        </div>
        <div class="stat">
          <label>SHIELDED POOL</label>
          <span class="value text-green">{{ shieldedBalance }} AETHEL</span>
        </div>
        <div class="stat">
          <label>NETWORK STATUS</label>
          <span class="value" :class="{ 'text-green': account, 'text-red': !account }">
            {{ account ? `CONNECTED: ${account.slice(0, 6)}...${account.slice(-4)}` : 'DISCONNECTED' }}
          </span>
        </div>
      </div>
      <div class="action-bar">
        <button v-if="!account" class="brutal-btn connect-btn" @click="connectWallet">
          [ CONNECT METAMASK ]
        </button>
        <div v-else class="zk-panel">
          <input type="number" v-model="shieldAmount" placeholder="Amount" class="brutal-input" />
          <button class="brutal-btn zk-btn" @click="generateZkProof" :disabled="isGeneratingZk">
            {{ isGeneratingZk ? 'GENERATING PROOF...' : '[ OBFUSCATE BALANCE (ZK-PROOF) ]' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="account" class="action-bar create-toggle">
      <button class="brutal-btn" @click="showCreate = !showCreate">
        {{ showCreate ? '[ CANCEL ]' : '[ + CREATE PROPOSAL ]' }}
      </button>
      <button class="brutal-btn" @click="deployContracts" :disabled="isDeploying" style="margin-left: 10px; background: #E03C31; color: white; border-color: #E03C31;">
        {{ isDeploying ? 'DEPLOYING TO CHAIN...' : '[ ⚠ DEPLOY CONTRACTS ]' }}
      </button>
    </div>

    <div v-if="account && showCreate" class="create-form">
      <h3>SUBMIT NEW PROPOSAL</h3>
      <input type="text" v-model="newTitle" placeholder="PROPOSAL TITLE" class="brutal-input full-width" />
      <textarea v-model="newDesc" placeholder="Describe the proposal in detail..." class="brutal-textarea"></textarea>
      <button class="brutal-btn submit-btn" @click="submitProposal" :disabled="isSubmitting || !newTitle || !newDesc">
        {{ isSubmitting ? 'TRANSMITTING...' : '[ SUBMIT TO BLOCKCHAIN ]' }}
      </button>
    </div>

    <div v-if="account" class="proposals-list">
      <div v-if="proposals.length === 0" class="proposal-card">
        <h3>NO PROPOSALS FOUND</h3>
        <p>The DAO is quiet. Wait for a proposal or submit one via CLI.</p>
      </div>

      <div v-for="proposal in proposals" :key="proposal.id" class="proposal-card">
        <div class="proposal-meta">
          <span class="proposal-id">PROP-{{ proposal.id }}</span>
          <span class="proposal-status" :class="proposal.status.toLowerCase()">[{{ proposal.status }}]</span>
        </div>
        
        <h3>{{ proposal.title }}</h3>
        <p class="description">{{ proposal.description }}</p>
        
        <div class="vote-bars">
          <div class="bar-label">FOR <span class="percent">{{ getPercent(proposal.forVotes, proposal.againstVotes) }}%</span></div>
          <div class="bar-bg">
            <div class="bar-fill for" :style="{ width: getPercent(proposal.forVotes, proposal.againstVotes) + '%' }"></div>
          </div>
          
          <div class="bar-label">AGAINST <span class="percent">{{ getPercent(proposal.againstVotes, proposal.forVotes) }}%</span></div>
          <div class="bar-bg">
            <div class="bar-fill against" :style="{ width: getPercent(proposal.againstVotes, proposal.forVotes) + '%' }"></div>
          </div>
        </div>
        
        <div class="actions">
          <button class="vote-btn for" @click="vote(proposal.id, true)" :disabled="isVoting === proposal.id">
            {{ isVoting === proposal.id ? 'TRANSMITTING...' : '▲ PUBLIC FOR' }}
          </button>
          <button class="vote-btn against" @click="vote(proposal.id, false)" :disabled="isVoting === proposal.id">
            {{ isVoting === proposal.id ? 'TRANSMITTING...' : '▼ PUBLIC AGAINST' }}
          </button>
          <button class="vote-btn shielded" @click="voteShielded(proposal.id, true)" :disabled="isVoting === proposal.id || !activeZkProof">
            [ SHIELDED FOR ]
          </button>
          <button class="vote-btn shielded-against" @click="voteShielded(proposal.id, false)" :disabled="isVoting === proposal.id || !activeZkProof">
            [ SHIELDED AGAINST ]
          </button>
        </div>
      </div>
    </div>
    <div v-else class="disconnect-msg">
      <h2>AWAITING AUTHORIZATION</h2>
      <p>You must connect your Web3 Wallet to access The Forge.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import ShieldedGovernance from '../components/ShieldedGovernance.vue'
import { ethers } from 'ethers'
import AethelTokenArtifact from '../AethelTokenArtifact.json'
import TheForgeArtifact from '../TheForgeArtifact.json'
import VerifierArtifact from '../VerifierArtifact.json'

const AETHEL_ADDRESS = '0x138246711caB8bB67a3f2B4AD13792C5E0Ca3329'
const AETHEL_ABI = [
  "function generateVotingProof(uint256 amount, bytes32 secretPhraseHash)",
  "function depositToShielded(uint256 amount)",
  "function shieldedBalanceOf(address user) view returns (uint256)",
  "function approve(address spender, uint256 value) returns (bool)"
]

const FORGE_ADDRESS = '0x81E3E4Cba25546b2e8339Bf9d7c46F6707cE88f2'
const FORGE_ABI = [
  "function nextProposalId() view returns (uint256)",
  "function proposals(uint256) view returns (uint256 id, string title, string description, uint256 forVotes, uint256 againstVotes, bool executed, uint256 endTime, address proposer)",
  "function createProposal(string title, string description)",
  "function votePublic(uint256 proposalId, bool support)",
  "function voteShielded(uint256 proposalId, bool support, uint256[2] a, uint256[2][2] b, uint256[2] c, uint256 nullifierHash, uint256 commitment)"
]

const account = ref('')
const proposals = ref([])
const isVoting = ref(null)
const shieldedBalance = ref('0')
const shieldAmount = ref(100)
const isGeneratingZk = ref(false)
const activeZkProof = ref(null) // Stores the hash generated
const showCreate = ref(false)
const newTitle = ref('')
const newDesc = ref('')
const isSubmitting = ref(false)
const isDeploying = ref(false)

const deployContracts = async () => {
  if (!account.value) return
  if (!confirm("Du bist dabei, den AethelToken und TheForge Smart Contract auf dem aktuellen Netzwerk über DEINE Wallet zu deployen. Kostet Gas! Fortfahren?")) return;
  
  isDeploying.value = true
  try {
    const provider = new ethers.BrowserProvider(window.ethereum)
    const signer = await provider.getSigner()
    
    console.log("Deploying AethelToken...")
    const TokenFactory = new ethers.ContractFactory(AethelTokenArtifact.abi, AethelTokenArtifact.bytecode, signer)
    const token = await TokenFactory.deploy()
    await token.waitForDeployment()
    const tokenAddr = await token.getAddress()
    
    console.log("Deploying Verifier...")
    const VerifierFactory = new ethers.ContractFactory(VerifierArtifact.abi, VerifierArtifact.bytecode, signer)
    const verifier = await VerifierFactory.deploy()
    await verifier.waitForDeployment()
    const verifierAddr = await verifier.getAddress()
    
    console.log("Deploying TheForge...")
    const ForgeFactory = new ethers.ContractFactory(TheForgeArtifact.abi, TheForgeArtifact.bytecode, signer)
    const forge = await ForgeFactory.deploy(verifierAddr)
    await forge.waitForDeployment()
    const forgeAddr = await forge.getAddress()
    
    alert(`Deployment Erfolgreich!\n\nAethelToken: ${tokenAddr}\nTheForge: ${forgeAddr}\n\nBitte kopiere diese Adressen und ersetze sie oben in TheForge.vue (Zeile 116 / 124)!!`)
    
  } catch (err) {
    console.error("Deploy failed", err)
    alert(err.reason || err.message || "Deployment failed.")
  } finally {
    isDeploying.value = false
  }
}

const submitProposal = async () => {
  if (!account.value || !newTitle.value || !newDesc.value) return
  isSubmitting.value = true
  try {
    const provider = new ethers.BrowserProvider(window.ethereum)
    const signer = await provider.getSigner()
    const contract = new ethers.Contract(FORGE_ADDRESS, FORGE_ABI, signer)
    
    const tx = await contract.createProposal(newTitle.value, newDesc.value)
    await tx.wait()
    
    newTitle.value = ''
    newDesc.value = ''
    showCreate.value = false
    await loadProposals()
  } catch (err) {
    console.error("Failed to create proposal", err)
    alert(err.reason || err.message || "Transaction failed.")
  } finally {
    isSubmitting.value = false
  }
}

const connectWallet = async () => {
  if (typeof window.ethereum !== 'undefined') {
    try {
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' })
      account.value = accounts[0]
      await loadProposals()
      await loadShieldedBalance()
    } catch (err) {
      console.error("Wallet connection failed", err)
    }
  } else {
    alert('MetaMask is not installed. Please install it to access The Forge.')
  }
}

const loadShieldedBalance = async () => {
  if (!account.value) return
  try {
    const provider = new ethers.BrowserProvider(window.ethereum)
    const contract = new ethers.Contract(AETHEL_ADDRESS, AETHEL_ABI, provider)
    const bal = await contract.shieldedBalanceOf(account.value)
    shieldedBalance.value = bal.toString()
  } catch (err) {
    console.error("Failed to load shielded balance", err)
  }
}

const generateZkProof = async () => {
  if (!account.value) return
  isGeneratingZk.value = true
  try {
    const provider = new ethers.BrowserProvider(window.ethereum)
    const signer = await provider.getSigner()
    const contract = new ethers.Contract(AETHEL_ADDRESS, AETHEL_ABI, signer)
    
    // First ensure we have shielded balance
    const currentBal = await contract.shieldedBalanceOf(account.value)
    if (Number(currentBal) < shieldAmount.value) {
      // Auto-deposit to shielded pool if needed
      const txDep = await contract.depositToShielded(shieldAmount.value)
      await txDep.wait()
    }

    // Generate ZK Proof Hash (Simulated local hashing of a secret)
    const secret = ethers.hexlify(ethers.randomBytes(32))
    const zkProofHash = ethers.keccak256(ethers.AbiCoder.defaultAbiCoder().encode(['uint256', 'bytes32'], [shieldAmount.value, secret]))
    
    const tx = await contract.generateVotingProof(shieldAmount.value, secret)
    await tx.wait()
    
    activeZkProof.value = zkProofHash
    alert(`ZK-Proof Generated & Registered! You can now cast a SHIELDED vote.\n\nHash: ${zkProofHash}`)
    await loadShieldedBalance()
  } catch (err) {
    console.error("ZK Generation failed", err)
    alert(err.reason || err.message)
  } finally {
    isGeneratingZk.value = false
  }
}

const loadProposals = async () => {
  if (!account.value) return
  try {
    const provider = new ethers.BrowserProvider(window.ethereum)
    const contract = new ethers.Contract(FORGE_ADDRESS, FORGE_ABI, provider)
    
    const count = await contract.nextProposalId()
    const loaded = []
    
    for (let i = Number(count) - 1; i >= 0; i--) {
      const p = await contract.proposals(i)
      loaded.push({
        id: Number(p.id),
        title: p.title,
        description: p.description,
        forVotes: Number(p.forVotes),
        againstVotes: Number(p.againstVotes),
        status: p.executed ? 'EXECUTED' : (Number(p.endTime) * 1000 > Date.now() ? 'ACTIVE' : 'ENDED')
      })
    }
    
    proposals.value = loaded
  } catch (err) {
    console.error("Failed to load proposals", err)
  }
}

const vote = async (id, support) => {
  if (!account.value) return
  isVoting.value = id
  
  try {
    const provider = new ethers.BrowserProvider(window.ethereum)
    const signer = await provider.getSigner()
    const contract = new ethers.Contract(FORGE_ADDRESS, FORGE_ABI, signer)
    
    const tx = await contract.votePublic(id, support)
    await tx.wait()
    
    await loadProposals()
  } catch (err) {
    console.error("Voting failed", err)
    alert(err.reason || err.message || "Voting transaction failed.")
  } finally {
    isVoting.value = null
  }
}

const voteShielded = async (id, support) => {
  alert("Bitte benutze das neue Dark Forest Governance Panel oben, um einen ZK-Beweis zu generieren!");
}

const handleZkVote = async (proofData) => {
  if (!account.value) {
    alert("Bitte verbinde zuerst deine Wallet!");
    return;
  }
  
  isVoting.value = proofData.proposalId
  
  try {
    const provider = new ethers.BrowserProvider(window.ethereum)
    const signer = await provider.getSigner()
    const contract = new ethers.Contract(FORGE_ADDRESS, FORGE_ABI, signer)
    
    console.log("Submitting ZK Proof On-Chain...");
    const tx = await contract.voteShielded(
      proofData.proposalId, 
      proofData.support, 
      proofData.a,
      proofData.b,
      proofData.c,
      proofData.nullifierHash,
      proofData.commitment
    )
    await tx.wait()
    
    alert("✅ ZK Vote erfolgreich auf der Blockchain registriert!");
    await loadProposals()
  } catch (err) {
    console.error("Shielded Voting failed", err)
    alert(err.reason || err.message || "Voting transaction failed.")
  } finally {
    isVoting.value = null
  }
}

const getPercent = (votesA, votesB) => {
  const total = votesA + votesB
  if (total === 0) return 0
  return ((votesA / total) * 100).toFixed(0)
}

onMounted(async () => {
  if (typeof window.ethereum !== 'undefined') {
    const accounts = await window.ethereum.request({ method: 'eth_accounts' })
    if (accounts.length > 0) {
      account.value = accounts[0]
      loadProposals()
      loadShieldedBalance()
    }
  }
})
</script>

<style scoped>
.forge-container {
  padding: 40px;
  background: #FFFFFF;
  color: #111111;
  height: 100%;
  overflow-y: auto;
  font-family: 'JetBrains Mono', monospace;
}

.forge-header {
  border-bottom: 4px solid #111111;
  padding-bottom: 20px;
  margin-bottom: 40px;
}

.forge-header h2 {
  font-size: 32px;
  font-weight: 900;
  letter-spacing: -1px;
  margin: 0 0 20px 0;
}

.forge-header h2 span {
  color: #666666;
}

.stats-bar {
  display: flex;
  gap: 40px;
  margin-bottom: 20px;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat label {
  font-size: 10px;
  font-weight: bold;
  letter-spacing: 2px;
  color: #666666;
}

.stat .value {
  font-size: 24px;
  font-weight: bold;
}

.text-green { color: #32D74B; }
.text-red { color: #FF3366; }

.brutal-btn {
  background: #111111;
  color: #FFFFFF;
  border: 4px solid #111111;
  padding: 15px 30px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px;
  font-weight: 900;
  cursor: pointer;
  text-transform: uppercase;
  transition: all 0.2s;
  box-shadow: 6px 6px 0px rgba(17, 17, 17, 0.2);
}

.brutal-btn:hover {
  background: #FFFFFF;
  color: #111111;
  box-shadow: 6px 6px 0px #111111;
  transform: translate(-2px, -2px);
}

.connect-btn {
  margin-top: 20px;
}

.proposals-list {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.proposal-card {
  border: 4px solid #111111;
  padding: 30px;
  background: #F8F8F8;
  box-shadow: 8px 8px 0px #111111;
}

.proposal-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  font-weight: bold;
  font-size: 14px;
}

.proposal-id {
  background: #111111;
  color: #FFFFFF;
  padding: 4px 8px;
}

.proposal-status.active {
  color: #32D74B;
  border-bottom: 2px solid #32D74B;
}

.proposal-card h3 {
  font-size: 24px;
  font-weight: 900;
  margin: 0 0 15px 0;
}

.description {
  font-size: 16px;
  line-height: 1.5;
  margin-bottom: 30px;
  max-width: 800px;
}

.vote-bars {
  margin-bottom: 30px;
}

.bar-label {
  font-weight: bold;
  margin-bottom: 5px;
  display: flex;
  justify-content: space-between;
}

.bar-bg {
  width: 100%;
  height: 20px;
  border: 2px solid #111111;
  margin-bottom: 15px;
  background: #FFFFFF;
}

.bar-fill {
  height: 100%;
  transition: width 0.5s ease;
}

.bar-fill.for { background: #111111; }
.bar-fill.against { background: #FF3366; }

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
}

.zk-panel {
  display: flex;
  gap: 15px;
  align-items: stretch;
}

.create-toggle {
  margin-bottom: 20px;
  justify-content: flex-end;
}

.create-form {
  border: 4px solid #111111;
  padding: 30px;
  background: #F8F8F8;
  margin-bottom: 30px;
  display: flex;
  flex-direction: column;
  gap: 15px;
  box-shadow: 8px 8px 0px #111111;
}

.create-form h3 {
  margin: 0 0 10px 0;
  font-size: 24px;
  font-weight: 900;
}

.brutal-input.full-width {
  width: 100%;
  box-sizing: border-box;
}

.brutal-textarea {
  width: 100%;
  height: 150px;
  background: #FFFFFF;
  border: 4px solid #111111;
  padding: 15px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 16px;
  font-weight: bold;
  resize: vertical;
  box-sizing: border-box;
}

.brutal-textarea:focus {
  outline: none;
  background: #F8F8F8;
}

.submit-btn {
  align-self: flex-start;
}

.brutal-input {
  background: #FFFFFF;
  border: 4px solid #111111;
  padding: 10px 15px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 16px;
  font-weight: bold;
  width: 150px;
}

.brutal-input:focus {
  outline: none;
  background: #F8F8F8;
}

.zk-btn {
  background: #111111;
  color: #FFFFFF;
  padding: 10px 20px;
}

.zk-btn:hover:not(:disabled) {
  background: #FFFFFF;
  color: #111111;
  box-shadow: 4px 4px 0px #111111;
  transform: translate(-2px, -2px);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.vote-btn {
  flex: 1 1 45%;
  padding: 15px;
  font-size: 16px;
  font-weight: bold;
  font-family: inherit;
  cursor: pointer;
  border: 4px solid #111111;
  background: #FFFFFF;
  color: #111111;
  text-transform: uppercase;
  transition: all 0.2s;
  box-shadow: 4px 4px 0px rgba(17, 17, 17, 0.2);
}

.vote-btn:hover:not(:disabled) {
  background: #111111;
  color: #FFFFFF;
  box-shadow: 4px 4px 0px #111111;
  transform: translate(-2px, -2px);
}

.vote-btn.shielded {
  background: #111111;
  color: #32D74B;
  border-color: #111111;
}
.vote-btn.shielded:hover:not(:disabled) {
  background: #32D74B;
  color: #111111;
}

.vote-btn.shielded-against {
  background: #111111;
  color: #FF3366;
  border-color: #111111;
}
.vote-btn.shielded-against:hover:not(:disabled) {
  background: #FF3366;
  color: #111111;
}

.vote-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #EAEAEA;
  color: #666666;
  border-color: #AAAAAA;
  box-shadow: none;
}

.disconnect-msg {
  text-align: center;
  padding: 100px 20px;
  border: 4px dashed #CCCCCC;
}

.disconnect-msg h2 {
  font-size: 32px;
  margin: 0 0 10px 0;
}
</style>
