# -*- coding: utf-8 -*-
"""
Created on Mon Feb  7 16:00:56 2022

@author: ba42pizo
"""

import pandas as pd
import numpy as np
import os
import seaborn as sns
import matplotlib.pyplot as plt
import sys
import pickle
sys.path.append('../features')
from build_features import prepare_final_files

#### visualisation of independent variables

df_studstart = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_studstart.pkl'))
df_Path = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_path.pkl'))
df_demo = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_demo.pkl'))
Final = prepare_final_files(1, df_studstart, df_Path, df_demo)[1]
Final = Final.rename(columns={'> 3 Jahre': '+ 3 Jahre'})

def visualization_of_independent_variables():
    for f in list(Final.iloc[:,3:].columns.values):
        plt.figure(f)
        #f = f.replace(">", "+")
        sns.countplot(x = f, data = Final, hue = 'final', palette = 'Set3').figure.savefig(os.path.abspath('../../reports/figures/plot_' + f +'.png'))
    

### visualize feature importance ###
def visualize_feature_importance():
    #from sklearn.ensemble import RandomForestClassifier
    Finals =Final.drop(['MNR_Zweit', 'Startsemester', 'studiengang', 'final'], axis = 1)
                                                        
    modelrf = pickle.load(open(os.path.abspath('../../models/modelrf_pickle'), 'rb'))
    
    importance = modelrf.feature_importances_
    
     #Create arrays from feature importance and feature names
    feature_importance = np.array(importance)
    heads = list(Finals)
    feature_names = np.array(heads)
    
    #Create a DataFrame using a Dictionary
    data={'feature_names':feature_names,'feature_importance':feature_importance}
    fi_df = pd.DataFrame(data)
    
    #Sort the DataFrame in order decreasing feature importance
    fi_df.sort_values(by=['feature_importance'], ascending=False,inplace=True)
    
    #Define size of bar plot
    plt.figure(figsize=(10,8))
    #Plot Searborn bar chart
    sns.barplot(x=fi_df['feature_importance'], y=fi_df['feature_names'])
    #Add chart labels
    plt.title('RF FEATURE IMPORTANCE')
    plt.xlabel('FEATURE IMPORTANCE')
    plt.ylabel('FEATURE NAMES') 
