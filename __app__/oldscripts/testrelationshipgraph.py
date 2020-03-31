from sqlalchemy import (create_engine, ForeignKey, MetaData, Table, Float, Column, Integer, String, DateTime, Text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker, relationship
#these two to create Relationship diagram
import codecs
import sadisplay


#Is used to tell SQL that the classes we create are db tables'''
#Base = declarative_base()

#engine = create_engine('postgresql://postgres:crop@localhost:5433/dvdrental')
#Base.metadata.create_all(engine)


desc = sadisplay.describe(globals().values())

with codecs.open('schema.plantuml', 'w', encoding='utf-8') as f:
     f.write(sadisplay.plantuml(desc))

with codecs.open('schema.dot', 'w', encoding='utf-8') as f:
     f.write(sadisplay.dot(desc))



  