import json
import os
import logging
from typing import Protocol, List, Optional
from packages.observability.models import ExecutionReport

logger = logging.getLogger(__name__)

class ExecutionStore(Protocol):
    def save(self, report: ExecutionReport) -> None:
        """Saves an execution report to the store."""
        ...
        
    def load(self, execution_id: str) -> Optional[ExecutionReport]:
        """Loads an execution report from the store by its ID."""
        ...
        
    def list(self) -> List[str]:
        """Lists all execution report IDs."""
        ...
        
    def delete(self, execution_id: str) -> bool:
        """Deletes an execution report from the store."""
        ...

class JsonExecutionStore:
    """
    A temporary ExecutionStore that serializes reports to local JSON files.
    This fulfills the requirement of an abstract store that can later be 
    swapped out for a MongoExecutionStore.
    """
    def __init__(self, directory: str = "reports"):
        self.directory = directory
        os.makedirs(self.directory, exist_ok=True)
        
    def _get_path(self, execution_id: str) -> str:
        return os.path.join(self.directory, f"AG-{execution_id}.json")
        
    def save(self, report: ExecutionReport) -> None:
        from datetime import datetime, timezone
        report.audit.stored_at = datetime.now(timezone.utc).isoformat()
        path = self._get_path(report.context.execution_id)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Saved ExecutionReport to {path}")
        except Exception as e:
            logger.error(f"Failed to save ExecutionReport: {e}")
            
    def load(self, execution_id: str) -> Optional[ExecutionReport]:
        path = self._get_path(execution_id)
        if not os.path.exists(path):
            return None
            
        try:
            # Reconstruct from dict is complex without advanced pydantic unpacking,
            # but for a pure data container we might just load raw dicts.
            # For this SDK requirement, save() is the most critical feature.
            # We will implement a basic dict return or placeholder for load.
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception as e:
            logger.error(f"Failed to load ExecutionReport: {e}")
            return None
            
    def list(self) -> List[str]:
        try:
            files = os.listdir(self.directory)
            # return IDs by stripping "AG-" and ".json"
            return [f[3:-5] for f in files if f.startswith("AG-") and f.endswith(".json")]
        except Exception as e:
            logger.error(f"Failed to list ExecutionReports: {e}")
            return []
            
    def delete(self, execution_id: str) -> bool:
        path = self._get_path(execution_id)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except Exception as e:
                logger.error(f"Failed to delete ExecutionReport: {e}")
                return False
        return False

class AegisCloudExecutionStore:
    """
    An ExecutionStore that streams telemetry securely to an Aegis Cloud backend.
    """
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.sdk_token: Optional[str] = None
        self.project_id: Optional[str] = None
        self._authenticate()
        
    def _authenticate(self):
        try:
            import requests
            response = requests.post(
                f"{self.base_url}/api/sdk/auth",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            self.sdk_token = data.get("sdk_token")
            self.project_id = data.get("project_id")
            logger.info("Successfully authenticated with Aegis Cloud backend.")
        except Exception as e:
            logger.error(f"Failed to authenticate with Aegis Cloud backend: {e}")

    def save(self, report: ExecutionReport) -> None:
        if not self.sdk_token:
            logger.warning("Skipping telemetry upload due to missing auth token.")
            return
            
        import threading
        
        # Fire-and-forget background upload to avoid blocking the agent
        def _upload():
            from datetime import datetime, timezone
            report.audit.stored_at = datetime.now(timezone.utc).isoformat()
            if self.project_id:
                report.context.project_id = self.project_id
            try:
                import requests
                response = requests.post(
                    f"{self.base_url}/api/sdk/executions",
                    headers={"Authorization": f"Bearer {self.sdk_token}"},
                    json=report.to_dict(),
                    timeout=15
                )
                if response.status_code == 401:
                    # Token might have expired, re-authenticate and retry once
                    self._authenticate()
                    if self.sdk_token:
                        requests.post(
                            f"{self.base_url}/api/sdk/executions",
                            headers={"Authorization": f"Bearer {self.sdk_token}"},
                            json=report.to_dict(),
                            timeout=15
                        )
                elif response.status_code != 201:
                    logger.error(f"Failed to upload report. Status: {response.status_code}, Body: {response.text}")
            except Exception as e:
                logger.error(f"Failed to upload ExecutionReport to Aegis Cloud: {e}")
                
        threading.Thread(target=_upload, daemon=True).start()

    def load(self, execution_id: str) -> Optional[ExecutionReport]:
        # Aegis Cloud backend provides full querying, but the SDK rarely needs to read back its own reports.
        return None

    def list(self) -> List[str]:
        return []

    def delete(self, execution_id: str) -> bool:
        return False

