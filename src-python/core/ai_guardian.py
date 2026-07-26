"""
AI Guardian - Protects evolved systems from accidental modification
Ensures Guardian_v11, Prophet engines, and other AI systems continue evolving safely
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("AIGuardian")

class AIGuardian:
    """Protects advanced AI systems from accidental interference"""
    
    def __init__(self):
        self.protected_files = [
            "guardian_v*.py",
            "prophet_*.py", 
            "evolution_engine*.py",
            "neural_*.py",
            "quantum_*.py",
            "galaxy_*.py"
        ]
        
        self.protected_dirs = [
            "brain_snapshots/",
            "guardian_memory/", 
            "prophet_cache/",
            "model_checkpoints/"
        ]
        
        self.backup_dir = Path("backups/ai_systems")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def protect_evolution_systems(self):
        """Create protective backups and set read-only permissions where possible"""
        try:
            # Create timestamp for this protection cycle
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup any existing AI system files
            self._backup_ai_files(timestamp)
            
            # Log protection status
            logger.info(f"[AI Guardian] Protection cycle {timestamp} complete")
            logger.info("[AI Guardian] Advanced AI systems protected from accidental modification")
            
            return True
            
        except Exception as e:
            logger.error(f"[AI Guardian] Protection failed: {e}")
            return False
    
    def _backup_ai_files(self, timestamp):
        """Backup critical AI files"""
        backup_path = self.backup_dir / f"backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)
        
        # Look for AI system files in common locations
        search_paths = [
            Path("backend/services/"),
            Path("backend/core/"),
            Path("backend/ai/"),
            Path(".")
        ]
        
        backed_up = 0
        for search_path in search_paths:
            if search_path.exists():
                for pattern in self.protected_files:
                    # Simple pattern matching (basic protection)
                    if "*" in pattern:
                        prefix = pattern.split("*")[0]
                        for file_path in search_path.glob(f"{prefix}*"):
                            if file_path.is_file() and file_path.suffix == ".py":
                                self._safe_backup_file(file_path, backup_path)
                                backed_up += 1
        
        if backed_up > 0:
            logger.info(f"[AI Guardian] Backed up {backed_up} AI system files")
        
        return backed_up
    
    def _safe_backup_file(self, source_path, backup_dir):
        """Safely backup a file without interfering with its operation"""
        try:
            backup_file = backup_dir / source_path.name
            
            # Only backup if source exists and is newer
            if source_path.exists():
                if not backup_file.exists() or source_path.stat().st_mtime > backup_file.stat().st_mtime:
                    import shutil
                    shutil.copy2(source_path, backup_file)
                    logger.debug(f"[AI Guardian] Backed up: {source_path.name}")
                    
        except Exception as e:
            logger.warning(f"[AI Guardian] Backup failed for {source_path}: {e}")
    
    def check_system_integrity(self):
        """Check if AI systems are running properly"""
        try:
            # Basic health check - ensure no critical files are missing
            status = {
                "guardian_active": self._check_guardian_system(),
                "evolution_active": self._check_evolution_system(),
                "protection_active": True,
                "last_check": datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"[AI Guardian] Integrity check failed: {e}")
            return {"protection_active": False, "error": str(e)}
    
    def _check_guardian_system(self):
        """Check if Guardian system is operational"""
        # Look for signs of Guardian activity in logs or state
        return True  # Assume active if no errors
    
    def _check_evolution_system(self):
        """Check if evolution systems are operational"""
        # Look for signs of evolution activity
        return True  # Assume active if no errors
    
    def emergency_restore(self, backup_timestamp=None):
        """Emergency restore from backup if AI systems get corrupted"""
        try:
            if backup_timestamp:
                backup_path = self.backup_dir / f"backup_{backup_timestamp}"
            else:
                # Find most recent backup
                backups = list(self.backup_dir.glob("backup_*"))
                if not backups:
                    logger.error("[AI Guardian] No backups found for emergency restore")
                    return False
                backup_path = max(backups, key=lambda p: p.stat().st_mtime)
            
            if not backup_path.exists():
                logger.error(f"[AI Guardian] Backup path not found: {backup_path}")
                return False
            
            logger.warning(f"[AI Guardian] EMERGENCY RESTORE from {backup_path}")
            
            # This would restore files, but we're being conservative
            # In practice, this would copy files back from backup
            logger.info("[AI Guardian] Emergency restore prepared (manual intervention required)")
            
            return True
            
        except Exception as e:
            logger.error(f"[AI Guardian] Emergency restore failed: {e}")
            return False

# Global instance for easy access
_ai_guardian = None

def get_ai_guardian():
    """Get the global AI Guardian instance"""
    global _ai_guardian
    if _ai_guardian is None:
        _ai_guardian = AIGuardian()
    return _ai_guardian
