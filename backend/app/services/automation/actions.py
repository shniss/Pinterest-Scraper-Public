"""
Reusable playwright actions for pinterest
Actions take a in a page object, use browser_factory to get the page object

TODO:
  Add a check to see if the board is already created, if so, skip the create board step
  Fix the save_pins_to_board function to actually save pins, improving recommendations
  Refactor longer actions into smaller functions
  Cache found DOM elements to avoid re-finding them
  Unit tests
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from playwright.async_api import Page, TimeoutError as PWTimeout, ElementHandle
import logging
from app.models.pinterest_account import PinterestAccount
import random
from functools import wraps

logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_TIMEOUT = 15000  # Increased for Docker
LONG_TIMEOUT = 45000     # Increased for Docker
NAVIGATION_TIMEOUT = 90000  # Increased for Docker
RETRY_ATTEMPTS = 3
RETRY_DELAY = 3  # Increased delay for Docker
SLEEP_TIME_LONG = 3  # seconds - increased for Docker
SLEEP_TIME_SHORT = 2  # seconds - increased for Docker

# =======Utility functions=======


def retry_on_failure(max_attempts: int = RETRY_ATTEMPTS, delay: float = RETRY_DELAY):
    """Decorator to retry functions on failure"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )
            raise last_exception

        return wrapper

    return decorator


async def wait_for_element(
    page: Page, selectors: List[str], timeout: int = DEFAULT_TIMEOUT
) -> Tuple[Optional[ElementHandle], Optional[str]]:
    """Wait for any of the provided selectors to appear and return the element and selector used"""
    for selector in selectors:
        try:
            element = await page.wait_for_selector(selector, timeout=timeout)
            if element:
                logger.debug(f"Found element with selector: {selector}")
                return element, selector
        except PWTimeout:
            continue
        except Exception as e:
            logger.debug(f"Error with selector {selector}: {e}")
            continue
    return None, None


async def click_element_safely(
    page: Page, element: ElementHandle, description: str = "element"
) -> bool:
    """Safely click an element with proper error handling"""
    try:
        # Ensure element is visible and clickable
        await element.wait_for_element_state("visible", timeout=5000)
        await element.scroll_into_view_if_needed()

        await element.click()
        logger.debug(f"Successfully clicked {description}")
        return True
    except Exception as e:
        logger.error(f"Failed to click {description}: {e}")
        return False


async def fill_input_safely(
    page: Page, element: ElementHandle, value: str, description: str = "input"
) -> bool:
    """Safely fill an input element with proper error handling"""
    try:
        await element.wait_for_element_state("visible", timeout=5000)
        await element.scroll_into_view_if_needed()

        # Clear existing content and fill
        await element.fill("")
        await element.type(value, delay=100)  # Type with delay for human-like behavior
        logger.debug(f"Successfully filled {description} with: {value[:20]}...")
        return True
    except Exception as e:
        logger.error(f"Failed to fill {description}: {e}")
        return False


async def sleep_random(min_seconds: float = 1, max_seconds: float = 3) -> None:
    """Sleep for a random amount of time between min_seconds and max_seconds"""
    await asyncio.sleep(random.uniform(min_seconds, max_seconds))


async def get_page_title(page: Page) -> str:
    """Get current page title with error handling"""
    try:
        return await page.title()
    except Exception as e:
        logger.error(f"Failed to get page title: {e}")
        return "Error getting title"


# =======Pinterest actions=======


@retry_on_failure(max_attempts=2, delay=1)
async def navigate_to_pinterest(page: Page) -> bool:
    """Navigate to Pinterest with retry mechanism"""
    try:
        logger.info("Navigating to Pinterest...")
        await page.goto(
            "https://www.pinterest.com",
            wait_until="domcontentloaded",
            timeout=NAVIGATION_TIMEOUT,
        )

        # Wait for page to be ready with CPU throttling
        await asyncio.sleep(SLEEP_TIME_LONG)
        
        # Add small delays to prevent CPU spikes
        await asyncio.sleep(0.5)

        # Verify we're on Pinterest
        title = await page.title()
        if "Pinterest" not in title:
            logger.warning(f"Unexpected page title: {title}")
            return False

        logger.info("Successfully navigated to Pinterest")
        return True
    except Exception as e:
        logger.error(f"Failed to navigate to Pinterest: {e}")
        return False


