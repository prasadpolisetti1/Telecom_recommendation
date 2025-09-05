import streamlit as st
import bcrypt
from pymongo import MongoClient
import pandas as pd
import random

# -----------------
# MongoDB Connection
# -----------------
# paste from MongoDB Atlas
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
    # Just returns a random plan now
    plans = ["Basic Plan", "Premium Plan", "Family Pack", "Data Booster"]
    return random.choice(plans)


# -----------------
# Streamlit App
# -----------------
st.set_page_config(page_title="Telecom Plan Recommender", layout="wide")
st.title("📡 Telecom Data Plan Recommendation System")

menu = ["Signup", "Login"]
choice = st.sidebar.selectbox("Menu", menu)

# -----------------
# SIGNUP PAGE
# -----------------
if choice == "Signup":
    st.markdown("### ✍️ Create Account")
    with st.form("signup_form"):
        name = st.text_input("👤 Name")
        email = st.text_input("📧 Email")
        password = st.text_input("🔑 Password", type="password")
        role = st.selectbox("🎭 Role", ["Customer", "Analyst"])
        submit_signup = st.form_submit_button("🚀 Signup")

    if submit_signup:
        success, msg = signup_user(name, email, password, role)
        if success:
            st.success(msg)
        else:
            st.error(msg)


# -----------------
# LOGIN PAGE
# -----------------
elif choice == "Login":
    st.markdown("### 🔐 Login to Your Account")
    with st.form("login_form"):
        email = st.text_input("📧 Email")
        password = st.text_input("🔑 Password", type="password")
        submit_login = st.form_submit_button("➡️ Login")

    if submit_login:
        success, result = login_user(email, password)
        if success:
            user = result
            st.success(f"🎉 Welcome {user['name']}! Role: {user['role']}")

            # ADMIN DASHBOARD
            if user["role"] == "Admin":
                st.subheader("👑 Admin Dashboard")
                pending_users = list(
                    users_collection.find({"approved": False}))
                if pending_users:
                    st.write("### Pending Approvals")
                    for p in pending_users:
                        st.write(f"{p['name']} ({p['role']}) - {p['email']}")
                        if st.button(f"Approve {p['email']}"):
                            users_collection.update_one(
                                {"email": p['email']}, {
                                    "$set": {"approved": True}}
                            )
                            st.success(f"Approved {p['email']}")
                else:
                    st.info("No pending users")

            # ANALYST DASHBOARD
            elif user["role"] == "Analyst":
                st.subheader("📊 Analyst Dashboard")
                st.write("Here you can analyze usage data (to be added later).")

            # CUSTOMER DASHBOARD
            elif user["role"] == "Customer":
                st.subheader("👤 Customer Dashboard")
                st.write("Your recommended plan:")
                rec = recommend_plan(user["email"])
                st.success(f"💡 Recommended: {rec}")

        else:
            st.error(result)
