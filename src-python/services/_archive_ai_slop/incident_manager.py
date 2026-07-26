import logging
import traceback
import hashlib
import json
import os
import requests
import asyncio
from typing import Optional, Any
from datetime import datetime
from config import get_settings

logger = logging.getLogger("IncidentManager")

class IncidentManager:
    """
    Automated Incident Reporting System.
    Detects internal errors, fingerprints them, and synchronizes with GitHub Issues.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IncidentManager, cls).__new__(cls)
            cls._instance.settings = get_settings()
            cls._instance.token = cls._instance.settings.GITHUB_TOKEN.get_secret_value() if cls._instance.settings.GITHUB_TOKEN else None
            cls._instance.repo = cls._instance.settings.GITHUB_REPO
            cls._instance.enabled = cls._instance.settings.INCIDENT_REPORTING_ENABLED and cls._instance.token is not None
        return cls._instance

    def _generate_fingerprint(self, exc: Exception) -> str:
        """Creates a unique hash for the error based on type and traceback."""
        try:
            tb = traceback.extract_tb(exc.__traceback__)
            # Last 3 frames are usually the most relevant
            relevant_tb = tb[-3:] if len(tb) >= 3 else tb
            tb_str = "".join([f"{f.filename}:{f.lineno}:{f.name}" for f in relevant_tb])
            content = f"{type(exc).__name__}:{str(exc)}:{tb_str}"
            return hashlib.md5(content.encode()).hexdigest()[:12]
        except Exception:
            return "unknown_error"

    async def report_incident(self, exc: Exception, context_data: Optional[dict] = None) -> Optional[str]:
        """
        Reports an incident to GitHub. 
        Returns the issue URL if successful, or None.
        """
        if not self.enabled:
            logger.debug("Incident reporting disabled or GITHUB_TOKEN missing.")
            return None

        fingerprint = self._generate_fingerprint(exc)
        title = f"[INCIDENT] {type(exc).__name__} in {fingerprint}"
        
        # Check if already reported
        existing_issue = self._find_existing_issue(fingerprint)
        if existing_issue:
            logger.info(f"Incident {fingerprint} already reported: {existing_issue['html_url']}")
            # Optional: Add a comment with more context if needed
            return existing_issue['html_url']

        # Construct Body
        tb_full = traceback.format_exc()
        body = (
            f"### [ SYSTEM ERROR REPORT ]\n"
            f"**Fingerprint:** `{fingerprint}`\n"
            f"**Timestamp:** `{datetime.utcnow().isoformat()}`\n"
            f"**Error Type:** `{type(exc).__name__}`\n"
            f"**Message:** `{str(exc)}`\n\n"
            f"#### Context Data:\n"
            f"```json\n{json.dumps(context_data or {}, indent=2)}\n```\n\n"
            f"#### Traceback:\n"
            f"```python\n{tb_full}\n```\n\n"
            f"---\n"
            f"*Automated report by Auratic Systems IncidentManager*"
        )

        try:
            url = f"https://api.github.com/repos/{self.repo}/issues"
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            data = {
                "title": title,
                "body": body,
                "labels": ["bug", "incident", "automated"]
            }
            
            # Use run_in_executor for requests if needed, but since this is a rare background task, 
            # simple requests is okay. For better hygiene, we use loop.run_in_executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.post(url, headers=headers, json=data))
            
            if response.status_code == 201:
                issue = response.json()
                logger.info(f"Successfully opened new issue: {issue['html_url']}")
                return issue['html_url']
            else:
                logger.error(f"Failed to open GitHub issue: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"Error communicating with GitHub: {e}")
        
        return None

    def _find_existing_issue(self, fingerprint: str) -> Optional[dict]:
        """Searches GitHub for an open issue with the given fingerprint."""
        try:
            url = f"https://api.github.com/repos/{self.repo}/issues"
            params = {
                "state": "open",
                "labels": "incident",
                "creator": "app/auratic-bot" # This might be hard if using personal token
            }
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Simple title-based search is more reliable for personal tokens
            response = requests.get(url, headers=headers, params={"state": "open"})
            if response.status_code == 200:
                issues = response.json()
                for issue in issues:
                    if fingerprint in issue.get('title', ''):
                        return issue
        except Exception as e:
            logger.error(f"Error searching for existing issues: {e}")
        return None

    async def sync_incidents(self):
        """
        Periodically checks open issues and logs their status.
        Could be expanded to notify users when a fix is deployed.
        """
        if not self.enabled:
            return

        logger.info("Syncing incidents with GitHub...")
        try:
            url = f"https://api.github.com/repos/{self.repo}/issues"
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.get(url, headers=headers, params={"state": "all", "labels": "incident"}))
            
            if response.status_code == 200:
                issues = response.json()
                completed = [i for i in issues if i['state'] == 'closed']
                if completed:
                    logger.info(f"Found {len(completed)} resolved incidents on GitHub.")
                    # In a real app, you might trigger a "thank you" to the user who reported it
            else:
                logger.error(f"Failed to sync issues: {response.status_code}")
        except Exception as e:
            logger.error(f"Error syncing incidents: {e}")

def get_incident_manager():
    return IncidentManager()
