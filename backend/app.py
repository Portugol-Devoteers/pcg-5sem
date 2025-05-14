from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.db import conn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def test():
    return {"message": "template with tailwind + ts + python + react + electron :)"}


@app.get("/companies")
def get_companies():
    with conn.cursor() as cur:
        cur.execute("SELECT b3_code FROM companies")
        tickers = [row[0] for row in cur.fetchall()]
    return {"tickers": tickers}