async def test_login_status_on_pinterest(page: Page) -> bool:
    """Test if logged in with improved detection"""
    logger.info("Testing login status on Pinterest...")
    try:
        # Wait for page to be fully loaded
        await asyncio.sleep(SLEEP_TIME_LONG)

        # Check if we're logged in by looking for multiple indicators
        login_indicators = [
            '[data-test-id="header-profile"]',
            '[data-test-id="profile-menu"]',
            'a[href*="/profile/"]',
            'a[href*="/settings/"]',
            '[aria-label*="profile" i]',
            '[aria-label*="account" i]',
            'button[aria-label*="profile" i]',
            'button[aria-label*="account" i]',
            '[data-test-id="user-menu"]',
            'div[data-test-id="header-profile"]',
        ]

        # Check for login page indicators (if we see these, we're NOT logged in)
        logout_indicators = [
            'input[name="id"]',
            'input[name="email"]',
            'input[type="email"]',
            'button:has-text("Log in")',
            'button:has-text("Sign in")',
            '[data-test-id="login-button"]',
            'form[action*="login"]',
        ]

        # Check for logout indicators
        logout_element, logout_selector = await wait_for_element(
            page, logout_indicators, timeout=3000
        )
        if logout_element:
            logger.info(f"Found logout indicator: {logout_selector}")
            logger.warning("Connected to Pinterest but not logged in")
            return False

        # Check for login indicators first
        login_element, login_selector = await wait_for_element(
            page, login_indicators, timeout=5000
        )
        if login_element:
            logger.info(f"Found login indicator: {login_selector}")
            logger.info("Successfully connected and logged in to Pinterest")
            return True

        # If we can't determine login status, take a screenshot and assume not logged in
        logger.warning("Connected to Pinterest but login status unclear")
        await page.screenshot(path="login_status_unclear.png")
        return False

    except Exception as e:
        logger.error(f"Failed to test login status: {e}")
        return False


@retry_on_failure(max_attempts=2, delay=2)
async def login_to_pinterest(page: Page, account: PinterestAccount) -> bool:
    """Attempt to login to Pinterest with improved error handling"""
    try:
        logger.info("Attempting to login to Pinterest")

        # Navigate to login page
        await page.goto(
            "https://www.pinterest.com/login/",
            wait_until="domcontentloaded",
            timeout=NAVIGATION_TIMEOUT,
        )
        await asyncio.sleep(SLEEP_TIME_LONG)

        # Wait for login form to load
        email_selectors = [
            'input[name="id"]',
            'input[name="email"]',
            'input[type="email"]',
            '[data-test-id="email-field"] input',
            'input[placeholder*="email" i]',
            'input[placeholder*="Email" i]',
            'input[autocomplete="email"]',
        ]

        email_field, email_selector = await wait_for_element(
            page, email_selectors, timeout=LONG_TIMEOUT
        )
        if not email_field:
            logger.error("Could not find email field on login page")
            await page.screenshot(path="login_email_field_debug.png")
            return False

        # Fill email
        if not await fill_input_safely(page, email_field, account.email, "email field"):
            return False

        await asyncio.sleep(SLEEP_TIME_SHORT)

        # Find and fill password field
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            '[data-test-id="password-field"] input',
            'input[placeholder*="password" i]',
            'input[placeholder*="Password" i]',
            'input[autocomplete="current-password"]',
        ]

        password_field, password_selector = await wait_for_element(
            page, password_selectors, timeout=DEFAULT_TIMEOUT
        )
        if not password_field:
            logger.error("Could not find password field on login page")
            return False

        # Fill password
        if not await fill_input_safely(
            page, password_field, account.password, "password field"
        ):
            return False

        await asyncio.sleep(SLEEP_TIME_SHORT)

        # Find and click login button
        login_button_selectors = [
            'button[type="submit"]',
            'button:has-text("Log in")',
            'button:has-text("Sign in")',
            '[data-test-id="login-button"]',
            'button[data-test-id="login-button"]',
            'input[type="submit"]',
        ]

        login_button, login_selector = await wait_for_element(
            page, login_button_selectors, timeout=DEFAULT_TIMEOUT
        )
        if not login_button:
            logger.error("Could not find login button on login page")
            return False

        # Click login button
        if not await click_element_safely(page, login_button, "login button"):
            return False

        # Wait for login to complete (either success or error)
        try:
            # Wait for either dashboard (success) or error message
            success_indicators = [
                '[data-test-id="header-profile"]',
                '[data-test-id="profile-menu"]',
                'a[href*="/profile/"]',
            ]

            error_indicators = [
                '[data-test-id="error-message"]',
                ".error-message",
                '[role="alert"]',
            ]

            # Wait for either success or error
            success_element, _ = await wait_for_element(
                page, success_indicators, timeout=30000
            )
            if success_element:
                logger.info("Login successful!")
                return True

            error_element, _ = await wait_for_element(
                page, error_indicators, timeout=5000
            )
            if error_element:
                error_text = await error_element.text_content()
                logger.error(f"Login failed with error: {error_text}")
                return False

        except Exception as e:
            logger.error(f"Login timeout or error: {e}")
            return False

        logger.error("Login failed - could not determine success or failure")
        return False

    except Exception as e:
        logger.error(f"Login process failed: {e}")
        return False


