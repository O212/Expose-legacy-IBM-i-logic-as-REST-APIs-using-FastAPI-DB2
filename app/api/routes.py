import logging

import pyodbc
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db import get_connection

router = APIRouter()
log = logging.getLogger("api")


@router.get("/health")
def health_check():
    """Liveness check. Does not touch Db2."""
    return {"status": "API is up"}


@router.get("/health/db")
def health_db():
    """Readiness check: verifies the ODBC connection to Db2 for i."""
    try:
        with get_connection() as conn:
            conn.cursor().execute("SELECT 1 FROM SYSIBM.SYSDUMMY1").fetchone()
    except (pyodbc.Error, RuntimeError):
        log.exception("Db2 health check failed")
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "Db2 connection OK"}


@router.get("/orders/{order_id}")
def get_order(order_id: int):
    """Example read endpoint. Replace MYLIB.ORDERS with your own table."""
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


class RunProgramRequest(BaseModel):
    param1: str = Field(..., max_length=6)
    param2: int


@router.post("/runpgm")
def run_program(body: RunProgramRequest):
    """Example call of an RPG program registered as an SQL procedure.

    Register it first (see README): MYLIB.MYPGM_SQL -> MYLIB/MYPGM
    """
    try:
        with get_connection() as conn:  # commits on clean exit
            conn.cursor().execute(
                "CALL MYLIB.MYPGM_SQL(?, ?)", body.param1, body.param2
            )
    except (pyodbc.Error, RuntimeError):
        log.exception("Procedure call failed")
        raise HTTPException(status_code=502, detail="Procedure call failed")
    return {"status": "executed"}
