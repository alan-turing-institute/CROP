import os
import csv
import pandas as pd
import numpy as np


#gets the path of current working directory
CWD = os.getcwd()

def read_core_csv(csv_path):
    """
    Reads and loads csv data to a pandas df. 
    Used to load the synthetic core data such as sensors or locations.  
    """
    try:
        df= pd.read_csv(csv_path)
        return "", df
        #print (df.head(n=2))
    except:
        return "Error reading csv with path: s%" %(csv_path), None





#'''this function reads csv using numpy without pandas (not used in this instance)'''
#def Load_Data_np (filename):
#    print ("starting")
#    data= np.genfromtxt(file_name, delimiter=',', skipskip_header=1, conconverters= {0: lambda s: str(s)})
#    return data





        #with open(advantix_raw) as csv_file:
        #    csv_reader = csv.reader(csv_file, delimiter=',')
        #    for row in csv_reader:

