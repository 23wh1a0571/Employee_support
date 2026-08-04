def reset_password_guidelines() -> str:
    """Provides self-service instructions for resetting user corporate password."""
    return (
        "To reset your corporate account password:\n"
        "1. Go to https://sso.enterprise.com/reset\n"
        "2. Enter your employee email address.\n"
        "3. Complete 2FA verification via Okta/Google Authenticator.\n"
        "4. Choose a new password containing at least 12 characters."
    )