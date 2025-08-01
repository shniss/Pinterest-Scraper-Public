"""
Pinterest Warmup and Scraping Task

This Celery task combines Pinterest account warmup and image scraping in a single workflow.
The task uses Playwright to automate browser interactions with Pinterest.

Warmup Phase:
1. Login to Pinterest or use existing cookies
2. Create a new board tailored to the user's prompt
3. Save relevant pins to the board to train Pinterest's recommendation algorithm
4. This enables access to personalized "More Ideas" recommendations

Scraping Phase:
1. Navigate to the "More Ideas" page for the created board
2. Extract pin images, titles, and links from the recommendations
3. Save extracted data to database and broadcast to frontend

Architecture Notes:
- High complexity due to browser automation and multi-phase workflow
- Production improvements: Extract PinterestSessionManager class
- Future refactoring: Separate orchestration, workflow, and data management concerns

TODO:
  • Split into separate warm_up() and scrape_board() tasks for better modularity
  • Extract SessionOrchestrator class to encapsulate login/board operations
  • Implement proper session persistence layer
"""

from app.services.celery_app import celery_app
from app.services.messaging.broadcast import broadcast
from app.models.update_messages import WarmupMessage, ScrapedImageMessage
import asyncio
import nest_asyncio
from app.services.database.repo import (
    PinterestAccountRepo,
    PromptRepo,
    SessionRepo,
    PinRepo,
)
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
from app.models.pin import Pin, PinMetadata
from datetime import datetime
import os
from app.models.pinterest_account import PinterestAccount, ProxyConfig

# Configuration constants
SCRAPING_CONFIG = {
    "acceptance_threshold": 0.7,
    "max_pins": 7,
    "max_scrolls": 4,
    "headless": True,
    "viewport_width": 1920,
    "viewport_height": 1080,
    "page_load_timeout": 30000,
    "navigation_timeout": 30000,
}


@celery_app.task(name="app.tasks.warmup_and_scraping")
def warm_up_scraping(pid: str, session_id: str, prompt: str):
    """
    Main Celery task that performs Pinterest warmup and image scraping.

    This task orchestrates a complete workflow:
    1. Validates input parameters
    2. Sets up browser automation with Playwright
    3. Performs Pinterest account warmup (login, board creation, pin saving)
    4. Scrapes recommended images from the "More Ideas" page
    5. Saves results to database and broadcasts to frontend

    Args:
        pid: Prompt ID for tracking and database storage
        session_id: Session ID for progress tracking and logging
        prompt: User's search prompt (used for board name and pin selection)

    Returns:
        None (task result is communicated via WebSocket broadcasts)

    Raises:
        ValueError: If input parameters are invalid
        RuntimeError: If critical operations fail (login, browser setup, etc.)
    """
    # Input validation
    if not pid or not session_id or not prompt:
        raise ValueError(
            "All parameters (pid, session_id, prompt) must be provided and non-empty"
        )

    if (
        not isinstance(pid, str)
        or not isinstance(session_id, str)
        or not isinstance(prompt, str)
    ):
        raise TypeError("All parameters must be strings")
    try:
        # Apply nest_asyncio only when we need it for the task
        try:
            nest_asyncio.apply()
        except ValueError as e:
            if "uvloop" in str(e):
                print("uvloop detected, nest_asyncio not needed")
            else:
                print(f"nest_asyncio error: {e}")

        # Get the current event loop or create a new one
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run the async function in the current loop
        return loop.run_until_complete(_warm_up_async(pid, session_id, prompt))
    except Exception as e:
        print(f"Task failed with error: {e}")
        import traceback

        print(f"Task traceback: {traceback.format_exc()}")
        return None
    finally:
        # Clean up any remaining tasks in the event loop
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                if pending:
                    loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
        except Exception as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}")


