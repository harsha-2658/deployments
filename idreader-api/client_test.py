import os
import requests

# 1. Base URL (Domain only)
BASE_URL = "https://id-reader-u4dc.onrender.com"

# 2. API Key
API_KEY = "ak_live_0517ff602fd6c48e2b44ef6b9e79715346ba915fb5c09ebe"

# 3. Local file path
IMAGE_PATH = "C:/Users/SriHarsha/Desktop/POC/End_to_end/aadhar_images/aadhar_card.png"

def process_id_document(image_file_path: str):
    endpoint = f"{BASE_URL}/api/v1/extract-id"
    headers = {"X-API-Key": API_KEY}

    try:
        filename = os.path.basename(image_file_path)
        with open(image_file_path, "rb") as file_data:
            files = {"file": (filename, file_data, "image/png")}
            
            print("Sending request to live API...")
            response = requests.post(endpoint, headers=headers, files=files)
            
            if response.status_code == 200:
                print("--- Extraction Successful ---")
                print(response.json())
            else:
                print(f"Error {response.status_code}: {response.text}")

    except FileNotFoundError:
        print(f"Error: Could not find file at '{image_file_path}'. Check the file path and try again.")

if __name__ == "__main__":
    process_id_document(IMAGE_PATH)



# import requests

# # 1. API Configuration
# API_URL = "http://127.0.0.1:8000/api/v1/extract-id"
# API_KEY = "ak_live_83195ad1198c8049d38800da9e734683e49d5c2a42422888"  # Replace with generated key
# IMAGE_PATH = "C:/Users/SriHarsha/Desktop/POC/End_to_end/aadhar_images/aadhar_card.png"            # Replace with path to test image

# # 2. Set API Key Header
# headers = {
#     "X-API-Key": API_KEY
# }

# # 3. Attach image file
# files = {
#     "file": ("document.jpg", open(IMAGE_PATH, "rb"), "image/jpeg")
# }

# # 4. Make HTTP POST Request
# print("Sending request to iDReader API...")
# response = requests.post(API_URL, headers=headers, files=files)

# # 5. Display Response
# if response.status_code == 200:
#     print("\n✅ Success!")
#     print(response.json())
# else:
#     print(f"\n❌ Request failed with status {response.status_code}:")
#     print(response.json())