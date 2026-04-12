from fastapi import FastAPI, HTTPException,Security, HTTPException, Depends
from typing import List, Dict, Any
from fastapi.security.api_key import APIKeyHeader
import db
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
SECRET_KEY_NAME = "X-API-Key"

api_key_header = APIKeyHeader(name=SECRET_KEY_NAME, auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key is None:
        raise HTTPException(status_code=401, detail="API key missing")

    if api_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return api_key

app = FastAPI(
    title="Take-Home API",
    version="0.1.0",
    dependencies=[Depends(get_api_key)]
)

# -----------------------------
# Health Check
# -----------------------------
@app.get("/")
def root():
    return {"message": "API is running"}


# -----------------------------
# Get All Data
# -----------------------------
@app.get("/data", response_model=List[Dict[str, Any]])
def get_all_data():
    try:
        return db.fetch_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Get Single Item (Optional)
# -----------------------------
@app.get("/data/{item_id}", response_model=Dict[str, Any])
def get_item(item_id: str):
    try:
        data = db.get_item_by_id(item_id)

        if not data:
            raise HTTPException(status_code=404, detail="Item not found")

        return data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Create Item (Optional)
# -----------------------------
@app.post("/data", response_model=Dict[str, Any])
def create_item(item: Dict[str, Any]):
    """
    This assumes you will later implement db.insert_data().
    For now, it's a placeholder.
    """
    try:
        # Example placeholder logic
        return {
            "message": "Item received (not yet stored in DB)",
            "data": item
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))