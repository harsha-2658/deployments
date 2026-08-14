import os
import io
import base64
import json
import hashlib
from PIL import Image
from typing import TypedDict, Optional, Literal
from dotenv import load_dotenv

from fastapi import FastAPI, Header, HTTPException, Security, UploadFile, File, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY_2")
GEMINI_MODEL = "gemini-2.5-flash-lite"
KEYS_DB = "api_keys.json"

app = FastAPI(
    title="iDReader API Service",
    description="Multi-agent document OCR and feature extraction powered by LangGraph",
    version="1.0.0"
)

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

# --- 3. AUTHENTICATION DEPENDENCY ---
async def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key in 'X-API-Key' header."
        )
    
    # Hash incoming key and match with stored database hashes
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    if not os.path.exists(KEYS_DB):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Key database not initialized."
        )

    with open(KEYS_DB, "r") as f:
        keys_store = json.load(f)

    if key_hash not in keys_store or not keys_store[key_hash].get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or inactive API Key."
        )
        
    return keys_store[key_hash]["client_name"]

# --- 4. API ENDPOINT ---
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
        
        return {
            "status": "success",
            "authenticated_as": client_name,
            "document_type": result.get("doc_type"),
            "extracted_data": result.get("extracted_results"),
            "error": result.get("error")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))