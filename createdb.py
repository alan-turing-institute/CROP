#libraries
import psycopg2
import sqlalchemy as sqla
from sqlalchemy_utils import database_exists


'''Checks if database exists, else it creates it and creates the tables.''' 
def Check_db_Status(db_string, defaultdb_string, tables):
    if not database_exists(db_string):
        Create_Database(defaultdb_string) #function to create database
        Test_Tables_Exist(db_string, tables) #fucntion to create the tables
        print(db_string+ " database created")
    else:
        print("db exists already")     
        Test_Tables_Exist(db_string, tables) #function to test if all tables already exist

'''Funtion to create a new database'''
def Create_Database(defaultdb_string):
    #On postgres, three databases are normally present by default. If you are
    # able to connect as a superuser (eg, the postgres role), then you can
    # connect to the postgres or template1 databases. The default pg_hba.conf
    # permits only the unix user named postgres to use the postgres role, so
    # the simplest thing is to just become that user. At any rate, create an
    # engine as usual with a user that has the permissions to create a database
    engine = sqla.create_engine(defaultdb_string)

    #You cannot use engine.execute() however, because postgres does not allow you to create databases inside transactions, and sqlalchemy always tries to run queries in a transaction. To get around this, get the underlying connection from the engine:
    conn = engine.connect()

    #But the connection will still be inside a transaction, so you have to end the open transaction with a commit:
    conn.execute("commit")

    #And you can then proceed to create the database using the proper PostgreSQL command for it.
    conn.execute("create database " + dbname)
    conn.close()   


'''fucntion to test if there are all the tables there and if not store new table names in lists'''
def Test_Tables_Exist(dbname, tables):
    #access the newly created database
    engine = sqla.create_engine('postgresql://postgres:crop@localhost:5433/'+ dbname)
    #get a list of existing tables in the db (access db)
    table_names = sqla.inspect(engine).get_table_names()
    
    #check if a specific table doesn't exist and stores its name in a list
    listofnewtables=[]
    for i in range  (len (tables)):
         if not engine.dialect.has_table(engine, tables[i]):
             listofnewtables.append(tables[i])
             print ("it doesnt have: " + tables[i])
         else:
             print ("it has: " + tables[i])

    #Checks if there is any new tables in the database and generates them. 
    if listofnewtables !=[] :
        #imports the file for creating all the tables
        import createtables
        #stores a list with all the new tables (currently not used)
        createtables.newtables=listofnewtables #<--- this one creates all tables, how can i create just one?? #subclass?
        #creates all the tables
        createtables.Createdb(dbname)
        
        print ("tables created")
    else:
        print ("no new tables in db")





