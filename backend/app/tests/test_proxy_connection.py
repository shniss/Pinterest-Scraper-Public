#!/usr/bin/env python3
"""
Test proxy connection to diagnose tunnel issues
Run with: python test_proxy_connection.py
"""

import asyncio
import logging
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def test_proxy_connection():
    """Test proxy connection without the full bot"""
    print("🔍 Testing Proxy Connection")
    print("=" * 50)

    # Proxy configuration (same as in your test account)
    proxy_config = {
        "server": "us-pr.oxylabs.io:10001",
        "username": "shniss_oleve_pFeOx",
        "password": "Oleve_test_password123",
    }

    print(f"Proxy Server: {proxy_config['server']}")
    print(f"Proxy Username: {proxy_config['username']}")
    print()

    try:
        async with async_playwright() as p:
            print("1. Launching browser...")
            browser = await p.chromium.launch(headless=False)

            print("2. Creating context with proxy...")
            context = await browser.new_context(
                proxy=proxy_config,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                ignore_https_errors=True,
            )

            print("3. Creating page...")
            page = await context.new_page()

            print("4. Testing proxy with httpbin.org...")
            try:
                await page.goto(
                    "https://httpbin.org/ip",
                    wait_until="domcontentloaded",
                    timeout=30000,
                )
                ip_info = await page.content()
                print("✅ Proxy test successful!")
                print(f"IP Info: {ip_info[:300]}...")
            except Exception as e:
                print(f"❌ Proxy test failed: {e}")
                return False

            print("5. Testing Pinterest connection...")
            try:
                await page.goto(
                    "https://www.pinterest.com",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                title = await page.title()
                print("✅ Pinterest connection successful!")
                print(f"Page title: {title}")

                # Take a screenshot
                await page.screenshot(path="proxy_test_screenshot.png")
                print("📸 Screenshot saved as proxy_test_screenshot.png")

            except Exception as e:
                print(f"❌ Pinterest connection failed: {e}")
                return False

            await browser.close()
            print("✅ All tests passed!")
            return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


async def test_without_proxy():
    """Test connection without proxy for comparison"""
    print("\n🔍 Testing Connection WITHOUT Proxy")
    print("=" * 50)

    try:
        async with async_playwright() as p:
            print("1. Launching browser...")
            browser = await p.chromium.launch(headless=False)

            print("2. Creating context without proxy...")
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )

            print("3. Creating page...")
            page = await context.new_page()

            print("4. Testing Pinterest connection...")
            try:
                await page.goto(
                    "https://www.pinterest.com",
                    wait_until="domcontentloaded",
                    timeout=30000,
                )
                title = await page.title()
                print("✅ Direct connection successful!")
                print(f"Page title: {title}")

            except Exception as e:
                print(f"❌ Direct connection failed: {e}")
                return False

            await browser.close()
            print("✅ Direct connection test passed!")
            return True

    except Exception as e:
        print(f"❌ Direct connection test failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Proxy Connection Test Suite")
    print("=" * 50)

    # Test without proxy first
    direct_success = await test_without_proxy()

    print("\n" + "=" * 50)

    # Test with proxy
    proxy_success = await test_proxy_connection()

    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"Direct connection: {'✅ PASS' if direct_success else '❌ FAIL'}")
    print(f"Proxy connection: {'✅ PASS' if proxy_success else '❌ FAIL'}")

    if not proxy_success and direct_success:
        print("\n🔧 Troubleshooting Tips:")
        print("1. Check if your Oxylabs proxy credentials are correct")
        print("2. Verify the proxy server is accessible from your network")
        print("3. Try a different proxy server or location")
        print("4. Check if your Oxylabs account has sufficient credits")
        print("5. Contact Oxylabs support if the issue persists")
        print("6. Try running without proxy for testing")


if __name__ == "__main__":
    asyncio.run(main())
