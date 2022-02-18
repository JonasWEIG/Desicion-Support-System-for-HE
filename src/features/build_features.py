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

def getDummies(semester, df, List, ColumnName):
    df[str(semester) + '_' + ColumnName + '_' + str(List[0])] = 0
    df.loc[df[ColumnName] <= List[0], str(semester) + '_' + ColumnName + '_' + str(List[0])] = 1
    for Element in List[1:]:
        df[str(semester) + '_' + ColumnName + '_' + str(Element)] = 0
        df.loc[(df[ColumnName] <= Element) & (df[ColumnName] > List[List.index(Element)-1]), str(semester) + '_' + ColumnName + '_' + str(Element)] = 1
    df[str(semester) + '_' + ColumnName + '_' + str(List[-1]) + '+'] = 0
    df.loc[df[ColumnName] > List[-1], str(semester) + '_' + ColumnName + '_' + str(List[-1])+ '+'] = 1
    
def drop_columns(df):
    df = df.drop(['MNR_neu', 'stg', 'stutyp', 'schwerpunkt_bei_abschluss', 'bestanden_x', 'Endnote', 'ECTS_final', 'Endsemester', 
                   'Fachsem_Final', 'geschl', 'gebdat', 'staat', 'hzbnote', 'hzb_erwerbsort', 'hzbart', 'hzbdatum', 'immadat',
                   'HZB_bis_Imma', 'HZB_art', 'semester_date', 'fachsem', 'Alter', 'bonus', 'angemeldet', 'bestanden_y',
                   'Status', 'Status_EN', 'Durchschnittsnote', 'nicht_bestanden', 'Durchschnittsnote_be', 'percentile'], axis=1)
    return df

def prepare_final_files(fachsem, df_studstart, df_path, df_demo, typ='bachelor'):
    
    if typ == 'bachelor':
        df_studstart_old = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_studstart_without_prediction.pkl'))
        #df_path = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_path.pkl'))
        #df_demo = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_demo.pkl'))
        #fachsem = 2
    else:
        df_studstart_old = pd.read_pickle(os.path.abspath('../../data/interim/master/df_studstart_without_prediction.pkl'))
        #df_path = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_path.pkl'))
        #df_demo = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_demo.pkl'))
        #fachsem = 2
    

    for fs in range(1,fachsem+1):
        if fs == 1:
            df_path_1 = df_path[df_path.fachsem == fs]
            df_path_1['nicht_bestanden'] = df_path_1['angemeldet'] - df_path_1['bestanden']
            
            #### prepare data
            Merge = pd.merge(df_studstart_old, df_demo, how= 'left', on = 'MNR_neu')
            Final = pd.merge(Merge, df_path_1, how= 'right', on = 'MNR_Zweit')
            df_PV = Final[Final.bestanden_x == 'PV']
            Final = Final[Final.bestanden_x != 'PV']
            
            #### compute independent variables
            getDummies(fs, df_PV, [5,10,15,20,25,30,35], 'bonus')
            getDummies(fs, df_PV, [20,25,30,35], 'Alter')
            getDummies(fs, df_PV, [1.5, 2, 2.5, 3, 3.5, 4], 'Durchschnittsnote')
            getDummies(fs, df_PV, [1.5, 2, 2.5, 3], 'hzbnote')
            getDummies(fs, df_PV, [1,2,3,4], 'nicht_bestanden')
            df_PV = getDummiesAndJoin(df_PV, 'HZB_typ')
            df_PV = getDummiesAndJoin(df_PV, 'HZB_bis_Imma_J')
            getDummies(fs, Final, [5,10,15,20,25,30,35], 'bonus')
            getDummies(fs, Final, [20,25,30,35], 'Alter')
            getDummies(fs, Final, [1.5, 2, 2.5, 3, 3.5, 4], 'Durchschnittsnote')
            getDummies(fs, Final, [1.5, 2, 2.5, 3], 'hzbnote')
            getDummies(fs, Final, [1,2,3,4], 'nicht_bestanden')
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
        else:
            df_path_2 = df_path[df_path.fachsem == fs]
            df_path_2['nicht_bestanden'] = df_path_2['angemeldet'] - df_path_2['bestanden']
            
            #### prepare data
            Merge = pd.merge(df_studstart_old, df_demo, how= 'left', on = 'MNR_neu')
            Final_2 = pd.merge(Merge, df_path_2, how= 'right', on = 'MNR_Zweit')
            df_PV_2 = Final_2[Final_2.bestanden_x == 'PV']
            Final_2 = Final_2[Final_2.bestanden_x != 'PV']
            
            #### compute independent variables
            getDummies(fs, df_PV_2, [5,10,15,20,25,30,35], 'bonus')
            getDummies(fs, df_PV_2, [1.5, 2, 2.5, 3, 3.5, 4], 'Durchschnittsnote')
            getDummies(fs, df_PV_2, [1,2,3,4], 'nicht_bestanden')
            getDummies(fs, Final_2, [5,10,15,20,25,30,35], 'bonus')
            #getDummies(fs, Final_2, [20,25,30,35], 'Alter')
            getDummies(fs, Final_2, [1.5, 2, 2.5, 3, 3.5, 4], 'Durchschnittsnote')
            #getDummies(fs, Final_2, [1.5, 2, 2.5, 3], 'hzbnote')
            getDummies(fs, Final_2, [1,2,3,4], 'nicht_bestanden')
            Final_2.iloc[:,-10:-1] = Final_2.iloc[:,-10:-1].astype(int)
            df_PV_2.iloc[:,-9:] = df_PV_2.iloc[:,-9:].astype(int)
            df_PV_2 = drop_columns(df_PV_2)
            Final_2 = drop_columns(Final_2)
            Final_2 = Final_2.drop(Final_2.columns[1:6], axis = 1)
            if typ != 'bachelor':
                df_PV_2 = df_PV_2.drop(df_PV_2.columns[1:6], axis = 1)
            Final = pd.merge(Final, Final_2, how = 'inner', on= 'MNR_Zweit')
            df_PV = pd.merge(df_PV, df_PV_2, how = 'inner', on= 'MNR_Zweit')
    #Final.to_pickle(os.path.abspath('../../data/interim/bachelor/df_Final.pkl'))
    return df_PV, Final

def add_probabilities(fachsem, df_studstart, df_path, df_demo, typ = 'bachelor'):
    
    df_PV, Final = prepare_final_files(fachsem, df_studstart, df_path, df_demo, typ)
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

#df_PV, Final = prepare_final_files(1, df_StudStart, df_Path, df_demo)   
    
    return df_studstart
'''
if __name__ == '__main__':
    df_studstart = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_studstart.pkl'))
    df_path = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_path.pkl'))
    df_demo = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_demo.pkl'))
    semesters = [2,3,4,5]
    
    for semester in semesters:
        df_studstart = prepare_final_files(1, df_studstart, df_path, df_demo)
    #df_studstart.to_csv(os.path.abspath('..\\WiSe2122\\csv\\df_studstart_bachelor_wise21.csv'), sep=';', decimal=',', encoding = 'utf-8')
'''