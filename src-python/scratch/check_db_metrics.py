from services.database import get_database
db = get_database()
key = 'layer_accuracy_rat_initiation_trend_KNN'
metrics = db.get_recent_metrics(key, limit=10)
print(f"Checking for key: {key}")
print(f"Metrics count: {len(metrics)}")
if metrics:
    print(f"Sample metric: {metrics[0]}")
else:
    print("No metrics found in DB.")
