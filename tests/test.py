#import createdb
import main

#check if files are loaded in the dataframes
def check(file):
    try:
        #main.Readings_Advantix ()
        print ("itworked")
    except AssertionError:
        assert False, "  cant read csv"

check(df)


