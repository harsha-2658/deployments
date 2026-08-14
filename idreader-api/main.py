import os
import json
import secrets
import hashlib
from typing import Dict
from fastapi import FastAPI, Header, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Initialize App
app = FastAPI(
    title="iDReader Developer Portal & API",
    description="Public API service for document extraction with instant key generation.",
    version="1.0.0"
)

# Enable CORS so developers can call your API from any frontend (web browser, React, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File where API keys are stored (JSON-backed for simplicity without external DB setup)
KEY_STORE_FILE = "api_keys.json"

# def load_keys() -> Dict[str, dict]:
#     """Loads hashed API keys from local disk."""
#     if not os.path.exists(KEY_STORE_FILE):
#         return {}
#     try:
#         with open(KEY_STORE_FILE, "r") as f:
#             return json.load(f)
#     except Exception:
#         return {}
def load_keys() -> Dict[str, dict]:
    if not os.path.exists(KEY_STORE_FILE):
        return {}
    try:
        with open(KEY_STORE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_keys(keys_data: Dict[str, dict]):
    """Saves hashed API keys to local disk."""
    with open(KEY_STORE_FILE, "w") as f:
        json.dump(keys_data, f, indent=2)

def hash_key(key: str) -> str:
    """Hashes API key before storage for basic security."""
    return hashlib.sha256(key.encode()).hexdigest()


# --- Dependency: Verify API Key ---
async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Validates incoming requests by checking hashed API key header."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing 'X-API-Key' header."
        )
    
    hashed_input = hash_key(x_api_key)
    all_keys = load_keys()

    if hashed_input not in all_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or revoked API Key."
        )
    
    # Check key active state
    key_info = all_keys[hashed_input]
    if not key_info.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This API Key has been deactivated."
        )
    
    return key_info


# --- Models ---
class KeyGenerationRequest(BaseModel):
    developer_name: str
    app_name: str

class KeyGenerationResponse(BaseModel):
    api_key: str
    base_url: str
    message: str


# --- Public Routes ---

@app.get("/", response_class=HTMLResponse)
async def developer_portal():
    """Serves the self-service web UI where anyone can generate an API key."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>iDReader API Developer Portal</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f4f6f9; color: #333; margin: 0; padding: 20px; }
            .container { max-width: 700px; margin: 40px auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
            h1 { color: #111827; font-size: 24px; margin-bottom: 8px; }
            p { color: #4b5563; line-height: 1.5; }
            input[type="text"] { width: 100%; padding: 12px; margin: 8px 0 20px; border: 1px solid #d1d5db; border-radius: 6px; box-sizing: border-box; font-size: 14px; }
            button { background: #2563eb; color: white; border: none; padding: 12px 20px; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 14px; width: 100%; }
            button:hover { background: #1d4ed8; }
            .result-box { margin-top: 25px; padding: 20px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; display: none; }
            .key-display { font-family: monospace; background: #1e293b; color: #38bdf8; padding: 10px; border-radius: 4px; overflow-x: auto; word-break: break-all; margin: 5px 0 15px; }
            code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-family: monospace; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>iDReader Developer Portal</h1>
            <p>Generate a live API key below to integrate document processing into your applications instantly.</p>
            
            <label><b>Your Name or Organization</b></label>
            <input type="text" id="devName" placeholder="e.g. Jane Doe" required />

            <label><b>Application Name</b></label>
            <input type="text" id="appName" placeholder="e.g. My Identity Verification App" required />

            <button onclick="generateKey()">Generate Live API Key</button>

            <div id="result" class="result-box">
                <h3 style="margin-top:0; color:#1e40af;">Your Credentials Are Ready!</h3>
                <p><b>Your Live API Key:</b> (Save this now! It won't be displayed again)</p>
                <div class="key-display" id="generatedKey"></div>

                <p><b>API Base Endpoint URL:</b></p>
                <div class="key-display" id="apiEndpoint"></div>

                <h4>Example Integration (cURL):</h4>
                <pre class="key-display" id="curlExample"></pre>
            </div>
        </div>

        <script>
            async function generateKey() {
                const devName = document.getElementById('devName').value.trim();
                const appName = document.getElementById('appName').value.trim();

                if (!devName || !appName) {
                    alert('Please fill out both fields.');
                    return;
                }

                const response = await fetch('/api/v1/keys/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ developer_name: devName, app_name: appName })
                });

                if (response.ok) {
                    const data = await response.json();
                    document.getElementById('generatedKey').innerText = data.api_key;
                    document.getElementById('apiEndpoint').innerText = data.base_url + '/api/v1/extract-id';
                    
                    const curlCmd = `curl -X POST "${data.base_url}/api/v1/extract-id" \\\n  -H "X-API-Key: ${data.api_key}" \\\n  -F "file=@path/to/document.jpg"`;
                    document.getElementById('curlExample').innerText = curlCmd;
                    
                    document.getElementById('result').style.display = 'block';
                } else {
                    alert('Error generating API key.');
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/api/v1/keys/generate", response_model=KeyGenerationResponse)
async def create_key(payload: KeyGenerationRequest):
    """Generates a new API key and returns endpoint information."""
    # Generate random key: ak_live_...
    raw_key = f"ak_live_{secrets.token_urlsafe(24)}"
    hashed = hash_key(raw_key)

    # Store hashed key metadata
    keys_db = load_keys()
    keys_db[hashed] = {
        "developer_name": payload.developer_name,
        "app_name": payload.app_name,
        "is_active": True
    }
    save_keys(keys_db)

    # Automatically derive the live host URL
    host_url = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8000")

    return KeyGenerationResponse(
        api_key=raw_key,
        base_url=host_url,
        message="API Key generated successfully."
    )


# --- Protected API Routes (Called by External Developers) ---

@app.post("/api/v1/extract-id")
async def extract_id_document(
    file: UploadFile = File(...),
    auth_info: dict = Depends(verify_api_key)
):
    try:
        file_bytes = await file.read()
        
        # --- Execute your LangGraph/Gemini Extraction here ---
        # extracted_result = run_langgraph_pipeline(file_bytes)
        
        return {
            "status": "success",
            "authenticated_as": auth_info.get("developer_name"),
            "extracted_data": {
                "full_name": "Sample Name",
                "dob": "01/01/1990",
                "gender": "MALE",
                "aadhaar_number": "[Aadhaar Redacted]"
            }
        }
    except Exception as err:
        # Prevents worker crash and returns readable JSON
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Extraction failed: {str(err)}"}
        )


# @app.post("/api/v1/extract-id")
# async def extract_id_document(
#     file: UploadFile = File(...),
#     auth_info: dict = Depends(verify_api_key)
# ):
#     """
#     Public document extraction endpoint.
#     Protected by X-API-Key header.
#     """
#     try:
#         file_bytes = await file.read()
        
#         # --- Run your LangGraph / Gemini processing logic here ---
#         # (Placeholder response demonstrating authenticated response)
        
#         return {
#             "status": "success",
#             "authenticated_app": auth_info["app_name"],
#             "filename": file.filename,
#             "extracted_data": {
#                 "document_type": "Identity Document",
#                 "status": "Processed"
#             }
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
