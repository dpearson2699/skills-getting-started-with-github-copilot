"""
Tests for the High School Management System API.
This file contains tests to verify that the duplicate sign-up validation works 
correctly, including checks with different email casing.
"""

from fastapi.testclient import TestClient
import pytest
from app import app

client = TestClient(app)

def test_signup_with_new_email():
    """Test that a new user can sign up for an activity successfully."""
    # This is a new email that doesn't exist in any activity
    email = "newuser@mergington.edu"
    activity = "Chess Club"
    
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    
    # Verify the user was actually added
    activities_response = client.get("/activities")
    assert email in activities_response.json()[activity]["participants"]

def test_duplicate_signup_same_casing():
    """Test that a user cannot sign up with the exact same email twice."""
    # Use an email that already exists in the activity
    email = "michael@mergington.edu"
    activity = "Chess Club"
    
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email}
    )
    
    # Should return a 400 error for duplicate signup
    assert response.status_code == 400
    assert "Already signed up for this activity" in response.json()["detail"]

def test_duplicate_signup_different_casing():
    """Test that a user cannot sign up with the same email but different casing."""
    # First sign up with a lowercase email
    new_email = "casetest@mergington.edu"
    activity = "Art Club"
    
    # Ensure this user isn't already in the system (can remove this in a real test)
    activities_response = client.get("/activities")
    if new_email in [p.lower() for p in activities_response.json()[activity]["participants"]]:
        pytest.skip("Test email already exists in system, skipping")
    
    # First signup should succeed
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": new_email}
    )
    assert response.status_code == 200
    
    # Try to sign up again with the same email but uppercase
    uppercase_email = "CASETEST@MERGINGTON.EDU"
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": uppercase_email}
    )
    
    # Should return a 400 error for duplicate signup
    assert response.status_code == 400
    assert "Already signed up for this activity" in response.json()["detail"]

def test_mixed_case_signup_validation():
    """Test that a user cannot sign up with mixed case email variations."""
    # First sign up with a mixed-case email
    mixed_case_email = "MixedCase@Mergington.edu"
    activity = "Math Club"
    
    # Ensure this user isn't already in the system
    activities_response = client.get("/activities")
    if mixed_case_email.lower() in [p.lower() for p in activities_response.json()[activity]["participants"]]:
        pytest.skip("Test email already exists in system, skipping")
    
    # First signup should succeed
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": mixed_case_email}
    )
    assert response.status_code == 200
    
    # Try different casing variations
    variations = [
        "mixedcase@mergington.edu",  # all lowercase
        "MIXEDCASE@MERGINGTON.EDU",  # all uppercase
        "Mixedcase@mergington.edu",  # different mixed case
    ]
    
    for variant in variations:
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": variant}
        )
        
        # Should return a 400 error for duplicate signup
        assert response.status_code == 400, f"Failed with email variant: {variant}"
        assert "Already signed up for this activity" in response.json()["detail"]