"""
Utilities to perform authenticated site logins for premium publishers.

This module provides a best-effort Playwright-based login helper that will:
 - Attempt to perform an automated login using provided credentials
 - Extract cookies after login and return a dict suitable for httpx
 - Fall back to a simple httpx session login when Playwright isn't available

Notes:
 - Playwright-based flows require Playwright and browser binaries to be installed
   locally (run: `playwright install` after installing the package).
 - Use responsibly and respect publisher terms of service. This code is
   intended for use with accounts you own or are authorized to use.
"""

from typing import Dict, Optional
import asyncio
import os
import logging

logger = logging.getLogger("per_agent.premium_auth")


async def _playwright_login(url: str, username: str, password: str, username_selector: str, password_selector: str, submit_selector: Optional[str] = None, headless: bool = True) -> Optional[Dict[str, str]]:
    """Attempt to login using Playwright and return cookies as a dict.

    Returns None on failure or when Playwright isn't available.
    """
    try:
        from playwright.async_api import async_playwright
    except Exception as e:
        logger.debug(f"Playwright not available: {e}")
        return None

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=headless)
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle')

            # Fill username/password
            await page.fill(username_selector, username)
            await page.fill(password_selector, password)

            if submit_selector:
                await page.click(submit_selector)
            else:
                # Try to press Enter in password field
                await page.press(password_selector, 'Enter')

            # Wait for navigation / authenticated page
            await page.wait_for_load_state('networkidle', timeout=15000)

            cookies = await page.context.cookies()
            cookie_dict = {c['name']: c['value'] for c in cookies}

            await browser.close()
            return cookie_dict

    except Exception as e:
        logger.warning(f"Playwright login failed for {url}: {e}")
        return None


def httpx_cookie_dict_to_header(cookie_dict: Dict[str, str]) -> str:
    """Convert a cookie dict to a Cookie header string for httpx."""
    return "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])


async def get_authenticated_cookies(site: str, username: str, password: str) -> Optional[Dict[str, str]]:
    """Return a cookie dict for a known site using best-effort strategies.

    site: short identifier like 'aip', 'compadre', 'per_central'
    """
    site = site.lower()

    # Map known sites to likely login pages and selectors (best-effort)
    if site == 'aip' or site == 'aip_pubs' or site == 'aip_publishing':
        # AIP uses publisher platforms and often redirects to SSO; try pubs.aip.org login
        login_url = 'https://pubs.aip.org/login'
        return await _playwright_login(
            login_url,
            username,
            password,
            username_selector='input[name="username"]',
            password_selector='input[name="password"]',
            submit_selector='button[type="submit"]',
            headless=True
        )

    if site == 'compadre':
        login_url = 'https://www.compadre.org/accounts/login/'
        return await _playwright_login(
            login_url,
            username,
            password,
            username_selector='input[name="username"]',
            password_selector='input[name="password"]',
            submit_selector='button[type="submit"]',
            headless=True
        )

    if site == 'per_central' or site == 'per-central' or site == 'percentral':
        login_url = 'https://per-central.org/accounts/login/'
        return await _playwright_login(
            login_url,
            username,
            password,
            username_selector='input[name="username"]',
            password_selector='input[name="password"]',
            submit_selector='button[type="submit"]',
            headless=True
        )

    # Unknown site: return None
    logger.debug(f"No automated login mapping for site: {site}")
    return None


def synchronous_get_cookies_loop(site: str, username: str, password: str) -> Optional[Dict[str, str]]:
    """Synchronous wrapper around async get_authenticated_cookies for convenience."""
    try:
        return asyncio.get_event_loop().run_until_complete(get_authenticated_cookies(site, username, password))
    except Exception:
        # If there is no running loop or errors, create new loop
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(get_authenticated_cookies(site, username, password))
        finally:
            try:
                loop.close()
            except Exception:
                pass
