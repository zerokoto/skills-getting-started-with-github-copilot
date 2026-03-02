"""
Tests for the Mergington High School Activities API

This module contains comprehensive tests for all API endpoints using the AAA
(Arrange-Act-Assert) testing pattern:
- Arrange: Set up test data and preconditions
- Act: Execute the code being tested
- Assert: Verify the results

Endpoints tested:
- GET /activities
- POST /activities/{activity_name}/signup
- DELETE /activities/{activity_name}/unregister
"""

import urllib.parse

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        k: {
            "description": v["description"],
            "schedule": v["schedule"],
            "max_participants": v["max_participants"],
            "participants": v["participants"].copy()
        }
        for k, v in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for activity_name, activity_data in original_activities.items():
        activities[activity_name] = activity_data


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client, reset_activities):
        """Test that GET /activities returns a 200 status code"""
        # Arrange
        endpoint = "/activities"
        
        # Act
        response = client.get(endpoint)
        
        # Assert
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client, reset_activities):
        """Test that GET /activities returns a dictionary"""
        # Arrange
        endpoint = "/activities"
        
        # Act
        response = client.get(endpoint)
        data = response.json()
        
        # Assert
        assert isinstance(data, dict)
    
    def test_get_activities_contains_expected_activities(self, client, reset_activities):
        """Test that response contains expected activity names"""
        # Arrange
        endpoint = "/activities"
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Art Studio",
            "Music Band",
            "Debate Club",
            "Science Club"
        ]
        
        # Act
        response = client.get(endpoint)
        data = response.json()
        
        # Assert
        for activity in expected_activities:
            assert activity in data
    
    def test_get_activities_has_correct_structure(self, client, reset_activities):
        """Test that each activity has the required fields"""
        # Arrange
        endpoint = "/activities"
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get(endpoint)
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Missing field '{field}' in {activity_name}"
            
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)
    
    def test_get_activities_participants_are_emails(self, client, reset_activities):
        """Test that all participants appear to be email addresses"""
        # Arrange
        endpoint = "/activities"
        
        # Act
        response = client.get(endpoint)
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant, f"Invalid email format: {participant}"


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        # Arrange
        activity = "Chess Club"
        email = "newstudent@mergington.edu"
        endpoint = f"/activities/{activity}/signup?email={email}"
        
        # Act
        response = client.post(endpoint)
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant to the activity"""
        # Arrange
        activity = "Chess Club"
        email = "newstudent@mergington.edu"
        endpoint = f"/activities/{activity}/signup?email={email}"
        
        activities_before = client.get("/activities").json()
        assert email not in activities_before[activity]["participants"]
        
        # Act
        response = client.post(endpoint)
        activities_after = client.get("/activities").json()
        
        # Assert
        assert response.status_code == 200
        assert email in activities_after[activity]["participants"]
    
    def test_signup_duplicate_email_returns_400(self, client, reset_activities):
        """Test that signing up with a duplicate email returns 400"""
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        endpoint = f"/activities/{activity}/signup?email={email}"
        
        # Act
        response = client.post(endpoint)
        data = response.json()
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that signing up for a non-existent activity returns 404"""
        # Arrange
        activity = "Nonexistent Activity"
        email = "student@mergington.edu"
        endpoint = f"/activities/{activity}/signup?email={email}"
        
        # Act
        response = client.post(endpoint)
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "not found" in data["detail"].lower()
    
    def test_signup_multiple_different_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple different activities"""
        # Arrange
        email = "student@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Programming Class"
        endpoint1 = f"/activities/{activity1}/signup?email={email}"
        endpoint2 = f"/activities/{activity2}/signup?email={email}"
        
        # Act
        response1 = client.post(endpoint1)
        response2 = client.post(endpoint2)
        activities_data = client.get("/activities").json()
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email in activities_data[activity1]["participants"]
        assert email in activities_data[activity2]["participants"]
    
    def test_signup_special_characters_in_email(self, client, reset_activities):
        """Test signup with properly URL-encoded special characters in email"""
        # Arrange
        activity = "Chess Club"
        email = "student+tag@mergington.edu"
        encoded_email = urllib.parse.quote(email)
        endpoint = f"/activities/{activity}/signup?email={encoded_email}"
        
        # Act
        response = client.post(endpoint)
        activities_data = client.get("/activities").json()
        
        # Assert
        assert response.status_code == 200
        assert email in activities_data[activity]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration from an activity"""
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        endpoint = f"/activities/{activity}/unregister?email={email}"
        
        # Act
        response = client.delete(endpoint)
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant"""
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"
        endpoint = f"/activities/{activity}/unregister?email={email}"
        
        activities_before = client.get("/activities").json()
        assert email in activities_before[activity]["participants"]
        
        # Act
        response = client.delete(endpoint)
        activities_after = client.get("/activities").json()
        
        # Assert
        assert response.status_code == 200
        assert email not in activities_after[activity]["participants"]
    
    def test_unregister_nonexistent_participant_returns_400(self, client, reset_activities):
        """Test that unregistering a non-existent participant returns 400"""
        # Arrange
        activity = "Chess Club"
        email = "nonexistent@mergington.edu"
        endpoint = f"/activities/{activity}/unregister?email={email}"
        
        # Act
        response = client.delete(endpoint)
        data = response.json()
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in data["detail"].lower()
    
    def test_unregister_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that unregistering from a non-existent activity returns 404"""
        # Arrange
        activity = "Nonexistent Activity"
        email = "student@mergington.edu"
        endpoint = f"/activities/{activity}/unregister?email={email}"
        
        # Act
        response = client.delete(endpoint)
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "not found" in data["detail"].lower()
    
    def test_unregister_allows_re_signup(self, client, reset_activities):
        """Test that a student can re-sign up after unregistering"""
        # Arrange
        activity = "Chess Club"
        email = "testuser@mergington.edu"
        signup_endpoint = f"/activities/{activity}/signup?email={email}"
        unregister_endpoint = f"/activities/{activity}/unregister?email={email}"
        
        # Act - Sign up
        response1 = client.post(signup_endpoint)
        
        # Act - Unregister
        response2 = client.delete(unregister_endpoint)
        
        # Act - Sign up again
        response3 = client.post(signup_endpoint)
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200


