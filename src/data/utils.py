# -*- coding: utf-8 -*-
"""
Created on Fri Feb  4 13:52:56 2022

@author: ba42pizo
"""
import argparse
import pandas as pd
import numpy as np
import os


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--student_data_ba', type=str, default='../../data/raw/20102021_WISO-Studierendendaten_3_BA_20212.csv',
                    help='path to bachelor student data')

    parser.add_argument('--exam_data_ba', type=str, default='../../data/raw/20102021_WISO-Leistungsdaten_BA_20212.csv',
                    help='path to  bachelor exam data')

    parser.add_argument('--next_master_study_ba', type=str, default='../../data/raw/20102021_WISO-Studierendendaten_3_MA_20212.csv',
                    help='path to master student data for identifiing next study')    
    
    parser.add_argument('--exam_regulation_ba', type=str, default='../../data/external/po_bachelor_sose21.csv',
                    help='obligatory modules bachelor')    
    
    parser.add_argument('--student_data_ma', type=str, default='../../data/raw/20102021_WISO-Studierendendaten_4_MA_20212.csv',
                    help='path to master student data')

    parser.add_argument('--exam_data_ma', type=str, default='../../data/raw/20102021_WISO-Leistungsdaten_2_MA_20212.csv',
                    help='path to  master exam data')

    parser.add_argument('--last_bachelor_study_ma', type=str, default='../../data/raw/20102021_WISO-Studierendendaten_3_BA_20212.csv',
                    help='path to  bachelor student data for identifiing last study')    
    
    parser.add_argument('--exam_regulation_ma', type=str, default='../../data/external/po_master_sose21.csv',
                    help='obligatory modules master')    
    
    parser.add_argument('--city_names', type=str, default='../../data/external/stadtnamen_by.csv',
                    help='city names for classifying HZB type')    
    
    parser.add_argument('--current semester', type=int, default=20212,
                        help='current semester')
    
    

    return parser.parse_args()


def clean_exam(exam_data):
    #exam_data = df_PrufData
    exam_data = exam_data.astype({'bonus': float})
    # clean pnote
    wrg_str = ['+  ', '-  ', 'NE ','RW ', 'VOU']
    for strs in wrg_str:
        exam_data.loc[exam_data.pnote == strs, 'pnote'] = np.nan
    exam_data = exam_data.astype({'pnote': float})

    # add module structure
    exam_data['Modulebene_1'] = exam_data['pfad'].str.extract('\,\d{4},(\d{5})', expand = True)
    exam_data['Modulebene_2'] = exam_data['pfad'].str.extract('(\d{5}),\d{5}\}$', expand = True)
    exam_data['Bereich_1'] = exam_data['pfad'].str.extract('2000,\d?\d?\d?\,?(\d{4}),', expand = True)
    exam_data['Bereich_2'] = exam_data['pfad'].str.extract('\,(\d{4}),\d{5}', expand = True)
    exam_data['study_sp'] = exam_data['pfad'].str.extract('2000,(\d?\d?\d?)\,?\d{4},', expand = True)
    exam_data['study_sp'] = pd.to_numeric(exam_data['study_sp'], errors = 'coerce').astype('float')
    lays = ['Modulebene_1', 'Modulebene_2', 'Bereich_1', 'Bereich_2']
    for empty in lays:
        exam_data[empty] = exam_data[empty].fillna(0)
    exam_data = exam_data.astype({'Modulebene_1': int,
                                      'Modulebene_2': int,
                                      'Bereich_1': int,
                                      'Bereich_2': int})
        
    # add studytype
    exam_data['stg'] = exam_data['pnr_zu'].str.extract('\d{2}\/(\d{3})', expand = True)
    
    # check if exam_data contains bachelor data
    if exam_data.prftitel.str.contains('Bachelorarbeit').any():
        
        #correct wrong bonus
        exam_data.loc[(exam_data.prftitel == 'Unternehmensplanspiel (Kurztest)') &
                        (exam_data.bonus == 1100), 'bonus'] = 3
                            
        # add Bachelorarbeit
        exam_data.loc[exam_data.prftitel == 'Bachelorarbeit', 'Modulebene_1'] = 1997
        exam_data.loc[exam_data.prftitel == 'Bachelorarbeit', 'Modulebene_2'] = 1997
        exam_data.loc[exam_data.prftitel == 'Bachelorarbeit', 'Bereich_1'] = 1997
        exam_data.loc[exam_data.prftitel == 'Bachelorarbeit', 'Bereich_2'] = 1997
        exam_data.loc[(exam_data.prftitel == 'Bachelorarbeit') & (exam_data.pstatus == 'BE'), 'bonus'] = 15 
        
        # add studytype
        exam_data['stg'] = exam_data['pnr_zu'].str.extract('\d{2}\/(\d{3})', expand = True)
    
    # check if exam_data contains master data    
    elif exam_data.prftitel.str.contains('Masterarbeit').any():    
        # add Masterarbeit
        exam_data.loc[exam_data.pnr == 1999, 'Modulebene_1'] = 1997
        exam_data.loc[exam_data.pnr == 1999, 'Modulebene_2'] = 1997
        exam_data.loc[exam_data.pnr == 1999, 'Bereich_1'] = 1997
        exam_data.loc[exam_data.pnr == 1999, 'Bereich_2'] = 1997

        # economics
        exam_data.loc[(exam_data.pnr == 1999) & (exam_data.pstatus == 'BE') &
                        ((exam_data.stg == '636') | (exam_data.stg == '673')), 'bonus'] = 30 

    return exam_data


def concate_all_data(exam_data, study_data):
    #study_data = df_StudData
    study_data = study_data.sort_values(by=['mtknr', 'semester'], ascending = [True, True])
    exam_data = exam_data.rename(columns = {'psem' : 'semester'})
    exam_data = exam_data.sort_values(by=['mtknr', 'semester'], ascending = [True, True])
    
    # add matriculation numbers
    i = 1
    MNRs = pd.unique(study_data['mtknr']).tolist()
    for MNR in MNRs:
        study_data.loc[study_data.mtknr == MNR, 'MNR_neu'] = i
        stgs = pd.unique(study_data.loc[study_data.mtknr == MNR, 'stg'].tolist())
        j = 1
        for stg in stgs:
            study_data.loc[(study_data.mtknr == MNR) & (study_data.stg == stg), 'MNR_Zweit'] = i*10+j
            j += 1  
        i += 1   
    exam_data = exam_data[(exam_data.Bereich_1 !=0) |(exam_data.prftitel == 'Gesamtkonto') ]
    exam_data = exam_data[exam_data.stg.notna()]
    exam_data = exam_data.astype({'mtknr': int, 'stg': int} )
    study_data = study_data.astype({'mtknr': int, 'stg': int} )
    data_concenated = exam_data.merge(study_data, on=['mtknr', 'stg', 'semester'], how='outer')        
    data_concenated = data_concenated.sort_values(by=['mtknr', 'semester'], ascending = [True, True]) 
    data_concenated = data_concenated.reset_index(drop=True)
    
    if 'schwerpunkt_bei_abschluss' not in data_concenated:
        data_concenated['schwerpunkt_bei_abschluss'] = np.nan
    
    # delete wrong HZB note
    data_concenated.loc[data_concenated.hzbnote == 450, 'hzbnote'] = np.nan
            
    # comlete MNRs, fachsem and study from Semester after finishing study       
    idex_ganz = data_concenated.index[data_concenated['MNR_neu'].isnull()].tolist()
    for zeile in idex_ganz:
        if (data_concenated.loc[zeile, 'mtknr'] == data_concenated.loc[zeile - 1, 'mtknr']) & (data_concenated.loc[zeile, 'stg'] == data_concenated.loc[zeile - 1, 'stg']):
            data_concenated.loc[zeile, ['MNR_neu', 'MNR_Zweit', 'studiengang', 'stutyp', 'schwerpunkt_bei_abschluss', 'geschl', 
                                   'gebdat', 'staat', 'hzbnote', 'hzb_erwerbsort', 'hzbart', 'hzbdatum', 'immadat', 
                                   'erfolg']] = data_concenated.loc[zeile - 1, ['MNR_neu', 'MNR_Zweit', 'studiengang', 'stutyp', 
                                                                            'schwerpunkt_bei_abschluss', 'geschl', 
                                                                            'gebdat', 'staat', 'hzbnote', 'hzb_erwerbsort', 
                                                                            'hzbart', 'hzbdatum', 'immadat', 'erfolg']]
            if data_concenated.loc[zeile, 'semester'] > data_concenated.loc[zeile - 1, 'semester']:
                data_concenated.loc[zeile, 'fachsem'] = data_concenated.loc[zeile - 1, 'fachsem'] + 1
            else:
                data_concenated.loc[zeile, 'fachsem'] = data_concenated.loc[zeile - 1, 'fachsem']
    
    idex_2 = sorted(data_concenated.index[data_concenated['MNR_neu'].isnull()].tolist(), reverse = True)
    for zeile in idex_2[1:]:
        if (data_concenated.loc[zeile, 'mtknr'] == data_concenated.loc[zeile + 1, 'mtknr']) & (data_concenated.loc[zeile, 'stg'] == data_concenated.loc[zeile + 1, 'stg']):
            data_concenated.loc[zeile, ['MNR_neu', 'MNR_Zweit', 'studiengang', 'stutyp', 'schwerpunkt_bei_abschluss', 'geschl', 
                                    'gebdat', 'staat', 'hzbnote', 'hzb_erwerbsort', 'hzbart', 'hzbdatum', 'immadat', 
                                    'erfolg']] = data_concenated.loc[zeile + 1, ['MNR_neu', 'MNR_Zweit', 'studiengang', 'stutyp', 
                                                                             'schwerpunkt_bei_abschluss', 'geschl', 
                                                                             'gebdat', 'staat', 'hzbnote', 'hzb_erwerbsort', 
                                                                             'hzbart', 'hzbdatum', 'immadat', 'erfolg']]
            if data_concenated.loc[zeile, 'semester'] < data_concenated.loc[zeile + 1, 'semester']:
                data_concenated.loc[zeile, 'fachsem'] = data_concenated.loc[zeile + 1, 'fachsem'] - 1
            else:
                data_concenated.loc[zeile, 'fachsem'] = data_concenated.loc[zeile + 1, 'fachsem']
    
    data_concenated = data_concenated.dropna(subset=['MNR_Zweit'])
    
    # delete personal columns        
    data_concenated = data_concenated.drop(columns = ['idm_username','email', 'abschl_x', 'abschl_y', 'abschluss', 'exmgrund'])
    
    # add schwerpunkte Sozök
    data_concenated['study_sp_ges'] = data_concenated.groupby('MNR_Zweit')['study_sp'].apply(lambda x: x.ffill().bfill())
    data_concenated.loc[data_concenated.study_sp_ges.isna(), 'schwerpunkt_bei_abschluss'] = np.nan
    data_concenated.loc[data_concenated.study_sp_ges == 612, 'schwerpunkt_bei_abschluss'] = 'International'
    data_concenated.loc[data_concenated.study_sp_ges == 611, 'schwerpunkt_bei_abschluss'] = 'Verhalten'
    
    # correct exam grade
    data_concenated.pnote = data_concenated.pnote/100
    
    return data_concenated

