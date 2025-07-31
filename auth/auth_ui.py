"""
Authentication UI components for Smart Campus Dashboard
"""

import streamlit as st
import time
import pandas as pd
from typing import Optional
from .user_manager import UserManager


def render_login_form(user_manager: UserManager) -> bool:
    """Render login form and handle authentication."""

    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "username" not in st.session_state:
        st.session_state.username = None

    def logout_user():
        """Handle user logout."""
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.session_state.username = None
        if "login_username" in st.session_state:
            del st.session_state.login_username
        if "login_password" in st.session_state:
            del st.session_state.login_password
        st.rerun()

    # Show logout button if authenticated
    if st.session_state.authenticated:
        with st.sidebar:
            st.markdown("---")
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"👤 **{st.session_state.username}**")
                st.caption(f"Role: {st.session_state.user_info.get('role', 'user')}")
            with col2:
                if st.button("🚪 Logout", key="logout_btn"):
                    logout_user()
        return True

    # Login interface
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Smart Campus Dashboard Login")
        st.markdown("---")

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input(
                "Password", type="password", placeholder="Enter your password"
            )
            login_submitted = st.form_submit_button(
                "🔑 Login", use_container_width=True
            )

            if login_submitted:
                if username and password:
                    success, user_info = user_manager.authenticate_user(
                        username, password
                    )
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_info = user_info
                        st.session_state.username = username
                        st.success(f"Welcome, {username}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials or inactive account")
                else:
                    st.error("❌ Please enter both username and password")

        st.markdown("---")
        st.markdown("### 🌟 Dashboard Features")
        st.markdown(
            """
        - 📊 **Real-time monitoring** from IoT sensors
        - 🌡️ **Environmental tracking** (temperature, humidity)  
        - 💡 **Classroom analytics** (light levels, occupancy)
        - 🔒 **Security management** (motion, RFID access)
        - 📱 **Mobile responsive** design
        - ⚡ **Auto-refresh** capabilities
        - 👥 **Multi-user access** with role-based permissions
        """
        )

    return False


def render_user_management(user_manager: UserManager) -> bool:
    """Display user management interface for admins. Returns True if should return to dashboard."""
    if (
        not st.session_state.user_info
        or st.session_state.user_info.get("role") != "admin"
    ):
        st.error("❌ Access denied. Admin privileges required.")
        return False

    # Header with return to dashboard button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("👥 User Management")
    with col2:
        if st.button("🏠 Return to Dashboard", key="return_dashboard"):
            return True

    tab1, tab2, tab3 = st.tabs(["👀 View Users", "➕ Add User", "✏️ Manage Users"])

    with tab1:
        _render_users_view(user_manager)

    with tab2:
        _render_add_user(user_manager)

    with tab3:
        _render_manage_users(user_manager)

    return False


def _render_users_view(user_manager: UserManager) -> None:
    """Render the users view tab."""
    st.subheader("📋 Current Users")
    users = user_manager.get_all_users()

    if users:
        users_data = []
        for username, user_info in users.items():
            users_data.append(
                {
                    "Username": username,
                    "Role": user_info.get("role", "user"),
                    "Status": (
                        "🟢 Active" if user_info.get("active", False) else "🔴 Inactive"
                    ),
                    "Created By": user_info.get("created_by", "Unknown"),
                    "Last Login": (
                        user_info.get("last_login", "Never")[:19]
                        if user_info.get("last_login")
                        else "Never"
                    ),
                    "Permissions": ", ".join(user_info.get("permissions", [])),
                }
            )

        df_users = pd.DataFrame(users_data)
        st.dataframe(df_users, use_container_width=True)
    else:
        st.info("No users found.")


