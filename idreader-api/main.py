# import os
# import json
# import secrets
# import hashlib
# from typing import Dict
# from fastapi import FastAPI, Header, HTTPException, Depends, UploadFile, File, Form, status
# from fastapi.responses import HTMLResponse, JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel

# # Initialize App
# app = FastAPI(
#     title="iDReader Developer Portal & API",
#     description="Public API service for document extraction with instant key generation.",
#     version="1.0.0"
# )

# # Enable CORS so developers can call your API from any frontend (web browser, React, etc.)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # File where API keys are stored (JSON-backed for simplicity without external DB setup)
# KEY_STORE_FILE = "api_keys.json"

# # def load_keys() -> Dict[str, dict]:
# #     """Loads hashed API keys from local disk."""
# #     if not os.path.exists(KEY_STORE_FILE):
# #         return {}
# #     try:
# #         with open(KEY_STORE_FILE, "r") as f:
# #             return json.load(f)
# #     except Exception:
# #         return {}
# def load_keys() -> Dict[str, dict]:
#     if not os.path.exists(KEY_STORE_FILE):
#         return {}
#     try:
#         with open(KEY_STORE_FILE, "r") as f:
#             return json.load(f)
#     except Exception:
#         return {}


# def save_keys(keys_data: Dict[str, dict]):
#     """Saves hashed API keys to local disk."""
#     with open(KEY_STORE_FILE, "w") as f:
#         json.dump(keys_data, f, indent=2)

# def hash_key(key: str) -> str:
#     """Hashes API key before storage for basic security."""
#     return hashlib.sha256(key.encode()).hexdigest()


# # --- Dependency: Verify API Key ---
# async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
#     """Validates incoming requests by checking hashed API key header."""
#     if not x_api_key:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Missing 'X-API-Key' header."
#         )
    
#     hashed_input = hash_key(x_api_key)
#     all_keys = load_keys()

#     if hashed_input not in all_keys:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Invalid or revoked API Key."
#         )
    
#     # Check key active state
#     key_info = all_keys[hashed_input]
#     if not key_info.get("is_active", True):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="This API Key has been deactivated."
#         )
    
#     return key_info


# # --- Models ---
# class KeyGenerationRequest(BaseModel):
#     developer_name: str
#     app_name: str

# class KeyGenerationResponse(BaseModel):
#     api_key: str
#     base_url: str
#     message: str


# # --- Public Routes ---

# @app.get("/", response_class=HTMLResponse)
# async def developer_portal():
#     """Serves the self-service web UI where anyone can generate an API key."""
#     return """
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <title>iDReader API Developer Portal</title>
#         <meta name="viewport" content="width=device-width, initial-scale=1">
#         <style>
#             body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f4f6f9; color: #333; margin: 0; padding: 20px; }
#             .container { max-width: 700px; margin: 40px auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
#             h1 { color: #111827; font-size: 24px; margin-bottom: 8px; }
#             p { color: #4b5563; line-height: 1.5; }
#             input[type="text"] { width: 100%; padding: 12px; margin: 8px 0 20px; border: 1px solid #d1d5db; border-radius: 6px; box-sizing: border-box; font-size: 14px; }
#             button { background: #2563eb; color: white; border: none; padding: 12px 20px; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 14px; width: 100%; }
#             button:hover { background: #1d4ed8; }
#             .result-box { margin-top: 25px; padding: 20px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; display: none; }
#             .key-display { font-family: monospace; background: #1e293b; color: #38bdf8; padding: 10px; border-radius: 4px; overflow-x: auto; word-break: break-all; margin: 5px 0 15px; }
#             code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-family: monospace; }
#         </style>
#     </head>
#     <body>
#         <div class="container">
#             <h1>iDReader Developer Portal</h1>
#             <p>Generate a live API key below to integrate document processing into your applications instantly.</p>
            
#             <label><b>Your Name or Organization</b></label>
#             <input type="text" id="devName" placeholder="e.g. Jane Doe" required />