class TestIntegrationScenarios:
    """Integration tests covering multiple operations"""
    
    def test_signup_then_unregister_flow(self, client, reset_activities):
        """Test complete flow of signing up and then unregistering"""
        # Arrange
        email = "integration@mergington.edu"
        activity = "Programming Class"
        signup_endpoint = f"/activities/{activity}/signup?email={email}"
        unregister_endpoint = f"/activities/{activity}/unregister?email={email}"
        
        activities_data = client.get("/activities").json()
        initial_count = len(activities_data[activity]["participants"])
        assert email not in activities_data[activity]["participants"]
        
        # Act - Sign up
        signup_response = client.post(signup_endpoint)
        activities_data_after_signup = client.get("/activities").json()
        
        # Act - Unregister
        unregister_response = client.delete(unregister_endpoint)
        activities_data_after_unregister = client.get("/activities").json()
        
        # Assert
        assert signup_response.status_code == 200
        assert email in activities_data_after_signup[activity]["participants"]
        assert len(activities_data_after_signup[activity]["participants"]) == initial_count + 1
        
        assert unregister_response.status_code == 200
        assert email not in activities_data_after_unregister[activity]["participants"]
        assert len(activities_data_after_unregister[activity]["participants"]) == initial_count
    
    def test_participant_count_tracking(self, client, reset_activities):
        """Test that participant counts are correctly updated"""
        # Arrange
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        activity = "Art Studio"
        
        activities_data = client.get("/activities").json()
        initial_count = len(activities_data[activity]["participants"])
        
        # Act - Sign up first student
        client.post(f"/activities/{activity}/signup?email={email1}")
        activities_after_signup1 = client.get("/activities").json()
        
        # Act - Sign up second student
        client.post(f"/activities/{activity}/signup?email={email2}")
        activities_after_signup2 = client.get("/activities").json()
        
        # Act - Unregister first student
        client.delete(f"/activities/{activity}/unregister?email={email1}")
        activities_after_unregister1 = client.get("/activities").json()
        
        # Act - Unregister second student
        client.delete(f"/activities/{activity}/unregister?email={email2}")
        activities_after_unregister2 = client.get("/activities").json()
        
        # Assert
        assert len(activities_after_signup1[activity]["participants"]) == initial_count + 1
        assert len(activities_after_signup2[activity]["participants"]) == initial_count + 2
        assert len(activities_after_unregister1[activity]["participants"]) == initial_count + 1
        assert len(activities_after_unregister2[activity]["participants"]) == initial_count
