import sys
import pandas as pd
import datetime
import psycopg2
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

print (sys.version)

#engine = sqlalchemy.create_engine("postgres://postgres@/postgres")
#engine = create_engine('postgresql+psycopg2://user:password@hostname/database_name')
engine = create_engine('postgresql://postgres:crop@localhost:5433/postgres')
connection = engine.connect()

#print('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.sdatetime.now()))

Base = declarative_base()

class Sensor (Base):
    __tablename__= 'sensor'
    ID = Column (Integer, primary_key=True)
    MODBUSID = Column (Integer)
    TIMESTAMP = Column(DateTime, default=datetime.datetime.utcnow)
    #TIME_CREATED = Column(DateTime(timezone=True), server_default=func.now())
    #TIME_UPDATED = Column(DateTime(timezone=True), onupdate=func.now())
    TEMPERATURE = Column(Integer)

    def __repr__(self):
        return "<Sensor(MODBUSID='{}', TIMESTAMP='{}', TEMPERATURE'{}')>"\
                .format(self.MODBUSID, self.TIMESTAMP, self.TEMPERATURE)

Base.metadata.create_all(engine)