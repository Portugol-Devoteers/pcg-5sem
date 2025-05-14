from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    return [
        {
            "type": "company",
            "ticker": "ITUB4",
            "name": "Itaú Unibanco",
            "sector": "Bancos",
            "price": 28.14,
            "variation": 1.12
        },
        {
            "type": "company",
            "ticker": "BBDC4",
            "name": "Bradesco",
            "sector": "Bancos",
            "price": 17.32,
            "variation": -0.45
        },
        {
            "type": "company",
            "ticker": "PETR4",
            "name": "Petrobras",
            "sector": "Petróleo e Gás",
            "price": 38.21,
            "variation": 2.45
        },
        {
            "type": "company",
            "ticker": "VALE3",
            "name": "Vale",
            "sector": "Energia",
            "price": 68.47,
            "variation": -1.21
        },
        {
            "type": "company",
            "ticker": "WEGE3",
            "name": "WEG",
            "sector": "Tecnologia",
            "price": 42.19,
            "variation": 0.86
        }
    ]

@app.get("/sectors")
def get_sectors():
    return [
        "Bancos",
        "Petróleo e Gás",
        "Energia",
        "Tecnologia"
    ]
