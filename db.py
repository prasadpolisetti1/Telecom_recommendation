from pymongo import MongoClient
from datetime import datetime

# --- Connect to MongoDB Atlas ---
client = MongoClient(
    "mongodb+srv://praveenkumar97213_db_user:Praveen%402005@user.bqzpob3.mongodb.net/Telecomdb?retryWrites=true&w=majority&appName=User"
)
db = client["Telecomdb"]

# Collections
users_collection = db["User"]
customer_plans_collection = db["CustomerPlans"]

# --- Create 15 Sample Users ---
sample_users = [
    {"email": f"customer{i}@example.com", "password": "hashed_password",
        "role": "Customer", "approved": True}
    for i in range(1, 16)
]

# Insert Users
users_collection.insert_many(sample_users)

# --- Sample Plans ---
plans = [
    {"plan_name": "Basic Plan", "monthly_cost": 199},
    {"plan_name": "Standard Plan", "monthly_cost": 299},
    {"plan_name": "Premium Plan", "monthly_cost": 499},
    {"plan_name": "Family Plan", "monthly_cost": 699},
    {"plan_name": "Unlimited Plan", "monthly_cost": 999}
]

# --- Assign Customer Plans ---
customer_plans = []
for i, user in enumerate(sample_users, start=1):
    plan = plans[i % len(plans)]  # rotate through available plans
    customer_plans.append({
        "email": user["email"],
        "plan_name": plan["plan_name"],
        "monthly_cost": plan["monthly_cost"],
        "usage_gb": (i * 10) % 200,  # mock usage
        "start_date": datetime(2025, 9, 1).strftime("%Y-%m-%d"),
        "end_date": None,
        "status": "Active",
        "previous_plans": [
            {
                "plan_name": "Basic Plan",
                "monthly_cost": 199,
                "usage_gb": (i * 5) % 100,
                "start_date": "2025-07-01",
                "end_date": "2025-08-31"
            }
        ]
    })

# Insert into CustomerPlans
customer_plans_collection.insert_many(customer_plans)

print("✅ 15 Customers with plans created successfully in Telecomdb!")