async def get_cookies(page: Page) -> List[Dict[str, Any]]:
    """Get cookies from page"""
    try:
        return await page.cookies()
    except Exception as e:
        logger.error(f"Failed to get cookies: {e}")
        return []


async def check_and_skip_popups(page: Page) -> bool:
    """Skip any popups that appear with improved detection"""
    try:
        # Wait a moment for popups to appear
        await asyncio.sleep(SLEEP_TIME_SHORT)

        # Look for popup close buttons
        popup_selectors = [
            'button:has-text("Skip")',
            'button:has-text("Skip all")',
            'button:has-text("Skip for now")',
            'button:has-text("Not now")',
            'button:has-text("Maybe later")',
            'button[aria-label*="Skip" i]',
            'button[aria-label*="Close" i]',
            '[data-test-id="close-button"]',
            'button[aria-label="Close"]',
            'svg[aria-label="Close"]',
            ".close-button",
            ".popup-close",
        ]

        for selector in popup_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    logger.info(f"Found popup close button: {selector}")
                    await click_element_safely(
                        page, element, f"popup close button ({selector})"
                    )
                    await asyncio.sleep(SLEEP_TIME_SHORT)
                    return True
            except Exception as e:
                logger.debug(f"Error with popup selector {selector}: {e}")
                continue

        logger.debug("No popups detected")
        return True

    except Exception as e:
        logger.error(f"Failed to check for popups: {e}")
        return True  # Don't fail the whole process for popup issues


@retry_on_failure(max_attempts=2, delay=1)
async def navigate_to_create_board(page: Page, account: PinterestAccount) -> bool:
    """Navigate to the create board page with improved navigation"""
    try:
        logger.info("Navigating to boards page...")

        accountpage = account.username.replace(" ", "").lower()
        # Try multiple approaches to get to boards page
        navigation_methods = [
            # Method 1 : Direct URL navigation to user profile
            lambda: page.goto(
                f"https://www.pinterest.com/{accountpage}/",
                wait_until="domcontentloaded",
                timeout=NAVIGATION_TIMEOUT,
            ),
            # Method 2: Click boards link
            lambda: _click_boards_link(page),
        ]

        for i, method in enumerate(navigation_methods):
            try:
                await method()
                await asyncio.sleep(SLEEP_TIME_LONG)

                # Check if we're on a boards page
                url = page.url
                title = await page.title()

                if accountpage in url.lower() or accountpage in title.lower():
                    logger.info(
                        f"Successfully navigated to boards page using method {i+1}"
                    )
                    return True

            except Exception as e:
                logger.debug(f"Navigation method {i+1} failed: {e}")
                continue

        logger.error("All navigation methods failed")
        await page.screenshot(path="boards_navigation_debug.png")
        return False

    except Exception as e:
        logger.error(f"Failed to navigate to boards page: {e}")
        return False


async def _click_boards_link(page: Page) -> None:
    """Helper function to click boards link"""
    board_selectors = [
        'a[aria-label="Your boards"]',
        'a:has-text("Your boards")',
        '[data-test-id="sidebar-boards-link"]',
        'a[href*="/boards/"]',
        'a[href*="/profile/"]',
        'a[href*="/pins/"]',
    ]

    board_element, _ = await wait_for_element(page, board_selectors, timeout=5000)
    if board_element:
        await click_element_safely(page, board_element, "boards link")
        await page.wait_for_load_state("domcontentloaded", timeout=10000)
    else:
        raise Exception("Could not find boards link")


