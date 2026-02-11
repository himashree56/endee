
from typing import Dict, Any
from datetime import datetime

class IngestionStatus:
    _instance = None
    
    def __init__(self):
        # Format: { filename: { status: 'queued'|'processing'|'completed'|'failed', 
        #                       progress: int, 
        #                       total: int, 
        #                       message: str,
        #                       updated_at: datetime } }
        self.status: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def update_status(self, filename: str, status: str, message: str = None, progress: int = 0, total: int = 0):
        print(f"[IngestionStatus] Updating {filename}: status={status}, progress={progress}/{total}, msg={message}")
        if filename not in self.status:
            self.status[filename] = {}
            
        self.status[filename].update({
            "status": status,
            "updated_at": datetime.now().isoformat()
        })
        
        if message:
            self.status[filename]["message"] = message
        if progress > 0:
            self.status[filename]["progress"] = progress
        if total > 0:
            self.status[filename]["total"] = total
            
    def get_status(self, filename: str = None):
        if filename:
            return self.status.get(filename)
        return self.status
    
    def clear_completed(self):
        """Remove completed tasks to keep memory clean"""
        to_remove = [k for k, v in self.status.items() if v['status'] in ['completed', 'failed']]
        for k in to_remove:
            del self.status[k]
