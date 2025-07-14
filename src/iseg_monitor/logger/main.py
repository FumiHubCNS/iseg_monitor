import os
import sys
import pathlib
import time
import datetime
import requests
import json
from dotenv import load_dotenv
from sqlmodel import Field, Session, SQLModel, create_engine

sys.path.append("../models")
from iseg_monitor.models.models import Detector, Voltage, Current, TimeValSet

def main():
    # Load config
    DOTENV_FILE = pathlib.Path(__file__).resolve().parent.parent.joinpath("conf/.env").resolve()
    load_dotenv(DOTENV_FILE)
    
    hostname = os.environ.get("MPOD_HOST")
    port = os.environ.get("MPOD_PORT")
    user = os.environ.get("MPOD_USER")
    password = os.environ.get("MPOD_PASS")
    baseurl = f"http://{hostname}:{port}"
    dbpath = os.environ.get("DBPATH")
    interval = int(os.environ.get("LOG_INTERVAL"))
    conf_det_list = os.environ.get("DET_LIST")

    # Define functions to communicate with iCS
    def get_apikey():
        r = requests.get(f"{baseurl}/api/login/{user}/{password}")
        if r.ok:
            return r.content.decode().replace('\n', '')
        else:
            print("Error: {r.status_code}")
            return None

    def measure_voltage(apikey, line="*", address="*", channel="*"):
        r = requests.get(f"{baseurl}/api/getItem/{apikey}/{line}/{address}/{channel}/Status.voltageMeasure")
        if r.ok:
            return r.content
        else:
            print("Error: {r.status_code}")
            return None
    
    def measure_current(apikey, line="*", address="*", channel="*"):
        r = requests.get(f"{baseurl}/api/getItem/{apikey}/{line}/{address}/{channel}/Status.currentMeasure")
        if r.ok:
            return r.content
        else:
            print("Error: {r.status_code}")
            return None

    # Load Channel Map
    with open(conf_det_list) as f:
        dets = json.load(f)
    
    # Create Engine
    engine = create_engine(dbpath)
    SQLModel.metadata.create_all(engine)

    # Register Detectors
    with Session(engine) as session:
        for det in dets:
            line = det["id"][0]
            addr = det["id"][1]
            ch   = det["id"][2]
            det_id = line<<16 | addr<<8 | ch
            name = det["name"]

            if det:=session.get(Detector, det_id):
                # If already registered
                if det.name != name:
                    det.name = name
                    session.add(det)
            else:
                session.add(
                    Detector(
                        id = line<<16 | addr<<8 | ch,
                        name = name,
                        line = line,
                        address = addr,
                        channel = ch
                    )
                )
        session.commit()
    
    # Start Logging
    while True:
        print(datetime.datetime.now())

        # Get API
        apikey = get_apikey()
        print(apikey)

        # Measure Volatage
        volts = json.loads(measure_voltage(apikey))

        # Measure Current
        currents = json.loads(measure_current(apikey))

        # Commit Data
        with Session(engine) as session:
            # Voltage
            for volt in volts[0]["c"]:
                data = volt["d"]
                line = int(data["p"]["l"])
                addr = int(data["p"]["a"])
                ch   = int(data["p"]["c"])
                val  = float(data["v"])
                unit = data["u"]
                t    = float(data["t"])
                if unit == "kV":
                    val *= 1e3
                session.add(
                    Voltage(
                        det_id = line<<16 | addr<<8 | ch,
                        line = line,
                        address = addr,
                        channel = ch,
                        value = val,
                        time = t
                    )
                )

            # Current
            for current in currents[0]["c"]:
                data = current["d"]
                line = int(data["p"]["l"])
                addr = int(data["p"]["a"])
                ch   = int(data["p"]["c"])
                val  = float(data["v"])
                unit = data["u"]
                t    = float(data["t"])
                if unit == "kA":
                    val *= 1e6
                elif unit == "A":
                    val *= 1e3
                elif unit == "µA":
                    val *= 1e-3
                elif unit == "nA":
                    val *= 1e-6
                session.add(
                    Current(
                        det_id = line<<16 | addr<<8 | ch,
                        line = line,
                        address = addr,
                        channel = ch,
                        value = val,
                        time = t
                    )
                )
            
            session.commit()
        
        # Interval
        time.sleep(interval)


if __name__ == "__main__":
    main()

