<template>
  <div class="governance-panel p-6 bg-[var(--surface-color)] rounded-xl border border-[var(--border-color)]">
    <h2 class="text-2xl font-bold mb-4 text-[var(--accent-color)]">The Forge (Dark Forest Governance)</h2>
    
    <div class="status-box mb-6 p-4 rounded bg-black/40 border border-[var(--border-light)]">
      <h3 class="font-semibold mb-2">Your Cypherpunk Identity</h3>
      <div v-if="!hasIdentity" class="flex flex-col gap-2">
        <p class="text-sm text-gray-400">You need a local secret and nullifier to vote anonymously.</p>
        <button @click="generateIdentity" class="btn-primary py-2 px-4 rounded bg-[var(--accent-color)] text-white hover:opacity-80 transition-opacity">
          Generate Secret Identity
        </button>
      </div>
      <div v-else class="flex flex-col gap-2">
        <p class="text-xs font-mono text-green-400">Identity Generated (Stored Locally)</p>
        <p class="text-xs text-gray-500">Public Commitment: <span class="truncate block w-full">{{ commitmentDisplay }}</span></p>
      </div>
    </div>

    <div class="proposals-box">
      <h3 class="font-semibold mb-3">Active Proposals</h3>
      
      <!-- Mock Proposal for UI -->
      <div class="proposal-card p-4 rounded bg-[var(--surface-light)] border border-[var(--border-color)] mb-4">
        <div class="flex justify-between items-start mb-2">
          <h4 class="font-bold text-lg">#0: Deploy Sovereign AI to Mainnet</h4>
          <span class="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded">Active</span>
        </div>
        <p class="text-sm text-gray-400 mb-4">Should we activate the Skynet protocol?</p>
        
        <div class="flex gap-4 items-center">
          <button 
            @click="castShieldedVote(0, true)" 
            :disabled="!hasIdentity || isVoting"
            class="px-6 py-2 rounded font-bold bg-green-500/20 text-green-400 hover:bg-green-500/30 disabled:opacity-50 transition-colors">
            VOTE YES (Shielded)
          </button>
          <button 
            @click="castShieldedVote(0, false)" 
            :disabled="!hasIdentity || isVoting"
            class="px-6 py-2 rounded font-bold bg-red-500/20 text-red-400 hover:bg-red-500/30 disabled:opacity-50 transition-colors">
            VOTE NO (Shielded)
          </button>
        </div>
        
        <div v-if="isVoting" class="mt-4 text-sm text-yellow-400 animate-pulse flex items-center gap-2">
          <lucide-loader class="animate-spin h-4 w-4" /> Generating Zero-Knowledge Proof... (This requires heavy CPU math)
        </div>
        
        <div v-if="voteStatus" class="mt-4 text-sm text-green-400 font-mono">
          {{ voteStatus }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
// We use dynamic imports for circomlibjs/snarkjs to avoid SSR/Tauri load issues
// import * as snarkjs from 'snarkjs'; 
// import { buildPoseidon } from 'circomlibjs';

const hasIdentity = ref(false);
const isVoting = ref(false);
const voteStatus = ref('');

const emit = defineEmits(['proof-generated']);

const cypherpunkIdentity = ref({
  secret: null,
  nullifier: null,
  commitment: null
});

const commitmentDisplay = computed(() => {
  if (!cypherpunkIdentity.value.commitment) return '';
  const str = cypherpunkIdentity.value.commitment.toString();
  return str.substring(0, 10) + '...' + str.substring(str.length - 10);
});

async function generateIdentity() {
  try {
    // Dynamic import to prevent bundler issues with node crypto
    const { buildPoseidon } = await import('circomlibjs');
    const poseidon = await buildPoseidon();
    const F = poseidon.F;

    // In a real app, generate cryptographically secure random numbers
    // For demo, we use Math.random() padded
    const secret = BigInt(Math.floor(Math.random() * 1000000000000));
    const nullifier = BigInt(Math.floor(Math.random() * 1000000000000));
    
    const commitmentHash = poseidon([nullifier, secret]);
    const commitment = F.toObject(commitmentHash);

    cypherpunkIdentity.value = {
      secret,
      nullifier,
      commitment
    };
    
    // Store locally so it never leaves the browser!
    localStorage.setItem('aethelnet_zk_identity', JSON.stringify({
      secret: secret.toString(),
      nullifier: nullifier.toString(),
      commitment: commitment.toString()
    }));
    
    hasIdentity.value = true;
  } catch (err) {
    console.error("Error generating identity:", err);
    alert("Failed to load ZK Cryptography module.");
  }
}

async function castShieldedVote(proposalId, support) {
  if (!hasIdentity.value) return;
  
  isVoting.value = true;
  voteStatus.value = '';
  
  try {
    const snarkjs = await import('snarkjs');
    
    const input = {
      commitment: cypherpunkIdentity.value.commitment.toString(),
      proposalId: proposalId.toString(),
      vote: support ? "1" : "0",
      secret: cypherpunkIdentity.value.secret.toString(),
      nullifier: cypherpunkIdentity.value.nullifier.toString()
    };

    console.log("Starting Proof Generation with Inputs:", input);

    // Fetch the wasm and zkey from the public folder
    const result = await snarkjs.groth16.fullProve(
      input, 
      "/zk/ShieldedVote.wasm", 
      "/zk/circuit_final.zkey"
    );

    console.log("Proof Generated!", result);
    const nullifierHash = result.publicSignals[0];
    
    voteStatus.value = `✅ ZK Proof Generated! NullifierHash: ${nullifierHash.substring(0, 10)}... (Ready for On-Chain tx)`;
    
    // Format proof for Solidity
    const a = [result.proof.pi_a[0], result.proof.pi_a[1]];
    const b = [
        [result.proof.pi_b[0][1], result.proof.pi_b[0][0]],
        [result.proof.pi_b[1][1], result.proof.pi_b[1][0]]
    ];
    const c = [result.proof.pi_c[0], result.proof.pi_c[1]];

    // Emit to parent to execute transaction via MetaMask
    emit('proof-generated', {
      proposalId,
      support,
      a,
      b,
      c,
      nullifierHash,
      commitment: input.commitment
    });
    
  } catch (err) {
    console.error("Proof Generation Failed:", err);
    voteStatus.value = "❌ Proof Generation Failed (See Console)";
  } finally {
    isVoting.value = false;
  }
}

// Check for existing identity on mount
const stored = localStorage.getItem('aethelnet_zk_identity');
if (stored) {
  const parsed = JSON.parse(stored);
  cypherpunkIdentity.value = {
    secret: BigInt(parsed.secret),
    nullifier: BigInt(parsed.nullifier),
    commitment: BigInt(parsed.commitment)
  };
  hasIdentity.value = true;
}
</script>

<style scoped>
/* Scoped styles can be added here if needed, but we rely mostly on Tailwind/Shared CSS */
</style>
