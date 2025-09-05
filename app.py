import streamlit as st
import bcrypt
from pymongo import MongoClient
import pandas as pd
import random
import plotly.express as px


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
# SIGNUP SCREEN
# -----------------


def render_signup():
    st.markdown("## ✍️ Create a New Account")

    with st.form("signup_form"):
        name = st.text_input("👤 Full Name")
        email = st.text_input("📧 Email")
        password = st.text_input("🔑 Password", type="password")
        role = st.selectbox("🎭 Role", ["Customer", "Analyst"])
        submit = st.form_submit_button("🚀 Sign Up")

    if submit:
        # ✅ Validate all fields
        if not name.strip() or not email.strip() or not password.strip() or not role:
            st.error("⚠️ All fields are required!")
            return

        # ✅ Check for duplicate email
        if users_collection.find_one({"email": email}):
            st.error("❌ Email already exists, try logging in.")
            return

        # ✅ Save user
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        users_collection.insert_one({
            "name": name,
            "email": email,
            "password": hashed_pw,
            "role": role,
            "approved": False  # Requires Admin approval
        })
        st.success("✅ Signup successful! Please wait for Admin approval.")
        st.session_state['show_login'] = True
        st.rerun()


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
# ADMIN DASHBOARD (Enhanced with Plan Management)
# -----------------


def admin_dashboard(user):
    st.markdown("## 👑 Admin Dashboard")
    tabs = st.tabs([
        "🔎 Pending Approvals",
        "👥 Active Users",
        "➕ Add User",
        "📦 Manage Plans",
        "📊 Plan Analytics",
        "⚙️ Admin Tools"
    ])

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

        subtab1, subtab2 = st.tabs(["📊 Analysts", "👤 Customers"])

        with subtab1:
            analysts = list(users_collection.find(
                {"approved": True, "role": "Analyst"}, {"password": 0}))
            if analysts:
                st.dataframe(pd.DataFrame(analysts)[["name", "email", "role"]])
            else:
                st.info("No analysts found.")

        with subtab2:
            customers = list(users_collection.find(
                {"approved": True, "role": "Customer"}, {"password": 0}))
            if customers:
                st.dataframe(pd.DataFrame(customers)[
                             ["name", "email", "role"]])
            else:
                st.info("No customers found.")

    # --- Tab 3: Add New User ---
    with tabs[2]:
        st.subheader("➕ Add a New User")
        with st.form("add_user_form"):
            name = st.text_input("👤 Name")
            email = st.text_input("📧 Email")
            password = st.text_input("🔑 Password", type="password")
            role = st.selectbox("🎭 Role", ["Customer", "Analyst"])
            submit = st.form_submit_button("🚀 Add User")

        if submit:
            if not name.strip() or not email.strip() or not password.strip():
                st.error("⚠️ All fields are required!")
            elif users_collection.find_one({"email": email}):
                st.error("❌ Email already exists!")
            else:
                hashed_pw = bcrypt.hashpw(
                    password.encode('utf-8'), bcrypt.gensalt())
                users_collection.insert_one({
                    "name": name,
                    "email": email,
                    "password": hashed_pw,
                    "role": role,
                    "approved": True
                })
                st.success(f"✅ {role} added successfully!")
                st.rerun()

    # --- Tab 4: Manage Plans ---
    with tabs[3]:
        st.subheader("📦 Manage Recharge Plans")
        plans_collection = db["Plans"]

        with st.form("add_plan_form"):
            plan_name = st.text_input("📛 Plan Name")
            monthly_cost = st.number_input(
                "💰 Monthly Cost (₹)", min_value=0.0, step=10.0)
            data_limit_gb = st.number_input(
                "📶 Data Limit (GB)", min_value=0, step=1)
            voice_minutes = st.number_input(
                "📞 Voice Minutes", min_value=0, step=10)
            validity_days = st.number_input(
                "📅 Validity (Days)", min_value=1, step=1)
            submit_plan = st.form_submit_button("➕ Add Plan")

        if submit_plan:
            if not plan_name.strip():
                st.error("⚠️ Plan name is required!")
            else:
                plans_collection.insert_one({
                    "plan_name": plan_name,
                    "monthly_cost": monthly_cost,
                    "data_limit_gb": data_limit_gb,
                    "voice_minutes": voice_minutes,
                    "validity_days": validity_days
                })
                st.success(f"✅ Plan '{plan_name}' added successfully!")
                st.rerun()

        st.markdown("### 📋 Existing Plans")
        all_plans = list(plans_collection.find())
        if all_plans:
            df = pd.DataFrame(all_plans).drop(columns=["_id"])
            st.dataframe(df)
            for p in all_plans:
                if st.button(f"🗑️ Delete {p['plan_name']}", key=f"del_plan_{p['plan_name']}"):
                    plans_collection.delete_one({"plan_name": p["plan_name"]})
                    st.warning(f"Deleted plan: {p['plan_name']}")
                    st.rerun()
        else:
            st.info("No plans added yet.")

    # --- Tab 5: Plan Analytics ---
    with tabs[4]:
        st.subheader("📊 Plan Analytics")
        plans_collection = db["Plans"]
        orders_collection = db["Orders"]

        # --- Available Plans Overview ---
        st.markdown("### 📦 Available Plans")
        plans = list(plans_collection.find({}, {"_id": 0}))
        if plans:
            df_plans = pd.DataFrame(plans)
            st.dataframe(df_plans)

            col1, col2 = st.columns(2)
            with col1:
                fig_price = px.bar(df_plans, x="plan_name",
                                   y="monthly_cost", title="Plan Pricing")
                st.plotly_chart(fig_price, use_container_width=True)
            with col2:
                fig_data = px.scatter(
                    df_plans, x="monthly_cost", y="data_limit_gb",
                    text="plan_name", size="data_limit_gb", color="validity_days",
                    title="Cost vs Data Limit"
                )
                st.plotly_chart(fig_data, use_container_width=True)

        # --- Customer Usage ---
        st.markdown("### 👥 Customer Usage")
        pipeline = [{"$group": {"_id": "$plan_name", "count": {"$sum": 1}}}]
        plan_usage = list(orders_collection.aggregate(pipeline))

        if plan_usage:
            df_usage = pd.DataFrame(plan_usage)
            df_usage.rename(
                columns={"_id": "Plan Name", "count": "Users"}, inplace=True)

            col1, col2 = st.columns(2)
            with col1:
                fig_popular = px.bar(
                    df_usage, x="Plan Name", y="Users", title="Plan Popularity")
                st.plotly_chart(fig_popular, use_container_width=True)
            with col2:
                fig_share = px.pie(df_usage, names="Plan Name",
                                   values="Users", title="Market Share")
                st.plotly_chart(fig_share, use_container_width=True)

            st.markdown("### 🏆 Top 3 Popular Plans")
            top3 = df_usage.sort_values("Users", ascending=False).head(3)
            for _, row in top3.iterrows():
                st.success(f"{row['Plan Name']} → {row['Users']} users")
        else:
            st.info("📉 No usage data available yet.")

    # --- Tab 6: Admin Tools ---
    with tabs[5]:
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
