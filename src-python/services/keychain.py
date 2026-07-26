import json
import os
import cryptography
from cryptography.fernet import Fernet
from typing import Dict, Optional

# Path to the KeyVault
KEYVAULT_PATH = "backend/secure_vault.enc"
KEY_FILE = "backend/master.key"

class KeyChain:
    """
    The KeyChain.
    Manages encrypted API keys for the Omni-Broker Nexus.
    """
    def __init__(self):
        self._load_master_key()
        self.keys: Dict[str, Dict[str, str]] = {}
        self._load_vault()

    def _load_master_key(self):
        """Loads or creates the symmetric encryption key."""
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "rb") as f:
                self.fernet_key = f.read()
        else:
            self.fernet_key = Fernet.generate_key()
            with open(KEY_FILE, "wb") as f:
                f.write(self.fernet_key)
        
        self.cipher = Fernet(self.fernet_key)

    def _load_vault(self):
        """Decrypts and loads the vault."""
        if not os.path.exists(KEYVAULT_PATH):
            return

        try:
            with open(KEYVAULT_PATH, "rb") as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            self.keys = json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"[KeyChain] Failed to unlock vault: {e}")
            self.keys = {}

    def _save_vault(self):
        """Encrypts and saves the vault."""
        json_data = json.dumps(self.keys)
        encrypted_data = self.cipher.encrypt(json_data.encode())
        
        with open(KEYVAULT_PATH, "wb") as f:
            f.write(encrypted_data)

    def add_key(self, exchange: str, api_key: str, secret_key: str):
        self.keys[exchange] = {
            "api_key": api_key,
            "secret_key": secret_key
        }
        self._save_vault()
        print(f"[KeyChain] Securely stored keys for {exchange}.")

    def get_keys(self, exchange: str) -> Optional[Dict[str, str]]:
        return self.keys.get(exchange)

    def list_chains(self):
        return list(self.keys.keys())

    def remove_key(self, exchange: str):
        if exchange in self.keys:
            del self.keys[exchange]
            self._save_vault()

# Singleton with re-entrancy guard to avoid import/init cycles
_instance = None
_keychain_initializing = False

def get_keychain():
    global _instance, _keychain_initializing
    if _instance is None:
        if _keychain_initializing:
            # Return a conservative stub while the real KeyChain is being initialized.
            class _StubKeyChain:
                def __init__(self):
                    self.keys = {}

                def get_keys(self, exchange: str):
                    return None

                def list_chains(self):
                    return []

                def add_key(self, exchange: str, api_key: str, secret_key: str):
                    # no-op during bootstrap
                    return

                def remove_key(self, exchange: str):
                    return

            return _StubKeyChain()

        _keychain_initializing = True
        try:
            _instance = KeyChain()
        finally:
            _keychain_initializing = False
    return _instance
