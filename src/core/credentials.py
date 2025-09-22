"""
Credentials configuration for premium database access.
Store your credentials here (this file should be added to .gitignore).
"""

from typing import Dict, Optional
import os
from pathlib import Path
from dotenv import load_dotenv


class PremiumCredentials:
    """
    Manage credentials for premium physics education databases.
    """
    
    def __init__(self):
        self.credentials_file = Path(".env")
        # Load environment variables from .env file
        load_dotenv(self.credentials_file)
        self._load_credentials()
    
    def _load_credentials(self):
        """Load credentials from environment variables or .env file."""
        # AIP Publishing credentials (pubs.aip.org)
        self.aip_username = os.getenv("AIP_USERNAME")
        self.aip_password = os.getenv("AIP_PASSWORD")
        
        # ComPADRE credentials (if needed)
        self.compadre_username = os.getenv("COMPADRE_USERNAME")
        self.compadre_password = os.getenv("COMPADRE_PASSWORD")
        
        # PER Central credentials (if needed)
        self.per_central_username = os.getenv("PER_CENTRAL_USERNAME")
        self.per_central_password = os.getenv("PER_CENTRAL_PASSWORD")
    
    def has_aip_access(self) -> bool:
        """Check if AIP Publishing credentials are available."""
        return bool(self.aip_username and self.aip_password)
    
    def has_compadre_access(self) -> bool:
        """Check if ComPADRE credentials are available."""
        return bool(self.compadre_username and self.compadre_password)
    
    def has_per_central_access(self) -> bool:
        """Check if PER Central credentials are available."""
        return bool(self.per_central_username and self.per_central_password)
    
    def get_aip_credentials(self) -> Optional[Dict[str, str]]:
        """Get AIP Publishing credentials if available."""
        if self.has_aip_access():
            return {
                "username": self.aip_username,
                "password": self.aip_password
            }
        return None
    
    def get_compadre_credentials(self) -> Optional[Dict[str, str]]:
        """Get ComPADRE credentials if available."""
        if self.has_compadre_access():
            return {
                "username": self.compadre_username,
                "password": self.compadre_password
            }
        return None
    
    def get_per_central_credentials(self) -> Optional[Dict[str, str]]:
        """Get PER Central credentials if available."""
        if self.has_per_central_access():
            return {
                "username": self.per_central_username,
                "password": self.per_central_password
            }
        return None