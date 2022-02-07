# -*- coding: utf-8 -*-
"""
Created on Thu Nov  4 11:29:10 2021

@author: ba42pizo
"""
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import numpy as np
from sklearn.model_selection import train_test_split
import sklearn
from sklearn import metrics
from sklearn.linear_model import LogisticRegression


#### define one hot encodings and final dfs
def getDummiesAndJoin(df, ColumnName):
    Dummies = pd.get_dummies(df[ColumnName])
    df = df.drop(ColumnName, axis = 1)
    df = df.join(Dummies)
    return df

def getDummies(df, List, ColumnName):
    df[ColumnName + '_' + str(List[0])] = 0
    df.loc[df[ColumnName] <= List[0], ColumnName + '_' + str(List[0])] = 1
    for Element in List[1:]:
        df[ColumnName + '_' + str(Element)] = 0
        df.loc[(df[ColumnName] <= Element) & (df[ColumnName] > List[List.index(Element)-1]), ColumnName + '_' + str(Element)] = 1
    df[ColumnName + '_' + str(List[-1]) + '+'] = 0
    df.loc[df[ColumnName] > List[-1], ColumnName + '_' + str(List[-1])+ '+'] = 1
    
def drop_columns(df):
    df = df.drop(['MNR_neu', 'stg', 'stutyp', 'schwerpunkt_bei_abschluss', 'bestanden_x', 'Endnote', 'ECTS_final', 'Endsemester', 
                   'Fachsem_Final', 'geschl', 'gebdat', 'staat', 'hzbnote', 'hzb_erwerbsort', 'hzbart', 'hzbdatum', 'immadat',
                   'HZB_bis_Imma', 'HZB_art', 'semester_date', 'fachsem', 'Alter', 'bonus', 'angemeldet', 'bestanden_y',
                   'Status', 'Status_EN', 'Durchschnittsnote', 'nicht_bestanden', 'Durchschnittsnote_be'], axis=1)
    return df

def prepare_final_files(fachsem, df_studstart, df_path, df_demo):
    #df_studstart = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_studstart.pkl'))
    #df_path = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_path.pkl'))
    #df_demo = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_demo.pkl'))
    #fachsem = 2
    df_path = df_path[df_path.fachsem == fachsem]
    df_path['nicht_bestanden'] = df_path['angemeldet'] - df_path['bestanden']
    
    #### prepare data
    Merge = pd.merge(df_studstart, df_demo, how= 'left', on = 'MNR_neu')
    Final = pd.merge(Merge, df_path, how= 'right', on = 'MNR_Zweit')
    df_PV = Final[Final.bestanden_x == 'PV']
    Final = Final[Final.bestanden_x != 'PV']
    
    #### compute independent variables
    getDummies(df_PV, [5,10,15,20,25,30,35], 'bonus')
    getDummies(df_PV, [20,25,30,35], 'Alter')
    getDummies(df_PV, [1.5, 2, 2.5, 3, 3.5, 4], 'Durchschnittsnote')
    getDummies(df_PV, [1.5, 2, 2.5, 3], 'hzbnote')
    getDummies(df_PV, [1,2,3,4], 'nicht_bestanden')
    df_PV = getDummiesAndJoin(df_PV, 'HZB_typ')
    df_PV = getDummiesAndJoin(df_PV, 'HZB_bis_Imma_J')
    getDummies(Final, [5,10,15,20,25,30,35], 'bonus')
    getDummies(Final, [20,25,30,35], 'Alter')
    getDummies(Final, [1.5, 2, 2.5, 3, 3.5, 4], 'Durchschnittsnote')
    getDummies(Final, [1.5, 2, 2.5, 3], 'hzbnote')
    getDummies(Final, [1,2,3,4], 'nicht_bestanden')
    Final = getDummiesAndJoin(Final, 'HZB_typ')
    Final = getDummiesAndJoin(Final, 'HZB_bis_Imma_J')
    Final = getDummiesAndJoin(Final, 'Region')
    df_PV = getDummiesAndJoin(df_PV, 'Region')
    Final.iloc[:,-10:-1] = Final.iloc[:,-10:-1].astype(int)
    df_PV.iloc[:,-9:] = df_PV.iloc[:,-9:].astype(int)
    
    #### add dependent variable
    Final['final'] = 0
    Final.loc[Final.bestanden_x == 'BE', 'final'] = 1
    df_PV = drop_columns(df_PV)
    Final = drop_columns(Final)
    
    #### train
    x_train, x_test, y_train, y_test = train_test_split(Final.iloc[:,3:-1], Final.iloc[:,-1], test_size = 0.25, random_state = 0)

    logReg = LogisticRegression()
    logReg.fit(x_train, y_train)
    #score = logReg.score(x_test, y_test)
    Final['Bestehenswahrscheinlichkeit_' + str(fachsem)] = logReg.predict_proba(Final.iloc[:,3:-1])[:,1]
    df_PV['Bestehenswahrscheinlichkeit_' + str(fachsem)] = logReg.predict_proba(df_PV.iloc[:,3:])[:,1]

    df_studstart = df_studstart.merge(df_PV[['MNR_Zweit', 'Bestehenswahrscheinlichkeit_' + str(fachsem)]], on = ['MNR_Zweit'], how = 'left')
    df_studstart.loc[df_studstart.bestanden == 'BE', 'Bestehenswahrscheinlichkeit_' + str(fachsem)] = 1
    df_studstart.loc[df_studstart.bestanden == 'EN', 'Bestehenswahrscheinlichkeit_' + str(fachsem)] = 0

    #df_studstart.to_pickle(os.path.abspath('..\\WiSe2122\\pickles\\df_studstart_bachelor_wise21_ext_' + fachsem + '.pkl'))
    #df_MNR.to_csv(os.path.abspath('..\\WiSe2122\\csv\\df_studstart_bachelor_wise21.csv'), sep=';', decimal=',', encoding = 'utf-8')
    
    return df_studstart

df_studstart = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_studstart.pkl'))
df_Path = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_path.pkl'))
df_demo = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_demo.pkl'))
df_Studstart = prepare_final_files(1, df_studstart, df_Path, df_demo)
semesters = [2,3,4,5]
for semester in semesters:
    df_Studstart = prepare_final_files(semester, df_Studstart, df_Path, df_demo)