async def _warm_up_async(pid: str, session_id: str, prompt: str):
    """
    Async implementation of the Pinterest warmup and scraping workflow.

    This function handles the core business logic:
    - Database repository initialization
    - Browser setup and configuration
    - Pinterest account warmup (login, board creation, pin saving)
    - Image scraping from recommendations
    - Data persistence and real-time updates

    Args:
        pid: Prompt ID for database operations
        session_id: Session ID for progress tracking
        prompt: User's search prompt

    Raises:
        RuntimeError: If any critical operation fails

    #TODO:
        -while we want real time updates to the frontend over websockets (at each scrape), we should switch to batching the mongodb updates so all images are scraped and then the results are send to mongo in a single message
    """
    try:
        # c
        prompt_repo = PromptRepo()
        account_repo = PinterestAccountRepo()
        session_repo = SessionRepo()
        pin_repo = PinRepo()

        # Update session stage and status
        try:
            await session_repo.update_stage(session_id, "warmup")
            await session_repo.update_status(session_id, "pending")
            await _full_warmup_log(
                pid, f"Warmup started for {prompt}!", session_repo, session_id
            )
        except Exception as e:
            print(f"Failed to update session {session_id} status: {e}")
            # Don't continue silently - this is critical for tracking
            raise RuntimeError(f"Failed to initialize session {session_id}: {e}")

        # Get Pinterest account credentials from database
        await _full_warmup_log(
            pid, "Getting Pinterest account info...", session_repo, session_id
        )
        account = await account_repo.get_first_account()

        if not account:
            await _full_warmup_log(
                pid, "No Pinterest account found, creating", session_repo, session_id
            )
            # Create account from environment variables as fallback
            
            email = os.getenv("PIN_EMAIL")
            password = os.getenv("PIN_PASSWORD")
            username = os.getenv("PIN_USERNAME", "Pinterest User")
            
            if not email or not password:
                await _full_warmup_log(
                    pid, "Missing login info", session_repo, session_id
                )
                raise RuntimeError("No Pinterest account found and missing required environment variables")
            
            # Create proxy config if available
            proxy_config = None
            proxy_server = os.getenv("PROXY_SERVER")
            proxy_username = os.getenv("PROXY_USERNAME")
            proxy_password = os.getenv("PROXY_PASSWORD")
            
            if proxy_server and proxy_username and proxy_password:
                proxy_config = ProxyConfig(
                    server=proxy_server,
                    username=proxy_username,
                    password=proxy_password
                )
            
            account = PinterestAccount(
                username=username,
                email=email,
                password=password,
                proxy=proxy_config,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            await _full_warmup_log(
                pid, f"Created fallback account", session_repo, session_id
            )

        # Initialize browser automation with Playwright
        browser_factory = None
        try:
            browser_factory = BrowserFactory()
            if not await browser_factory.start(headless=SCRAPING_CONFIG["headless"]):
                await _full_warmup_log(
                    pid, "Failed to start browser", session_repo, session_id
                )
                raise RuntimeError("Failed to start browser")

            await _full_warmup_log(pid, "Browser started", session_repo, session_id)

            # Configure proxy settings if available
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

            await _full_warmup_log(pid, "Proxy configured", session_repo, session_id)

            # Create browser context with proxy and user agent
            if not await browser_factory.create_context(
                proxy_config=proxy_config, user_agent=account.user_agent
            ):
                await _full_warmup_log(
                    pid, "Failed to create browser context", session_repo, session_id
                )
                raise RuntimeError("Failed to create browser context")

            await _full_warmup_log(
                pid, "Browser context created", session_repo, session_id
            )

            # Configure browser settings for Pinterest automation
            await _full_warmup_log(
                pid, "Configuring browser...", session_repo, session_id
            )
            # Set Pinterest-optimized headers
            await browser_factory.page.set_extra_http_headers(
                {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Cache-Control": "max-age=0",
                    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    "Sec-Ch-Ua-Mobile": "?0",
                    "Sec-Ch-Ua-Platform": '"macOS"',
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                }
            )

            # Set viewport and other page properties
            await browser_factory.page.set_viewport_size(
                {
                    "width": SCRAPING_CONFIG["viewport_width"],
                    "height": SCRAPING_CONFIG["viewport_height"],
                }
            )

            # Add anti-detection script to bypass Pinterest's bot detection
            await browser_factory.page.add_init_script(
                """
                // Override webdriver property to avoid detection
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Override chrome property
                Object.defineProperty(window, 'chrome', {
                    writable: true,
                    enumerable: true,
                    configurable: true,
                    value: {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    }
                });
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Ensure JavaScript is enabled
                window.navigator = window.navigator || {};
                window.navigator.userAgent = window.navigator.userAgent || 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
            """
            )

            # Load saved cookies for session persistence
            if account.cookies:
                print(f"Adding {len(account.cookies)} cookies...")
                playwright_cookies = account.playwright_cookies()
                if playwright_cookies:
                    await browser_factory.add_cookies(playwright_cookies)
                    await _full_warmup_log(
                        pid,
                        f"Added {len(playwright_cookies)} cookies",
                        session_repo,
                        session_id,
                    )
                else:
                    await _full_warmup_log(
                        pid, "No valid cookies to add", session_repo, session_id
                    )

            await _full_warmup_log(pid, "Browser configured", session_repo, session_id)

            # Navigate to Pinterest homepage
            await _full_warmup_log(
                pid, "Navigating to Pinterest...", session_repo, session_id
            )
            if not await navigate_to_pinterest(browser_factory.page):
                await _full_warmup_log(
                    pid, "Failed to navigate to Pinterest", session_repo, session_id
                )
                raise RuntimeError("Failed to navigate to Pinterest")
            await _full_warmup_log(
                pid, "Navigated to Pinterest", session_repo, session_id
            )

            # Wait for page to fully load and add debugging
            await _full_warmup_log(
                pid, "Waiting for page to fully load...", session_repo, session_id
            )
            await asyncio.sleep(3)  # Allow dynamic content to load

            # Check if already logged in or need to authenticate
            is_logged_in = await test_login_status_on_pinterest(browser_factory.page)

            if not is_logged_in:
                await _full_warmup_log(
                    pid, "Not logged in, attempting login...", session_repo, session_id
                )
                if not await login_to_pinterest(browser_factory.page, account):
                    await _full_warmup_log(
                        pid, "Failed to login to Pinterest", session_repo, session_id
                    )
                    raise RuntimeError("Failed to login to Pinterest")

            await _full_warmup_log(pid, "Login successful", session_repo, session_id)

            # Handle any popup dialogs that might interfere with automation
            await check_and_skip_popups(browser_factory.page)

            # Navigate to Pinterest boards section
            await _full_warmup_log(
                pid, "Navigating to boards page...", session_repo, session_id
            )
            if not await navigate_to_create_board(browser_factory.page, account):
                await _full_warmup_log(
                    pid, "Failed to navigate to boards page", session_repo, session_id
                )
                raise RuntimeError("Failed to navigate to boards page")

            await _full_warmup_log(
                pid, "Navigated to boards page", session_repo, session_id
            )

            # Create a new board with the user's prompt as the name
            await _full_warmup_log(
                pid, f"Creating board: {prompt}", session_repo, session_id
            )
            if not await create_board(
                browser_factory.page, board_name=prompt, is_secret=True
            ):
                await _full_warmup_log(
                    pid, "Failed to create board", session_repo, session_id
                )
                raise RuntimeError("Failed to create board")
            await _full_warmup_log(pid, "Board created", session_repo, session_id)

            # Save relevant pins to the board to train Pinterest's recommendation algorithm
            await _full_warmup_log(
                pid, "Saving pins to board...", session_repo, session_id
            )
            if not await save_pins_to_board(
                browser_factory.page,
                prompt=prompt,
                acceptance_threshold=SCRAPING_CONFIG["acceptance_threshold"],
                max_pins=SCRAPING_CONFIG["max_pins"],
                max_scrolls=SCRAPING_CONFIG["max_scrolls"],
            ):
                await _full_warmup_log(
                    pid, "Failed to save pins to board", session_repo, session_id
                )
                raise RuntimeError("Failed to save pins to board")
            await _full_warmup_log(pid, "Pins saved to board", session_repo, session_id)

            # Navigate to "More Ideas" page to access personalized recommendations
            await _full_warmup_log(
                pid, "Getting recommendations from board...", session_repo, session_id
            )
            if not await navigate_to_more_ideas(browser_factory.page):
                await _full_warmup_log(
                    pid,
                    "Failed to navigate to more ideas page",
                    session_repo,
                    session_id,
                )
                raise RuntimeError("Failed to navigate to more ideas page")
            await _full_warmup_log(
                pid, "Navigated to more ideas page", session_repo, session_id
            )

            # Warmup phase completed successfully
            await _full_warmup_log(
                pid,
                "Pinterest account successfully warmed up!",
                session_repo,
                session_id,
            )

            # Begin the scraping phase
            await _full_warmup_log(
                pid, "Beginning scraping...", session_repo, session_id
            )

            # ============== SCRAPING PHASE ==============

            # Update session status to indicate scraping phase
            await session_repo.update_stage(session_id, "scraping")
            await session_repo.update_status(session_id, "pending")

            # Extract pin images, titles, and links from the recommendations page
            pins = await extract_pin_images_from_more_ideas(browser_factory.page)
            curr_url = browser_factory.page.url

            if pins is None:
                await _full_warmup_log(
                    pid,
                    "Failed to extract pins - function returned None",
                    session_repo,
                    session_id,
                )
                await session_repo.update_status(session_id, "failed")
                return

            if not pins:
                await _full_warmup_log(
                    pid, "No pins found to process", session_repo, session_id
                )
                await session_repo.update_status(session_id, "completed")
                return

            # Process each extracted pin and save to database
            for pin in pins:
                print(f"Pin: {pin}")

                # Create metadata for tracking when pin was collected
                metadata = PinMetadata(collected_at=datetime.utcnow())

                # Construct valid Pinterest pin URL with fallback handling
                pin_link = pin.get("pin_link", "")
                if pin_link and pin_link.startswith("/"):
                    _pin_url = f"https://www.pinterest.com{pin_link}"
                elif pin_link and pin_link.startswith("http"):
                    _pin_url = pin_link
                else:
                    # Fallback to current page URL if no valid pin link
                    _pin_url = curr_url
                    print(
                        f"Warning: Invalid pin link '{pin_link}', using current URL as fallback"
                    )

                # Create database document for the pin
                pin_doc = Pin(
                    prompt_id=pid,
                    image_url=pin["image_url"],
                    pin_url=_pin_url,
                    title=pin.get("title", ""),
                    description=pin.get("alt_text", ""),
                    match_score=0.0,
                    status="pending",
                    ai_explanation="",
                    metadata=metadata,
                )

                # Save pin to database and broadcast to frontend
                pin_id = await pin_repo.create(pin_doc)
                print(f"Saved pin: {pin_id}")
                await session_repo.add_log(session_id, f"Saved pin: {pin_id}")

                # Broadcast pin data to frontend for real-time updates
                try:
                    broadcast(
                        pid,
                        ScrapedImageMessage(
                            type="scraped_image",
                            pin_id=pin_id,
                            url=pin["image_url"],
                            pin_url=_pin_url,
                            image_title=pin["title"],
                        ).model_dump(mode="json"),
                    )
                except Exception as broadcast_error:
                    print(f"Broadcast error: {broadcast_error}")
                    await session_repo.add_log(
                        session_id, f"Broadcast error: {broadcast_error}"
                    )

            # Mark session as completed after processing all pins
            await session_repo.update_status(session_id, "completed")

        finally:
            # Clean up browser resources to prevent memory leaks
            if browser_factory:
                try:
                    await browser_factory.stop()
                except Exception as stop_error:
                    print(f"Error stopping browser: {stop_error}")

    except Exception as e:
        print(f"Exception caught: {e}")
        print(f"Exception type: {type(e)}")
        import traceback

        print(f"Traceback: {traceback.format_exc()}")

        # Only try to log if we have valid repos and the event loop is still open
        try:
            if session_repo and session_id:
                await _full_warmup_log(pid, f"Error: {e}", session_repo, session_id)
        except Exception as log_error:
            print(f"Error in _full_warmup_log: {log_error}")

        try:
            if session_repo and prompt_repo and session_id:
                await _fail_playwright_bot(pid, session_id, prompt_repo, session_repo)
        except Exception as fail_error:
            print(f"Error in _fail_playwright_bot: {fail_error}")

        # Log the original error for debugging
        print(f"Original error that caused failure: {e}")
        print(f"Error type: {type(e).__name__}")

        # Re-raise the exception to ensure the task is marked as failed
        raise


async def _full_warmup_log(
    pid: str, message: str, session_repo: SessionRepo, session_id: str
) -> WarmupMessage:
    """
    Comprehensive logging function that handles progress tracking and real-time updates.

    This function:
    1. Logs messages to console for debugging
    2. Saves messages to session log history in database
    3. Broadcasts messages to frontend via WebSocket for real-time progress updates

    Args:
        pid: Prompt ID for WebSocket broadcasting
        message: Progress message to log and broadcast
        session_repo: Database repository for session operations
        session_id: Session ID for database logging

    Returns:
        WarmupMessage: Message object for broadcasting
    """
    print(f"Warmup: {message}")

    update_message = WarmupMessage(type="warmup", message=message)
    await session_repo.add_log(session_id, f"Warmup: {message}")
    try:
        broadcast(pid, update_message.model_dump(mode="json"))
    except Exception as broadcast_error:
        print(f"Broadcast error in _full_warmup_log: {broadcast_error}")


async def _fail_playwright_bot(
    pid: str, session_id: str, prompt_repo: PromptRepo, session_repo: SessionRepo
):
    """
    Handle task failure by updating database status and cleaning up resources.

    This function is called when the main task encounters an unrecoverable error.
    It ensures that both the session and prompt are marked as failed in the database
    so the frontend can display appropriate error states.

    Args:
        pid: Prompt ID to mark as failed
        session_id: Session ID to mark as failed
        prompt_repo: Database repository for prompt operations
        session_repo: Database repository for session operations
    """
    await session_repo.update_status(session_id, "failed")
    await prompt_repo.update_status(pid, "error")
