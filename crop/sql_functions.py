#import datetime
#import psycopg2
#import sqlalchemy as sqla
import pandas as pd
from sqlalchemy.orm import sessionmaker, relationship

# NOTE: switch to sqlite for convinience. 


def read_core_csv(csv_path):
    """
    Reads and loads csv data to a pandas df. 
    Used to load the synthetic core data such as sensors or locations.  
    """
    print (csv_path)
    try:
        df= pd.read_csv(csv_path)
        print (df.head(n=2))
        return True, "", df
    except:
        return False, "Error reading csv with path: %s" % csv_path, None


def bulk_insert_df (engine, Data, Class):
    """
    Bulk insert data into the database. 
    It creates a new connection which binds the engine and then pulls the df in a dictionary. 
    """
    
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
    #print (Data)
    #s.bulk_insert_mappings(Sensor, Data.to_dict(orient="records"))   #with everychange in the csv, it doesnt replace data, it adds them in. probably need a uuid or delete everything before. 
    #commits the changes of the session
    s.commit()
    s.close()
    return (Data)

def update_df (engine, Data, Class):
    """
    Bulk update data into the database. 
    Can update values based on id but cant insert new.
    """
    #Creates/Opens a new session (connection to the db)
    session = sessionmaker()
    #binds the engine to this session
    session.configure(bind=engine)
    s = session()

    #listentries
    #dict = Data.to_dict(orient="records")
    #print (dict)
    
    

        #entry = Class(type_id=5, sensor_type="hola", description = "sldkjfsldkj")
    #s.add(Class(type_id=5, sensor_type="hola", description = "sldkjfsldkj"))
    #s.add_all(Class(Data.to_dict(orient="records")))
    #s.bulk_update_mappings(Class, Data.to_dict(orient="records"))

    s.commit()
    s.close()
    return (Data)
 
def merge_df (engine, Data, Class):
    """
    Bulk update data into the database. 
    Can update values based on id but cant insert new.
    """
    
    #Creates/Opens a new session (connection to the db)
    session = sessionmaker()
    #binds the engine to this session
    session.configure(bind=engine)
    s = session()
    
    #TODO: TRY TO FIND A SOLUTION FOR UPDATING DATA
    for row in Data: 
        s.add(Class, row)
    
    s.bulk_update_mappings(Class, Data.to_dict(orient="records"))

    s.commit()
    s.close()
    return (Data)


def check_sensor_exists (device_id, type_id, df_type, df_device_id):
    """
    Checks if a sensor exists in the db. 
    """
    
    # Creates a new session
    session = sessionmaker()
    
    # Binds the engine to this session
    session.configure(bind=engine)
    s = session()

    # Accesses databases
    iengine = inspect(engine)

    #print (tables)
    sensors_list = session.query(type_id).filter_by(name=str(df_type)).scalar() is not None
    print (sensors_list)

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

