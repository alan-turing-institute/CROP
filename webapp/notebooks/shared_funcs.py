import requests
import numpy as np 
import pandas as pd 
import itertools

def get_live_data():
    r = requests.get("https://cropapptest.azurewebsites.net/queries/harvests")
    df = pd.DataFrame.from_dict(r.json())
    df['event_time'] = pd.to_datetime(df['event_time'])
    return df 


def get_synth_data(df=None):

    if df is None:
        df = get_live_data()

    cols_to_normal_sample = ['crop_yield', 'number_of_trays','over_production', 'waste_defect', 'waste_disease']

    date_samples = pd.date_range(start=df['event_time'].min(),
                    end=pd.to_datetime('today'),
                    periods=10000)

    parameter_samples = {}

    for col in df.columns:
        if col == 'event_time':
            parameter_samples[col] = date_samples
            continue
        parameter_samples[col] = df[col].unique()

    def build_row_dict(parameters, df):
        row = {}
        # one option is just shuffle existing data i.e.: 
        # row = {k:np.random.choice(v) for k,v in parameters.items()}
        # but lets make numbers for things a bit random to add something somewhat
        # interesting and varied? 

        for k,v in parameters.items():
            row[k] = np.random.choice(v) if k not in cols_to_normal_sample else np.floor(np.abs(np.random.normal(df[k].mean(), df[k].std())))
        return row 
        
    def make_table_synth_data(parameter_samples, df, n=100):
        data = [build_row_dict(parameter_samples, df) for _ in range(n)]
        return pd.DataFrame(data)

    return make_table_synth_data(parameter_samples, df)
    