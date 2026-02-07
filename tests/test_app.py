"""
Tests for the Mergington High School Activities API
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class TestActivities:
    """Test the /activities endpoint"""

    def test_get_activities(self):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert "Chess Club" in activities
        assert "Programming Class" in activities

    def test_activities_have_required_fields(self):
        """Test that activities have all required fields"""
        response = client.get("/activities")
        activities = response.json()

        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_activities_have_initial_participants(self):
        """Test that some activities have initial participants"""
        response = client.get("/activities")
        activities = response.json()
        chess_club = activities["Chess Club"]
        assert len(chess_club["participants"]) > 0
        assert "michael@mergington.edu" in chess_club["participants"]


class TestSignup:
    """Test the signup endpoint"""

    def test_signup_for_activity(self):
        """Test signing up a student for an activity"""
        response = client.post(
            "/activities/Art%20Studio/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "newstudent@mergington.edu" in result["message"]
        assert "Art Studio" in result["message"]

    def test_signup_verifies_activity_exists(self):
        """Test that signup fails if activity doesn't exist"""
        response = client.post(
            "/activities/NonexistentActivity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_signup_prevents_duplicate_registration(self):
        """Test that a student cannot sign up twice for the same activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"]

    def test_signup_adds_participant_to_activity(self):
        """Test that a signed-up student appears in the participants list"""
        # Sign up a student
        email = "testparticipant@mergington.edu"
        signup_response = client.post(
            f"/activities/Soccer%20Club/signup?email={email}"
        )
        assert signup_response.status_code == 200

        # Verify the student is now in the participants list
        activities_response = client.get("/activities")
        activities = activities_response.json()
        soccer_club = activities["Soccer Club"]
        assert email in soccer_club["participants"]


class TestUnregister:
    """Test the unregister endpoint"""

    def test_unregister_from_activity(self):
        """Test unregistering a student from an activity"""
        # First sign up
        email = "unregister_test@mergington.edu"
        client.post(f"/activities/Basketball/signup?email={email}")

        # Then unregister
        response = client.post(
            f"/activities/Basketball/unregister?email={email}"
        )
        assert response.status_code == 200
        result = response.json()
        assert "Unregistered" in result["message"]

    def test_unregister_verifies_activity_exists(self):
        """Test that unregister fails if activity doesn't exist"""
        response = client.post(
            "/activities/FakeActivity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_unregister_verifies_student_is_registered(self):
        """Test that unregister fails if student is not registered"""
        response = client.post(
            "/activities/Drama%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        result = response.json()
        assert "not registered" in result["detail"]

    def test_unregister_removes_participant(self):
        """Test that an unregistered student is removed from the participants list"""
        email = "remove_test@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Debate%20Team/signup?email={email}")
        
        # Verify they're signed up
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Debate Team"]["participants"]

        # Unregister
        client.post(f"/activities/Debate%20Team/unregister?email={email}")

        # Verify they're removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities["Debate Team"]["participants"]


class TestRootEndpoint:
    """Test the root endpoint"""

    def test_root_redirects_to_static(self):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
