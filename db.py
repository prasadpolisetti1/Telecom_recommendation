from pymongo import MongoClient
from datetime import datetime, timedelta
import bcrypt
import random

# --- Connect to MongoDB Atlas ---
client = MongoClient(
    "mongodb+srv://praveenkumar97213_db_user:Praveen%402005@user.bqzpob3.mongodb.net/Telecomdb?retryWrites=true&w=majority&appName=User"
)
db = client["Telecomdb"]

# Collections
users_collection = db["User"]
customer_plans_collection = db["CustomerPlans"]
plans_collection = db["Plans"]

# --- Sample Users (5 customers with hashed passwords) ---
raw_users = [
    {"name": "Ravi Kumar", "email": "ravi@example.com", "password": "Ravi@123"},
    {"name": "Anita Sharma", "email": "anita@example.com", "password": "Anita@123"},
    {"name": "Manoj Reddy", "email": "manoj@example.com", "password": "Manoj@123"},
    {"name": "Priya Singh", "email": "priya@example.com", "password": "Priya@123"},
    {"name": "Arjun Das", "email": "arjun@example.com", "password": "Arjun@123"},
]

sample_users = []
for u in raw_users:
    hashed_pw = bcrypt.hashpw(u["password"].encode("utf-8"), bcrypt.gensalt())
    sample_users.append({
        "name": u["name"],
        "email": u["email"],
        "password": hashed_pw,
        "role": "Customer",
        "approved": True
    })

# Insert Users
users_collection.insert_many(sample_users)

# --- Fetch all available Plans from DB ---
plans = list(plans_collection.find({}))
if not plans:
    raise Exception(
        "⚠️ No plans found in the Plans collection. Please seed plans first!")

# --- Assign 5 plans to each user (1 active + 4 expired) ---
customer_plans = []
for user in sample_users:
    chosen_plans = random.sample(plans, 5) if len(plans) >= 5 else plans

    for idx, plan in enumerate(chosen_plans):
        start_date = datetime(2025, 5, 1) + timedelta(days=30 * idx)
        end_date = start_date + timedelta(days=plan.get("validity_days", 30))

        status = "Active" if idx == len(chosen_plans) - 1 else "Expired"

        customer_plans.append({
            "email": user["email"],
            "name": user["name"],
            "plan_name": plan["plan_name"],
            "monthly_cost": plan["monthly_cost"],
            "data_limit_gb": plan.get("data_limit_gb", 50),
            "usage_gb": random.randint(1, plan.get("data_limit_gb", 50)),
            "validity_days": plan.get("validity_days", 30),
            "status": status,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": None if status == "Active" else end_date.strftime("%Y-%m-%d"),
        })

# Insert into CustomerPlans
customer_plans_collection.insert_many(customer_plans)

print("✅ 5 Customers with 5 plans each created successfully in Telecomdb!")
