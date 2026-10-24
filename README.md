# Expose Legacy IBM i Logic as REST APIs using FastAPI + Db2

> ⚠️ **Status: experimental prototype.** This project was built with AI assistance and has **not yet been validated against a live IBM i system**. Treat it as a starting point: review the code, and test it in a non-production environment before relying on it.

This project explores how existing IBM i (AS/400) business logic and data (SQL tables, SQL stored procedures, and RPG/RPGLE programs registered as SQL procedures) can be exposed as REST APIs using Python's [FastAPI](https://fastapi.tiangolo.com/) framework and an ODBC connection to Db2 for i.

IBM i already offers other ways to build APIs, such as Integrated Web Services (IWS), Mapepire, and the `itoolkit` library. This repository is not a replacement for them. It is a small, readable example of a Python + ODBC approach, shared to gather feedback from the IBM i community.

---

## Features

- FastAPI-based REST API server (`app.main:app`)
- `pyodbc` connectivity to Db2 for i
- Read from Db2 tables and call SQL procedures (including RPG programs registered as procedures)
- Auto-generated Swagger UI at `/docs`
- Parameterized SQL (no string concatenation) to avoid SQL injection
- Small, minimal starter code you can extend

---

## Project structure

```
.
├── app/
│   ├── main.py          # FastAPI application entry point
│   ├── db.py            # pyodbc connection helper (commit/rollback/close)
│   └── api/
│       └── routes.py    # /health, /health/db, /orders/{id}, /runpgm
├── .env.example         # sample DB_DSN (copy to .env, never commit .env)
├── requirements.txt
├── .gitignore
└── README.md
```

`app/main.py` creates the FastAPI app (titled "AS400 API Wrapper") and includes the router defined in `app/api/routes.py`. `app/db.py` opens Db2 connections and handles commit, rollback and close.

Endpoints: `GET /health` (no Db2), `GET /health/db` (checks the Db2 connection), `GET /orders/{order_id}` (sample read) and `POST /runpgm` (sample procedure call). The two sample endpoints use placeholder objects (`MYLIB.ORDERS`, `MYLIB.MYPGM_SQL`) that you must replace with your own.

---

## Requirements

### IBM i (server side)

- IBM i 7.4 or higher (7.5 recommended). IBM i 7.3 is out of IBM support.
- Db2 for i, plus the tables, procedures or programs you plan to expose
- A dedicated **least-privilege** IBM i user profile for the API (do not use QSECOFR or a powerful personal profile)

### Client / runtime (Linux, Windows or macOS)

- Python 3.9 or higher
- IBM i Access ODBC Driver (installed with IBM i Access Client Solutions) and, on Linux/macOS, unixODBC
- Git

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/O212/Expose-legacy-IBM-i-logic-as-REST-APIs-using-FastAPI-DB2.git
cd Expose-legacy-IBM-i-logic-as-REST-APIs-using-FastAPI-DB2
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> Versions in `requirements.txt` are minimums. Pin exact versions once you have tested in your environment.

---

## ODBC configuration

### Option A: DSN

Add to `odbc.ini` (Linux/macOS) or define a System DSN (Windows):

```ini
[IBMi]
Driver=IBM i Access ODBC Driver
System=YOUR_IBMI_HOSTNAME_OR_IP
UserID=SVC_USER
Password=CHANGE_ME
Naming=0
```

> `Naming=0` selects SQL naming (`SCHEMA.TABLE`); `Naming=1` selects system naming (`LIBRARY/FILE`). The examples in this README use SQL naming.
>
> **Security note:** `odbc.ini` stores the password in plain text. Restrict file permissions, or prefer Option B with a secrets manager.

### Option B: Direct connection string (recommended)

Set an environment variable, or use a `.env` file that is **never committed** (make sure it is listed in `.gitignore`):

```
DB_DSN=DRIVER={IBM i Access ODBC Driver};SYSTEM=your.ibmi.host;UID=SVC_USER;PWD=CHANGE_ME;
```

If you use a `.env` file, your code must load it explicitly, for example with `python-dotenv`:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Running the API

From the **repository root** (the entry point is `app.main:app`, not `main:app`):

```bash
export DB_DSN="DRIVER={IBM i Access ODBC Driver};SYSTEM=your.ibmi.host;UID=SVC_USER;PWD=CHANGE_ME;"

uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

`--reload` is for development only.

Open your browser:

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

> 🔒 **Do not expose this API publicly without authentication and TLS.** Binding to `0.0.0.0` makes it reachable from your network. Authentication (for example JWT/OAuth) is not implemented yet.

---

## Sample endpoint (read from Db2)

The snippets below are simplified versions of the code in `app/api/routes.py` and `app/db.py`.

Assumes a sample table such as:

```sql
CREATE TABLE MYLIB.ORDERS (
  ORDER_ID INTEGER NOT NULL PRIMARY KEY,
  ITEM     VARCHAR(50) NOT NULL
);
INSERT INTO MYLIB.ORDERS VALUES (1001, 'Sample item');
```

```python
import logging

