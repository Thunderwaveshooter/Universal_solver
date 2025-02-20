from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import sympy as sp
import pytesseract
from PIL import Image
import io
import firebase_admin
from firebase_admin import credentials, firestore, auth

# Initialize Firebase
cred = credentials.Certificate("path/to/firebase-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI()

# Model for equation solving
class EquationRequest(BaseModel):
    equation: str

@app.post("/solve")
def solve_equation(data: EquationRequest):
    try:
        solution = sp.solve(sp.sympify(data.equation))
        return {"solution": str(solution)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# OCR Processing for images
@app.post("/upload-image")
def process_image(file: UploadFile = File(...)):
    try:
        image = Image.open(io.BytesIO(file.file.read()))
        text = pytesseract.image_to_string(image)
        return {"extracted_text": text}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# User Authentication
@app.post("/login")
def login_user(email: str, password: str):
    try:
        user = auth.get_user_by_email(email)
        return {"message": "User exists", "user_id": user.uid}
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")

@app.post("/register")
def register_user(email: str, password: str):
    try:
        user = auth.create_user(email=email, password=password)
        return {"message": "User registered", "user_id": user.uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/session/{user_id}")
def get_sessions(user_id: str):
    sessions = db.collection("sessions").where("user_id", "==", user_id).stream()
    return {"sessions": [session.to_dict() for session in sessions]}
