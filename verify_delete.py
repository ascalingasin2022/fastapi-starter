import requests
import time
import random
import sys

print(sys.path)

BASE_URL = "http://localhost:8000/api/v1"

def register_user(prefix):
    suffix = random.randint(1000, 9999)
    username = f"{prefix}_{suffix}"
    password = "Password123"
    email = f"{username}@example.com"
    
    resp = requests.post(f"{BASE_URL}/auth/register", json={
        "username": username,
        "password": password,
        "email": email,
        "first_name": "Test",
        "last_name": "User"
    })
    
    if resp.status_code == 200:
        return resp.json(), password
    else:
        print(f"Failed to register {username}: {resp.text}")
        return None, None

def test_delete():
    print("--- 1. Setup Users ---")
    victim, victim_pass = register_user("victim")
    attacker, attacker_pass = register_user("attacker")
    
    if not victim or not attacker:
        print("Setup failed")
        return

    print(f"Victim: {victim['username']} (ID: {victim['id']})")
    print(f"Attacker: {attacker['username']} (ID: {attacker['id']})")

    # 2. Attacker tries to delete Victim
    print("\n--- 2. Unauthorized Delete (Attacker -> Victim) ---")
    resp = requests.delete(
        f"{BASE_URL}/users/{victim['id']}",
        auth=(attacker['username'], attacker_pass)
    )
    if resp.status_code == 403:
        print("✅ Correctly Forbidden (403)")
    else:
        print(f"❌ Unexpected status: {resp.status_code} {resp.text}")

    # 3. Victim tries to delete Self (Soft Delete)
    print("\n--- 3. Authorized Self-Delete (Victim -> Victim) ---")
    resp = requests.delete(
        f"{BASE_URL}/users/{victim['id']}",
        auth=(victim['username'], victim_pass)
    )
    
    if resp.status_code == 200:
        print("✅ Delete Success (200)")
        data = resp.json()['data']
        if data['is_active'] == False:
             print("✅ User is_active = False (Soft Deleted)")
        else:
             print(f"❌ User is_active is {data.get('is_active')}")
    else:
        print(f"❌ Delete Failed: {resp.status_code} {resp.text}")

    # 4. Verify Access Revoked
    print("\n--- 4. Verify Login with Deleted Account ---")
    # Try to access a protected endpoint (DELETE again)
    print("\n--- 4. Verify Login with Deleted Account (Try DELETE again) ---")
    resp = requests.delete(
        f"{BASE_URL}/users/{victim['id']}",
        auth=(victim['username'], victim_pass)
    )
    # Authorization dependency `get_current_active_user` throws 400 if inactive
    if resp.status_code == 400 and "Inactive user" in resp.text:
         print("✅ Access Denied (Inactive User)")
    elif resp.status_code == 401:
         print("✅ Access Denied (401)")
    else:
         print(f"❌ Unexpected Access: {resp.status_code}")

if __name__ == "__main__":
    test_delete()