#             <label><b>Application Name</b></label>
#             <input type="text" id="appName" placeholder="e.g. My Identity Verification App" required />

#             <button onclick="generateKey()">Generate Live API Key</button>

#             <div id="result" class="result-box">
#                 <h3 style="margin-top:0; color:#1e40af;">Your Credentials Are Ready!</h3>
#                 <p><b>Your Live API Key:</b> (Save this now! It won't be displayed again)</p>
#                 <div class="key-display" id="generatedKey"></div>

#                 <p><b>API Base Endpoint URL:</b></p>
#                 <div class="key-display" id="apiEndpoint"></div>

#                 <h4>Example Integration (cURL):</h4>
#                 <pre class="key-display" id="curlExample"></pre>
#             </div>
#         </div>

#         <script>
#             async function generateKey() {
#                 const devName = document.getElementById('devName').value.trim();
#                 const appName = document.getElementById('appName').value.trim();

#                 if (!devName || !appName) {
#                     alert('Please fill out both fields.');
#                     return;
#                 }

#                 const response = await fetch('/api/v1/keys/generate', {
#                     method: 'POST',
#                     headers: { 'Content-Type': 'application/json' },
#                     body: JSON.stringify({ developer_name: devName, app_name: appName })
#                 });

#                 if (response.ok) {
#                     const data = await response.json();
#                     document.getElementById('generatedKey').innerText = data.api_key;
#                     document.getElementById('apiEndpoint').innerText = data.base_url + '/api/v1/extract-id';
                    
#                     const curlCmd = `curl -X POST "${data.base_url}/api/v1/extract-id" \\\n  -H "X-API-Key: ${data.api_key}" \\\n  -F "file=@path/to/document.jpg"`;
#                     document.getElementById('curlExample').innerText = curlCmd;
                    
#                     document.getElementById('result').style.display = 'block';
#                 } else {
#                     alert('Error generating API key.');
#                 }
#             }
#         </script>
#     </body>
#     </html>
#     """

# @app.post("/api/v1/keys/generate", response_model=KeyGenerationResponse)
# async def create_key(payload: KeyGenerationRequest):
#     """Generates a new API key and returns endpoint information."""
#     # Generate random key: ak_live_...
#     raw_key = f"ak_live_{secrets.token_urlsafe(24)}"
#     hashed = hash_key(raw_key)

#     # Store hashed key metadata
#     keys_db = load_keys()
#     keys_db[hashed] = {
#         "developer_name": payload.developer_name,
#         "app_name": payload.app_name,
#         "is_active": True
#     }
#     save_keys(keys_db)

#     # Automatically derive the live host URL
#     host_url = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8000")

#     return KeyGenerationResponse(
#         api_key=raw_key,
#         base_url=host_url,
#         message="API Key generated successfully."
#     )


# # --- Protected API Routes (Called by External Developers) ---

# import os
# import json
# from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
# from fastapi.responses import JSONResponse
# import google.generativeai as genai

# # Configure Gemini AI using your environment variable set in Render
# GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY_2")
# if GEMINI_API_KEY:
#     genai.configure(api_key=GEMINI_API_KEY)

# @app.post("/api/v1/extract-id")
# async def extract_id_document(
#     file: UploadFile = File(...),
#     auth_info: dict = Depends(verify_api_key)
# ):
#     try:
#         # 1. Read uploaded image bytes directly from the request
#         file_bytes = await file.read()
        
#         if not file_bytes:
#             raise HTTPException(status_code=400, detail="Uploaded file is empty.")

#         # 2. Prepare Gemini Model (use gemini-2.5-flash or gemini-1.5-flash)
#         # model = genai.GenerativeModel("gemini-2.5-flash")
#         model=ChatG

#         # 3. Format the image payload for Gemini SDK
#         image_part = {
#             "mime_type": file.content_type or "image/jpeg",
#             "data": file_bytes
#         }

