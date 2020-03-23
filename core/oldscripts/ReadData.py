import os
import csv
import pandas as pd
import numpy as np

import test


#gets the path of current working directory
CWD = os.getcwd()

def Load_Data (csvpath):

    try:
        datapath = CWD + csvpath
        df= pd.read_csv(datapath)
    except:
        print("Error with reading csv: ", csvpath)
    print (df.head(n=2))
    return (df)



def Readings_Advantix ():
    try:
        #advantix_cleaned = CWD+ "\\Data\\Cleaned\\data-20190821-pt00.csv"
        advantix_raw_path = CWD + "\\Data\\Raw\\raw-20191127-pt01.csv"
        #data= pd.read_csv(advantix_cleaned)
        advantix_raw= pd.read_csv(advantix_raw_path)
        #print (advantix_raw.head())
        return (advantix_raw)

    except:
        print("Can't read raw advantix readings csv")


  

'''this function reads csv using numpy without pandas (not used in this instance)'''
def Load_Data_np (filename):
    print ("starting")
    data= np.genfromtxt(file_name, delimiter=',', skipskip_header=1, conconverters= {0: lambda s: str(s)})
    return data





        #with open(advantix_raw) as csv_file:
        #    csv_reader = csv.reader(csv_file, delimiter=',')
        #    for row in csv_reader:

