import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from db import recharges_col, plans_col


def _build_user_plan_matrix():


docs = list(recharges_col.find({}, {"user_email": 1, "plan_id": 1}))
if not docs:
return pd.DataFrame()
df = pd.DataFrame(docs)
df['count'] = 1
mat = df.pivot_table(index='user_email', columns='plan_id',
                     values='count', aggfunc='sum', fill_value=0)
return mat


def recommend_plans_for_user(user_email, top_k=3, n_similar=5):


mat = _build_user_plan_matrix()
if mat.empty:
    # fallback: top popular plans
return list(plans_col.find({}).sort([("popularity", -1)]).limit(top_k))


if user_email not in mat.index:
    # cold start -> popular
return list(plans_col.find({}).sort([("popularity", -1)]).limit(top_k))


sims = cosine_similarity(mat)
sims_df = pd.DataFrame(sims, index=mat.index, columns=mat.index)


sim_scores = sims_df[user_email].sort_values(ascending=False)
sim_scores = sim_scores.drop(user_email, errors='ignore')
top_users = sim_scores.head(n_similar).index.tolist()


if not top_users:
return list(plans_col.find({}).sort([("popularity", -1)]).limit(top_k))


neighbors_usage = mat.loc[top_users].sum(axis=0)
user_usage = mat.loc[user_email]


candidates = neighbors_usage[user_usage == 0]
if candidates.empty:
candidates = neighbors_usage


candidates = candidates.sort_values(ascending=False)
recommended_plan_ids = candidates.head(top_k).index.tolist()


# fetch plan documents
plans = []
for pid in recommended_plan_ids:
p = plans_col.find_one({"plan_id": pid})
if p:
plans.append(p)
if not plans:
return list(plans_col.find({}).limit(top_k))
return plans