#         # 4. Strict extraction prompt forcing JSON format
#         prompt = """
#         You are an expert OCR document extractor. 
#         Analyze the provided document image and extract the following fields in valid JSON format ONLY:
#         {
#           "full_name": "string or null",
#           "dob": "DD/MM/YYYY or null",
#           "gender": "MALE/FEMALE/OTHER or null",
#           "document_type": "Aadhaar/PAN/Passport/etc",
#           "id_number": "string or null"
#         }
#         Do not wrap in markdown fences or add extra text.
#         """

#         # 5. Call Gemini API
#         response = model.generate_content([prompt, image_part])
        
#         # 6. Parse JSON output from Gemini
#         cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
#         extracted_data = json.loads(cleaned_text)

#         # 7. Mask sensitive government ID numbers before returning
#         if "id_number" in extracted_data and extracted_data["id_number"]:
#             extracted_data["id_number"] = "[ID Redacted]"

#         return {
#             "status": "success",
#             "authenticated_as": auth_info.get("developer_name", "Developer"),
#             "extracted_data": extracted_data
#         }

#     except json.JSONDecodeError:
#         # Fallback if Gemini returns plain text instead of structured JSON
#         return {
#             "status": "success",
#             "authenticated_as": auth_info.get("developer_name", "Developer"),
#             "raw_text": response.text
#         }

#     except Exception as e:
#         # Prevents 502 Bad Gateway by catching runtime errors gracefully
#         return JSONResponse(
#             status_code=500,
#             content={
#                 "status": "error",
#                 "detail": f"Document extraction failed: {str(e)}"
#             }
#         )


# # @app.post("/api/v1/extract-id")
# # async def extract_id_document(
# #     file: UploadFile = File(...),
# #     auth_info: dict = Depends(verify_api_key)
# # ):
# #     try:
# #         file_bytes = await file.read()
        
# #         # --- Execute your LangGraph/Gemini Extraction here ---
# #         # extracted_result = run_langgraph_pipeline(file_bytes)
        
# #         return {
# #             "status": "success",
# #             "authenticated_as": auth_info.get("developer_name"),
# #             "extracted_data": {
# #                 "full_name": "Sample Name",
# #                 "dob": "01/01/1990",
# #                 "gender": "MALE",
# #                 "aadhaar_number": "[Aadhaar Redacted]"
# #             }
# #         }
# #     except Exception as err:
# #         # Prevents worker crash and returns readable JSON
# #         return JSONResponse(
# #             status_code=500,
# #             content={"status": "error", "message": f"Extraction failed: {str(err)}"}
# #         )


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




import os
import io
import base64
import json
import secrets
import hashlib
from PIL import Image
from typing import TypedDict, Optional, Literal
from dotenv import load_dotenv

from fastapi import FastAPI, Header, HTTPException, Security, UploadFile, File, status
from fastapi.security import APIKeyHeader
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

# --- ENV & GLOBAL CONFIG ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY_2")
GEMINI_MODEL = "gemini-2.5-flash-lite"
KEYS_DB = "api_keys.json"

app = FastAPI(
    title="iDReader API Service",
    description="Multi-agent document OCR and feature extraction powered by LangGraph",
    version="1.0.0"
)

# Mount static directory for style.css and app.js
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# --- 1. SCHEMAS ---
class AadhaarData(BaseModel):
    full_name: str = Field(description="The full name on the card.")
    dob: str = Field(description="Date of birth in DD/MM/YYYY format.")
    gender: str = Field(description="Gender (Male/Female/Transgender).")
    aadhaar_number: str = Field(description="The 12-digit card number.")

class PANData(BaseModel):
    full_name: str = Field(description="The full name on the PAN card.")
    dob: str = Field(description="Date of birth in DD/MM/YYYY format.")
    pan_number: str = Field(description="The 10-digit alphanumeric PAN number.")

