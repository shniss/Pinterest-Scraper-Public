"""
Browser Factory for Playwright Automation

This module provides a factory class for creating and managing Playwright browser instances
used in Pinterest automation. It handles browser lifecycle, context creation, proxy configuration,
and resource cleanup.

Features:
- Anti-detection browser configuration
- Proxy support with validation
- User agent customization
- Comprehensive resource cleanup
- Error handling and logging

TODO:
    - Finish cookie management
"""

from __future__ import annotations
import logging
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from typing import Optional

logger = logging.getLogger(__name__)

# Configuration constants
BROWSER_CONFIG = {
    "viewport": {"width": 1920, "height": 1080},
    "timeout": 30000,
    "headless": True,
    "args": [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--no-first-run",
        "--no-zygote",
        "--disable-blink-features=AutomationControlled",
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor",
        "--force-color-profile=srgb",
        "--no-default-browser-check",
        "--password-store=basic",
        "--use-mock-keychain",
    ],
}

# Default HTTP headers for browser context - more realistic for Pinterest
DEFAULT_HEADERS = {
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


class BrowserFactory:
    """
    Factory class for creating and managing Playwright browser instances.

    This class handles the complete browser lifecycle including:
    - Browser startup with anti-detection configuration
    - Context creation with proxy and user agent support
    - Page management and cookie handling
    - Resource cleanup and error recovery

    The factory is designed to work with Pinterest automation and includes
    measures to avoid bot detection.
    """

    def __init__(self):
        """
        Initialize the browser factory with empty resource references.

        All browser resources start as None and are created as needed.
        This allows for proper resource management and cleanup.
        """
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def start(self, headless: bool = True) -> bool:
        """
        Start the Playwright browser with anti-detection configuration.

        Args:
            headless: Whether to run browser in headless mode (default: True)

        Returns:
            bool: True if browser started successfully, False otherwise

        The browser is configured with anti-detection measures to avoid
        being identified as an automated browser.
        """
        try:
            logger.info("Starting Playwright browser")
            self.playwright = await async_playwright().start()

            # Launch browser with anti-detection configuration and CPU throttling
            browser_args = BROWSER_CONFIG["args"] + [
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows", 
                "--disable-renderer-backgrounding",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
                "--disable-hang-monitor",
                "--disable-prompt-on-repost",
                "--disable-domain-reliability",
                "--disable-component-extensions-with-background-pages",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--force-color-profile=srgb",
                "--no-default-browser-check",
                "--password-store=basic",
                "--use-mock-keychain",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
            ]
            
            self.browser = await self.playwright.chromium.launch(
                headless=headless, 
                args=browser_args,
                timeout=60000  # 60 second timeout for Docker
            )

            logger.info("Playwright browser started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            return False

    async def stop(self):
        """
        Stop the Playwright browser and clean up all resources.

        This method ensures proper cleanup of all browser resources in the correct order:
        1. Page (if exists)
        2. Context (if exists)
        3. Browser (if exists)
        4. Playwright instance (if exists)

        Each cleanup step is handled independently to ensure maximum resource cleanup
        even if individual steps fail.
        """
        # Define cleanup order (page -> context -> browser -> playwright)
        cleanup_order = [
            ("page", self.page),
            ("context", self.context),
            ("browser", self.browser),
            ("playwright", self.playwright),
        ]

        for resource_name, resource in cleanup_order:
            if resource:
                try:
                    if resource_name == "page":
                        await resource.close()
                    elif resource_name == "context":
                        await resource.close()
                    elif resource_name == "browser":
                        await resource.close()
                    elif resource_name == "playwright":
                        await resource.stop()

                    # Clear the reference
                    setattr(self, resource_name, None)
                    logger.debug(f"Cleaned up {resource_name}")

                except Exception as e:
                    logger.error(f"Error cleaning up {resource_name}: {e}")

        logger.info("Playwright browser cleanup completed")

    def _validate_proxy_config(self, proxy_config: dict) -> bool:
        """
        Validate proxy configuration structure.

        Args:
            proxy_config: Proxy configuration dictionary

        Returns:
            bool: True if proxy config is valid, False otherwise
        """
        if not isinstance(proxy_config, dict):
            logger.error("Invalid proxy_config: must be a dictionary")
            return False

        required_keys = ["server", "username", "password"]
        missing_keys = [key for key in required_keys if key not in proxy_config]

        if missing_keys:
            logger.error(f"Invalid proxy_config: missing required keys: {missing_keys}")
            return False

        return True

    async def create_context(
        self, proxy_config: Optional[dict] = None, user_agent: Optional[str] = None
    ) -> bool:
        """
        Create a browser context with optional proxy configuration and user agent.

        Args:
            proxy_config: Optional proxy configuration dictionary with server, username, password
            user_agent: Optional custom user agent string

        Returns:
            bool: True if context created successfully, False otherwise

        The context is configured with anti-detection measures and proper headers
        for web scraping operations.
        """
        # Validate browser is available
        if not self.browser:
            logger.error("No browser available for context creation")
            return False

        # Validate proxy configuration if provided
        if proxy_config and not self._validate_proxy_config(proxy_config):
            return False

        try:
            logger.info("Creating browser context")

            # Prepare context options with default configuration
            context_options = {
                "viewport": BROWSER_CONFIG["viewport"],
                "ignore_https_errors": True,
                "extra_http_headers": DEFAULT_HEADERS,
            }

            # Add user agent if provided
            if user_agent:
                if not isinstance(user_agent, str):
                    logger.error("Invalid user_agent: must be a string")
                    return False
                context_options["user_agent"] = user_agent
                logger.info(f"Using custom user agent: {user_agent[:50]}...")

            # Add proxy configuration if provided
            if proxy_config:
                context_options["proxy"] = proxy_config
                logger.info(
                    f"Added proxy configuration: {proxy_config.get('server', 'unknown')}"
                )

            # Create browser context
            self.context = await self.browser.new_context(**context_options)

            # Create a new page in the context
            self.page = await self.context.new_page()

            # Set page headers (same as context headers for consistency)
            await self.page.set_extra_http_headers(DEFAULT_HEADERS)

            logger.info("Browser context created successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to create context: {e}")
            return False

    async def add_cookies(self, cookies: list) -> bool:
        """
        Add cookies to the browser context for session persistence.

        Args:
            cookies: List of cookie dictionaries with name, value, domain, path, etc.

        Returns:
            bool: True if cookies added successfully, False otherwise

        This method is used to restore previous session cookies to maintain
        login state across browser sessions.
        """
        # Validate context is available
        if not self.context:
            logger.error("No context available for adding cookies")
            return False

        # Validate cookies parameter
        if not isinstance(cookies, list):
            logger.error("Invalid cookies parameter: must be a list")
            return False

        if not cookies:
            logger.warning("Empty cookies list provided")
            return True  # Not an error, just no cookies to add

        try:
            logger.info(f"Adding {len(cookies)} cookies to context")
            await self.context.add_cookies(cookies)
            logger.info("Cookies added successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to add cookies: {e}")
            return False