import pyodbc
from fastapi import APIRouter, HTTPException

from app.db import get_connection

router = APIRouter()
log = logging.getLogger("api")


@router.get("/orders/{order_id}")
def get_order(order_id: int):
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT ORDER_ID, ITEM FROM MYLIB.ORDERS WHERE ORDER_ID = ?",
                order_id,
            )
            row = cur.fetchone()
    except (pyodbc.Error, RuntimeError):
        log.exception("Db2 error while reading order")
        raise HTTPException(status_code=502, detail="Database error")

    if row is None:
        raise HTTPException(status_code=404, detail="Order not found")

    return {"order_id": row.ORDER_ID, "item": row.ITEM}

```

Notes:

- `get_connection()` (in `app/db.py`) commits on success, rolls back on error and always closes the connection. Note that pyodbc's own `with pyodbc.connect(...)` block commits but does not close it.
- A missing record returns HTTP 404 instead of crashing.
- Column names are selected explicitly instead of `SELECT *`, so the result does not depend on column order.


## Calling RPG or SQL programs

SQL `CALL` works most reliably when the program is registered as an SQL external procedure, because Db2 then knows the parameter types.

Assume an existing RPG program `MYLIB/MYPGM` that takes a 6-character field and an integer. Register it once:

```sql
CREATE OR REPLACE PROCEDURE MYLIB.MYPGM_SQL (
  IN P1 CHAR(6),
  IN P2 INTEGER
)
LANGUAGE RPGLE
EXTERNAL NAME 'MYLIB/MYPGM'
PARAMETER STYLE GENERAL;
```

Then call it from FastAPI:

```python
@router.post("/runpgm")
def run_program(param1: str, param2: int):
    try:
        with pyodbc.connect(os.environ["DB_DSN"]) as conn:  # commits on clean exit
            conn.cursor().execute("CALL MYLIB.MYPGM_SQL(?, ?)", param1, param2)
    except pyodbc.Error:
        log.exception("Procedure call failed")
        raise HTTPException(status_code=502, detail="Procedure call failed")
    return {"status": "executed"}
```

Notes:

- Do **not** use CL syntax such as `CALL MYLIB/MYPGM(...)` through SQL. In CL, the command is `CALL PGM(MYLIB/MYPGM) PARM('ABC123' 5)`.
- pyodbc runs with autocommit **off** by default. Writes made by a procedure are only persisted if the transaction is committed (here, when the `with` block exits cleanly). Take care if your procedure uses commitment control.
- To run a CL command from SQL, use `CALL QSYS2.QCMDEXC('your CL command')`. This is powerful, so never build the command string from user input.

---

## Error handling

Return proper HTTP status codes and keep database details out of API responses. Log them on the server instead:

```python
try:
    with pyodbc.connect(os.environ["DB_DSN"]) as conn:
        ...
except pyodbc.Error:
    log.exception("Db2 error")
    raise HTTPException(status_code=502, detail="Database error")
```

Returning `str(e)` to the caller can leak host names, library names and other internal details.

---

## Security considerations

- Use a dedicated service profile with only the authorities the exposed objects need.
- Add authentication (JWT/OAuth) before any non-local use.
- Always use TLS when exposing the API beyond localhost (for example, behind a reverse proxy such as Nginx).
- Keep credentials out of source control (`.env`, `odbc.ini` and similar files belong in `.gitignore`).
- Use parameter markers (`?`) for all user-supplied values.

---

## Deploying to production

This prototype is not production-ready. If you extend it, one common pattern is to run it behind a reverse proxy with TLS:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
```

Each ODBC connection on IBM i uses a server job, so connection pooling and sensible worker counts matter.

---

## Testing

With the server running, use Swagger UI at `/docs`, or cURL:

```bash
curl http://localhost:8000/orders/1001
```

This requires the sample `MYLIB.ORDERS` table from above.

---

## Next steps

- Authentication (JWT/OAuth) and TLS
- Connection pooling
- Pinned `requirements.txt`
- Dockerfile for easier deployment
- Automated tests
- Centralized logging and monitoring
- Validation against a live IBM i environment

---

## Contributing

Feedback is very welcome, especially from RPG/RPGLE developers, IBM i architects and Db2 professionals. Please open an issue or submit a pull request.

## License

MIT License. See the [LICENSE](LICENSE) file.
