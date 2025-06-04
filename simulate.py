import requests
import random
import time

# Replace with your actual API base (no trailing slash)
API_BASE =  "https://njgyhvjif8.execute-api.us-east-1.amazonaws.com/Prod"

# Define “true” conversion rates for each arm (unknown to Lambda)
TRUE_CVR = {
    "arm-1": 0.02,  # price $9.99 → 2% chance
    "arm-2": 0.03,  # price $11.99 → 3% chance
    "arm-3": 0.01   # price $13.99 → 1% chance
}

def get_price():
    resp = requests.get(f"{API_BASE}/getPrice?productId=widget-A")
    return resp.json()

def report_outcome(request_id, bought):
    data = {"requestId": request_id, "bought": bought}
    requests.post(f"{API_BASE}/reportOutcome", json=data)

def simulate_one_user():
    result = get_price()
    arm_id = result['armId']
    request_id = result['requestId']

    # Randomly decide if the “user” actually buys, based on TRUE_CVR
    if random.random() < TRUE_CVR[arm_id]:
        report_outcome(request_id, True)
    else:
        report_outcome(request_id, False)

if __name__ == "__main__":
    for i in range(2000):
        simulate_one_user()
        if i%200==0:
            print(f"Simulated user {i+1}")
        time.sleep(0.05)
