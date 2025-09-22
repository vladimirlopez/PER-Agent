"""
Simple cookie loader for premium sources
"""
import json
from pathlib import Path
from typing import Dict, Optional

def load_captured_cookies(source: str) -> Optional[Dict[str, str]]:
    """Load cookies captured by the Playwright script"""
    # Use cache/auth directory for security
    cache_dir = Path("cache/auth")
    
    cookie_file_map = {
        'aip': cache_dir / 'aip_cookies.json',
        'compadre': cache_dir / 'compadre_cookies.json',
        'per_central': cache_dir / 'per_central_cookies.json'
    }
    
    cookie_file = cookie_file_map.get(source)
    if not cookie_file or not cookie_file.exists():
        return None
    
    try:
        with open(cookie_file, 'r') as f:
            cookies = json.load(f)
        
        # Convert to simple dict format for httpx
        return {c['name']: c['value'] for c in cookies}
    except Exception:
        return None