def _render_add_user(user_manager: UserManager) -> None:
    """Render the add user tab."""
    st.subheader("➕ Add New User")

    with st.form("add_user_form"):
        new_username = st.text_input("Username", placeholder="Enter unique username")
        new_password = st.text_input(
            "Password", type="password", placeholder="Enter password"
        )
        new_role = st.selectbox("Role", ["user", "admin", "viewer"])

        st.write("**Permissions:**")
        perm_dashboard = st.checkbox("Dashboard Access", value=True)
        perm_sensors = st.checkbox("Sensor Data Access", value=True)
        perm_user_mgmt = st.checkbox(
            "User Management", value=False, disabled=(new_role != "admin")
        )
        perm_all_sensors = st.checkbox("All Sensors Access", value=True)

        add_user_submitted = st.form_submit_button("👤 Create User")

        if add_user_submitted:
            if new_username and new_password:
                permissions = []
                if perm_dashboard:
                    permissions.append("dashboard")
                if perm_sensors:
                    permissions.append("sensors")
                if perm_user_mgmt and new_role == "admin":
                    permissions.append("user_management")
                if perm_all_sensors:
                    permissions.append("all_sensors")

                success, message = user_manager.add_user(
                    new_username,
                    new_password,
                    new_role,
                    permissions,
                    st.session_state.username,
                )

                if success:
                    st.success(f"✅ {message}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("❌ Please provide both username and password")


def _render_manage_users(user_manager: UserManager) -> None:
    """Render the manage users tab."""
    st.subheader("✏️ Manage Existing Users")

    users = user_manager.get_all_users()
    user_list = [u for u in users.keys() if u != "admin"]  # Don't allow managing admin

    if user_list:
        selected_user = st.selectbox("Select User to Manage", user_list)

        if selected_user:
            user_info = users[selected_user]

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Current User Info:**")
                st.write(f"Username: {selected_user}")
                st.write(f"Role: {user_info.get('role', 'user')}")
                status_color = "🟢" if user_info.get("active", False) else "🔴"
                status_text = "Active" if user_info.get("active", False) else "Inactive"
                st.write(f"Status: {status_color} {status_text}")
                st.write(f"Created by: {user_info.get('created_by', 'Unknown')}")
                if user_info.get("last_login"):
                    st.write(f"Last login: {user_info.get('last_login')[:19]}")
                else:
                    st.write("Last login: Never")
                st.write(f"Permissions: {', '.join(user_info.get('permissions', []))}")

            with col2:
                with st.form(f"manage_user_{selected_user}"):
                    st.write("**Update User:**")

                    # Role selection
                    current_role = user_info.get("role", "user")
                    new_role_update = st.selectbox(
                        "Role",
                        ["user", "admin", "viewer"],
                        index=["user", "admin", "viewer"].index(current_role),
                    )

                    # Auto-update permissions help text
                    if new_role_update != current_role:
                        if new_role_update == "admin":
                            st.info(
                                "💡 Admin role will automatically get all permissions including user management"
                            )
                        elif new_role_update == "viewer":
                            st.info(
                                "💡 Viewer role will have limited read-only permissions"
                            )
                        else:
                            st.info(
                                "💡 User role will have standard dashboard and sensor permissions"
                            )

                    # Password update
                    new_password_update = st.text_input(
                        "New Password (leave empty to keep current)",
                        type="password",
                        placeholder="Enter new password",
                    )

                    # Action buttons
                    col_update, col_status, col_delete = st.columns(3)

                    with col_update:
                        update_submitted = st.form_submit_button("🔄 Update User")

                    with col_status:
                        if user_info.get("active", False):
                            status_submitted = st.form_submit_button(
                                "🚫 Deactivate", type="secondary"
                            )
                        else:
                            status_submitted = st.form_submit_button(
                                "✅ Activate", type="secondary"
                            )

                    with col_delete:
                        delete_submitted = st.form_submit_button(
                            "🗑️ Delete", type="secondary"
                        )

                    # Handle form submissions
                    if update_submitted:
                        update_data = {"role": new_role_update}

                        # Auto-assign permissions based on role
                        if new_role_update == "admin":
                            update_data["permissions"] = [
                                "dashboard",
                                "user_management",
                                "all_sensors",
                                "sensors",
                            ]
                        elif new_role_update == "viewer":
                            update_data["permissions"] = ["dashboard", "sensors"]
                        else:  # user
                            update_data["permissions"] = [
                                "dashboard",
                                "sensors",
                                "all_sensors",
                            ]

                        if new_password_update:
                            update_data["password"] = new_password_update

                        success, message = user_manager.update_user(
                            selected_user, **update_data
                        )
                        if success:
                            st.success(f"✅ {message}")
                            # Update session state if user updated themselves
                            if selected_user == st.session_state.username:
                                st.session_state.user_info = users[selected_user]
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")

                    if status_submitted:
                        if user_info.get("active", False):
                            success, message = user_manager.deactivate_user(
                                selected_user
                            )
                        else:
                            success, message = user_manager.activate_user(selected_user)

                        if success:
                            st.success(f"✅ {message}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")

                    if delete_submitted:
                        # Confirmation dialog
                        if st.session_state.get(
                            f"confirm_delete_{selected_user}", False
                        ):
                            success, message = user_manager.delete_user(
                                selected_user, st.session_state.username
                            )
                            if success:
                                st.success(f"✅ {message}")
                                if (
                                    f"confirm_delete_{selected_user}"
                                    in st.session_state
                                ):
                                    del st.session_state[
                                        f"confirm_delete_{selected_user}"
                                    ]
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                        else:
                            st.session_state[f"confirm_delete_{selected_user}"] = True
                            st.warning(
                                f"⚠️ Click 'Delete' again to confirm permanent deletion of user '{selected_user}'"
                            )
                            st.rerun()

    else:
        st.info("No users to manage (excluding admin).")


def check_permission(permission: str) -> bool:
    """Check if current user has specific permission."""
    if not st.session_state.get("authenticated", False):
        return False

    user_permissions = st.session_state.user_info.get("permissions", [])
    return permission in user_permissions or "all_sensors" in user_permissions
