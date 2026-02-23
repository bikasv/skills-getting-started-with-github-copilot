"""Tests for FastAPI endpoints."""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities."""
        response = client.get("/activities")
        
        assert response.status_code == 200
        activities = response.json()
        
        # Verify all expected activities are present
        expected_activities = {
            "Chess Club", "Programming Class", "Gym Class", "Basketball Team",
            "Tennis Club", "Drama Club", "Art Studio", "Debate Society", "Science Club"
        }
        assert set(activities.keys()) == expected_activities

    def test_get_activities_structure(self, client):
        """Test that activities have correct structure."""
        response = client.get("/activities")
        activities = response.json()
        
        # Verify each activity has required fields
        for activity_name, details in activities.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)

    def test_get_activities_participants_count(self, client):
        """Test that participant counts are correct."""
        response = client.get("/activities")
        activities = response.json()
        
        # Chess Club should have 2 participants initially
        assert len(activities["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in activities["Chess Club"]["participants"]


class TestRootRedirect:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_static_index(self, client):
        """Test that GET / redirects to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/static/index.html"


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_valid_student(self, client):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
        assert len(activities["Chess Club"]["participants"]) == 3

    def test_signup_duplicate_student(self, client):
        """Test that duplicate signup returns error."""
        # Try to signup a student already registered
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity returns 404."""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_multiple_activities(self, client):
        """Test that a student can signup for multiple activities."""
        email = "multi@mergington.edu"
        
        # Signup for Chess Club
        response1 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Signup for Programming Class
        response2 = client.post(
            f"/activities/Programming Class/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify student is in both activities
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]

    def test_signup_multiple_emails(self, client):
        """Test that multiple students can signup for the same activity."""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for email in emails:
            response = client.post(
                f"/activities/Art Studio/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all students are registered
        activities_response = client.get("/activities")
        activities = activities_response.json()
        
        for email in emails:
            assert email in activities["Art Studio"]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint."""

    def test_unregister_valid_student(self, client):
        """Test successful unregistration from activity."""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Verify student is registered initially
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister student
        response = client.delete(
            f"/activities/{activity}/signup?email={email}"
        )
        
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
        # Verify student was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == 1

    def test_unregister_student_not_registered(self, client):
        """Test unregister for student not in activity."""
        response = client.delete(
            "/activities/Chess Club/signup?email=notregistered@mergington.edu"
        )
        
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from non-existent activity."""
        response = client.delete(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_decreases_count(self, client):
        """Test that unregistering decreases participant count."""
        activity = "Drama Club"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Unregister a participant
        client.delete(
            f"/activities/{activity}/signup?email=lucas@mergington.edu"
        )
        
        # Verify count decreased
        response = client.get("/activities")
        new_count = len(response.json()[activity]["participants"])
        assert new_count == initial_count - 1


class TestIntegration:
    """Integration tests for signup and unregister workflows."""

    def test_signup_then_unregister(self, client):
        """Test full workflow: signup then unregister."""
        email = "workflow@mergington.edu"
        activity = "Art Studio"
        
        # Signup
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/signup?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]

    def test_participant_isolation_across_tests(self, client):
        """Test that each test gets fresh activity state."""
        # Signup a participant
        client.post(
            "/activities/Science Club/signup?email=isolated@mergington.edu"
        )
        
        # Verify it was added
        response = client.get("/activities")
        participants = response.json()["Science Club"]["participants"]
        assert "isolated@mergington.edu" in participants
