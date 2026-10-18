from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
def hello():
    # sprawdzenie, czy baza odpowiada
    try:
        conn = psycopg2.connect(
            host="db",
            user="postgres",
            password="mysecretpassword",
            port=5432
        )
        conn.close()
        baza_status = "Baza danych odpowiada!"
    except Exception as e:
        baza_status = f"Baza nie dziala: {e}"

    return {
        "wiadomosc": "backend dziala!",
        "baza": baza_status
    }