@retry_on_failure(max_attempts=2, delay=1)
async def create_board(page: Page, board_name: str, is_secret: bool = False) -> bool:
    """
    Create a new board on Pinterest with improved error handling
    Known issues:
        - If a board with the same name is already created, the create board step will fail
        - Adding numbers to the end of a board name will break pinterest recommendations for that board
    """
    try:
        logger.info(f"Creating board: {board_name}")

        # First, look for the plus button (create button)
        plus_button_selectors = [
            'div[class*="SPw"] svg path[d="M11 13v10h2V13h10v-2H13V1h-2v10H1v2z"]',
            'svg[class*="gUZ"] path[d="M11 13v10h2V13h10v-2H13V1h-2v10H1v2z"]',
            'div[style*="height: 48px; width: 48px;"] svg path[d="M11 13v10h2V13h10v-2H13V1h-2v10H1v2z"]',
        ]

        plus_button, _ = await wait_for_element(
            page, plus_button_selectors, timeout=LONG_TIMEOUT
        )
        if not plus_button:
            logger.error("Could not find plus/create button")
            await page.screenshot(path="plus_button_debug.png")
            return False

        logger.info("Found plus button, clicking to open dropdown...")

        # Click the plus button to open the dropdown
        if not await click_element_safely(page, plus_button, "plus button"):
            return False

        await asyncio.sleep(SLEEP_TIME_LONG)  # Wait for dropdown to appear

        # Now look for the "Board" option in the dropdown - using actual Pinterest DOM
        board_option_selectors = [
            'button[data-test-id="Create board"]',
            'button[id="board_actions-item-1"]',
            'div[data-test-id="create-board-button"]',
        ]

        board_option, _ = await wait_for_element(
            page, board_option_selectors, timeout=DEFAULT_TIMEOUT
        )
        if not board_option:
            logger.error("Could not find 'Board' option in dropdown")
            await page.screenshot(path="board_option_debug.png")
            return False

        logger.info("Found Board option, clicking to create board...")

        # Click the Board option
        if not await click_element_safely(page, board_option, "Board option"):
            return False

        await page.wait_for_load_state("domcontentloaded", timeout=10000)
        await asyncio.sleep(SLEEP_TIME_LONG)

        # Enhanced debugging before looking for inputs
        logger.info("=== DEBUGGING BOARD FORM ===")
        try:
            current_url = page.url
            logger.info(f"Current URL: {current_url}")
            
            # Take a screenshot for visual debugging
            await page.screenshot(path="/app/debug_screenshots/board_form_debug.png")
            logger.info("Screenshot saved: /app/debug_screenshots/board_form_debug.png")
            
            # Check page title
            title = await page.title()
            logger.info(f"Page title: {title}")
            
            # Check if we're in a modal
            modal = await page.query_selector('[role="dialog"], [class*="modal"], [class*="popup"]')
            if modal:
                logger.info("Found modal container")
            else:
                logger.info("No modal found")
                
        except Exception as e:
            logger.error(f"Debugging error: {e}")

        logger.info("Filling board name...")
        # Now fill in the board name - using actual Pinterest DOM selectors
        name_input_selectors = [
            'input[id="boardEditName"]',
            'input[name="boardName"]',
            'input[placeholder*="Places" i]',
            'input[placeholder*="Like" i]',
            '[data-test-id="board-name-input"]',
            'input[class*="_Jl"]',
            'input[type="text"][name="boardName"]',
        ]

        # Try multiple strategies to find the input
        name_input = None
        used_strategy = None
        
        # Strategy 1: Wait for specific input
        logger.info("Strategy 1: Looking for board name input...")
        name_input, _ = await wait_for_element(
            page, name_input_selectors, timeout=DEFAULT_TIMEOUT
        )
        if name_input:
            used_strategy = "direct_selector"
        
        # Strategy 2: Wait for any text input and check if it's the right one
        if not name_input:
            logger.info("Strategy 2: Looking for any text input...")
            try:
                await asyncio.sleep(2)  # Wait a bit more
                all_text_inputs = await page.query_selector_all('input[type="text"]')
                logger.info(f"Found {len(all_text_inputs)} text inputs")
                
                for i, inp in enumerate(all_text_inputs):
                    try:
                        placeholder = await inp.get_attribute('placeholder')
                        name_attr = await inp.get_attribute('name')
                        id_attr = await inp.get_attribute('id')
                        
                        logger.info(f"Text input {i}: placeholder='{placeholder}', name='{name_attr}', id='{id_attr}'")
                        
                        # Check if this looks like a board name input
                        if (placeholder and ("board" in placeholder.lower() or "name" in placeholder.lower() or "like" in placeholder.lower())) or \
                           (name_attr and "board" in name_attr.lower()) or \
                           (id_attr and "board" in id_attr.lower()):
                            logger.info(f"Found likely board input: {placeholder} | {name_attr} | {id_attr}")
                            name_input = inp
                            used_strategy = "text_input_search"
                            break
                    except Exception as e:
                        logger.warning(f"Error checking input {i}: {e}")
                        
            except Exception as e:
                logger.error(f"Strategy 2 failed: {e}")
        
        # Strategy 3: Wait longer and try again
        if not name_input:
            logger.info("Strategy 3: Waiting longer and retrying...")
            await asyncio.sleep(5)  # Wait 5 more seconds
            name_input, _ = await wait_for_element(
                page, name_input_selectors, timeout=DEFAULT_TIMEOUT
            )
            if name_input:
                used_strategy = "longer_wait"
        
        if not name_input:
            logger.error("Could not find board name input")
            await page.screenshot(path="/app/debug_screenshots/board_name_input_debug.png")
            
            # Enhanced debugging - check what inputs are actually available
            try:
                all_inputs = await page.query_selector_all('input')
                logger.error(f"Found {len(all_inputs)} input elements on page")
                for i, inp in enumerate(all_inputs[:5]):  # Log first 5 inputs
                    try:
                        input_id = await inp.get_attribute('id')
                        input_name = await inp.get_attribute('name')
                        input_placeholder = await inp.get_attribute('placeholder')
                        input_type = await inp.get_attribute('type')
                        logger.error(f"Input {i}: id='{input_id}', name='{input_name}', placeholder='{input_placeholder}', type='{input_type}'")
                    except Exception as e:
                        logger.error(f"Input {i}: <error reading attributes: {e}>")
            except Exception as e:
                logger.error(f"Could not inspect input elements: {e}")
            
            return False

        logger.info(f"Found name input using strategy: {used_strategy}, filling with: {board_name}")

        # Fill board name
        if not await fill_input_safely(
            page, name_input, board_name, "board name input"
        ):
            return False

        await asyncio.sleep(SLEEP_TIME_SHORT)

        logger.info("Setting board privacy...")
        # Set board privacy if needed - based on the "Keep this board secret" checkbox in the image
        if is_secret:
            secret_selectors = [
                'input[type="checkbox"][name="secret"]',
                'input[type="checkbox"][aria-label*="secret" i]',
                '[data-test-id="secret-board-toggle"]',
            ]

            secret_toggle, _ = await wait_for_element(
                page, secret_selectors, timeout=5000
            )
            if secret_toggle:
                await secret_toggle.check()
                logger.info("Set board to secret")
            else:
                logger.warning("Could not find secret board checkbox")

        # Click create button - based on the gray "Create" button in the modal
        create_button_selectors = [
            'button:has-text("Create")',
            'button[type="submit"]:has-text("Create")',
            '[data-test-id="create-board-submit"]',
            'button[aria-label*="Create" i]',
            'button:has-text("Save")',
            'button:has-text("Done")',
        ]

        create_button, _ = await wait_for_element(
            page, create_button_selectors, timeout=DEFAULT_TIMEOUT
        )
        if not create_button:
            logger.error("Could not find Create button")
            await page.screenshot(path="create_button_debug.png")
            return False

        logger.info("Found Create button, clicking to create board...")

        # Click create and wait for completion
        if not await click_element_safely(page, create_button, "Create button"):
            return False

        await page.wait_for_load_state("domcontentloaded", timeout=10000)
        await asyncio.sleep(SLEEP_TIME_LONG)

        logger.info(f"Successfully created board: {board_name}")
        return True

    except Exception as e:
        logger.error(f"Failed to create board: {e}")
        return False


@retry_on_failure(max_attempts=2, delay=1)
async def save_pins_to_board(
    page: Page,
    prompt: str,
    acceptance_threshold: float = 0.7,
    max_pins: int = 7,
    max_scrolls: int = 4,
) -> bool:
    """Save pins to a board with improved error handling"""
    try:
        # Wait for the modal to load
        await asyncio.sleep(SLEEP_TIME_LONG)
        await check_and_skip_popups(page)

        # Constants for selectors
        DONE_BTN = 'button:has-text("Done")'

        await asyncio.sleep(SLEEP_TIME_LONG)

        # TODO: I'd like to implement pre-screening of the suggested pin board to populate some basic
        # pins in my recommended board. Will come back to this

        # TODO: add a check to see if the board is already created, if so, skip the create board step

        # Click the Done button
        try:
            logger.info("Clicking Done button...")
            done_button = page.locator(DONE_BTN)
            await done_button.wait_for(state="visible", timeout=5000)
            await done_button.click()
            logger.info("✅ Done button clicked")

            # Wait for modal to close
            await page.wait_for_load_state("domcontentloaded", timeout=10000)
            await asyncio.sleep(2)

        except Exception as e:
            logger.warning(f"Could not click Done button: {e}")
            # The modal might dismiss automatically, so we don't fail here
            pass

        logger.info("Successfully saved pins to board")
        return True

    except Exception as e:
        logger.error(f"Failed to save pins to board: {e}")
        return False


