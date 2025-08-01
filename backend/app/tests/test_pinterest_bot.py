#!/usr/bin/env python3
"""
Test script for Pinterest bot
Run with: python test_pinterest_bot.py
"""

import sys
import os
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# noqa: E402 - Imports after sys.path modification are necessary for test script
from app.services.automation.browser_factory import BrowserFactory
from app.services.automation.actions import (
    navigate_to_pinterest,
    test_login_status_on_pinterest,
    login_to_pinterest,
    check_and_skip_popups,
    navigate_to_create_board,
    create_board,
    save_pins_to_board,
    navigate_to_more_ideas,
    extract_pin_images_from_more_ideas,
)
from app.services.database.repo import PinterestAccountRepo
from app.models.pinterest_account import PinterestAccount, PinterestCookie, ProxyConfig


async def create_test_account() -> str:
    """Create a test Pinterest account in the database"""
    print("=== Creating Test Account ===")

    repo = PinterestAccountRepo()

    # Create test account with proper model structure
    test_account = PinterestAccount(
        username="Sean Nissenbaum",
        email="slayerniss@gmail.com",
        password="oleve-test-password",
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        cookies=[
            PinterestCookie(
                name="_auth",
                value="your_auth_cookie_value_here",
                domain=".pinterest.com",
            ),
            PinterestCookie(
                name="csrftoken", value="your_csrf_token_here", domain=".pinterest.com"
            ),
        ],
        proxy=ProxyConfig(
            server="us-pr.oxylabs.io:10001",
            username="shniss_oleve_pFeOx",
            password="Oleve_test_password123",
        ),
    )

    # Create account in database
    account_id = await repo.create(test_account)

    if account_id:
        print(f"✅ Created test account with ID: {account_id}")
        print(f"Username: {test_account.username}")
        print(f"Email: {test_account.email}")
        print(f"Cookies: {len(test_account.cookies)}")
        return account_id
    else:
        print("❌ Failed to create test account")
        return None


