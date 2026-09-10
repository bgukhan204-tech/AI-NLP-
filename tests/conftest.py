import os

# Test imports require a JWT secret; CI supplies DATABASE_URL separately.
os.environ.setdefault("JWT_SECRET", "test-secret-for-ci-only")
os.environ.setdefault("JWT_EXPIRES_SECONDS", "3600")
