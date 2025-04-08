"""
Tests for the High School Management System JavaScript functionality.
This file contains tests to validate the HTML generation of the participants list
and ensure that HTML content is escaped properly.
"""

import pytest
import time
import json
import os
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup
from app import app
import re

client = TestClient(app)

def test_html_escaping_in_static_file():
    """Test that the escapeHTML function exists in app.js and properly escapes HTML."""
    # Read the app.js file
    with open(os.path.join(os.path.dirname(__file__), 'static', 'app.js'), 'r') as f:
        js_content = f.read()
    
    # Check if escapeHTML function exists
    assert 'function escapeHTML' in js_content, "escapeHTML function not found in app.js"
    
    # Check if the function handles the common HTML entities
    common_entities = ["&", "<", ">", '"', "'"]
    escaped_entities = ["&amp;", "&lt;", "&gt;", "&quot;", "&#039;"]
    
    for entity, escaped in zip(common_entities, escaped_entities):
        assert f"{entity}" in js_content and f"{escaped}" in js_content, f"Escaping for {entity} not found in app.js"

def test_participants_list_structure():
    """Test that the HTML structure in index.html supports participants lists with proper classes."""
    # Read the index.html file
    with open(os.path.join(os.path.dirname(__file__), 'static', 'index.html'), 'r') as f:
        html_content = f.read()
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check for activities-list container where activity cards will be dynamically added
    activities_container = soup.select('#activities-list')
    assert len(activities_container) > 0, "No activities container found in index.html"
    
    # Check if app.js contains code to create elements with these classes
    with open(os.path.join(os.path.dirname(__file__), 'static', 'app.js'), 'r') as f:
        js_content = f.read()
    
    # Check for the creation of activity-card elements
    assert 'activity-card' in js_content, "No activity-card class creation found in app.js"
    
    # Check for the creation of participants-list elements
    assert 'participants-list' in js_content, "No participants-list class creation found in app.js"

def test_app_js_fetch_functionality():
    """Test that app.js contains code to fetch activities and participants."""
    # Read the app.js file
    with open(os.path.join(os.path.dirname(__file__), 'static', 'app.js'), 'r') as f:
        js_content = f.read()
    
    # Check for fetch API usage
    assert 'fetch(' in js_content, "No fetch API calls found in app.js"
    assert '/activities' in js_content, "No activities endpoint referenced in app.js"
    
    # Check for participant list generation logic
    assert 'participants' in js_content and 'forEach' in js_content, "Participants list generation code not found"

def test_html_escaping_integration():
    """Test integration between backend and frontend for HTML escaping."""
    # First, add a user with potentially dangerous HTML to an activity via the API
    malicious_email = "<script>alert('XSS')</script>@example.com"
    activity = "Math Club"
    
    # Add the malicious email to an activity
    response = client.post(f"/activities/{activity}/signup", params={"email": malicious_email})
    assert response.status_code == 200 or response.status_code == 400, f"Failed to add test user: {response.status_code}"
    
    # Get the activities to check if the email was stored
    activities = client.get("/activities").json()
    
    # Check that our test participant is in the activity (case-insensitive)
    participants = activities.get(activity, {}).get("participants", [])
    participants_lower = [p.lower() for p in participants]
    assert malicious_email.lower() in participants_lower, "Test participant not found in activities data"
    
    # Examine the raw JSON to ensure proper escaping is required
    activities_json = json.dumps(activities)
    assert "<script>" in activities_json or "<script>".lower() in activities_json, "Test script tag not found in JSON output"
    
    # Read the escapeHTML function from app.js
    with open(os.path.join(os.path.dirname(__file__), 'static', 'app.js'), 'r') as f:
        js_content = f.read()
    
    # Extract the escapeHTML function
    escape_html_match = re.search(r'function\s+escapeHTML\s*\(.*?\)\s*\{([^}]+)\}', js_content, re.DOTALL)
    assert escape_html_match, "Could not extract escapeHTML function"
    
    # Check if the function handles script tags
    escape_html_body = escape_html_match.group(1)
    assert "&lt;" in escape_html_body and "&gt;" in escape_html_body, "escapeHTML doesn't handle < and > characters"

def test_empty_participants_handling():
    """Test that app.js handles empty participants lists correctly."""
    # Read the app.js file
    with open(os.path.join(os.path.dirname(__file__), 'static', 'app.js'), 'r') as f:
        js_content = f.read()
    
    # Check for empty participants list handling
    no_participants_patterns = [
        "No participants", 
        "participants.length === 0", 
        "participants.length == 0",
        "!participants.length"
    ]
    
    has_empty_check = any(pattern in js_content for pattern in no_participants_patterns)
    assert has_empty_check, "No handling for empty participants list found in app.js"