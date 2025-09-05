import streamlit as st
import bcrypt
from pymongo import MongoClient
import pandas as pd
import random

# --- Always FIRST Streamlit command ---
st.set_page_config(page_title="Telecom Plan Recommender", layout="wide")

# -----------------
# MongoDB Connection
# -----------------
client = MongoClient(
    "mongodb+srv://praveenkumar97213_db_user:Praveen%402005@user.bqzpob3.mongodb.net/Telecomdb?retryWrites=true&w=majority&appName=User")
db = client["Telecomdb"]
users_collection = db["User"]

# -----------------
# Ensure Single Admin
# -----------------


def create_admin():
    admin_email = "admin@telecom.com"
    admin_user = users_collection.find_one({"email": admin_email})
    if not admin_user:
        hashed_pw = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
        users_collection.insert_one({
            "name": "Super Admin",
            "email": admin_email,
            "password": hashed_pw,
            "role": "Admin",
            "approved": True
        })
        st.success("✅ Default Admin created (admin@telecom.com / admin123)")
    else:
        st.info("ℹ️ Admin already exists")


create_admin()  # Ensure the admin is always present

# -----------------
# Signup Function
# -----------------


def signup_user(name, email, password, role):
    if role == "Admin":
        return False, "❌ You cannot create an Admin account!"
    if users_collection.find_one({"email": email}):
        return False, "❌ User already exists!"
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    users_collection.insert_one({
        "name": name,
        "email": email,
        "password": hashed_pw,
        "role": role,
        "approved": False
    })
    return True, "✅ Signup successful! Waiting for Admin approval."

# -----------------
# Login Function
# -----------------


def login_user(email, password):
    user = users_collection.find_one({"email": email})
    if user and bcrypt.checkpw(password.encode('utf-8'), user["password"]):
        if not user.get("approved", False):
            return False, "⏳ Account pending approval by Admin"
        return True, user
    return False, "❌ Invalid email or password"

# -----------------
# Dummy Recommendation (to replace later with ML)
# -----------------


def recommend_plan(user_email):
    plans = ["Basic Plan", "Premium Plan", "Family Pack", "Data Booster"]
    return random.choice(plans)

# -----------------
# SIGNUP PAGE LOGIC
# -----------------


def render_signup():
    st.markdown("### ✍️ Create Account")
    with st.form("signup_form"):
        name = st.text_input("👤 Name", key="signup_name")
        email = st.text_input("📧 Email", key="signup_email")
        password = st.text_input(
            "🔑 Password", type="password", key="signup_pw")
        role = st.selectbox(
            "🎭 Role", ["Customer", "Analyst"], key="signup_role")
        submit = st.form_submit_button("🚀 Signup")
    if submit:
        ok, msg = signup_user(name, email, password, role)
        if ok:
            st.success(msg)
        else:
            st.error(msg)

# -----------------
# LOGIN PAGE LOGIC
# -----------------


def render_login():
    st.markdown("### 🔐 Login to Your Account")
    with st.form("login_form"):
        email = st.text_input("📧 Email", key="login_email")
        password = st.text_input("🔑 Password", type="password", key="login_pw")
        submit = st.form_submit_button("🔓 Login")
    if submit:
        ok, user = login_user(email, password)
        if ok:
            st.session_state["user"] = user
            st.success("✅ Logged in!")
            st.rerun()
        else:
            st.error(user)

# -----------------
# ADMIN DASHBOARD
# -----------------


def admin_dashboard(user):
    st.markdown("## 👑 Admin Dashboard")
    tabs = st.tabs(["🔎 Pending Approvals", "👥 Active Users", "⚙️ Admin Tools"])

    # --- Tab 1: Pending Approvals ---
    with tabs[0]:
        st.subheader("🔎 Pending Approvals")
        pending_users = list(users_collection.find({"approved": False}))
        if pending_users:
            for p in pending_users:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(
                        f"**{p.get('name', '-')}** — {p.get('role', '-')} — {p.get('email', '-')}")
                with col2:
                    if st.button("✅ Approve", key=f"approve_{p.get('email')}"):
                        users_collection.update_one({"email": p['email']}, {
                                                    "$set": {"approved": True}})
                        st.success(f"Approved {p['email']}")
                        st.rerun()
                with col3:
                    if st.button("❌ Reject", key=f"reject_{p.get('email')}"):
                        users_collection.delete_one({"email": p['email']})
                        st.warning(f"Rejected {p['email']}")
                        st.rerun()
        else:
            st.info("✅ No pending users")

    # --- Tab 2: Active Users ---
    with tabs[1]:
        st.subheader("👥 Active Users")
        active_users = list(users_collection.find(
            {"approved": True, "role": {"$ne": "Admin"}}, {"password": 0}))
        if active_users:
            df = pd.DataFrame(active_users)
            st.dataframe(df[["name", "email", "role"]])
        else:
            st.info("No active users yet.")

    # --- Tab 3: Admin Tools ---
    with tabs[2]:
        st.subheader("⚙️ Admin Tools")
        if st.button("Export all users to CSV"):
            all_users = list(users_collection.find({}, {"password": 0}))
            if all_users:
                df = pd.DataFrame(all_users)
                st.download_button(
                    "Download users.csv",
                    df.to_csv(index=False).encode("utf-8"),
                    file_name="users.csv"
                )
            else:
                st.info("No users to export")

# -----------------
# ANALYST DASHBOARD
# -----------------


def analyst_dashboard(user):
    st.subheader("📊 Analyst Dashboard")
    st.write("Here you will be able to analyze usage and recharge data.")
    total_customers = users_collection.count_documents(
        {"role": "Customer", "approved": True})
    total_analysts = users_collection.count_documents(
        {"role": "Analyst", "approved": True})
    col1, col2 = st.columns(2)
    col1.metric("✅ Approved Customers", total_customers)
    col2.metric("✅ Approved Analysts", total_analysts)
    st.info("📈 Charts and analytics will be added here later.")

# -----------------
# CUSTOMER DASHBOARD
# -----------------


def customer_dashboard(user):
    st.subheader("👤 Customer Dashboard")
    st.write(f"Welcome, **{user.get('name')}** ({user.get('email')})")
    st.markdown("**💡 Your Recommended Plan:**")
    try:
        rec = recommend_plan(user.get("email"))
        st.success(f"👉 {rec}")
    except Exception as e:
        st.info("No recommendation available yet.")
        st.write("Error:", e)
    st.markdown("### 📜 Your Profile")
    st.json({k: v for k, v in user.items() if k not in ["_id", "password"]})

# -----------------
# MAIN APP FLOW
# -----------------


def main_ui():
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if st.session_state["user"] is None:
        page = st.sidebar.selectbox("📌 Menu", ["Signup", "Login"])
        if page == "Signup":
            render_signup()
        else:
            render_login()
    else:
        user = st.session_state["user"]
        st.sidebar.markdown(
            f"**Logged in:** {user.get('name', '-')}  \nRole: **{user.get('role', '-')}**")
        if st.sidebar.button("🔓 Logout"):
            st.session_state["user"] = None
            st.rerun()
        role = user.get("role", "").capitalize()
        if role == "Admin":
            admin_dashboard(user)
        elif role == "Analyst":
            analyst_dashboard(user)
        else:
            customer_dashboard(user)


# -----------------
# Run app
# -----------------
if __name__ == "__main__":
    main_ui()
