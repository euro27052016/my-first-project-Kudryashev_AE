"""
Locust Load Testing File for Email Validator API

Run with:
    locust -f locustfile.py --host=http://localhost:5000

Then open http://localhost:8089 in your browser to control the test.
"""

import random
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner


# Sample email datasets for testing
VALID_EMAILS = [
    "user@example.com",
    "john.doe@company.org",
    "alice123@gmail.com",
    "bob_smith@yahoo.com",
    "charlie.brown@outlook.com",
    "david+tag@proton.me",
    "eve@subdomain.example.co.uk",
    "frank@my-domain.io",
    "grace@university.edu",
    "henry@government.gov",
    "iris@startup.tech",
    "jack@corporate.biz",
    "kate@nonprofit.org",
    "leo@media.news",
    "mary@health.clinic",
    "nick@finance.bank",
    "olivia@travel.agency",
    "peter@food.restaurant",
    "quinn@sports.club",
    "rachel@music.band",
]

INVALID_EMAILS = [
    "plainaddress",
    "@missing-local.com",
    "missing-domain@",
    "user@.com",
    "user@domain",
    "user@@double-at.com",
    "user@domain..com",
    ".user@domain.com",
    "user.@domain.com",
    "user@-domain.com",
    "user@domain-.com",
    "user space@domain.com",
    "",
    "user@",
    "@",
    "user@domain.c",
    "user@.domain.com",
    "user@domain.",
    "user@domain.com.",
    "user..name@domain.com",
]

MIXED_EMAILS = VALID_EMAILS + INVALID_EMAILS


class EmailValidatorUser(HttpUser):
    """
    Simulates a user of the Email Validator API.
    """

    # Wait between 0.5 and 2 seconds between requests
    wait_time = between(0.5, 2)

    def on_start(self):
        """Called when a user starts."""
        self.valid_emails = VALID_EMAILS.copy()
        self.invalid_emails = INVALID_EMAILS.copy()
        self.all_emails = MIXED_EMAILS.copy()

    @task(10)
    def validate_valid_email(self):
        """Validate a valid email address (most common operation)."""
        email = random.choice(self.valid_emails)
        self.client.post(
            "/validate",
            json={"email": email},
            name="/validate [valid]"
        )

    @task(3)
    def validate_invalid_email(self):
        """Validate an invalid email address."""
        email = random.choice(self.invalid_emails)
        self.client.post(
            "/validate",
            json={"email": email},
            name="/validate [invalid]"
        )

    @task(2)
    def validate_random_email(self):
        """Validate a random email from mixed dataset."""
        email = random.choice(self.all_emails)
        self.client.post(
            "/validate",
            json={"email": email},
            name="/validate [mixed]"
        )

    @task(5)
    def quick_check(self):
        """Quick GET validation check."""
        email = random.choice(self.valid_emails)
        self.client.get(
            f"/quick-check?email={email}",
            name="/quick-check"
        )

    @task(1)
    def validate_batch(self):
        """Validate a batch of emails."""
        # Pick 5-10 random emails
        batch_size = random.randint(5, 10)
        emails = random.sample(self.all_emails, min(batch_size, len(self.all_emails)))
        self.client.post(
            "/validate/batch",
            json={"emails": emails},
            name="/validate/batch"
        )

    @task(1)
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/health", name="/health")


class QuickValidatorUser(HttpUser):
    """
    A user that only does quick validation checks.
    Higher frequency, lighter load.
    """

    wait_time = between(0.1, 0.5)

    @task
    def quick_validate(self):
        """Perform quick validation."""
        email = random.choice(VALID_EMAILS)
        self.client.get(f"/quick-check?email={email}")


class BatchValidatorUser(HttpUser):
    """
    A user that sends batch validation requests.
    Lower frequency, heavier load per request.
    """

    wait_time = between(2, 5)

    @task
    def batch_validate(self):
        """Send a batch of emails for validation."""
        batch_size = random.randint(10, 50)
        emails = [random.choice(MIXED_EMAILS) for _ in range(batch_size)]
        self.client.post(
            "/validate/batch",
            json={"emails": emails}
        )


class StressTestUser(HttpUser):
    """
    Stress test user with minimal wait time.
    Used to test maximum throughput.
    """

    wait_time = between(0.01, 0.1)

    @task
    def rapid_validation(self):
        """Rapid-fire validation requests."""
        email = random.choice(MIXED_EMAILS)
        self.client.post(
            "/validate",
            json={"email": email}
        )


# Event handlers for custom statistics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log request details for analysis."""
    if exception:
        print(f"Request failed: {name} - {exception}")
    elif response_time > 1000:  # Log slow requests (>1s)
        print(f"Slow request: {name} took {response_time:.2f}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("=" * 50)
    print("Email Validator Load Test Starting")
    print("=" * 50)
    if isinstance(environment.runner, MasterRunner):
        print("Running in distributed mode (master)")
    elif isinstance(environment.runner, WorkerRunner):
        print("Running in distributed mode (worker)")
    else:
        print("Running in standalone mode")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    print("=" * 50)
    print("Email Validator Load Test Complete")
    print("=" * 50)

    # Print statistics
    if hasattr(environment, 'stats'):
        stats = environment.stats
        print(f"\nTotal Requests: {stats.total.num_requests}")
        print(f"Total Failures: {stats.total.num_failures}")
        print(f"Average Response Time: {stats.total.avg_response_time:.2f}ms")
        print(f"Median Response Time: {stats.total.median_response_time:.2f}ms")
        print(f"95th Percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
        print(f"Requests/sec: {stats.total.total_rps:.2f}")


# Custom shape for ramping up load
class RampUpShape:
    """
    Custom load test shape that ramps up users gradually.
    Use with: locust -f locustfile.py --headless --run-time 5m
    """

    def __init__(self):
        self.stages = [
            {"duration": 60, "users": 10, "spawn_rate": 1},   # 1 min: 10 users
            {"duration": 120, "users": 50, "spawn_rate": 5},  # 2 min: 50 users
            {"duration": 180, "users": 100, "spawn_rate": 10}, # 3 min: 100 users
            {"duration": 240, "users": 200, "spawn_rate": 20}, # 4 min: 200 users
            {"duration": 300, "users": 500, "spawn_rate": 50}, # 5 min: 500 users
        ]

    def tick(self):
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]

        return None


# To use custom shape, uncomment:
# class ShapeUser(HttpUser):
#     tasks = [EmailValidatorUser]


if __name__ == "__main__":
    import os
    os.system("locust -f locustfile.py")
