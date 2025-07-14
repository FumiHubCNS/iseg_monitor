import os
import sys
import pathlib
import time
from dotenv import load_dotenv
from fastapi import FastAPI
from sqlmodel import Field, Session, SQLModel, create_engine, select
from typing import List

sys.path.append("../models")
from iseg_monitor.models.models import Detector, Voltage, Current, TimeValSet

DOTENV_FILE = pathlib.Path(__file__).resolve().parent.parent.joinpath("conf/.env").resolve()
print(DOTENV_FILE)
load_dotenv(DOTENV_FILE)

dbpath = os.environ.get("DBPATH")
conf_det_list = os.environ.get("DET_LIST")

app = FastAPI()

engine = create_engine(dbpath)

@app.get("/detectors/", response_model=list[Detector])
async def get_detectors():
    with Session(engine) as session:
        statement = select(Detector)
        results = session.exec(statement).all()
    return results

@app.get("/detector/{det_id}", response_model=Detector)
async def get_detector(det_id: int):
    with Session(engine) as session:
        detector = session.get(Detector, det_id)
    return detector

@app.get("/detector/", response_model=list[Detector])
async def get_detector_by_name(name: str):
    with Session(engine) as session:
        statement = select(Detector).where(Detector.name == name)
        results = session.exec(statement).all()
    return results

@app.get("/voltage/{det_id}", response_model=list[TimeValSet])
async def get_voltage(
    det_id: int,
    start: int | None = None,
    stop: int | None = None,
    last: int | None = None):
    with Session(engine) as session:
        statement = select(Voltage.time, Voltage.value).where(Voltage.det_id == det_id)
        if start is not None:
            statement = statement.where(Voltage.time > start)
        if stop is not None:
            statement = statement.where(Voltage.time < stop)
        if last is not None:
            statement = statement.where(Voltage.time > time.time() - last)
        results = session.exec(statement).all()
    data = []
    if results:
        for res in results:
            data.append(TimeValSet(res.time, res.value))
    return data

@app.get("/current/{det_id}", response_model=list[TimeValSet])
async def get_current(
    det_id: int,
    start: int | None = None,
    stop: int | None = None,
    last: int | None = None):
    with Session(engine) as session:
        statement = select(Current.time, Current.value).where(Current.det_id == det_id)
        if start is not None:
            statement = statement.where(Current.time > start)
        if stop is not None:
            statement = statement.where(Current.time < stop)
        if last is not None:
            statement = statement.where(Current.time > time.time() - last)
        results = session.exec(statement).all()
    data = []
    if results:
        for res in results:
            data.append(TimeValSet(res.time, res.value))
    return data
