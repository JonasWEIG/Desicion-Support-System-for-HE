# -*- coding: utf-8 -*-
"""
Created on Mon Feb  7 15:59:44 2022

@author: ba42pizo
"""
import pandas as pd
import os
import statsmodels.api as sm
#import matplotlib.pyplot as plt
#### finalize dataframe
def calculate_logit_model(fachsem, inkl_demo='yes'):
    df_studstart_old = pd.read_pickle(os.path.abspath('../data/interim/bachelor/df_studstart_without_prediction.pkl'))
    df_path = pd.read_pickle(os.path.abspath('../data/interim/bachelor/df_path.pkl'))
    df_demo = pd.read_pickle(os.path.abspath('../data/interim/bachelor/df_demo.pkl'))
    #fachsem = 1
    inkl_demo = 'yes'
    
    df_path_1 = df_path[df_path.fachsem == fachsem]
    df_path_1['nicht_bestanden'] = df_path_1['angemeldet'] - df_path_1['bestanden']
    
    #### prepare data
    Merge = pd.merge(df_studstart_old, df_demo, how= 'left', on = 'MNR_neu')
    Final = pd.merge(Merge, df_path_1, how= 'right', on = 'MNR_Zweit')
    Final = Final[Final.bestanden_x != 'PV']

    Final2 = Final.iloc[:,16:]
    if inkl_demo == 'yes':
        Final3 = Final2.drop(['hzb_erwerbsort', 'hzbart', 'hzbdatum', 'immadat', 'HZB_bis_Imma_J', 'semester_date', 
                          'fachsem', 'Status', 'Status_EN', 'Durchschnittsnote_be', 'bestanden_y', 'angemeldet',], axis = 1)
        Final3 = pd.get_dummies(Final3, columns=['HZB_art', 'HZB_typ', 'Region'], drop_first=False)
    else:
        Final3 = Final2.drop(['hzb_erwerbsort', 'hzbart', 'hzbdatum', 'immadat', 'HZB_bis_Imma_J', 
                          'HZB_art', 'HZB_typ', 'Region',  'semester_date', 
                          'fachsem', 'Status', 'Status_EN', 'Durchschnittsnote_be', 'bestanden_y', 'angemeldet',
                          'HZB_bis_Imma', 'Alter', 'hzbnote'], axis = 1)
    Final3.loc[Final3.hzbnote.isna(),'hzbnote'] = Final3.hzbnote.mean()
    Final3.loc[Final3.Durchschnittsnote.isna(),'Durchschnittsnote'] = 5
    Final3.loc[Final3.HZB_bis_Imma < 0, 'HZB_bis_Imma'] = 0
    Final3.loc[Final3.HZB_bis_Imma > 7000, 'HZB_bis_Imma'] = 7000
    Final3['Alter'] = Final3['Alter'].astype('int')
    normalized_df=(Final3-Final3.min())/(Final3.max()-Final3.min())
    Final['final'] = 0
    Final.loc[Final.bestanden_x == 'BE', 'final'] = 1
    y = Final.final

    #Final2['HZB_bis_Imma'].plot()
   
    model = sm.Logit(y, normalized_df)
    result =model.fit()
    result.summary2()
    
    normalized_df['bonus'].corr(normalized_df['Alter'])
    
calculate_logit_model(1)