def getting_encrypting_dataframes(data):
    
    # create dataframes for every study programme
    stgs = pd.unique(data.studiengang.tolist())
    if 'Wirtschaftswissenschaften' in stgs:
        dfs = {}
        for stg in stgs:
            dfs[stg] = pd.DataFrame()
            dfs[stg] = data.loc[data.studiengang == stg, ['mtknr', 'MNR_Zweit']]
            dfs[stg] = dfs[stg].drop_duplicates(subset = ['MNR_Zweit'], keep = 'first').reset_index(drop=True)
            dfs[stg].to_csv(os.path.abspath('../../data/processed/encrypting_' + stg + '_ba.csv'), sep=';', decimal=',')
    elif 'Marketing' in stgs:
        dfs = {}
        for stg in stgs:
            dfs[stg] = pd.DataFrame()
            dfs[stg] = data.loc[data.studiengang == stg, ['mtknr', 'MNR_Zweit']]
            dfs[stg] = dfs[stg].drop_duplicates(subset = ['MNR_Zweit'], keep = 'first').reset_index(drop=True)
            dfs[stg].to_csv(os.path.abspath('../../data/processed/encrypting_' + stg + '_ma.csv'), sep=';', decimal=',')

def delete_personal_data(data, StudStart, Next):
    
    # delete old MNR        
    df_Studies = data.drop(columns = ['mtknr'])
    df_StudStart = StudStart.drop(columns = ['mtknr'])
    df_Next = Next.drop(columns = ['mtknr'])
    
    return df_Studies, df_StudStart, df_Next