class DrivingLicenseData(BaseModel):
    full_name: str = Field(description="The full name on the driving licence.")
    dob: str = Field(description="Date of birth in DD/MM/YYYY format.")
    licence_number: str = Field(description="Driving licence number.")
    validity: str = Field(description="Validity period of the licence.")

class PassportData(BaseModel):
    full_name: str = Field(description="The full name on the passport.")
    dob: str = Field(description="Date of birth in DD/MM/YYYY format.")
    passport_number: str = Field(description="The passport number.")
    date_of_expiry: str = Field(description="Date of expiry in DD/MM/YYYY format.")

class VoterIDData(BaseModel):
    full_name: str = Field(description="The full name on the voter ID.")
    dob: str = Field(description="Date of birth in DD/MM/YYYY format.")
    voter_id_number: str = Field(description="The voter ID number.")

class KeyGenRequest(BaseModel):
    client_name: str

# --- 2. LANGGRAPH AGENT SETUP ---
class AgentState(TypedDict):
    image_base64: str
    doc_type: Optional[Literal["Aadhaar", "PAN", "Driving License", "Passport", "Voter ID", "Unknown"]]
    extracted_results: Optional[dict]
    error: Optional[str]

llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GEMINI_API_KEY)
aadhaar_extractor = llm.with_structured_output(AadhaarData)
pan_extractor = llm.with_structured_output(PANData)
driving_license_extractor = llm.with_structured_output(DrivingLicenseData)
passport_extractor = llm.with_structured_output(PassportData)
voter_id_extractor = llm.with_structured_output(VoterIDData)

def to_serializable(model):
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()

def supervisor_agent(state: AgentState):
    prompt = "Identify if this image is an 'Aadhaar' card, a 'PAN' card, a 'Driving License', a 'Passport', a 'Voter ID', or 'Unknown'. Respond with ONLY one short phrase."
    message = HumanMessage(content=[
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{state['image_base64']}"}}
    ])
    response = llm.invoke([message]).content.strip().lower()

    if "aadhaar" in response:
        doc_type = "Aadhaar"
    elif "pan" in response:
        doc_type = "PAN"
    elif "driving" in response or "license" in response or "licence" in response:
        doc_type = "Driving License"
    elif "passport" in response:
        doc_type = "Passport"
    elif "voter" in response or "elector" in response:
        doc_type = "Voter ID"
    else:
        doc_type = "Unknown"

    return {"doc_type": doc_type}

def aadhaar_agent(state: AgentState):
    message = HumanMessage(content=[
        {"type": "text", "text": "Extract Name, DOB, Gender, and 12-digit Aadhaar Number."},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{state['image_base64']}"}}
    ])
    try:
        res = aadhaar_extractor.invoke([message])
        return {"extracted_results": to_serializable(res)}
    except Exception as e:
        return {"error": f"Aadhaar Extraction Failed: {str(e)}"}

def pan_agent(state: AgentState):
    message = HumanMessage(content=[
        {"type": "text", "text": "Extract Full Name, DOB, and 10-digit PAN Number."},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{state['image_base64']}"}}
    ])
    try:
        res = pan_extractor.invoke([message])
        return {"extracted_results": to_serializable(res)}
    except Exception as e:
        return {"error": f"PAN Extraction Failed: {str(e)}"}

def driving_license_agent(state: AgentState):
    message = HumanMessage(content=[
        {"type": "text", "text": "Extract full name, DOB, driving licence number, and validity of the licence."},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{state['image_base64']}"}}
    ])
    try:
        res = driving_license_extractor.invoke([message])
        return {"extracted_results": to_serializable(res)}
    except Exception as e:
        return {"error": f"Driving License Extraction Failed: {str(e)}"}

def passport_agent(state: AgentState):
    message = HumanMessage(content=[
        {"type": "text", "text": "Extract full name, DOB, passport number, and date of expiry."},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{state['image_base64']}"}}
    ])
    try:
        res = passport_extractor.invoke([message])
        return {"extracted_results": to_serializable(res)}
    except Exception as e:
        return {"error": f"Passport Extraction Failed: {str(e)}"}

