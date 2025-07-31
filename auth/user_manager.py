"""
User Management System for Smart Campus Dashboard
Handles authentication, user creation, and permission management.
"""

import hashlib
import json
import os
import streamlit as st
from datetime import datetime
from typing import Dict, Tuple, List, Optional
from config import USER_CONFIG, SECURITY_CONFIG


class UserManager:
    """Manages user authentication and authorization."""

    def __init__(self, users_file: str = "users.json"):
        self.users_file = users_file
        self.load_users()

    def hash_password(self, password: str) -> str:
        """Hash password with salt."""
        salt = SECURITY_CONFIG.get("password_salt", "smart_campus_salt")
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

    def load_users(self) -> None:
        """Load users from JSON file."""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, "r") as f:
                    self.users = json.load(f)
            else:
                # Initialize with default admin user from config
                default_password = USER_CONFIG.get(
                    "default_admin_password", "cisco6776"
                )
                self.users = {
                    "admin": {
                        "password": self.hash_password(default_password),
                        "role": "admin",
                        "permissions": [
                            "dashboard",
                            "user_management",
                            "all_sensors",
                            "sensors",
                        ],
                        "created_by": "system",
                        "created_at": datetime.now().isoformat(),
                        "active": True,
                        "last_login": None,
                    }
                }
                self.save_users()
        except Exception as e:
            st.error(f"Error loading users: {e}")
            self.users = {}

    def save_users(self) -> None:
        """Save users to JSON file."""
        try:
            with open(self.users_file, "w") as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            st.error(f"Error saving users: {e}")

    def authenticate_user(
        self, username: str, password: str
    ) -> Tuple[bool, Optional[Dict]]:
        """Authenticate user credentials."""
        if username in self.users:
            user = self.users[username]
            if user["active"] and user["password"] == self.hash_password(password):
                # Update last login
                self.users[username]["last_login"] = datetime.now().isoformat()
                self.save_users()
                return True, user
        return False, None

    def add_user(
        self,
        username: str,
        password: str,
        role: str,
        permissions: List[str],
        created_by: str,
    ) -> Tuple[bool, str]:
        """Add new user (admin only)."""
        if username in self.users:
            return False, "User already exists"

        self.users[username] = {
            "password": self.hash_password(password),
            "role": role,
            "permissions": permissions,
            "created_by": created_by,
            "created_at": datetime.now().isoformat(),
            "active": True,
            "last_login": None,
        }
        self.save_users()
        return True, "User created successfully"

    def update_user(self, username: str, **kwargs) -> Tuple[bool, str]:
        """Update user details (admin only)."""
        if username not in self.users:
            return False, "User not found"

        for key, value in kwargs.items():
            if key == "password":
                self.users[username][key] = self.hash_password(value)
            else:
                self.users[username][key] = value

        self.save_users()
        return True, "User updated successfully"

    def delete_user(self, username: str, requester: str) -> Tuple[bool, str]:
        """Permanently delete user (admin only)."""
        if username not in self.users:
            return False, "User not found"

        if username == "admin":
            return False, "Cannot delete admin user"

        if username == requester:
            return False, "Cannot delete your own account"

        del self.users[username]
        self.save_users()
        return True, "User deleted successfully"

    def deactivate_user(self, username: str) -> Tuple[bool, str]:
        """Deactivate user (admin only)."""
        if username in self.users and username != "admin":
            self.users[username]["active"] = False
            self.save_users()
            return True, "User deactivated"
        return False, "Cannot deactivate admin or user not found"

    def activate_user(self, username: str) -> Tuple[bool, str]:
        """Activate user (admin only)."""
        if username in self.users:
            self.users[username]["active"] = True
            self.save_users()
            return True, "User activated"
        return False, "User not found"

    def get_all_users(self) -> Dict:
        """Get all users (admin only)."""
        return self.users

    def check_permission(self, username: str, permission: str) -> bool:
        """Check if user has specific permission."""
        if username not in self.users:
            return False

        user_permissions = self.users[username].get("permissions", [])
        return permission in user_permissions or "all_sensors" in user_permissions
