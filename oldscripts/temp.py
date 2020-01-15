import psycopg2
from sqlalchemy import (create_engine, ForeignKey, MetaData, Table, Float, Column, Integer, String, DateTime, Text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

#these two to create Relationship diagram
import codecs
import sadisplay

dbname="temp"
Base = declarative_base()

class Parent(Base):
    __tablename__ = 'Parent'
    id = Column(Integer, primary_key=True)
    #iddd = Column(Integer)
    #child_id = Column (Integer)
    child_id = Column(Integer, ForeignKey('child2.id'))
    child = relationship("Child")

class Child(Base):
    __tablename__ = 'child2'
    id = Column(Integer, primary_key=True)

def createtables (dbname):
    #create_engine('postgresql+psycopg2://user:password@hostname/database_name')

    engine = create_engine('postgresql://postgres:crop@localhost:5433/'+dbname)
    #con = engine.connect()
  
    Base.metadata.create_all(engine)

createtables (dbname)

desc = sadisplay.describe(globals().values())

with codecs.open('schema.plantuml', 'w', encoding='utf-8') as f:
     f.write(sadisplay.plantuml(desc))

with codecs.open('schema.dot', 'w', encoding='utf-8') as f:
     f.write(sadisplay.dot(desc))


