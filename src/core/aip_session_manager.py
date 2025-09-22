"""
AIP Session Manager - Handles long-lived session authentication with graceful fallbacks
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright
import httpx
from datetime import datetime, timedelta

class AIPSessionManager:
    """Manages AIP authentication sessions with automatic fallbacks"""
    
    def __init__(self, storage_file: str = "cache/auth/aip_session_state.json"):
        # Use cache/auth directory for security
        self.cache_dir = Path("cache/auth")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.storage_file = Path(storage_file)
        self.logger = logging.getLogger(__name__)
        self.session_timeout = timedelta(days=7)  # Sessions typically last about a week
        
    def _is_session_expired(self, session_data: Dict[str, Any]) -> bool:
        """Check if stored session has expired"""
        if 'timestamp' not in session_data:
            return True
            
        last_login = datetime.fromisoformat(session_data['timestamp'])
        return datetime.now() - last_login > self.session_timeout
    
    async def get_authenticated_session(self, force_reauth: bool = False) -> Optional[Dict[str, str]]:
        """
        Get an authenticated AIP session, with fallbacks:
        1. Try stored session if not expired
        2. If expired/invalid, prompt for manual login
        3. If user skips, return None (graceful degradation)
        """
        
        # Try stored session first (unless forced reauth)
        if not force_reauth and self.storage_file.exists():
            try:
                with open(self.storage_file, 'r') as f:
                    session_data = json.load(f)
                
                if not self._is_session_expired(session_data):
                    self.logger.info("Using existing AIP session")
                    return session_data.get('cookies', {})
                else:
                    self.logger.info("Stored AIP session expired")
            except Exception as e:
                self.logger.warning(f"Could not load stored session: {e}")
        
        # Stored session unavailable/expired - prompt for login
        return await self._manual_login()
    
    async def _manual_login(self) -> Optional[Dict[str, str]]:
        """Prompt user for manual login and capture session"""
        
        print("\n" + "="*60)
        print("🔐 AIP Authentication Required")
        print("="*60)
        print("Your AIP session has expired or is unavailable.")
        print("Please complete login in the browser window that will open.")
        print("This setup takes ~30 seconds and sessions last ~7 days.")
        print("="*60)
        
        response = input("\nProceed with AIP login? (y/n): ").strip().lower()
        if response != 'y':
            print("⚠️  Skipping AIP authentication - will use free sources only")
            return None
        
        try:
            async with async_playwright() as p:
                # Launch browser in headful mode for user interaction
                browser = await p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
                context = await browser.new_context()
                page = await context.new_page()
                
                print("\n🌐 Opening AIP login page...")
                await page.goto("https://pubs.aip.org/signin")
                
                print("👤 Please complete your login in the browser window.")
                print("⏳ Waiting for successful login (checking for account page)...")
                
                # Wait for successful login (user reaches account/profile area)
                try:
                    await page.wait_for_url("**/my-account/**", timeout=180000)  # 3 minutes max
                    print("✅ Login detected! Capturing session...")
                except Exception:
                    # Fallback: wait for any post-login page
                    await asyncio.sleep(10)  # Give user time to complete login
                    if "signin" in page.url:
                        print("⚠️  Login not detected. Please try again.")
                        await browser.close()
                        return None
                
                # Capture cookies
                cookies = await context.cookies()
                
                # Store session data
                session_data = {
                    'cookies': {c['name']: c['value'] for c in cookies},
                    'timestamp': datetime.now().isoformat(),
                    'source': 'manual_login'
                }
                
                with open(self.storage_file, 'w') as f:
                    json.dump(session_data, f, indent=2)
                
                await browser.close()
                
                print(f"🎉 AIP session saved! ({len(cookies)} cookies captured)")
                print("💾 Session will be valid for ~7 days")
                
                return session_data['cookies']
                
        except Exception as e:
            self.logger.error(f"Manual login failed: {e}")
            print(f"❌ Authentication failed: {e}")
            return None
    
    async def search_aip_articles(self, query: str, limit: int = 10) -> list:
        """Search AIP publications with authenticated session"""
        
        cookies = await self.get_authenticated_session()
        if not cookies:
            self.logger.warning("No AIP session available")
            return []
        
        try:
            async with httpx.AsyncClient(cookies=cookies, timeout=30.0) as client:
                # Use AIP's search API
                search_url = "https://pubs.aip.org/search"
                params = {
                    'q': query,
                    'rows': limit,
                    'start': 0
                }
                
                response = await client.get(search_url, params=params)
                
                if response.status_code != 200:
                    self.logger.warning(f"AIP search failed: {response.status_code}")
                    return []
                
                # Parse search results (simplified)
                articles = []
                # TODO: Implement proper HTML parsing for AIP search results
                
                return articles
                
        except Exception as e:
            self.logger.error(f"AIP search error: {e}")
            return []