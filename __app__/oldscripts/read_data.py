from constants import CWD
import csv
import pandas as pd
import numpy as np

import test


def Load_Data (csvpath):

    try:
        datapath = CWD + csvpath
        df= pd.read_csv(datapath)
        print (df.head(n=2))
    except:
        print("Error with reading csv: ", csvpath)
    
    return (df)

  

#'''this function reads csv using numpy without pandas (not used in this instance)'''
#def Load_Data_np (filename):
#    print ("starting")
#    data= np.genfromtxt(file_name, delimiter=',', skipskip_header=1, conconverters= {0: lambda s: str(s)})
#    return data





        #with open(advantix_raw) as csv_file:
        #    csv_reader = csv.reader(csv_file, delimiter=',')
        #    for row in csv_reader:

