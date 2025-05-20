from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.companies_service import get_companies_from_db
from services.sectors_service import get_sectors_from_db
from services.prediction_service import get_prediction_from_db


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajuste para o domínio do frontend se necessário
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def test():
    return {"message": "template with tailwind + ts + python + react + electron :)"}

@app.get("/companies")
def get_companies():
    return get_companies_from_db()

@app.get("/sectors")
def get_sectors():
    return get_sectors_from_db()

@app.get("/prediction/{company_id}")
def get_prediction(company_id: int):
    return get_prediction_from_db(company_id)
