"""
Simple headful Playwright helper to open a login page, let you sign in, and save cookies to a JSON file.
Usage (PowerShell):
    python -m pip install --upgrade pip; python -m pip install playwright
    python -m playwright install
    python scripts\capture_playwright_cookies.py "https://www.example.com/login" -o compadre_cookies.json

After running, sign in in the opened browser window, then press Enter in this terminal to save cookies.
"""

from playwright.sync_api import sync_playwright
import json
import argparse


def capture_login_cookies(url: str, output: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        print(f"Opening {url}. Complete the login in the browser window. When finished, return here and press Enter.")
        page.goto(url)
        input("Press Enter after you have completed login (or Ctrl+C to cancel)...")
        cookies = context.cookies()
        with open(output, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2)
        print(f"Saved {len(cookies)} cookies to {output}")
        browser.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Capture cookies after manual headful login with Playwright')
    parser.add_argument('url', help='Login page URL to open')
    parser.add_argument('-o', '--output', default='cookies.json', help='Output JSON file')
    args = parser.parse_args()
    capture_login_cookies(args.url, args.output)