def voter_id_agent(state: AgentState):
    message = HumanMessage(content=[
        {"type": "text", "text": "Extract full name, DOB, and voter ID number."},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{state['image_base64']}"}}
    ])
    try:
        res = voter_id_extractor.invoke([message])
        return {"extracted_results": to_serializable(res)}
    except Exception as e:
        return {"error": f"Voter ID Extraction Failed: {str(e)}"}

def router(state: AgentState):
    doc = state["doc_type"]
    mapping = {
        "Aadhaar": "aadhaar",
        "PAN": "pan",
        "Driving License": "driving_license",
        "Passport": "passport",
        "Voter ID": "voter_id"
    }
    return mapping.get(doc, "end")

builder = StateGraph(AgentState)
builder.add_node("supervisor", supervisor_agent)
builder.add_node("aadhaar", aadhaar_agent)
builder.add_node("pan", pan_agent)
builder.add_node("driving_license", driving_license_agent)
builder.add_node("passport", passport_agent)
builder.add_node("voter_id", voter_id_agent)
builder.set_entry_point("supervisor")
builder.add_conditional_edges("supervisor", router, {
    "aadhaar": "aadhaar", 
    "pan": "pan", 
    "driving_license": "driving_license", 
    "passport": "passport", 
    "voter_id": "voter_id", 
    "end": END
})
builder.add_edge("aadhaar", END)
builder.add_edge("pan", END)
builder.add_edge("driving_license", END)
builder.add_edge("passport", END)
builder.add_edge("voter_id", END)
graph = builder.compile()

# --- 3. KEY STORE HELPER FUNCTIONS ---
def load_keys_store() -> dict:
    if not os.path.exists(KEYS_DB):
        return {}
    try:
        with open(KEYS_DB, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_keys_store(store: dict):
    with open(KEYS_DB, "w") as f:
        json.dump(store, f, indent=2)

# --- 4. AUTHENTICATION DEPENDENCY ---
async def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key in 'X-API-Key' header."
        )
    
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    keys_store = load_keys_store()

    if key_hash not in keys_store or not keys_store[key_hash].get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or inactive API Key."
        )
        
    return keys_store[key_hash].get("client_name", "Developer")

# --- 5. FRONTEND PORTAL ENDPOINTS ---
@app.get("/", response_class=HTMLResponse)
async def portal_page():
    # Serves static/index.html if present, else renders the HTML string directly
    if os.path.exists("static/index.html"):
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    elif os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()

    return HTMLResponse(content="<h1>Index file not found.</h1>", status_code=404)

# Endpoint matching fetch('/api/v1/generate-key') in app.js
@app.post("/api/v1/generate-key")
async def generate_api_key(payload: KeyGenRequest):
    raw_key = f"ak_live_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    store = load_keys_store()
    store[key_hash] = {
        "client_name": payload.client_name,
        "is_active": True
    }
    save_keys_store(store)
    
    return {
        "status": "success",
        "api_key": raw_key,
        "client_name": payload.client_name
    }

# --- 6. CORE EXTRACTION API ENDPOINT ---
@app.post("/api/v1/extract-id")
async def extract_id_details(
    file: UploadFile = File(...),
    client_name: str = Security(verify_api_key)
):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGB")
            
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=80)
        img_b64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Execute LangGraph workflow
        result = graph.invoke({"image_base64": img_b64})
        extracted_data = result.get("extracted_results") or {}

        # Safeguard Redaction
        if "aadhaar_number" in extracted_data:
            extracted_data["aadhaar_number"] = "[Aadhaar Redacted]"

        return {
            "status": "success",
            "authenticated_as": client_name,
            "document_type": result.get("doc_type"),
            "extracted_data": extracted_data,
            "error": result.get("error")
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Extraction failed: {str(e)}"}
        )

