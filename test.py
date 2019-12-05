import sys
import pandas as pd
import sqlalchemy as db


engine = db.create_engine('postgresql://postgresql:crops@localhost:5433/cropdb')
connection = engine.connect()
print (sys.version)
