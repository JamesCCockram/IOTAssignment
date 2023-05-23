import serial
import json
from sqlalchemy import create_engine, Table, Column, MetaData, DATETIME, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import time


device = '/dev/tty.usbmodem212401'
serial = serial.Serial(device, 9600, timeout=1)

engine = create_engine('postgresql://localhost/weather_db')

Base = declarative_base()

#Create a class to store weather data in before sending to Postgres
class aqData(Base):
    __tablename__ = 'aqData'
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DATETIME)
    co2 = Column(Integer)
    tvoc = Column(Integer)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()


#Wait 10s to ensure all Sensors are ready
time.sleep(10)

while True:
    #Write Command to Arduino to recieve the JSON data
    serial.write(b"getData")
    # {co2: 44, tvoc: 1}
    #Wait 5s to ensure we don't miss the output
    time.sleep(5)
    #Read the recieved line and decode it
    data = serial.readline().decode('utf-8')
    print(data)
    #Use Python's JSON library to read the JSON data
    j = json.loads(data)

    new_data = aqData(time = (time.strftime('%Y-%m-%d %H:%M:%S')), co2 = int(j["co2"]), tvoc = int(j["tvoc"]))
    session.add(new_data)
    session.commit()

    #Wait for 30 seconds before getting data again
    time.sleep(30)