@retry_on_failure(max_attempts=2, delay=1)
async def navigate_to_more_ideas(page: Page) -> bool:
    """
    Find and click the 'More Ideas' button to navigate to more suggestions
    Known issues:
        - The 'More Ideas' button is not always present in non-deterministic ways (prompt is something weird),
        and if it is not, the function will fail
    """
    try:
        logger.info("Looking for 'More Ideas' button...")

        # Multiple selectors to find the "More Ideas" button
        more_ideas_selectors = [
            'button:has-text("More Ideas")',
            'a:has-text("More Ideas")',
            '[data-test-id="more-ideas-button"]',
            '[aria-label*="More Ideas" i]',
            'button[aria-label*="More Ideas" i]',
            'a[aria-label*="More Ideas" i]',
            'button:has-text("more ideas")',
            'a:has-text("more ideas")',
            'button:has-text("More ideas")',
            'a:has-text("More ideas")',
            # Pinterest specific selectors
            '[data-test-id="pinner-recommendations-more-ideas"]',
            'button[data-test-id*="more-ideas"]',
            'a[data-test-id*="more-ideas"]',
        ]

        # Wait for any of the selectors to appear
        more_ideas_button, used_selector = await wait_for_element(
            page, more_ideas_selectors, timeout=DEFAULT_TIMEOUT
        )

        if not more_ideas_button:
            logger.warning("Could not find 'More Ideas' button with any selector")
            # Take a screenshot for debugging
            await page.screenshot(path="more_ideas_button_debug.png")
            return False

        logger.info(f"Found 'More Ideas' button with selector: {used_selector}")

        # Click the button
        if not await click_element_safely(page, more_ideas_button, "More Ideas button"):
            return False

        # Wait for navigation to complete
        await page.wait_for_load_state("domcontentloaded", timeout=NAVIGATION_TIMEOUT)
        await asyncio.sleep(2)

        # Verify we're on a new page (URL should have changed)
        current_url = page.url
        logger.info(f"Successfully navigated to: {current_url}")

        return True

    except Exception as e:
        logger.error(f"Failed to navigate to more ideas: {e}")
        return False


