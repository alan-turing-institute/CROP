#files
import createtables as tbls
#libraries
import datetime
import psycopg2
import sqlalchemy as sqla
from sqlalchemy.orm import sessionmaker, relationship

# NOTE: switch to sqlite for convinience. 
    
def populatesensors (dbname, Data, Class):
    #creates a connection to PostgreSQL
    engine = sqla.create_engine('postgresql://postgres:crop@localhost:5433/'+dbname)
    #Creates the database with all the Base Classes
    #Base.metadata.create_all(engine)
    
    #Creates/Opens a new session (connection to the db)
    session = sessionmaker()
    #binds the engine to this session
    session.configure(bind=engine)
    s = session()
    #is used to add data generaly
    #s.add(Rawdata) 
        
    #Bulks insterst the data to the database (fastest and best method)(matches names of headers autoatically as long as they are declared in the class)

    # if one of these doesnt work, just delete the tables from the postgres
    #session bulk is the fastest and best way to import 
    s.bulk_insert_mappings(Class, Data.to_dict(orient="records"))
    print ("stored: " , Data)
    #s.bulk_insert_mappings(Sensor, Data.to_dict(orient="records"))   #with everychange in the csv, it doesnt replace data, it adds them in. probably need a uuid or delete everything before. 
    #commits the changes of the session
    s.commit()
    s.close()



#def Populatedb():
#    try: 
#        #Creates/Opens a new session (connection to the db)
#        session = sessionmaker()
#        #binds the engine to this session
#        session.configure(bind=engine)
#        s = session()
#        #is used to add data generaly
#        #s.add(Rawdata) 
        
#        #Bulks insterst the data to the database (fastest and best method)(matches names of headers autoatically as long as they are declared in the class)

#        # if one of these doesnt work, just delete the tables from the postgres
#        s.bulk_insert_mappings(ReadingsAdvantix, Advantix_Data.to_dict(orient="records"))
#        s.bulk_insert_mappings(Type, Sensor_Types_data.to_dict(orient="records"))   #with everychange in the csv, it doesnt replace data, it adds them in. probably need a uuid or delete everything before. 
#        #commits the changes of the session
#        s.commit()
#    except:
#        print ("commits were not made")
    
#    finally:
#        #closses the session
#        s.close()


#        #with open(advantix_raw) as csv_file:
#        #    csv_reader = csv.reader(csv_file, delimiter=',')
#        #    for row in csv_reader:
#        #       print(row)

