# import secrets
# import hashlib
# import json
# import os

# KEYS_DB = "api_keys.json"

# def generate_api_key(client_name: str):
#     # 1. Generate secure random raw key with prefix
#     raw_key = f"ak_live_{secrets.token_hex(24)}"
    
#     # 2. Hash raw key using SHA-256
#     key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
#     # 3. Load existing keys database
#     db = {}
#     if os.path.exists(KEYS_DB):
#         with open(KEYS_DB, "r") as f:
#             try:
#                 db = json.load(f)
#             except json.JSONDecodeError:
#                 db = {}
            
#     # 4. Save hashed key (never store raw key)
#     db[key_hash] = {
#         "client_name": client_name,
#         "is_active": True
#     }
    
#     with open(KEYS_DB, "w") as f:
#         json.dump(db, f, indent=4)
        
#     print("=" * 60)
#     print(f"✅ API Key Created for: '{client_name}'")
#     print(f"🔑 RAW API KEY (Give this to developer - SAVE IT NOW):")
#     print(f"    {raw_key}")
#     print(f"🔒 HASH STORED IN DATABASE:")
#     print(f"    {key_hash}")
#     print("=" * 60)

# if __name__ == "__main__":
#     import sys
#     name = sys.argv[1] if len(sys.argv) > 1 else "Demo_Developer"
#     generate_api_key(name)
