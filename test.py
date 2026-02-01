import requests
import uuid
from dotenv import load_dotenv
import os

load_dotenv()  # loads .env into environment variables

# Configuration
BASE_URL = os.getenv("URL", "http://127.0.0.1:8000")

# Generate a unique username so we can run this script multiple times
# without getting "User already registered" errors.
random_id = str(uuid.uuid4())[:8]
USERNAME = f"user_{random_id}"
PASSWORD = "secretpassword"
EMAIL = f"user_{random_id}@example.com"

def test_workflow():
    print(f"--- TESTING USER: {USERNAME} ---")

    # 1. REGISTER
    print("\n[1] Registering User...")
    register_payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "email": EMAIL
    }
    response = requests.post(f"{BASE_URL}/register", json=register_payload)
    
    if response.status_code == 201:
        print("✅ Registration Successful:", response.json())
    else:
        print("❌ Registration Failed:", response.text)
        return

    # 2. LOGIN (Get Token)
    print("\n[2] Logging in to get Access Token...")
    # OAuth2 specifies form-data, not JSON, for the token endpoint
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    response = requests.post(f"{BASE_URL}/token", data=login_data)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access_token"]
        print("✅ Login Successful. Token received.")
        print(f"   Token: {access_token[:20]}...") # Print first 20 chars only
    else:
        print("❌ Login Failed:", response.text)
        return

    # 3. CALL PROTECTED ROUTE (Authorization Header)
    print("\n[3] Accessing Protected Endpoint (/users/me)...")
    
    # This is the key step: Add the 'Authorization' header
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    
    if response.status_code == 200:
        print("✅ Protected Route Accessed Successfully:")
        print("   User Data:", response.json())
    else:
        print("❌ Access Denied:", response.status_code, response.text)

    # 4. CALL DASHBOARD
    print("\n[4] Accessing Dashboard (/dashboard)...")
    response = requests.get(f"{BASE_URL}/dashboard", headers=headers)
    
    if response.status_code == 200:
        print("✅ Dashboard Accessed:", response.json())

    # 5. TEST UNAUTHORIZED ACCESS (Negative Test)
    print("\n[5] Testing Unauthorized Access (No Token)...")
    response = requests.get(f"{BASE_URL}/users/me") # No headers passed
    
    if response.status_code == 401:
        print("✅ Security Check Passed: Request was blocked as expected.")
    else:
        print("❌ Security Check Failed: Request should have been blocked.")

if __name__ == "__main__":
    try:
        # Check if server is running first
        requests.get(f"{BASE_URL}/docs")
        test_workflow()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server.")
        print("   Make sure you are running 'uvicorn main:app --reload' in another terminal.")