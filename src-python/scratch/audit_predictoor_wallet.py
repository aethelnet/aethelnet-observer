
import asyncio
from web3 import Web3
from eth_account import Account
import os

# --- CONFIG ---
RPC_URL = "https://sapphire.oasis.io"
CHAIN_ID = 23294
OCEAN_TOKEN_ADDRESS = "0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520"
ERC20_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

async def audit_wallet():
    # 1. Get Key from ENV
    from config.settings import get_settings
    settings = get_settings()
    pk = settings.OCEAN_PRIVATE_KEY
    
    if not pk or "placeholder" in str(pk).lower():
        print("❌ CRITICAL: OCEAN_PRIVATE_KEY is missing or placeholder.")
        return

    pk_str = pk.get_secret_value() if hasattr(pk, 'get_secret_value') else str(pk)
    account = Account.from_key(pk_str)
    wallet_addr = account.address
    
    print(f"🕵️  AUDITING PREDICTOOR WALLET: {wallet_addr}")
    print(f"🌐 Chain: Oasis Sapphire Mainnet (ID: {CHAIN_ID})")
    
    # 2. Connect
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("❌ Could not connect to Oasis Sapphire RPC.")
        return
        
    # 3. Check ROSE (Gas)
    balance_wei = w3.eth.get_balance(wallet_addr)
    balance_rose = w3.from_wei(balance_wei, 'ether')
    
    print(f"💎 ROSE Balance: {balance_rose:.4f}")
    if balance_rose < 0.1:
        print("⚠️  WARNING: ROSE balance is critically low. You need ROSE for gas to submit predictions.")
    else:
        print("✅ ROSE gas balance is sufficient.")
        
    # 4. Check OCEAN (Stake)
    token_contract = w3.eth.contract(address=w3.to_checksum_address(OCEAN_TOKEN_ADDRESS), abi=ERC20_ABI)
    ocean_wei = token_contract.functions.balanceOf(wallet_addr).call()
    ocean_amt = w3.from_wei(ocean_wei, 'ether')
    
    print(f"🌊 OCEAN Balance: {ocean_amt:.4f}")
    if ocean_amt < 1.0:
        print("⚠️  WARNING: OCEAN balance is low. High-accuracy predictions require staking OCEAN to earn rewards.")
    else:
        print(f"✅ OCEAN stake balance is ready ({ocean_amt:.4f} OCEAN).")

    print("\n--- SUMMARY ---")
    if balance_rose > 0.1 and ocean_amt > 1.0:
        print("🚀 STATUS: GREEN. Wallet is primed for Ocean Predictoor activation.")
    else:
        print("🧱 STATUS: AMBER. Replenish balances before activating live submissions.")

if __name__ == "__main__":
    asyncio.run(audit_wallet())