async def test_pinterest_bot(account_id: str):
    """Test the Pinterest bot with a specific account"""
    print("\n=== Testing Pinterest Bot ===")
    print(f"Account ID: {account_id}")

    # Test parameters
    test_prompt = "cottagecore house"

    try:
        # Get account from database
        repo = PinterestAccountRepo()
        account = await repo.get_account_by_id(account_id)

        if not account:
            print("❌ Failed to load account from database")
            return False

        print(f"✅ Loaded account: {account.username} ({account.email})")
        print(f"Cookies: {len(account.cookies)}")
        print(f"Proxy: {'Yes' if account.proxy else 'No'}")

        # Initialize browser factory
        browser_factory = BrowserFactory()

        try:
            # Start browser
            print("\n=== Browser Setup ===")
            if not await browser_factory.start(headless=False):
                print("❌ Failed to start browser")
                return False
            print("✅ Browser started")

            # Prepare proxy configuration
            proxy_config = None
            if account.proxy:
                # Ensure proxy server has proper format
                server = account.proxy.server
                if not server.startswith(("http://", "https://")):
                    server = f"http://{server}"

                proxy_config = {
                    "server": server,
                    "username": account.proxy.username,
                    "password": account.proxy.password,
                }
                print(f"✅ Proxy configured: {server}")

            # Create browser context
            if not await browser_factory.create_context(
                proxy_config=proxy_config, user_agent=account.user_agent
            ):
                print("❌ Failed to create browser context")
                return False
            print("✅ Browser context created")

            # Enable JavaScript and set additional page options
            print("Configuring page settings...")
            await browser_factory.page.set_extra_http_headers(
                {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                }
            )

            # Set viewport and other page properties
            await browser_factory.page.set_viewport_size(
                {"width": 1920, "height": 1080}
            )

            # Enable JavaScript (should be enabled by default, but let's be explicit)
            await browser_factory.page.add_init_script(
                """
                // Ensure JavaScript is enabled
                window.navigator = window.navigator || {};
                window.navigator.userAgent = window.navigator.userAgent || 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
            """
            )

            print("✅ Page settings configured")

            # Add cookies if available
            if account.cookies:
                print(f"Adding {len(account.cookies)} cookies...")
                playwright_cookies = account.playwright_cookies()
                if playwright_cookies:
                    await browser_factory.add_cookies(playwright_cookies)
                    print(f"✅ Added {len(playwright_cookies)} cookies")
                else:
                    print("⚠️  No valid cookies to add")

            # Navigate to Pinterest
            print("\n=== Pinterest Navigation ===")
            if not await navigate_to_pinterest(browser_factory.page):
                print("❌ Failed to navigate to Pinterest")
                return False
            print("✅ Navigated to Pinterest")

            # Wait for page to fully load and add debugging
            print("Waiting for page to fully load...")
            await asyncio.sleep(3)

            # Get page info for debugging
            title = await browser_factory.page.title()
            url = browser_factory.page.url
            print(f"Current URL: {url}")
            print(f"Page title: {title}")

            # Check if page has content
            try:
                body_text = await browser_factory.page.text_content("body")
                if body_text:
                    print(f"Page has content (first 200 chars): {body_text[:200]}...")
                else:
                    print("⚠️  Page appears to be empty")
            except Exception as e:
                print(f"⚠️  Could not get page content: {e}")

            # Test login status
            is_logged_in = await test_login_status_on_pinterest(browser_factory.page)

            if not is_logged_in:
                print("Not logged in, attempting login...")
                if not await login_to_pinterest(browser_factory.page, account):
                    print("❌ Failed to login to Pinterest")
                    return False
                print("✅ Login successful")

            else:
                print("✅ Already logged in")

            # Handle popups
            await check_and_skip_popups(browser_factory.page)

            # Navigate to boards page
            print("\n=== Board Creation ===")
            if not await navigate_to_create_board(browser_factory.page, account):
                print("❌ Failed to navigate to boards page")
                return False
            print("✅ Navigated to boards page")

            # Create board
            board_name = f"{test_prompt}"
            print(f"Creating board: {board_name}")
            if not await create_board(
                browser_factory.page, board_name=board_name, is_secret=True
            ):
                print("❌ Failed to create board")
                return False
            print("✅ Board created")

            # Save pins to board
            print("\n=== Pin Saving ===")
            if not await save_pins_to_board(
                browser_factory.page,
                prompt=test_prompt,
                acceptance_threshold=0.7,
                max_pins=7,
                max_scrolls=4,
            ):
                print("❌ Failed to save pins to board")
                return False
            print("✅ Pins saved to board")

            # Navigate to more ideas page
            print("\n=== More Ideas Navigation ===")
            if not await navigate_to_more_ideas(browser_factory.page):
                print("❌ Failed to navigate to more ideas page")
                return False
            print("✅ Navigated to more ideas page")

            # Extract pin images
            print("\n=== Extracting Pin Images ===")
            pins = await extract_pin_images_from_more_ideas(browser_factory.page)
            if not pins:
                print("❌ Failed to extract pin images")
                return False
            print(f"✅ Extracted {len(pins)} pin images")

            print(f"Pins: {pins}")

            return True

        finally:
            # Always stop the browser
            await browser_factory.stop()
            print("🔄 Browser stopped")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        print(f"Traceback: {traceback.format_exc()}")
        return False


async def main():
    """Main test function"""
    print("🤖 Pinterest Bot Test Suite")
    print("=" * 50)

    # Initialize repository
    repo = PinterestAccountRepo()

    # Try to get existing account or create new one
    print("Looking for existing account...")
    account_data = await repo._col.find_one()

    if account_data:
        account_id = str(account_data["_id"])
        print(
            f"✅ Found existing account: {account_data['username']} ({account_data['email']})"
        )
        print(f"Account ID: {account_id}")
    else:
        print("No existing account found, creating test account...")
        account_id = await create_test_account()

        if not account_id:
            print("❌ Failed to create test account")
            return

    # Run the test
    success = await test_pinterest_bot(account_id)

    if success:
        print("\n🎉 Pinterest bot test completed successfully!")
    else:
        print("\n💥 Pinterest bot test failed!")
        print("\nTroubleshooting tips:")
        print("1. Check your Pinterest credentials")
        print("2. Verify proxy settings (if using)")
        print("3. Ensure Playwright is installed: poetry run playwright install")
        print("4. Check network connectivity")


if __name__ == "__main__":
    asyncio.run(main())
