


# Expose Legacy IBM i Logic as REST APIs using FastAPI + Db2

This project shows how to wrap existing IBM i (AS/400) business logic—RPG, CL, or SQL—into modern REST APIs with Python’s FastAPI framework and an ODBC connection to Db2.

---

## Features
- FastAPI-based REST API server  
- `pyodbc` connectivity to IBM i Db2  
- Call stored procedures or read/write Db2 tables  
- Auto-generated Swagger UI at `/docs`  
- Clean, minimal starter code you can extend

---

## Requirements

### IBM i (server side)
- IBM i 7.3 or higher  
- Db2 and the programs/procedures you plan to expose

### Client / runtime (Linux, Windows, or IBM i PASE)
- Python 3.7+  
- IBM i Access ODBC driver  
- Git

---

## Setup

### 1 – Clone the repository

```bash
git clone https://github.com/O212/Expose-legacy-IBM-i-logic-as-REST-APIs-using-FastAPI-DB2.git
cd Expose-legacy-IBM-i-logic-as-REST-APIs-using-FastAPI-DB2
```

### 2 – Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
```

### 3 – Install dependencies

If `requirements.txt` is present:

```bash
pip install -r requirements.txt
```

Otherwise:

```bash
pip install fastapi uvicorn pyodbc python-dotenv
```

---

## ODBC configuration

### Option A – DSN

Add to `odbc.ini` (Linux/macOS) or define a System DSN (Windows):

```
[IBMi]
Driver=IBM i Access ODBC Driver
System=YOUR_IBMI_HOSTNAME_OR_IP
UserID=MYUSER
Password=MYPASS
Naming=1
```

### Option B – Direct connection string

Set an environment variable (or `.env` file):

```env
DB_DSN=DRIVER={IBM i Access ODBC Driver};SYSTEM=192.168.1.100;UID=MYUSER;PWD=MYPASS;
```

---

## Running the API

```bash
# If using .env, ensure it’s loaded; or export manually:
export DB_DSN="DRIVER={IBM i Access ODBC Driver};SYSTEM=192.168.1.100;UID=MYUSER;PWD=MYPASS;"

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open your browser:

* Swagger UI → [http://localhost:8000/docs](http://localhost:8000/docs)
* OpenAPI JSON → [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## Sample endpoint (read from Db2)

```python
@app.get("/orders/{order_id}")
def get_order(order_id: int):
    conn = pyodbc.connect(os.environ["DB_DSN"])
    cur  = conn.cursor()
    cur.execute("SELECT * FROM ORDERS WHERE ORDER_ID = ?", order_id)
    row = cur.fetchone()
    return {"order_id": row[0], "item": row[1]}
```

---

## Calling RPG or SQL programs

Assume an existing program or stored procedure:

```sql
CALL MYLIB/MYPGM('ABC123', 5)
```

FastAPI wrapper:

```python
@app.post("/runpgm")
def run_program(param1: str, param2: int):
    conn = pyodbc.connect(os.environ["DB_DSN"])
    cur  = conn.cursor()
    cur.execute("{CALL MYLIB.MYPGM (?, ?)}", param1, param2)
    return {"status": "executed"}
```

---

## Error handling

```python
try:
    conn = pyodbc.connect(os.environ["DB_DSN"])
    ...
except pyodbc.Error as e:
    return {"error": str(e)}
```

---

## Deploying to production

Behind Nginx or another reverse proxy:

```bash
gunicorn main:app \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  -k uvicorn.workers.UvicornWorker
```

Add HTTPS with Let’s Encrypt if exposing externally.

---

## Testing

With the server running, use Swagger at `/docs` or cURL:

```bash
curl http://localhost:8000/orders/1001
```

---

## Next steps

* Token-based auth (JWT)
* Async Db2 connection pooling
* Docker image for easier deployment
* Central logging and monitoring

---

## Contributing

Feel free to open issues or submit pull requests. Improvements and bug fixes are welcome.

