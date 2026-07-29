import os

os.environ.setdefault("AUTH_TOKEN_SECRET", "test-auth-token-secret-32-bytes-min")
os.environ.setdefault(
    "FIELD_ENCRYPTION_KEY",
    "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
)
os.environ.setdefault("FIELD_LOOKUP_HMAC_KEY", "test-email-lookup-hmac-key-32-bytes")
os.environ.setdefault("FIELD_KEY_VERSION", "test-v1")