# TODO: break function into smaller more testable functions
@retry_on_failure(max_attempts=2, delay=1)
async def extract_pin_images_from_more_ideas(page: Page) -> List[Dict[str, str]]:
    """
    Wait for the more ideas page to load and extract all pin image URLs and alt text
        Returns a list of dictionaries with the following keys:
            - image_url: the URL of the pin image
            - alt_text: the alt text of the pin image
            - title: the title of the pin image
            - pin_link: the link to the pin image
            - selector_used: the selector used to find the pin image

        Note: this differs from the bool returns of the rest of the actions
    """
    try:
        logger.info("Waiting for more ideas page to load...")

        # Wait for the page to fully load (simplified for Docker)
        await page.wait_for_load_state("domcontentloaded", timeout=NAVIGATION_TIMEOUT)
        await asyncio.sleep(5)  # Simple wait instead of networkidle, networkidle breaks in docker container

        # Take a screenshot for debugging
        try:
            await page.screenshot(path="/app/debug_screenshots/more_ideas_page.png")
            logger.info("Screenshot saved: /app/debug_screenshots/more_ideas_page.png")
        except Exception as e:
            logger.warning(f"Could not take screenshot: {e}")

        logger.info("Page loaded, extracting pin images...")
        
        # Debug: Check what's actually on the page
        try:
            current_url = page.url
            logger.info(f"Current URL: {current_url}")
            
            # Check page title
            title = await page.title()
            logger.info(f"Page title: {title}")
            
            # Count total images on page
            all_images = await page.query_selector_all("img")
            logger.info(f"Total images found on page: {len(all_images)}")
            
            # Log first few images for debugging
            for i, img in enumerate(all_images[:5]):
                try:
                    src = await img.get_attribute("src")
                    alt = await img.get_attribute("alt")
                    logger.info(f"Image {i}: src='{src[:50] if src else 'None'}...', alt='{alt[:50] if alt else 'None'}...'")
                except Exception as e:
                    logger.warning(f"Error reading image {i}: {e}")
            
            # Count total divs on page
            all_divs = await page.query_selector_all("div")
            logger.info(f"Total divs found on page: {len(all_divs)}")
            
        except Exception as e:
            logger.error(f"Error during page analysis: {e}")

        # First, try to find pin containers (the full pin components)
        pin_container_selectors = [
            'div[data-test-id="pin"]',
            "div[data-test-pin-id]",
            "div[data-grid-item-idx]",
            'div[class*="pin"]',
            'div[class*="Pin"]',
            'article[data-test-id="pin"]',
            'div[role="button"][tabindex="0"]',  # Pinterest often uses these for pin containers
        ]

        extracted_pins = []

        # Try to find pin containers first
        for container_selector in pin_container_selectors:
            try:
                logger.info(f"Trying container selector: {container_selector}")

                # Try to find containers without waiting (more robust)
                containers = await page.query_selector_all(container_selector)
                
                if not containers:
                    logger.info(f"No containers found with selector: {container_selector}")
                    continue

                if containers:
                    logger.info(
                        f"Found {len(containers)} pin containers with selector: {container_selector}"
                    )

                    for container in containers:
                        try:
                            # Extract pin metadata from container
                            pin_id = (
                                await container.get_attribute("data-test-pin-id") or ""
                            )

                            # Find the link element within the container
                            link_element = await container.query_selector(
                                "a[href*='/pin/']"
                            )
                            pin_link = ""
                            title_description = ""

                            if link_element:
                                pin_link = (
                                    await link_element.get_attribute("href") or ""
                                )
                                title_description = (
                                    await link_element.get_attribute("aria-label") or ""
                                )

                            # Find the image within the container
                            img_element = await container.query_selector(
                                "img[src*='pinimg.com']"
                            )
                            if not img_element:
                                # Fallback to any img in the container
                                img_element = await container.query_selector("img")

                            if img_element:
                                # Extract image data
                                src = await img_element.get_attribute("src")
                                alt_text = await img_element.get_attribute("alt") or ""
                                img_title = (
                                    await img_element.get_attribute("title") or ""
                                )

                                if src and src.startswith("http"):
                                    # Combine container metadata with image data
                                    pin_data = {
                                        "image_url": src,
                                        "alt_text": alt_text,
                                        "title": title_description
                                        or img_title,  # Prefer container description
                                        "pin_link": pin_link,
                                        "pin_id": pin_id,
                                        "selector_used": container_selector,
                                    }

                                    # Avoid duplicates based on image URL
                                    if not any(
                                        pin["image_url"] == src
                                        for pin in extracted_pins
                                    ):
                                        extracted_pins.append(pin_data)
                                        logger.debug(
                                            f"Extracted pin: {src[:50]}... (ID: {pin_id})"
                                        )

                        except Exception as e:
                            logger.debug(f"Error processing individual container: {e}")
                            continue

                    # If we found pins with this container selector, break to avoid duplicates
                    if extracted_pins:
                        break

            except Exception as e:
                logger.debug(f"Container selector {container_selector} failed: {e}")
                continue

        # Fallback: If no containers found, try the old image-only approach
        if not extracted_pins:
            logger.info(
                "No pin containers found, falling back to image-only extraction..."
            )

            # Multiple selectors to find pin images on Pinterest
            pin_image_selectors = [
                'img[src*="pinimg.com"]',  # Pinterest's image CDN
                'img[data-test-id*="pin"]',
                'img[alt*="Pin"]',
                'img[src*="i.pinimg.com"]',
                'img[data-test-id="pin-image"]',
                'img[data-test-id="pin-img"]',
                'img[class*="pin"]',
                'img[class*="Pin"]',
                # More specific Pinterest selectors
                'img[data-test-id="pin-image"]',
                'img[data-test-id="pin-img"]',
                'img[data-test-id="pin-image-img"]',
                # Fallback to any image that might be a pin
                'img[src*="pin"]',
                'img[alt*="pin"]',
            ]

            # Try each selector to find pin images
            for selector in pin_image_selectors:
                try:
                    logger.info(f"Trying image selector: {selector}")

                    # Try to find images without waiting (more robust)
                    images = await page.query_selector_all(selector)
                    
                    if not images:
                        logger.info(f"No images found with selector: {selector}")
                        continue

                    if images:
                        logger.info(
                            f"Found {len(images)} images with selector: {selector}"
                        )

                        for img in images:
                            try:
                                # Extract image URL
                                src = await img.get_attribute("src")
                                if not src:
                                    continue

                                # Extract alt text
                                alt = await img.get_attribute("alt") or ""

                                # Extract title if available
                                title = await img.get_attribute("title") or ""

                                # Get the parent element to find pin link if available
                                parent = await img.query_selector("xpath=..")
                                pin_link = ""
                                if parent:
                                    link_element = await parent.query_selector(
                                        "a[href*='/pin/']"
                                    )
                                    if link_element:
                                        pin_link = (
                                            await link_element.get_attribute("href")
                                            or ""
                                        )

                                # Only include if we have a valid image URL
                                if src and src.startswith("http"):
                                    pin_data = {
                                        "image_url": src,
                                        "alt_text": alt,
                                        "title": title,
                                        "pin_link": pin_link,
                                        "pin_id": "",
                                        "selector_used": selector,
                                    }

                                    # Avoid duplicates based on image URL
                                    if not any(
                                        pin["image_url"] == src
                                        for pin in extracted_pins
                                    ):
                                        extracted_pins.append(pin_data)
                                        logger.debug(f"Extracted pin: {src[:50]}...")

                            except Exception as e:
                                logger.debug(f"Error processing individual image: {e}")
                                continue

                        # If we found images with this selector, break to avoid duplicates
                        if extracted_pins:
                            break

                except Exception as e:
                    logger.debug(f"Image selector {selector} failed: {e}")
                    continue

            # If still no images found, try a broader approach
            if not extracted_pins:
                logger.info(
                    "No images found with specific selectors, trying broader approach..."
                )

                # Get all images on the page
                all_images = await page.query_selector_all("img")
                logger.info(f"Trying broader approach with {len(all_images)} total images")

                for img in all_images:
                    try:
                        src = await img.get_attribute("src")
                        alt = await img.get_attribute("alt") or ""

                        # Filter for likely Pinterest images
                        if (
                            src
                            and src.startswith("http")
                            and (
                                "pinimg.com" in src
                                or "pin" in src.lower()
                                or "pin" in alt.lower()
                            )
                        ):

                            pin_data = {
                                "image_url": src,
                                "alt_text": alt,
                                "title": await img.get_attribute("title") or "",
                                "pin_link": "",
                                "selector_used": "broad_search",
                            }

                            if not any(pin["image_url"] == src for pin in extracted_pins):
                                extracted_pins.append(pin_data)

                    except Exception as e:
                        logger.debug(f"Error processing image in broad search: {e}")
                        continue

        logger.info(f"Successfully extracted {len(extracted_pins)} unique pin images")

        return extracted_pins

    except Exception as e:
        logger.error(f"Failed to extract pin images: {e}")
        return []
