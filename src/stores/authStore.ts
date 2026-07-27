import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { createPublicClient, http, formatUnits, parseAbi } from 'viem'
import { hardhat } from 'viem/chains'

const AETHEL_CONTRACT = '0x5FbDB2315678afecb367f032d93F642f64180aa3' // Deployed on localhost

const publicClient = createPublicClient({
  chain: hardhat,
  transport: http('http://127.0.0.1:8545')
})

export const useAuthStore = defineStore('authStore', () => {
  const isConnected = ref(false)
  const walletAddress = ref<string | null>(null)
  const aethelBalance = ref('0.00')
  const shieldedBalance = ref('0.00')

  const connectWallet = async () => {
    if (typeof (window as any).ethereum !== 'undefined') {
      try {
        const accounts = await (window as any).ethereum.request({ method: 'eth_requestAccounts' })
        walletAddress.value = accounts[0]
        isConnected.value = true
        
        console.log(`[SystemLogsHUD] 🔗 WALLET CONNECTED: ${walletAddress.value}`)
        
        await syncBalance()
        await initiateWeb3Auth()
      } catch (error) {
        console.error("User denied account access", error)
      }
    } else {
      console.log('Please install MetaMask!')
    }
  }

  const initiateWeb3Auth = async () => {
    try {
      const challengeRes = await fetch('http://130.61.202.29:8000/web3/challenge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address: walletAddress.value })
      })
      const { nonce, challenge } = await challengeRes.json()
      
      const signature = await (window as any).ethereum.request({
        method: 'personal_sign',
        params: [challenge, walletAddress.value]
      })

      const loginRes = await fetch('http://130.61.202.29:8000/web3/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address: walletAddress.value, signature, nonce })
      })
      
      if (loginRes.ok) {
        const { access_token } = await loginRes.json()
        localStorage.setItem('aethelnet_token', access_token)
        console.log(`[SystemLogsHUD] 🔒 WEB3 AUTHENTICATED. JWT SECURED.`)
      }
    } catch(err) {
      console.error("Auth failed:", err)
    }
  }

  const syncBalance = async () => {
    if (!isConnected.value) return;

    try {
      const abi = parseAbi([
        'function balanceOf(address owner) view returns (uint256)',
        'function shieldedBalanceOf(address owner) view returns (uint256)'
      ])

      // Public Balance
      const balance = await publicClient.readContract({
        address: AETHEL_CONTRACT as `0x${string}`,
        abi,
        functionName: 'balanceOf',
        args: [walletAddress.value as `0x${string}`]
      })
      
      // Shielded Balance
      const shielded = await publicClient.readContract({
        address: AETHEL_CONTRACT as `0x${string}`,
        abi,
        functionName: 'shieldedBalanceOf',
        args: [walletAddress.value as `0x${string}`]
      })
      
      aethelBalance.value = formatUnits(balance, 18)
      shieldedBalance.value = formatUnits(shielded, 18)
      
      localStorage.setItem('aethelnet_treasury', aethelBalance.value)
      console.log(`[SystemLogsHUD] 💎 TREASURY SYNCED - Public: ${aethelBalance.value}, Shielded: ${shieldedBalance.value}`)
    } catch (error) {
      console.error("Failed to sync balance:", error)
    }
  }

  const shortAddress = computed(() => {
    if (!walletAddress.value) return ''
    return `${walletAddress.value.substring(0, 6)}...${walletAddress.value.substring(walletAddress.value.length - 4)}`
  })

  return {
    isConnected,
    walletAddress,
    shortAddress,
    aethelBalance,
    shieldedBalance,
    connectWallet
  }
})
