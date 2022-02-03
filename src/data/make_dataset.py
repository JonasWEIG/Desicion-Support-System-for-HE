# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 14:03:47 2021

@author: ba42pizo
"""
import pandas as pd
import numpy as np
import os

def clean_exam(exam_data):
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
    exam_data = exam_data.astype({'mtknr': int, 'stg': int} )
    study_data = study_data.astype({'mtknr': int, 'stg': int} )
    data_concenated = exam_data.merge(study_data, on=['mtknr', 'stg', 'semester'], how='outer')        
    data_concenated = data_concenated.sort_values(by=['mtknr', 'semester'], ascending = [True, True]) 
    data_concenated = data_concenated.reset_index(drop=True)
    
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
    for zeile in idex_2:
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

def stud_data(data, akt_semester):
    # getting final grade Data
    ## getting the information from 'Gesamtkonto'
    df_Ges = data.loc[data.prftitel == 'Gesamtkonto', ['MNR_Zweit', 'stg', 'prftitel', 'pstatus', 'pnote', 'bonus', 'semester', 'fachsem']]
   
    ## adding students that do not have a 'Gesamtkonto' (yet)
    df_StudStart = data.drop_duplicates(subset = ['MNR_Zweit'], keep = 'first')
    df_Ges = df_Ges.astype({'MNR_Zweit': int, 'stg': int} )
    df_StudStart = df_StudStart.astype({'MNR_Zweit': int, 'stg': int} )
    df_StudStart = df_StudStart.merge(df_Ges, on=['MNR_Zweit', 'stg'], how='left')

    # select columns
    if 'schwerpunkt_bei_abschluss' in df_StudStart.columns:
        df_StudStart = df_StudStart[['mtknr', 'MNR_neu', 'MNR_Zweit', 'semester_x', 'studiengang', 'stg', 
                                         'stutyp', 'schwerpunkt_bei_abschluss', 'pstatus_y', 'pnote_y', 'bonus_y', 'semester_y', 'fachsem_y']]
        df_StudStart = df_StudStart.rename(columns = {'semester_x' : 'Startsemester', 'semester_y': 'Endsemester', 'fachsem_y': 'Fachsem_Final', 
                                                          'pnote_y': 'Endnote', 'bonus_y': 'ECTS_final', 'pstatus_y': 'bestanden'})
    else:
        df_StudStart = df_StudStart[['mtknr', 'MNR_neu', 'MNR_Zweit', 'semester_x', 'studiengang', 'stg', 
                                         'stutyp', 'pstatus_y', 'pnote_y', 'bonus_y', 'semester_y', 'fachsem_y']]
        df_StudStart = df_StudStart.rename(columns = {'semester_x' : 'Startsemester', 'semester_y': 'Endsemester', 'fachsem_y': 'Fachsem_Final', 
                                                          'pnote_y': 'Endnote', 'bonus_y': 'ECTS_final', 'pstatus_y': 'bestanden'})
    # fill nan
    ## current semesters are mostly empty, but should not be marked as 'EN'
    df_StudStart.loc[(df_StudStart.Startsemester == akt_semester) & (df_StudStart.bestanden.isna()), 'bestanden'] = 'PV'
    df_StudStart = df_StudStart.fillna({'bestanden': 'EN', 'Endnote': 5, 'ECTS_final': 0, 'Fachsem_Final': 1})
    df_StudStart.loc[df_StudStart.Endsemester.isna(), 'Endsemester'] = df_StudStart['Startsemester']

    # change for current semester  & add average grade
    ## filtering out 'PVs' that seem to no longer actually study 
    df_StudStart.loc[(df_StudStart.Endsemester < akt_semester - 20) & (df_StudStart.bestanden == 'PV'), 'bestanden'] = 'EN'
    df_StudStart.loc[(df_StudStart.Endsemester == akt_semester) & (df_StudStart.bestanden == 'PV'), 'Endnote'] = np.nan
    df_StudStart = df_StudStart.drop_duplicates(subset = ['MNR_Zweit'], keep = 'first')
    df_StudStart.loc[df_StudStart.bestanden == 'EN', 'Endnote'] = 5
    
    return df_StudStart



# load data

path_stud = os.path.abspath('.\\WiSe2122\\data\\20102021_WISO-Studierendendaten_3_BA_20212.csv')
df_StudData = pd.read_csv(path_stud, sep=';', engine = 'python', encoding = 'utf-8')
path_pruf = os.path.abspath('.\\WiSe2122\\data\\20102021_WISO-Leistungsdaten_BA_20212.csv')
path_pruf = pd.read_csv(path_pruf, sep=';', engine = 'python', encoding = 'utf-8')
test = clean_exam(path_pruf)
concated_data = concate_all_data(clean_exam(path_pruf), df_StudData)


