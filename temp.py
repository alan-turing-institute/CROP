import psycopg2
from sqlalchemy import (create_engine, ForeignKey, MetaData, Table, Float, Column, Integer, String, DateTime, Text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class Parent(Base):
    __tablename__ = 'parent'
    #id = Column(Integer, primary_key=True)
    #iddd = Column(Integer)
    #child_id = Column (Integer)
    #child_id = Column(Integer, ForeignKey('child1.id'))
    #child1 = relationship("Child")

class Child(Base):
    __tablename__ = 'child'
    #id = Column(Integer, primary_key=True)

#create_engine('postgresql+psycopg2://user:password@hostname/database_name')
engine = create_engine('postgresql://postgres:crop@localhost:5433/test')
#con = engine.connect()
  
Base.metadata.create_all(engine)
