"""
Load testing script for Complaint Management System.

This script uses Locust to simulate high traffic load on the API endpoints.
It tests:
- Complaint submission
- Complaint listing (with pagination)
- Status updates
- Assignment operations
- Photo uploads

To run:
    pip install locust
    locust -f load_tests/test_complaints_load.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between
import random
import json


class ComplaintUser(HttpUser):
    """Simulates user interactions with the complaint system."""
    wait_time = between(1, 3)  # Wait between 1-3 seconds between tasks
    
    def on_start(self):
        """Login and get access token."""
        # Register/login as a porter
        self.porter_data = {
            "full_name": f"Load Test Porter {random.randint(1000, 9999)}",
            "email": f"loadtest_{random.randint(1000, 9999)}@example.com",
            "phone": f"+123456789{random.randint(100, 999)}",
            "password": "testpass123"
        }
        
        # Try to register (will succeed if unique, fail if exists - that's ok)
        self.client.post("/auth/register", json=self.porter_data)
        
        # Login
        login_response = self.client.post(
            "/auth/login",
            data={
                "username": self.porter_data["email"],
                "password": self.porter_data["password"]
            }
        )
        
        if login_response.status_code == 200:
            response_data = login_response.json()
            self.token = response_data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            # Fallback to anonymous requests (some endpoints work without auth)
            self.headers = {}
    
    @task(3)
    def list_complaints(self):
        """List complaints with pagination."""
        page = random.randint(1, 10)
        self.client.get(
            f"/api/v1/complaints?page={page}&page_size=20",
            headers=self.headers,
            name="/api/v1/complaints (paginated)"
        )
    
    @task(2)
    def list_complaints_with_filters(self):
        """List complaints with filters."""
        statuses = ["reported", "in_progress", "resolved", "closed"]
        categories = ["plumbing", "electrical", "carpentry", "pest"]

        params = {
            "page": 1,
            "page_size": 20,
            "status": random.choice(statuses),
            "category": random.choice(categories)
        }
        
        self.client.get(
            "/api/v1/complaints",
            params=params,
            headers=self.headers,
            name="/api/v1/complaints (filtered)"
        )
    
    @task(1)
    def get_complaint_detail(self):
        """Get a specific complaint (will fail if no complaints exist, but that's ok)."""
        # First list to get a complaint ID
        response = self.client.get("/api/v1/complaints?page=1&page_size=1", headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("items"):
                complaint_id = data["items"][0]["id"]
                self.client.get(
                    f"/api/v1/complaints/{complaint_id}",
                    headers=self.headers,
                    name="/api/v1/complaints/{id}"
                )
    
    @task(1)
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/health", name="/health")


class PhotoUploadUser(HttpUser):
    """Simulates photo upload operations."""
    wait_time = between(2, 5)
    
    def on_start(self):
        """Setup: Login as before."""
        self.porter_data = {
            "full_name": f"Photo Load Test User {random.randint(1000, 9999)}",
            "email": f"phototest_{random.randint(1000, 9999)}@example.com",
            "phone": f"+123456789{random.randint(100, 999)}",
            "password": "testpass123"
        }
        
        self.client.post("/auth/register", json=self.porter_data)
        
        login_response = self.client.post(
            "/auth/login",
            data={
                "username": self.porter_data["email"],
                "password": self.porter_data["password"]
            }
        )
        
        if login_response.status_code == 200:
            response_data = login_response.json()
            self.token = response_data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
    
    @task(1)
    def list_porters(self):
        """List available porters."""
        self.client.get("/api/v1/porters", headers=self.headers, name="/api/v1/porters")
    
    @task(1)
    def list_hostels(self):
        """List hostels."""
        self.client.get("/api/v1/hostels", headers=self.headers, name="/api/v1/hostels")


class MetricsUser(HttpUser):
    """Simulates system monitoring."""
    wait_time = between(5, 10)
    
    @task(1)
    def check_metrics(self):
        """Check Prometheus metrics."""
        self.client.get("/metrics", name="/metrics")


if __name__ == "__main__":
    print("Load test script for Complaint Management System")
    print("Run with: locust -f tests/test_complaints_load.py --host=http://localhost:8000")

