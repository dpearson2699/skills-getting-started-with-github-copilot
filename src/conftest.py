"""
Pytest configuration file for the High School Management System tests.
This file contains fixtures for setting up the live server for JavaScript tests.
"""

import os
import pytest
import threading
import time
import uvicorn
import socket
from contextlib import closing
from app import app
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options as FirefoxOptions

def find_free_port():
    """Find a free port to run the test server."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

class LiveServer:
    def __init__(self, app, port):
        self.app = app
        self.port = port
        self.url = f"http://localhost:{port}"
        self.server_thread = None
        self.ready = threading.Event()

    def start(self):
        """Start the live server in a separate thread."""
        self.server_thread = threading.Thread(
            target=self._run_server,
            daemon=True
        )
        self.server_thread.start()
        
        # Wait for server to start
        retry = 0
        while retry < 5:
            try:
                with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
                    s.connect(('localhost', self.port))
                    self.ready.set()
                    return
            except socket.error:
                time.sleep(0.1)
                retry += 1
    
    def stop(self):
        """Signal the server to stop."""
        # The server will stop when the thread is killed
        pass
        
    def _run_server(self):
        """Run the server using Uvicorn."""
        uvicorn.run(app, host="0.0.0.0", port=self.port, log_level="error")

@pytest.fixture(scope="function")
def live_server():
    """Provide a live server for testing with Selenium."""
    port = find_free_port()
    server = LiveServer(app, port)
    server.start()
    
    # Wait for the server to be ready
    if not server.ready.wait(timeout=5):
        raise Exception("Server failed to start within timeout")
    
    try:
        yield server
    finally:
        server.stop()

@pytest.fixture
def selenium(request):
    """
    Create and configure a Selenium WebDriver instance using Firefox.
    This fixture is specifically configured for GitHub Codespaces environment.
    """
    # Configure Firefox options for headless environment
    options = FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")
    
    driver = None
    try:
        # Try to install and setup GeckoDriver
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        
        # Set an implicit wait to handle potential timing issues
        driver.implicitly_wait(10)
        
        yield driver
        
    except Exception as e:
        # If Firefox fails, try using a web testing library that doesn't require a browser
        pytest.skip(f"Skipping test because Firefox WebDriver couldn't be initialized: {str(e)}")
    
    finally:
        # Quit the driver after the test is complete (if it was created)
        if driver:
            driver.quit()