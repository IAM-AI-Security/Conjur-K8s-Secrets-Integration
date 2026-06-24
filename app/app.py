import os
import time

print("=== Conjur Kubernetes Authentication Demo ===")
print(f"Pod is running in namespace: demo-app")
print(f"Service account: conjur-demo")

db_password = os.environ.get('DB_PASSWORD', 'NOT FOUND')

if db_password != 'NOT FOUND':
    print(f"SUCCESS: Secret retrieved from Conjur via Kubernetes identity")
    print(f"DB_PASSWORD retrieved: {len(db_password)} characters")
    print(f"DB_PASSWORD value: [REDACTED - secret retrieved successfully]")
else:
    print("FAILED: Could not retrieve secret from Conjur")

print("=== Demo Complete ===")

while True:
    time.sleep(60)
