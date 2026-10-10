import os

os.environ.setdefault("JOB_HUNT_DATABASE_URL", "postgresql+psycopg://jobhunt:jobhunt@localhost:5432/jobhunt")
os.environ.setdefault("JOB_HUNT_GOOGLE_CLIENT_ID", "test-google-client-id")
os.environ.setdefault("JOB_HUNT_SESSION_SIGNING_KEY", "test-session-signing-key-with-at-least-32-characters")
os.environ.setdefault("JOB_HUNT_SESSION_COOKIE_SECURE", "false")
