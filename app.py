from sklearn.neighbors import NearestNeighbors
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

    # --- Analysts Subtab ---
    with subtab1:
        analysts = list(users_collection.find(
            {"approved": True, "role": "Analyst"}, {"password": 0}))
        if analysts:
            for a in analysts:
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.write(f"**{a.get('name', '')}** — {a['email']}")
                with col2:
                    edit_key = f"edit_{a['email']}"
                    if st.button("✏️ Edit", key=edit_key):
                        st.session_state["edit_email"] = a['email']

                # Show edit form only for the selected user
                if st.session_state.get("edit_email") == a['email']:
                    with st.form(f"edit_form_{a['email']}"):
                        new_name = st.text_input(
                            "Name", value=a.get('name', ''))
                        new_email = st.text_input("Email", value=a['email'])
                        submit_edit = st.form_submit_button("Update")
                        if submit_edit:
                            users_collection.update_one(
                                {"email": a['email']},
                                {"$set": {"name": new_name, "email": new_email}}
                            )
                            st.success(f"✅ Updated {new_email}")
                            del st.session_state["edit_email"]
                            st.experimental_rerun = lambda: None  # Dummy, Streamlit reruns automatically
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{a['email']}"):
                        users_collection.delete_one({"email": a['email']})
                        st.warning(f"Deleted {a['email']}")
                        st.experimental_rerun = lambda: None  # Dummy, Streamlit reruns automatically
        else:
            st.info("No analysts found.")

    # --- Customers Subtab ---
    with subtab2:
        customers = list(users_collection.find(
            {"approved": True, "role": "Customer"}, {"password": 0}))
        if customers:
            for c in customers:
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.write(f"**{c.get('name', '')}** — {c['email']}")
                with col2:
                    edit_key = f"edit_{c['email']}"
                    if st.button("✏️ Edit", key=edit_key):
                        st.session_state["edit_email"] = c['email']

                if st.session_state.get("edit_email") == c['email']:
                    with st.form(f"edit_form_{c['email']}"):
                        new_name = st.text_input(
                            "Name", value=c.get('name', ''))
                        new_email = st.text_input("Email", value=c['email'])
                        submit_edit = st.form_submit_button("Update")
                        if submit_edit:
                            users_collection.update_one(
                                {"email": c['email']},
                                {"$set": {"name": new_name, "email": new_email}}
                            )
                            st.success(f"✅ Updated {new_email}")
                            del st.session_state["edit_email"]
                            st.experimental_rerun = lambda: None
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{c['email']}"):
                        users_collection.delete_one({"email": c['email']})
                        st.warning(f"Deleted {c['email']}")
                        st.experimental_rerun = lambda: None
        else:
            st.info("No customers found.")

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

    # --- Total approved customers ---
    total_customers = users_collection.count_documents(
        {"role": "Customer", "approved": True})

    # --- Customer plan data ---
    customer_plans = list(db["CustomerPlans"].find({}))
    df_customer = pd.DataFrame(customer_plans)

    # --- Key Metrics ---
    col1, col2, col3 = st.columns(3)
    col1.metric("✅ Approved Customers", total_customers)
    col2.metric("📦 Active Subscriptions", len(df_customer))
    col3.metric("💰 Total Revenue", df_customer["monthly_cost"].sum(
    ) if not df_customer.empty else 0)

    if not df_customer.empty:
        # =====================
        # ACTIVE PLANS OVERVIEW
        # =====================
        st.markdown("### 📌 Currently Active Plans")
        active_df = df_customer[df_customer["status"] == "Active"]
        st.dataframe(
            active_df[["email", "plan_name", "monthly_cost", "usage_gb", "start_date"]])

        # =====================
        # PLAN DISTRIBUTION
        # =====================
        st.markdown("### 📝 Plan Distribution")
        plan_counts = active_df["plan_name"].value_counts().reset_index()
        plan_counts.columns = ["Plan Name", "Users"]
        fig1 = px.pie(plan_counts, names="Plan Name",
                      values="Users", title="Plan Popularity")
        st.plotly_chart(fig1, use_container_width=True)

        # =====================
        # REVENUE ANALYSIS
        # =====================
        st.markdown("### 💰 Revenue Insights")
        revenue_per_plan = active_df.groupby(
            "plan_name")["monthly_cost"].sum().reset_index()
        fig2 = px.bar(revenue_per_plan, x="plan_name", y="monthly_cost",
                      title="Revenue per Plan", color="plan_name")
        st.plotly_chart(fig2, use_container_width=True)

        # Revenue share
        fig3 = px.pie(revenue_per_plan, names="plan_name", values="monthly_cost",
                      title="Revenue Share by Plan")
        st.plotly_chart(fig3, use_container_width=True)

        # =====================
        # CUSTOMER PLAN HISTORY
        # =====================
        st.markdown("### 📜 Customer Previous Plans Usage")
        history_records = []
        for _, row in df_customer.iterrows():
            prev_plans = row.get("previous_plans", [])
            for p in prev_plans:
                history_records.append({
                    "email": row["email"],
                    "plan_name": p["plan_name"],
                    "monthly_cost": p["monthly_cost"],
                    "usage_gb": p["usage_gb"],
                    "start_date": p["start_date"],
                    "end_date": p["end_date"]
                })

        if history_records:
            df_history = pd.DataFrame(history_records)
            st.dataframe(df_history)

            # Visualize usage trend per customer
            fig4 = px.line(df_history, x="start_date", y="usage_gb",
                           color="email", title="Customer Previous Plan Usage Over Time")
            st.plotly_chart(fig4, use_container_width=True)

        else:
            st.info("No previous plan history available.")

    else:
        st.info("No customer plan data available yet.")


