# --- BIBLIOTEKI FASTAPI ---
# FastAPI: Główny framework do budowy szybkiego API.
# HTTPException: Pozwala "rzucać" błędy HTTP (np. 404 Nie znaleziono, 400 Złe żądanie), by odpowiednio poinformować frontend.
# status: Zawiera stałe z kodami HTTP (np. status.HTTP_200_OK), choć w tym kodzie używamy przeważnie cyfr bezpośrednio.
from fastapi import FastAPI, HTTPException, status

# CORSMiddleware: Mechanizm pozwalający przeglądarce (w której działa frontend) na komunikację z backendem 
# działającym na innym porcie/domenie (tzw. omijanie blokady CORS, która domyślnie blokuje takie strzały ze względów bezpieczeństwa).
from fastapi.middleware.cors import CORSMiddleware

# --- BIBLIOTEKI PYDANTIC (Do walidacji) ---
# BaseModel: Klasa bazowa do tworzenia tzw. "schematów" danych. Automatycznie konwertuje JSONy na obiekty Pythona i weryfikuje ich typy.
# Field: Pozwala nakładać dodatkowe restrykcje na pola (np. minimalna wartość, opisy do dokumentacji).
from pydantic import BaseModel, Field

# --- BIBLIOTEKI BAZY DANYCH ---
# psycopg2: Najpopularniejszy sterownik pozwalający Pythonowi "rozmawiać" z bazą PostgreSQL.
import psycopg2
# RealDictCursor: Domyślnie psycopg2 zwraca wyniki z bazy jako krotki (np. (1, "Jan", "Kowalski")).
# RealDictCursor zmienia to na słowniki (np. {"id": 1, "imie": "Jan"}), co o wiele łatwiej potem odesłać jako JSON do frontendu.
from psycopg2.extras import RealDictCursor

# os: Standardowa biblioteka Pythona do interakcji z systemem operacyjnym. Tutaj używamy jej do czytania zmiennych z pliku .env.
import os


# Inicjalizacja api
app = FastAPI()

# Polityka CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # zezwolenie na zapytania z DOWOLNEGO adresu
    allow_methods=["*"], # zezwolenie na wszytkie metody HTTP (GET, POST, PUT, DELETE)
    allow_headers=["*"], # Zezwala na dowolne nagłówki
)


# === FUNKCJE POMOCNICZE ===

# funkcja tworząca połączenie z bazą przy każdym nowym żądaniu (np. nowym GET lub POST)
def get_db_connection():
    try:
       
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "haslo"),     # po lewej wartość która ma zostać odczytana
            dbname=os.getenv("DB_NAME", "postgres"),        # po prawej wartość która zostanie odczytana w przypadku błędu odczytu (np. brak .env)
            port=os.getenv("DB_PORT", "5432")
        )
        return conn
    
    except Exception as e:
        print(f"Błąd połączenia z bazą: {e}")
        return None



# === ENDPOINTY ===

# --- /health ---
@app.get("/health")
def health_check():
    conn = get_db_connection()
    if conn:
        conn.close() # Zamykanie połączenie od razu żeby nie zapchać bazy
        return {"status": "ok", "db": "connected"}
    
    # w przypadku zwrócenia None wystąpi błąd serwera (kod 500)
    raise HTTPException(status_code=500, detail="Database not connected")


# --- GET: lista zasobów (pobieranie uczniów) ---
@app.get("/api/students")
def get_students():
    conn = get_db_connection()
    
    cursor = conn.cursor(cursor_factory=RealDictCursor) # RealDictCursor zmienia dane na słownik zamiast krotki
    cursor.execute("SELECT * FROM students;")
    students = cursor.fetchall()        # fetchall() pobiera wszystkie znalezione wiersze jako listę słowników
    conn.close()
    # FastAPI zamieni listę słowników na format JSON
    return students


# --- GET: pojedynczy zasób (Pobieranie ucznia + jego ocen) ---
@app.get("/api/students/{student_id}")      # np. /api/students/5
def get_student(student_id: int):           
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # %s w zapytaniu SQL jest bezpieczniejsze niż f-stringi
    cursor.execute("SELECT * FROM students WHERE id = %s;", (student_id,))
    
    student = cursor.fetchone()     # fetchone() pobiera tylko jeden wiersz lub None
    
    if not student:
        conn.close()
        # błąd 404 (Not Found) jesli nie ma takiego ucznia
        raise HTTPException(status_code=404, detail="Nie znaleziono takiego ucznia")    
        
    # drugie zapytanie o oceny jezeli istnieje
    cursor.execute("SELECT * FROM grades WHERE student_id = %s;", (student_id,))
    student['grades'] = cursor.fetchall()           # wklejenie w nowym 'grades' listy ocen
    conn.close()
    return student


# === MODELE PYDANTIC ===
# Klasa wymuszająca prawidłowe wejscie JSON
class GradeCreate(BaseModel):
    student_id: int 
    subject: str    
    grade: float = Field(..., ge=1.0, le=6.0, description="Ocena musi być między 1.0 a 6.0")


# --- POST: dodawanie nowej oceny ---
# zmiana na 201 (utworzono) z domyślnego 200
@app.post("/api/grades", status_code=201)
def add_grade(grade_data: GradeCreate): # sprawdzenie zgodnosci z GradeCreate
    
    if grade_data.grade not in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]: # rozszerzenie o to czego nie sprawdza pydantic
        raise HTTPException(status_code=400, detail="Nieprawidłowa wartość oceny.")     # błąd 400 w przypadku złych danych

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # RETURNING id - na koniec wstawiania baza zwróci nowe ID tego wpisu
        cursor.execute(
            "INSERT INTO grades (student_id, subject, grade) VALUES (%s, %s, %s) RETURNING id;",
            (grade_data.student_id, grade_data.subject, grade_data.grade)
        )

        new_id = cursor.fetchone()[0]   # pobranie nowego ID
        
        conn.commit()       # zatwierdzenie zapisu

    except Exception as e: 
        conn.rollback()     # reset Transakcji po błędzie - żeby się nie zawiesiła od zepsutych w połowie pytań
        raise HTTPException(status_code=400, detail="Błąd przy dodawaniu oceny, sprawdź czy student istnieje.")
    finally:
        conn.close()   

    return {"message": "Dodano ocenę", "id": new_id}

# --- DELETE: usuwanie oceny ---
@app.delete("/api/grades/{grade_id}")
def delete_grade(grade_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    # RETURNING id - zwraca id, a jezeli go nie byllo to nic nie zwróci.
    cursor.execute("DELETE FROM grades WHERE id = %s RETURNING id;", (grade_id,))
    deleted = cursor.fetchone()
    
    conn.commit() # Zatwierdzenie usunięcia
    conn.close()
    
    # kod 404 jesli nic nie usunieto
    if not deleted:
        raise HTTPException(status_code=404, detail="Ocena nie istnieje")
        
    return {"message": "Usunięto ocenę"}