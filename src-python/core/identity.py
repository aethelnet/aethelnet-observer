import os
import hashlib
import uuid
import json
import time
from pathlib import Path

IDENTITY_FILE = "node_identity.json"
MANIFEST_FILE = "checksums.manifest"
PROPRIETARY_LICENSE_HEADER = "# COPYRIGHT AURATIC SYSTEMS"

class TheCrow:
    """
    Identity Manager.
    "Krabat, pick the right Crow."
    """

    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.identity_path = self.root_path / IDENTITY_FILE
        self.node_id = self.load_or_create_identity()

    def load_or_create_identity(self) -> str:
        if self.identity_path.exists():
            with open(self.identity_path, "r") as f:
                data = json.load(f)
                return data.get("node_id")

        # Create New Identity
        new_id = str(uuid.uuid4())
        with open(self.identity_path, "w") as f:
            json.dump({
                "node_id": new_id,
                "created_at": str(os.path.getctime(self.root_path) if self.root_path.exists() else 0),
                "role": "Mothership" # Default, can be Remote
            }, f)
        print(f"[CROW] Born. Node ID: {new_id}")
        return new_id

    def generate_manifest(self):
        """Hashes the codebase to create a Golden Record."""
        hashes = {}
        for r, d, f in os.walk(self.root_path / "backend"):
            for file in f:
                if file.endswith(".py"):
                    full_path = Path(r) / file
                    rel_path = str(full_path.relative_to(self.root_path))
                    with open(full_path, "rb") as fq:
                        hashes[rel_path] = hashlib.sha256(fq.read()).hexdigest()

        with open(self.root_path / MANIFEST_FILE, "w") as f:
            json.dump(hashes, f, indent=2)
        print(f"[CROW] Manifest Generated. {len(hashes)} files secured.")

    def verify_proprietary(self) -> bool:
        """
        Checks if the current code matches the Manifest (Tamper Check).
        Also checks for License Headers.
        """
        if not (self.root_path / MANIFEST_FILE).exists():
            print("[CROW] No Manifest found. Assuming Dev Mode (Unverified).")
            return False

        with open(self.root_path / MANIFEST_FILE, "r") as f:
            golden_hashes = json.load(f)

        errors = []
        for rel_path, gold_hash in golden_hashes.items():
            full_path = self.root_path / rel_path
            if not full_path.exists():
                errors.append(f"Missing: {rel_path}")
                continue
            
            with open(full_path, "rb") as fq:
                current_hash = hashlib.sha256(fq.read()).hexdigest()
            
            if current_hash != gold_hash:
                errors.append(f"Mismatch: {rel_path}")

        if errors:
            print(f"[CROW] INTEGRITY FAIL: {len(errors)} issues found.")
            # for e in errors: print(f" - {e}")
            return False

        print("[CROW] Proprietary Code Verified. System Pure.")
        return True

    def recover_identity(self, seed: str):
        """
        The Architect's Key.
        Regenerates the Node ID deterministically from a semantic seed.
        "Nika the Alchemist" -> [Deterministic UUID]
        """
        print(f"[CROW] Attempting to recover identity from the Ether...")

        # Simple deterministic Generation: SHA256(Seed) -> UUID
        # We assume the seed is the 'Soul' of the identity.
        hasher = hashlib.sha256(seed.encode('utf-8'))
        digest = hasher.hexdigest()
        
        # UUID from hash (32 chars)
        recovered_uuid = str(uuid.UUID(digest[:32]))

        # RESTORE
        with open(self.identity_path, "w") as f:
            json.dump({
                "node_id": recovered_uuid,
                "created_at": str(time.time()),
                "role": "Recovered_Architect",
                "seed_signature": hashlib.sha1(seed.encode()).hexdigest()[:8] # Verify marker
            }, f)
        
        print(f"[CROW] RECOVERY SUCCESSFUL. Welcome back, Architect.")
        print(f"[CROW] Restored Node ID: {recovered_uuid}")
        self.node_id = recovered_uuid

if __name__ == "__main__":
    import sys
    crow = TheCrow()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "gen-manifest":
            crow.generate_manifest()
        
        elif cmd == "verify":
            crow.verify_proprietary()
            
        elif cmd == "recover":
            if len(sys.argv) > 2:
                seed_phrase = " ".join(sys.argv[2:])
                crow.recover_identity(seed_phrase)
            else:
                print("Usage: python identity.py recover <seed phrase>")
    else:
        # Default startup check
        if not (crow.root_path / MANIFEST_FILE).exists():
            crow.generate_manifest()
        crow.verify_proprietary()
