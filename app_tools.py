import pandas as pd
import numpy as np
import json
import os

import settings
import ml_tools
import datetime
from tensorflow.keras.models import load_model
# with open(settings.conf_u_path) as config_file:
#     conf = json.load(config_file)

# data = pd.read_excel(settings.ex_data, sheet_name='data')
# data['DateTime'] = pd.to_datetime(data['DateTime'])
# data.set_index('DateTime', inplace=True)
# #data = data[:-120]
# data = data.astype(float)
# #data = data['ENERGY']
# data[conf["y_var"]].astype(float)

#---------------------------------------------
def get_lib_models():
    list_model = []
    list_config = []
    model_type = '_u'
    with os.scandir(settings.app_models_path) as folders:
        folders = [folders.name for folders in folders if folders.is_dir()]  
        
    for folder in folders:
        with os.scandir(settings.app_models_path +'/' +folder ) as files:
            files = [files.name for files in files if files.is_file() and files.name.endswith(model_type +'.h5')]
        model = load_model(settings.app_models_path +'/' + folder +'/' +files[0])
        list_model.append(model)
        with os.scandir(settings.app_models_path +'/' +folder ) as files:
            files = [files.name for files in files if files.is_file() and files.name.endswith('config.json')]
            with open(settings.app_models_path +'/' + folder +'/' +files[0]) as config_file:
                conf = json.load(config_file)
        list_config.append(conf)
    return list_config, list_model

def get_lib_models_config():
    list_config = []
    with os.scandir(settings.app_models_path) as folders:
        folders = [folders.name for folders in folders if folders.is_dir()]  
        
    for folder in folders:
        with os.scandir(settings.app_models_path +'/' +folder ) as files:
            files = [files.name for files in files if files.is_file() and files.name.endswith('config.json')]
            with open(settings.app_models_path +'/' + folder +'/' +files[0]) as config_file:
                conf = json.load(config_file)
        list_config.append(conf)
    return list_config, folders

def get_model_by_folderindex(folders, index):
    model_type = '_u'
    with os.scandir(settings.app_models_path +'/' + folders[index] ) as files:
        files = [files.name for files in files if files.is_file() and files.name.endswith(model_type +'.h5')]
    model = load_model(settings.app_models_path +'/' + folders[index] +'/' +files[0], compile=False)
    return model
    
#---------------------------------------------
def dict_compare(d1, d2):
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    shared_keys = d1_keys.intersection(d2_keys)
    same = set(o for o in shared_keys if d1[o] == d2[o])
    return same
#---------------------------------------------
#list_config, list_model = get_lib_models()
def find_model(list_config, list_model, query):
    foud_index=None
    for i in range(len(list_config)):
        if dict_compare(list_config[i], query) == set(query.keys()):
            foud_index=i
    if foud_index is None:
        return [],[]
    else:
        return list_model[foud_index], list_config[foud_index]

def find_model_by_config(list_config, query):
    foud_index=None
    for i in range(len(list_config)):
        if dict_compare(list_config[i], query) == set(query.keys()):
            foud_index=i
    if foud_index is None:
        return [],[]
    else:
        return  list_config[foud_index], foud_index
#------------------------------------------------
    
def get_data_2_predict(data, conf, date):
    #data= data[conf["y_var"]]
    date_time_str = date
    date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
    last_val = date_time_obj - datetime.timedelta(hours= 1)
    first_val =  last_val - datetime.timedelta(hours= conf["past_hist"])
    data = data.loc[first_val:last_val]
    if len(data) != conf["past_hist"]:
        data=data.iloc[1:]
    data_r, data_mean, data_std = ml_tools.normalize(data[conf["y_var"]].values)
    data_r.reshape((len(data_r),1))
    return data, data_r, data_mean, data_std

#---------------------------------------------
def make_prediccion(model, n_ahead, data, data_r, data_mean_2, data_std_2):
    data_r.reshape((len(data_r),1))
    yhat = ml_tools.predict_n_ahead(model, n_ahead, data_r)
    yhat = ml_tools.desnormalize(np.array(yhat), data_mean_2, data_std_2)
    yhat = ml_tools.model_out_tunep(yhat)
    #-----------------------------------------------
#    graphs.plot_next_forecast(data, yhat, n_ahead, save=True)
    fc = ml_tools.forecast_dataframe(data, yhat, n_ahead)
    return fc
#----------------------------------------------------
def compare_df(data_master,fc):
    p_df = fc.loc[fc["type"]=='forecast']    
    t_strt = p_df["DateTime"].iloc[0]
    t_end = p_df["DateTime"].iloc[-1]
    r_df = data_master.loc[t_strt:t_end]
#    r_mean = r_df["ENERGY"].values.mean()
#    r_sum = r_df["ENERGY"].values.sum()
    comp_df = fc
    comp_df.set_index("DateTime", inplace = True)
    comp_df = comp_df.rename(columns = {'ENERGY':'Prediccion'})
    r_df= r_df["ENERGY"]
    comp_df = comp_df.join(r_df)
    comp_df = comp_df.rename(columns = {'ENERGY':'Real'})
    comp_df.Real.fillna(comp_df.Prediccion, inplace=True)
    return comp_df

def comp_stats(comp_df):
    comp = comp_df.loc[comp_df["type"]=='forecast']
    p_mean = comp["Prediccion"].values.mean()
    p_sum = comp["Prediccion"].values.sum()
    p_max = comp["Prediccion"].values.max()
    r_mean = comp["Real"].values.mean()
    r_sum = comp["Real"].values.sum()
    r_max = comp["Real"].values.max()
    stats_dic={'Suma':[p_sum, r_sum],'Media':[p_mean, r_mean],'M??ximo':[p_max, r_max]}
    stats_df = pd.DataFrame(stats_dic, index=['Prediccion', 'Real'])
    return stats_df
#----------------------------------------------------
