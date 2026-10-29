"""
HoneyChain User Model
"""
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timezone


class User:
    """Represents a system user in the HoneyChain platform."""

    VALID_ROLES = ["admin", "beekeeper", "lab", "packager", "seller", "consumer"]

    def __init__(self, id=None, username="", email="", password="", full_name="", role="beekeeper", organization="", phone=""):
        self.id = id
        self.username = username or (email.split("@")[0] if email else "")
        self.email = email
        self.password = password
        self.full_name = full_name or self.username
        self.role = role.lower() if role else "beekeeper"
        self.organization = organization
        self.phone = phone

    def verify_password(self, plain_password):
        """Verifies plain password against stored hash."""
        if not self.password:
            return False
        return check_password_hash(self.password, plain_password)

    def set_password(self, plain_password):
        """Hashes and sets the user's password."""
        self.password = generate_password_hash(plain_password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "organization": self.organization,
            "phone": self.phone,
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        keys = row.keys() if hasattr(row, "keys") else []
        return cls(
            id=row["id"] if "id" in keys else None,
            username=row["username"] if "username" in keys else "",
            email=row["email"] if "email" in keys else "",
            password=row["password"] if "password" in keys else "",
            full_name=row["full_name"] if "full_name" in keys else "",
            role=row["role"] if "role" in keys else "beekeeper",
            organization=row["organization"] if "organization" in keys else "",
            phone=row["phone"] if "phone" in keys else "",
        )

