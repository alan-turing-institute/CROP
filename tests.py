#import createdb
import main

#check if files are loaded in the dataframes
def checkloadcsv():
    try:
        df= main.Readings_Advantix ()
        print ("itworked")
    except AssertionError:
        assert False, "Cant read csv"

checkloadcsv()