def path_preparation(data):
    
    # calculate angemeldet, bestanden & ECTS per semester
    df_Path = data.loc[data.Modulebene_1 != 0]
    df_Path1 = df_Path.groupby(['MNR_Zweit', 'fachsem'])[['bonus']].sum().reset_index()
    df_Path2 = df_Path.groupby(['MNR_Zweit', 'fachsem'])[['bonus']].count().reset_index()
    df_Path2 = df_Path2.rename(columns = {'bonus' : 'angemeldet'})
    df_Path3 = df_Path.loc[df_Path.pstatus == 'BE']
    df_Path3 = df_Path3.groupby(['MNR_Zweit', 'fachsem'])[['bonus']].count().reset_index()
    df_Path3 = df_Path3.rename(columns = {'bonus' : 'bestanden'})
    
    # select needed rows
    df_Path = data.drop_duplicates(subset = ['MNR_Zweit', 'fachsem'])
    
    # calculate age
    df_Path['semester_date'] = df_Path['semester']
    df_Path.semester = df_Path.semester.astype(str)
    df_Path.loc[df_Path.semester.str.slice(4,) == '1','period'] = '4'
    df_Path.loc[df_Path.semester.str.slice(4,) == '2','period'] = '10'
    df_Path['semester'] = df_Path['semester'].str.slice(0,4)   
    df_Path['semester'] =pd.to_datetime(df_Path['semester'].astype(str) + df_Path['period'], format='%Y%m')
    df_Path['Alter'] = df_Path.semester - pd.to_datetime(df_Path.gebdat, errors = 'coerce')
    df_Path['Alter'] = df_Path['Alter'].dt.days/364
    df_Path.Alter = df_Path.Alter.round().astype('Int64')
    
    # select needed columns
    df_Path = df_Path[['MNR_Zweit', 'semester_date', 'fachsem', 'Alter']]
    
    # merge dataframes
    df_Path = df_Path.merge(df_Path1, on=['MNR_Zweit', 'fachsem'], how='left')
    df_Path = df_Path.merge(df_Path2, on=['MNR_Zweit', 'fachsem'], how='left')
    df_Path = df_Path.merge(df_Path3, on=['MNR_Zweit', 'fachsem'], how='left')
    df_Path[['bestanden', 'bonus', 'angemeldet']] = df_Path[['bestanden', 'bonus', 'angemeldet']].fillna(0)
    
    df_Path = df_Path.sort_values(by = ['MNR_Zweit', 'fachsem'])
    df_Path = df_Path.reset_index(drop = True)
    
    # add Status
    df_Path.loc[:,'Status'] = 'M'
    df_Path.loc[0,'Status'] = 'S'
    df_Path.loc[df_Path.drop_duplicates(subset = ['MNR_Zweit'], keep = 'last').index, 'Status'] = 'E'
    df_Path.loc[df_Path.drop_duplicates(subset = ['MNR_Zweit'], keep = 'first').index, 'Status'] = 'S'
    df_Path['Status_EN'] = df_Path['Status']
    df_Path.loc[df_Path.drop_duplicates(subset = ['MNR_Zweit'], keep = 'last').index, 'Status_EN'] = 'E'

    return df_Path

def add_term(data, PO, Studiengang, Bereich, Zielmodul, Plansem):
    data.loc[(data.Bezeichnung.isna()) & 
              (data.Bereich_1 == Bereich) &
              (data.studiengang == Studiengang) &
              (data.po_version == PO), ['Bezeichnung', 'Plan_sem']] = Zielmodul, Plansem
    return data