# -----------------
# CUSTOMER DASHBOARD
# -----------------


def customer_dashboard(user):
    st.subheader("👤 Customer Dashboard")
    st.write(f"Welcome, **{user.get('name')}** ({user.get('email')})")

    tabs = st.tabs([
        "📝 Profile",
        "📦 Current Plan",
        "📜 Previous Plans",
        "🤖 Recommendations"
    ])

    # --- Tab 1: Profile ---
    with tabs[0]:
        st.markdown("### 📝 Your Profile")

        # Show profile in table format
        profile_data = {
            "Name": [user.get("name", "")],
            "Email": [user.get("email", "")]
        }
        st.table(pd.DataFrame(profile_data))

        # Edit profile option
        st.markdown("### ✏️ Edit Profile")
        with st.form("edit_profile"):
            new_name = st.text_input("Name", user.get("name", ""))
            new_email = st.text_input("Email", user.get("email", ""))
            submit_profile = st.form_submit_button("💾 Update Profile")

        if submit_profile:
            users_collection.update_one(
                {"email": user["email"]},
                {"$set": {"name": new_name, "email": new_email}}
            )
            st.success("✅ Profile updated! Please refresh.")

    # --- Tab 2: Current Plan ---
    with tabs[1]:
        st.markdown("### 📦 Current Active Plan")
        current_plan = db["CustomerPlans"].find_one(
            {"email": user["email"], "status": "Active"}
        )
        if current_plan:
            st.success(
                f"**{current_plan['plan_name']}** — ₹{current_plan['monthly_cost']} for {current_plan['validity_days']} days"
            )

            # Show plan details in table format
            plan_data = {
                "Plan Name": [current_plan.get("plan_name", "")],
                "Monthly Cost (₹)": [current_plan.get("monthly_cost", 0)],
                "Data Limit (GB)": [current_plan.get("data_limit_gb", 0)],
                "Usage (GB)": [current_plan.get("usage_gb", 0)],
                "Validity (Days)": [current_plan.get("validity_days", 0)],
                "Start Date": [current_plan.get("start_date", "")],
                "End Date": [current_plan.get("end_date", "")]
            }
            st.table(pd.DataFrame(plan_data))

            # Usage visualization
            st.markdown("#### 📊 Current Usage")
            usage_df = pd.DataFrame([{
                "Data Used (GB)": current_plan["usage_gb"],
                "Data Left (GB)": current_plan["data_limit_gb"] - current_plan["usage_gb"]
            }])
            fig = px.pie(
                usage_df.melt(),
                names="variable",
                values="value",
                title="Data Usage Split"
            )
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("No active plan found.")

    # --- Tab 3: Previous Plans ---
    with tabs[2]:
        st.markdown("### 📜 Previous Plans")
        prev_plans = db["CustomerPlans"].find(
            {"email": user["email"], "status": "Expired"}
        )
        prev_df = pd.DataFrame(list(prev_plans))
        if not prev_df.empty:
            st.dataframe(
                prev_df[["plan_name", "monthly_cost", "usage_gb", "start_date", "end_date"]])

            # Usage trend
            fig2 = px.line(prev_df, x="start_date", y="usage_gb",
                           title="Usage Over Time", markers=True)
            st.plotly_chart(fig2, use_container_width=True)

            # Cost vs Usage
            fig3 = px.scatter(prev_df, x="monthly_cost", y="usage_gb", size="usage_gb",
                              text="plan_name", title="Cost vs Usage")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No previous plan history found.")

    # --- Tab 4: Recommendations ---
    with tabs[3]:
        st.markdown("### 🎯 Plan Recommendations")

        # ---------------- Manual Recommendation ----------------
        st.markdown("#### ✋ Manual Input Recommendation")
        budget = st.slider("Your Budget (₹)", 100, 2000, 500)
        data_need = st.slider("Expected Data (GB)", 1, 200, 20)
        validity = st.slider("Validity (Days)", 1, 90, 28)

        if st.button("🔍 Find Matching Plans"):
            match_plans = list(db["Plans"].find({
                "monthly_cost": {"$lte": budget},
                "data_limit_gb": {"$gte": data_need},
                "validity_days": {"$gte": validity}
            }))

            if match_plans:
                df_match = pd.DataFrame(match_plans).drop(columns=["_id"])
                st.dataframe(df_match)

                # Select plan to buy
                plan_names = [p["plan_name"] for p in match_plans]
                selected_plan = st.selectbox(
                    "Choose a plan to buy", plan_names)

                if st.button("🛒 Buy Selected Plan"):
                    chosen = next(
                        p for p in match_plans if p["plan_name"] == selected_plan)

                    active_plan = db["CustomerPlans"].find_one(
                        {"email": user["email"]})
                    if active_plan:
                        # Push current active plan to previous_plans
                        prev = {
                            "plan_name": active_plan["plan_name"],
                            "monthly_cost": active_plan["monthly_cost"],
                            "usage_gb": active_plan["usage_gb"],
                            "start_date": active_plan["start_date"],
                            "end_date": str(pd.Timestamp.now())
                        }
                        db["CustomerPlans"].update_one(
                            {"email": user["email"]},
                            {
                                "$push": {"previous_plans": prev},
                                "$set": {
                                    "plan_name": chosen["plan_name"],
                                    "monthly_cost": chosen["monthly_cost"],
                                    "data_limit_gb": chosen["data_limit_gb"],
                                    "usage_gb": 0,
                                    "validity_days": chosen["validity_days"],
                                    "status": "Active",
                                    "start_date": str(pd.Timestamp.now().date()),
                                    "end_date": str((pd.Timestamp.now() + pd.Timedelta(days=chosen["validity_days"])).date())
                                }
                            }
                        )
                    else:
                        # First plan purchase
                        db["CustomerPlans"].insert_one({
                            "email": user["email"],
                            "plan_name": chosen["plan_name"],
                            "monthly_cost": chosen["monthly_cost"],
                            "data_limit_gb": chosen["data_limit_gb"],
                            "usage_gb": 0,
                            "validity_days": chosen["validity_days"],
                            "status": "Active",
                            "start_date": str(pd.Timestamp.now().date()),
                            "end_date": str((pd.Timestamp.now() + pd.Timedelta(days=chosen["validity_days"])).date()),
                            "previous_plans": []
                        })

                    st.success(
                        f"✅ You have successfully purchased **{chosen['plan_name']}**")

            else:
                st.warning("No matching plans found!")

        # ---------------- ML Recommendation ----------------
        st.markdown("#### 🤖 AI-Based Recommendation")

        all_plans = list(db["Plans"].find({}))
        df_plans = pd.DataFrame(all_plans)

        if not df_plans.empty:
            features = df_plans[["monthly_cost",
                                 "data_limit_gb", "validity_days"]]
            model = NearestNeighbors(n_neighbors=3)
            model.fit(features)

            last_plan = db["CustomerPlans"].find_one({"email": user["email"]})

            if last_plan:
                query = [[last_plan["monthly_cost"],
                          last_plan["data_limit_gb"], last_plan["validity_days"]]]
                distances, indices = model.kneighbors(query)
                recommended = df_plans.iloc[indices[0]]
                st.success("Based on your past usage, we recommend:")
                st.dataframe(recommended)

                rec_plan_names = recommended["plan_name"].tolist()
                rec_selected = st.selectbox(
                    "Choose a recommended plan to buy", rec_plan_names, key="rec")

                if st.button("🛒 Buy Recommended Plan"):
                    chosen = df_plans[df_plans["plan_name"]
                                      == rec_selected].iloc[0].to_dict()

                    active_plan = db["CustomerPlans"].find_one(
                        {"email": user["email"]})
                    if active_plan:
                        prev = {
                            "plan_name": active_plan["plan_name"],
                            "monthly_cost": active_plan["monthly_cost"],
                            "usage_gb": active_plan["usage_gb"],
                            "start_date": active_plan["start_date"],
                            "end_date": str(pd.Timestamp.now())
                        }
                        db["CustomerPlans"].update_one(
                            {"email": user["email"]},
                            {
                                "$push": {"previous_plans": prev},
                                "$set": {
                                    "plan_name": chosen["plan_name"],
                                    "monthly_cost": chosen["monthly_cost"],
                                    "data_limit_gb": chosen["data_limit_gb"],
                                    "usage_gb": 0,
                                    "validity_days": chosen["validity_days"],
                                    "status": "Active",
                                    "start_date": str(pd.Timestamp.now().date()),
                                    "end_date": str((pd.Timestamp.now() + pd.Timedelta(days=chosen["validity_days"])).date())
                                }
                            }
                        )
                    else:
                        db["CustomerPlans"].insert_one({
                            "email": user["email"],
                            "plan_name": chosen["plan_name"],
                            "monthly_cost": chosen["monthly_cost"],
                            "data_limit_gb": chosen["data_limit_gb"],
                            "usage_gb": 0,
                            "validity_days": chosen["validity_days"],
                            "status": "Active",
                            "start_date": str(pd.Timestamp.now().date()),
                            "end_date": str((pd.Timestamp.now() + pd.Timedelta(days=chosen["validity_days"])).date()),
                            "previous_plans": []
                        })

                    st.success(
                        f"✅ You have successfully purchased **{chosen['plan_name']}**")
            else:
                st.info("Not enough history for ML-based recommendation.")

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
