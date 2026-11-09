# Dziennik ocen

Projekt na przedmiot **Metody Wirtualizacji**.

Aplikacja webowa do prowadzenia dziennika ocen z wykorzystaniem wirtualizacji i konteneryzacji (Docker + Docker Compose).

## Skład grupy

- Franciszek Wybicki
- Miłosz Wybrański

## Stack technologiczny

| Warstwa       | Technologia                          |
|---------------|--------------------------------------|
| Frontend      | HTML + CSS + JavaScript (nginx)      |
| Backend       | Python + FastAPI                     |
| Baza danych   | PostgreSQL 15 (oficjalny obraz)      |
| Kontenery     | Docker + Docker Compose              |
| Komunikacja   | HTTP + JSON                          |

Frontend łączy się **wyłącznie** z backendem. Backend łączy się z bazą danych.

## Uruchomienie

### Wymagania
- Docker
- Docker Compose

### Kroki

1. Skopiuj plik konfiguracyjny środowiska:
   ```bash
   cp .env.example .env.
   ```

2. Uzupełnij wartości w pliku `.env` (użytkownik, hasło i nazwa bazy).

3. Uruchom projekt:
    ```bash
    docker compose up --build
    ```
    Aplikacja będzie dostępna pod adresami:
    - Frontend: http://localhost
    - Backend (API): http://localhost:3000
    - Dokumentacja interaktywna API (Swagger): http://localhost:3000/docs

    Zatrzymanie:
        ```bash
        docker compose down
        ```

    Usunięcie danych bazy (reset):
        ```bash
        docker compose down -v
        ```

## Struktura projektu

```
dziennik-ocen/
├── backend/
│   ├── Dockerfile
│   ├── main.py              # API FastAPI
│   └── requirements.txt
├── frontend/
│   ├── Dockerfile
│   └── index.html           # Interfejs użytkownika
├── db/
│   └── init.sql             # Inicjalizacja tabel + dane przykładowe
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## API – dokumentacja (JSON)

Wszystkie endpointy zwracają i przyjmują dane w formacie JSON.

Base URL: `http://localhost:3000`

### Health check

```
GET /health
```

#### Odpowiedź (200):

```
{
  "status": "ok",
  "db": "connected"
}
```

### Uczniowie

#### Lista uczniów

```
GET /api/students
```

#### Odpowiedź (200):

```
[
  {
    "id": 1,
    "first_name": "Jan",
    "last_name": "Kowalski"
  },
  {
    "id": 2,
    "first_name": "Anna",
    "last_name": "Nowak"
  }
]
```

#### Szczegóły ucznia + jego oceny

```
GET /api/students/{id}
```

#### Odpowiedź (200):

```
{
  "id": 1,
  "first_name": "Jan",
  "last_name": "Kowalski",
  "grades": [
    {
      "id": 1,
      "student_id": 1,
      "subject": "Matematyka",
      "grade": 4.5
    },
    {
      "id": 2,
      "student_id": 1,
      "subject": "Fizyka",
      "grade": 3.0
    }
  ]
}
```

#### Błąd (404):

```
{
  "detail": "Nie znaleziono takiego ucznia"
}
```

### Oceny

#### Dodanie oceny

```
POST /api/grades
Content-Type: application/json
```

#### Body:

```
{
  "student_id": 1,
  "subject": "Matematyka",
  "grade": 4.5
}
```

Dozwolone wartości oceny: `1.0`, `1.5`, `2.0`, `2.5`, `3.0`, `3.5`, `4.0`, `4.5`, `5.0`, `5.5`, `6.0`.

#### Odpowiedź (201):

```
{
  "message": "Dodano ocenę",
  "id": 3
}
```

#### Przykładowe błędy:

```
{
  "detail": "Nieprawidłowa wartość oceny."
}
```
```
{
  "detail": "Błąd przy dodawaniu oceny, sprawdź czy student istnieje."
}
```

#### Usunięcie oceny

```
DELETE /api/grades/{id}
```

#### Odpowiedź (200):

```
{
  "message": "Usunięto ocenę"
}
```

#### Błąd (404):

```
{
  "detail": "Ocena nie istnieje"
}
```

## Frontend

Frontend zawiera dwa widoki:
1. Lista uczniów – pobierana z GET /api/students
2. Szczegóły ucznia – oceny ucznia + możliwość dodawania i usuwania ocen

Komunikacja odbywa się wyłącznie przez API backendu (fetch + JSON).

## Baza danych

Przy pierwszym uruchomieniu kontenera bazy wykonywany jest skrypt `db/init.sql`, który:
- tworzy tabele `students` i `grades`,
- wstawia przykładowych uczniów i oceny.

Dane są przechowywane w volume Docker (`db_data`), więc przetrwają restart kontenerów.

## Status projektu

- Szkielet 3 kontenerów (frontend + backend + baza)
- API backendu (uczniowie + oceny)
- Frontend współpracujący z aktualnym API (2 widoki)
- Dokumentacja API w README