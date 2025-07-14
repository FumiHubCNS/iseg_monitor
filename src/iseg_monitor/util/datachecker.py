"""!
@file datachecker.py
@version 1
@author Fumitaka ENDO
@date 2025-07-14T12:56:14+09:00
@brief utilities for checking output data
"""
import argparse
import pathlib
from sqlalchemy import create_engine, text
import os
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots


this_file_path = pathlib.Path(__file__).parent


def show_tables(db_path: str, number:int =10):
    """!
    @brief dump last 10 rows of each table
    @param db_path input path of database file
    @return None
    """
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url)

    with engine.connect() as conn:
        for table in ['detector', 'current', 'voltage']:
            print(f"\n=== {table} (last {number}) ===")

            try:
                result = conn.execute(
                    text(f"""
                        SELECT * FROM {table}
                        ORDER BY rowid DESC
                        LIMIT {number}
                    """)
                )
                rows = list(result)
               
                for row in reversed(rows):
                    print(row)

            except Exception as e:
                print(f"table '{table}' can not read: {e}")

def load_measurements(db_path: str):
    """!
    @brief load data base file for plotting
    @param db_path input path of database file
    @return current, voltage, det_map (DataFrame DataFrame dict)
    """
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url)

    with engine.connect() as conn:
        # id → name マッピングを作る
        det_map = dict(conn.execute(text("SELECT id, name FROM detector")).fetchall())

        current = pd.read_sql(
            text(f"""
                SELECT det_id, value, time FROM current
                WHERE det_id IN ({','.join(map(str, det_map.keys()))})
            """),
            conn
        )

        voltage = pd.read_sql(
            text(f"""
                SELECT det_id, value, time FROM voltage
                WHERE det_id IN ({','.join(map(str, det_map.keys()))})
            """),
            conn
        )

    current["time"] = pd.to_datetime(current["time"], unit="s")
    voltage["time"] = pd.to_datetime(voltage["time"], unit="s")

    return current, voltage, det_map


def plot_all(current, voltage, det_map, downsample: int = 1):
    """!
    @brief load data base file for plotting
    
    @param current: current DataFrame
    @param voltage: voltage DataFrame
    @param det_map: dict for det_id -> name conversion
    @param downsample: number of downsample
    """

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Current over Time", "Voltage over Time")
    )

    # Current
    for det_id, df_orig in current.groupby("det_id"):
        df = df_orig.copy()
        if downsample > 1:
            df = df.iloc[::downsample, :]
        fig.add_trace(
            go.Scatter(
                x=df["time"], y=df["value"],
                mode="lines",
                name=f"Current {det_map.get(det_id, det_id)}"
            ),
            row=1, col=1
        )

    # Voltage
    for det_id, df_orig in voltage.groupby("det_id"):
        df = df_orig.copy()
        if downsample > 1:
            df = df.iloc[::downsample, :]
        fig.add_trace(
            go.Scatter(
                x=df["time"], y=df["value"],
                mode="lines",
                name=f"Voltage {det_map.get(det_id, det_id)}"
            ),
            row=2, col=1
        )

    fig.update_layout(
        height=800,
        title_text="Current and Voltage Measurements",
        xaxis_title="Time",
    )
    fig.show()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input", help="input path of database file", type=str, default="../db/iseg.db")
    parser.add_argument("-n", "--number", help="number of lines to be dumped", type=int, default=10)
    parser.add_argument("-d", "--downsample", help="number of downsampling", type=int, default=1)
    parser.add_argument("-f", "--flag", help="draw flag", action="store_true")

    args = parser.parse_args()
    db_file_path = this_file_path / args.input

    show_tables(db_file_path, args.number)

    current, voltage, det_map = load_measurements(db_file_path)
    if args.flag:
        plot_all(current, voltage, det_map, args.downsample)


if __name__ == "__main__":
    main()
