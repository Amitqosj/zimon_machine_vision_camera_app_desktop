import serial.tools.list_ports
from typing import List

from fastapi import APIRouter, Depends

from backend.api.app_state import get_arduino
from backend.api.deps import get_current_user
from backend.api.schemas import ArduinoCommandRequest, ArduinoConnectRequest

router = APIRouter(prefix="/arduino", tags=["arduino"])


@router.get("/ports")
def list_ports(_user: dict = Depends(get_current_user)):
    return {"ports": [p.device for p in serial.tools.list_ports.comports()]}


@router.get("/status")
def arduino_status(_user: dict = Depends(get_current_user)):
    a = get_arduino()
    return {
        "connected": a.is_connected(),
        "port": a.port,
    }


@router.post("/connect")
def arduino_connect(body: ArduinoConnectRequest, _user: dict = Depends(get_current_user)):
    a = get_arduino()
    ok = a.connect(body.port)
    return {"ok": ok, "port": a.port if ok else None}


@router.post("/auto-connect")
def arduino_auto(_user: dict = Depends(get_current_user)):
    a = get_arduino()
    ok = a.auto_connect()
    return {"ok": ok, "port": a.port if ok else None}


@router.post("/disconnect")
def arduino_disconnect(_user: dict = Depends(get_current_user)):
    get_arduino().close()
    return {"ok": True}


@router.post("/command")
def arduino_command(body: ArduinoCommandRequest, _user: dict = Depends(get_current_user)):
    a = get_arduino()
    reply = a.send(body.command)
    return {"reply": reply}


@router.get("/temperature")
def arduino_temp(_user: dict = Depends(get_current_user)):
    t = get_arduino().read_temperature_c()
    return {"celsius": t}
