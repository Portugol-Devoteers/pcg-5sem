from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.companies_service import get_companies_from_db
from services.sectors_service import get_sectors_from_db
from services.prediction_service import get_prediction_from_db
from services.comparison_service import comparar_dados_empresa
from services.statistics_service import gerar_estatisticas_gerais
from services.statistics_service_sector import gerar_estatisticas_por_setor


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

@app.get("/prediction/{ticker}")
def get_prediction(ticker: str):
    return get_prediction_from_db(ticker)

@app.get("/comparison/{ticker}")
def get_comparison(ticker: str):
    return comparar_dados_empresa(ticker)

@app.get("/statistics")
def get_statistics():
    return gerar_estatisticas_gerais()

@app.get("/statistics/{sector_id}")
def get_statistics_by_sector(sector_id: int):
    return gerar_estatisticas_por_setor(sector_id)
