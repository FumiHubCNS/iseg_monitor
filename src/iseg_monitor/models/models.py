from sqlmodel import Field, SQLModel, Relationship
from pydantic import BaseModel
from typing import Optional

class Detector(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True) # line<<16 | address<<8 | channel
    name: str
    line: int
    address: int
    channel: int
    voltage: list["Voltage"] = Relationship(back_populates="detector")
    current: list["Current"] = Relationship(back_populates="detector")

class Voltage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    det_id: int | None = Field(default=None, foreign_key="detector.id")
    detector : Detector | None = Relationship(back_populates="voltage")
    line: int
    address: int
    channel: int
    value: float # V
    time: float

class Current(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    det_id: int | None = Field(default=None, foreign_key="detector.id")
    detector : Detector | None = Relationship(back_populates="current")
    line: int
    address: int
    channel: int
    value: float # mA
    time: float

class TimeValSet(BaseModel):
    time: float
    value: float
    def __init__(self, time: float, value: float):
        super().__init__(time=time, value=value)
