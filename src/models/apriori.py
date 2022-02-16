# -*- coding: utf-8 -*-
"""
Created on Fri Feb 11 08:20:52 2022

@author: ba42pizo
"""

import pandas as pd
#import numpy as np
from mlxtend.frequent_patterns import apriori, association_rules
import os


def add_association_rules(df_layers, df_StudStart, min_support = 0.2):  

    df_apri = pd.merge(df_layers, df_StudStart[['MNR_Zweit', 'ECTS_final']], how= 'left', on = 'MNR_Zweit')
    #df_apri = pd.merge(df_apri, df_clusters[['MNR_Zweit', 'y_predicted']], how = 'left', on = 'MNR_Zweit')
    
    df_apri = df_apri[df_apri.ECTS_final != 0]
    
    studiengangs = pd.unique(df_apri.studiengang).tolist()
    studiengang = 'Wirtschaftswissenschaften'
    df_final = pd.DataFrame()
    for studiengang in studiengangs:
        # select modules with mnote > 3.4
        df = df_apri.loc[(df_apri.note_m2 > 3.2) & (df_apri.studiengang == studiengang) &
                         (df_apri.Startsemester > 20131),]
        min_support = 0.02
        # one hot encoding modultitel
        df = pd.concat([df['MNR_Zweit'], pd.get_dummies(df['modultitel'])], axis = 1)
        
        # group by mnr_zweit & do apriori and association
        df = df.groupby(by = ['MNR_Zweit']).max()
        df_apr = apriori(df, min_support = min_support, use_colnames = True, verbose = 1, max_len = 2)
        df_ar = association_rules(df_apr, metric = 'confidence', min_threshold = 0.65)
        
        # add lists
        df_ar['associate'] = df_ar.loc[:,'antecedents'].apply(list)
        df_ar['consequ'] = df_ar['consequents'].apply(list)
        df_ar['modultitel'] = df_ar['associate'].apply(lambda x: ','.join(map(str, x)))
        df_ar['problem'] = df_ar['consequ'].apply(lambda x: ','.join(map(str, x)))
        df = df_layers.loc[(df_layers.note_m2 > 3.2) & (df_layers.studiengang == studiengang) & 
                           (df_layers.bestanden == 'PV'), ['MNR_Zweit', 'modultitel', 'note_m2']]
        test = df.merge(df_ar[['modultitel', 'problem']], on = 'modultitel', how = 'left')
        test = test.drop_duplicates()
        
        df2 = df_layers.loc[(df_layers.studiengang == studiengang) & 
                           (df_layers.bestanden == 'PV'), ['MNR_Zweit', 'modultitel', 'note_m2']]
        test2 = test.merge(df2, on = ['MNR_Zweit', 'modultitel'], how = 'right')
        test2 = test2.drop_duplicates()
      
        mnrs = pd.unique(test2.MNR_Zweit)
         
        for mnr in mnrs:
            titles = pd.unique(test2.loc[test2.MNR_Zweit == mnr, 'problem'])
            liste = pd.unique(test2.loc[test2.MNR_Zweit == mnr, 'modultitel'])
            for title in titles:
                if title not in liste:
                    test2.loc[(test2.MNR_Zweit == mnr) & (test2.problem == title), 'real'] = title
                    
        df = test2[test2.real.notna()]
        df = df[['MNR_Zweit', 'modultitel', 'problem']]
        df = df.merge(df_ar[['problem', 'modultitel', 'lift', 'confidence']], on = ['problem', 'modultitel'], how = 'left')  
        df_final = pd.concat([df, df_final], ignore_index = True, sort = True)
        df_ar.to_csv(os.path.abspath('../../data/processed/apriori_data/df_apriori_ba_' + studiengang + '.csv'), sep=';', decimal=',', encoding = 'utf-8')
     
    return df_final

if __name__ == '__main__':
    
    df_layers = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_layers.pkl'))
    df_StudStart = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_studstart.pkl'))    
    
    df_final = add_association_rules(df_layers, df_StudStart)   
    df_final.to_pickle(os.path.abspath('../../data/interim/bachelor/df_apriori.pkl'))
    df_final.to_csv(os.path.abspath('../../data/processed/bachelor/df_apriori.csv'), sep=';', decimal=',', encoding = 'utf-8')
        

