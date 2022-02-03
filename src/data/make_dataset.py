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

def getting_next_study(data, master_data):

    # get next bachelor study
    next_stud = data.loc[data.MNR_Zweit % 10 > 1, 'MNR_Zweit' ].tolist()
    df_next = data[['mtknr', 'MNR_Zweit', 'bestanden', 'Endnote', 'studiengang']]
    for row in next_stud:
        df_next.loc[df_next.MNR_Zweit == row-1, 'next_study'] = df_next.loc[df_next['MNR_Zweit'] == row, 'studiengang'].item()

    # get next master study
    df_Master_Stud = master_data.rename(columns = {'studiengang': 'studiengang_master'})
    df_Master_Stud = df_Master_Stud[['mtknr', 'studiengang_master']].drop_duplicates(subset = ['mtknr', 'studiengang_master'], keep = 'first')
    
    # dropduplicates
    df_next = df_next.merge(df_Master_Stud, on = ['mtknr'], how = 'left')
    df_next.studiengang_master = 'Master_' + df_next.studiengang_master
    df_next.loc[df_next.bestanden == 'BE', 'next_study'] = df_next.studiengang_master
    df_next = df_next.drop(columns = ['studiengang_master'])
    
    return df_next

def getting_encrypting_dataframes(data):
    
    # create dataframes for every study programme
    stgs = pd.unique(data.studiengang.tolist())
    dfs = {}
    for stg in stgs:
        dfs[stg] = pd.DataFrame()
        dfs[stg] = data.loc[data.studiengang == stg, ['mtknr', 'MNR_Zweit']]
        dfs[stg] = dfs[stg].drop_duplicates(subset = ['MNR_Zweit'], keep = 'first').reset_index(drop=True)
        dfs[stg].to_csv(os.path.abspath('..\\WiSe2122\\csv\\df_' + stg + '.csv'), sep=';', decimal=',')

def delete_personal_data(data, StudStart, Next):
    
    # delete old MNR        
    df_Studies = data.drop(columns = ['mtknr'])
    df_StudStart = StudStart.drop(columns = ['mtknr'])
    df_Next = Next.drop(columns = ['mtknr'])
    
    return df_Studies, df_StudStart, df_Next

def demo_data(data, stadt):

    # preprocessing time to imma 
    df_demo = data[['MNR_neu', 'geschl', 'gebdat', 'staat', 'hzbnote', 'hzb_erwerbsort', 'hzbart', 'hzbdatum', 'immadat']]
    df_demo = df_demo.drop_duplicates(subset = ['MNR_neu'], keep = 'first')
    df_demo['HZB_bis_Imma'] = pd.to_datetime(df_demo.immadat, dayfirst=True) - pd.to_datetime(df_demo.hzbdatum)
    df_demo.HZB_bis_Imma = df_demo.HZB_bis_Imma.dt.days
    df_demo.loc[df_demo.HZB_bis_Imma >= 3*365, 'HZB_bis_Imma_J'] = '> 3 Jahre'
    df_demo.loc[df_demo.HZB_bis_Imma < 3*365, 'HZB_bis_Imma_J'] = '3 Jahre'
    df_demo.loc[df_demo.HZB_bis_Imma < 2*365, 'HZB_bis_Imma_J'] = '2 Jahre'
    df_demo.loc[df_demo.HZB_bis_Imma < 1*365, 'HZB_bis_Imma_J'] = '1 Jahr'
    
    # preprocessing hzb type 
    df_demo.loc[df_demo.hzbart.str.contains('allgemeine Hochsc'), 'HZB_art'] = 'allgemeine Hochschulreife'
    df_demo.loc[df_demo.hzbart.str.contains('fachgebundene Hochsc'), 'HZB_art'] = 'fachgebundene Hochschulreife'
    df_demo.loc[df_demo.hzbart.str.contains('Fachhochschul'), 'HZB_art'] = 'Fachhochschulreife'
    df_demo.loc[df_demo.hzbart.str.contains('Gymnasium') |
                  df_demo.hzbart.str.contains('Gesamtschule'), 'HZB_typ'] = 'Gymnasium'
    df_demo.loc[df_demo.hzbart.str.contains('Ausland') |
                  df_demo.hzbart.str.contains('Studienkolleg'), 'HZB_typ'] = 'Im Ausland erworben'
    df_demo.loc[df_demo.hzbart.str.contains('Fachgym') | 
                  df_demo.hzbart.str.contains('Fachober'), 'HZB_typ'] = 'Berufliche Oberschule'
    df_demo.loc[df_demo.hzbart.str.contains('Berufsober') |
                  df_demo.hzbart.str.contains('Abendgym') |
                  df_demo.hzbart.str.contains('Kolleg') |
                  df_demo.hzbart.str.contains('Fachak') |
                  df_demo.hzbart.str.contains('Berufsfach'), 'HZB_typ'] = 'Zweiter Bildungsweg'
    df_demo.loc[df_demo.hzbart.str.contains('Beruflich ') |
                  df_demo.hzbart.str.contains('Sonstige ') |
                  df_demo.hzbart.str.contains('Eignungs'), 'HZB_typ'] = 'Beruflich qualifiziert'
            
    # preprocessing place 
    #HZB_Ort = pd.unique(df_demo['hzb_erwerbsort']).tolist()
    Mittelfranken = ['Ansbach',
                     'Erlangen', 
                     'Fürth',
                     'Neustadt a.d. Aisch',
                     'Nürnberg', 
                     'Roth',
                     'Pegnitz',               
                     'Schwabach',
                     'Weissenburg-Gunzenhausen']
    
    Bayern = pd.unique(stadt.loc[stadt.Bundesland == 'Bayern', 'Kreis']).tolist()
    df_demo.loc[:,'Region'] = 'Deutschland'
    
    for Ort in Bayern:
        df_demo.loc[df_demo.hzb_erwerbsort.str.contains(Ort, na=False), 'Region'] = 'Bayern'
    
    for Ort in Mittelfranken:
        df_demo.loc[df_demo.hzb_erwerbsort.str.contains(Ort, na=False), 'Region'] = 'Mittelfranken'
    
    df_demo.loc[df_demo['HZB_typ'] == 'Im Ausland erworben', 'Region'] = 'Ausland'
    df_demo.hzbnote = df_demo.hzbnote/100
    
    return df_demo

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

def get_exam_data(data, StudStart, structure):
    
    df_Exam = data.loc[data.Modulebene_1 != 0]
    df_Exam = df_Exam[['MNR_Zweit', 'fachsem', 'semester', 'pstatus', 'pnote', 'bonus', 'pversuch', 'pnr', 'prftitel', 'Modulebene_1', 'Modulebene_2', 'modultitel', 'Bereich_1', 'Bereich_2', 'study_sp']]
    df_Exam = df_Exam.merge(StudStart[['MNR_Zweit', 'bestanden']], on='MNR_Zweit', how='left')

    ### getting relevant exam data
    df_module_2 = df_Exam.loc[(df_Exam.pstatus != 'AN') & (df_Exam.pstatus.notna()), ]
    
    ### aggregating for every module, see if module was passed
    df_module_2['not_passed']= 2
    df_module_2.loc[df_module_2.pstatus == 'BE', 'not_passed'] = 1
    df_module_2 = df_module_2.groupby(["MNR_Zweit", "Modulebene_2", "pversuch"]).agg(bonus_m2=("bonus", "sum"), 
                                                                         max_sem_m2=('fachsem', 'max'), 
                                                                         not_passed_m2=('not_passed', 'max')).reset_index()
    df_module_2.loc[df_module_2.not_passed_m2 == 1, 'not_passed_m2'] = 'BE'
    df_module_2.loc[df_module_2.not_passed_m2 == 2, 'not_passed_m2'] = 'NB'
    
    
    ### check if bonus is enough (mode) for module
    def mode(a):
        u, c = np.unique(a, return_counts=True)
        return u[c.argmax()]
    
    df_mod_bon = df_module_2.groupby(['Modulebene_2'])[['bonus_m2']].apply(mode).reset_index()
    df_mod_bon = df_mod_bon.astype({'Modulebene_2': int})
    module_2 = df_mod_bon.set_index('Modulebene_2')[0].to_dict()
    df_module_2 = df_module_2.astype({'bonus_m2': float, 'Modulebene_2': int})
    
    for key in module_2:
        df_module_2.loc[(df_module_2.Modulebene_2 == key) & (df_module_2.bonus_m2 < float(module_2[key])), 'exam_open'] = 1
    
    ### add 'PV' if module not finished
    df_module_2.loc[(df_module_2.not_passed_m2 =='BE') & (df_module_2.exam_open == 1), 'not_passed_m2'] = 'PV' 
    
    
    ### add module grade
    df_module_2_passed = df_Exam.loc[(df_Exam.bonus != 0) & (df_Exam.Modulebene_1 != 0) & (df_Exam.pnote != 0)]
    
    
    #df_Modulebene2_test = df_Modulebene2_bestanden.groupby(["MNR_Zweit", "Modulebene_2"]).agg(bonus_m2=("bonus", "sum"), 
                                                           #max_sem_m2=('fachsem', 'max'), max_versuch_m2=('pversuch', 'max')).reset_index()
    #df_Modulebene2_bestanden_note = df_Modulebene2_bestanden.loc[df_Modulebene2_bestanden.pnote != 0]
    wm_note = lambda x: np.average(x, weights=df_module_2_passed.loc[x.index, "bonus"])
    df_module_2_passed = df_module_2_passed.groupby(["MNR_Zweit", "Modulebene_2"]).agg(note_m2=("pnote", wm_note)).reset_index()
    
    df_module_2 = df_module_2.merge(df_module_2_passed, on = ['MNR_Zweit', 'Modulebene_2'], how = 'left')
    
    
    ######################
    
    
    # Get Modulebene_1 Infos
    df_Modulebene1_bestanden = data.loc[data.bonus != 0]
    df_Modulebene1_bestanden = df_Modulebene1_bestanden.loc[df_Modulebene1_bestanden.Modulebene_1 != 0]
    df_Modulebene1_test = df_Modulebene1_bestanden.groupby(["MNR_Zweit", "Modulebene_1"]).agg(bonus_m1=("bonus", "sum"),
                                                           max_sem_m1=('fachsem', 'max'), pversuch=('pversuch', 'max')).reset_index()
    df_Modulebene1_bestanden_note = df_Modulebene1_bestanden.loc[(df_Modulebene1_bestanden.pnote != 0) & (df_Modulebene1_bestanden.pnote.notna())]
    wm_note_1 = lambda x: np.average(x, weights=df_Modulebene1_bestanden_note.loc[x.index, "bonus"])
    df_Modulebene1_note = df_Modulebene1_bestanden_note.groupby(["MNR_Zweit", "Modulebene_1"]).agg(note_m1=("pnote", wm_note_1)).reset_index()
    df_Modulebene1 = df_Modulebene1_test.merge(df_Modulebene1_note, on = ['MNR_Zweit', 'Modulebene_1'], how = 'left')
    
    
    
    ######################
    
    
    # Get Bereich1 Infos
    df_Bereich = data.loc[data.bonus != 0]
    df_Bereich = df_Bereich.loc[df_Bereich.Modulebene_1 != 0]
    df_Bereich1_test = df_Bereich.groupby(["MNR_Zweit", "Bereich_1"]).agg(bonus_b1=("bonus", "sum"),
                                     max_sem_b1=('fachsem', 'max')).reset_index()
    df_Bereich1_bestanden_note = df_Bereich.loc[(df_Bereich.pnote != 0) & (df_Bereich.pnote.notna())]
    wm_ber_1 = lambda x: np.average(x, weights=df_Bereich1_bestanden_note.loc[x.index, "bonus"])
    df_Bereich1_note = df_Bereich1_bestanden_note.groupby(["MNR_Zweit", "Bereich_1"]).agg(note_b1=("pnote", wm_ber_1)).reset_index()
    df_Bereich1 = df_Bereich1_test.merge(df_Bereich1_note, on = ['MNR_Zweit', 'Bereich_1'], how = 'left')
    
    
    
    ######################
    
    
    # Get Bereich2 Infos
    df_Bereich = data.loc[data.bonus != 0]
    df_Bereich = df_Bereich.loc[df_Bereich.Modulebene_1 != 0]
    df_Bereich2_test = df_Bereich.groupby(["MNR_Zweit", "Bereich_2"]).agg(bonus_b2=("bonus", "sum"),
                                          max_sem_b2=('fachsem', 'max')).reset_index()
    df_Bereich2_bestanden_note = df_Bereich.loc[(df_Bereich.pnote != 0) & (df_Bereich.pnote.notna())]
    wm_ber_2 = lambda x: np.average(x, weights=df_Bereich2_bestanden_note.loc[x.index, "bonus"])
    df_Bereich2_note = df_Bereich2_bestanden_note.groupby(["MNR_Zweit", "Bereich_2"]).agg(note_b2=("pnote", wm_ber_2)).reset_index()
    
    df_Bereich2 = df_Bereich2_test.merge(df_Bereich2_note, on = ['MNR_Zweit', 'Bereich_2'], how = 'left')
    
    
    ######################
    
    
    # Put layers together 
    
    df_layers1 = df_Exam.merge(df_module_2, on =['MNR_Zweit', 'Modulebene_2', 'pversuch'], how='outer')
    df_layers2 = df_layers1.merge(df_Modulebene1, on =['MNR_Zweit', 'Modulebene_1', 'pversuch'], how='outer')
    df_layers3 = df_layers2.merge(df_Bereich1, on =['MNR_Zweit', 'Bereich_1'], how='outer')
    df_layers4 = df_layers3.merge(df_Bereich2, on =['MNR_Zweit', 'Bereich_2'], how='outer')
    df_layers4.loc[df_layers4.Bereich_1 == 1100, 'GOP_bestanden'] = 'EN'
    df_layers4.loc[(df_layers4.Bereich_1 == 1100) & (df_layers4.bestanden == 'PV') & (df_layers4.bonus_b1 < 60), 'GOP_bestanden'] = 'PV'
    df_layers4.loc[(df_layers4.Bereich_1 == 1100) & (df_layers4.bonus_b1 >= 60), 'GOP_bestanden'] = 'BE'
    df_layers4.loc[df_layers4.Bereich_1 == 1000, 'GOP_bestanden'] = 'EN'
    df_layers4.loc[(df_layers4.Bereich_1 == 1000) & (df_layers4.bestanden == 'PV') & (df_layers4.bonus_b1 < 30), 'GOP_bestanden'] = 'PV'
    df_layers4.loc[(df_layers4.Bereich_1 == 1000) & (df_layers4.bonus_b1 >= 30), 'GOP_bestanden'] = 'BE'
    df_layers4[['note_b1', 'note_b2', 'note_m1', 'note_m2']] = df_layers4[['note_b1', 'note_b2', 'note_m1', 'note_m2']].round(1)
    
    ############### Add study path analysis #################
    
    structure['SP'] = pd.to_numeric(structure['SP'], errors = 'coerce').astype('Int64')
    df_layers = df_layers4.merge(StudStart[['MNR_Zweit', 'Startsemester', 'studiengang' ]], on = 'MNR_Zweit', how  = 'left')
    
    studiengangs = pd.unique(structure.Studiengang).tolist()
    for studiengang in studiengangs:
        po_versions = pd.unique(structure.loc[structure.Studiengang == studiengang, 'PO_Version']).tolist()
        po_versions.sort()
        for po_version in po_versions:
            df_layers.loc[(df_layers.Startsemester >= po_version) & (df_layers.studiengang == studiengang), 'po_version'] = po_version
    
    df_layers['Mod'], df_layers['Bezeichnung'], df_layers['Plan_sem'] = [np.nan, np.nan,np.nan]
    
    structure = structure.astype({'Bereich': float, 'PO_Version': float, 'SP': float})
    for i in range(0,len(structure)):
        df_layers.loc[(df_layers.studiengang == structure.iloc[i,0]) &  
                      (df_layers.po_version == structure.iloc[i,1]) & 
                          ((df_layers.study_sp == structure.iloc[i,2]) |
                            ((df_layers.study_sp.isnull()) & (np.isnan(structure.iloc[i,2])))) & 
                      (df_layers.Bereich_1 == structure.iloc[i,3]) & 
                          ((df_layers.Modulebene_2 == structure.iloc[i,4]) | 
                          (df_layers.Modulebene_1 == structure.iloc[i,4]) | 
                          (df_layers.Bereich_2 == structure.iloc[i,4]) |
                          (df_layers.Bereich_1 == structure.iloc[i,4]) |
                          (df_layers.modultitel == structure.iloc[i,5])), 
                                  ['Mod', 'Bezeichnung', 'Plan_sem' ]] = structure.iloc[i,4], structure.iloc[i,5], structure.iloc[i,6]
    
    
    add_term(df_layers, 20132, 'International Business Studies', 1100, 'Sprachen 1.1', 1)
    add_term(df_layers, 20202, 'International Business Studies', 1100, 'Foreign languages 1.1', 1)
    add_term(df_layers, 20132, 'Sozialökonomik', 1100, 'Sprachen', 2)
    add_term(df_layers, 20152, 'Sozialökonomik', 1100, 'Sprachen', 2)
    add_term(df_layers, 20162, 'Sozialökonomik', 1100, 'Sprachen', 2)
    add_term(df_layers, 20172, 'Sozialökonomik', 1100, 'Sprachen', 2)
    add_term(df_layers, 20132, 'Sozialökonomik', 1920, 'Sprachen 2.2', 2)
    add_term(df_layers, 20132, 'Wirtschaftswissenschaften', 1100, 'Sprachen', 2)
    
    df_layers.loc[df_layers['Bezeichnung'].notnull(),'final_verlauf'] = df_layers.Plan_sem.astype('Int64').astype(str) + '_' + df_layers.Bezeichnung.astype(str)
    
    # add average grade of exam per semester
    df_exam_passed = df_layers.loc[df_layers.pnote <= 4.0]
    df_avg = df_layers.groupby(['prftitel', 'semester'])[['pnote']].mean().reset_index()
    df_avg = df_avg.rename(columns = {'pnote': 'pnote_avg'})
    df_avg_passed = df_exam_passed.groupby(['prftitel', 'semester'])[['pnote']].mean().reset_index()
    df_avg_passed = df_avg_passed.rename(columns = {'pnote': 'pnote_avg_passed'})
    df_avg.loc[df_avg.pnote_avg < 1] = 0
    df_layers = df_layers.merge(df_avg, how = 'left', on = ['prftitel', 'semester'])
    df_avg_passed.loc[df_avg_passed.pnote_avg_passed < 1] = 0
    df_layers = df_layers.merge(df_avg_passed, how = 'left', on = ['prftitel', 'semester'])
    df_layers = df_layers.rename(columns = {'not_passed_m2': 'status_m2'})
    df_layers.loc[df_layers.status_m2 == 'NB', 'note_m2'] = 5
    
    return df_layers


def path_final(path, layers, akt_semester):
    
    df_Path4 = layers.groupby(['MNR_Zweit', 'fachsem'])[['note_m2']].mean().reset_index()
    df_Path4 = df_Path4.rename(columns = {'note_m2' : 'Durchschnittsnote'})
    df_Path4 = df_Path4.round({'Durchschnittsnote': 1})
    df_Path5 = layers.loc[layers.status_m2 == 'BE']
    df_Path5 = df_Path5.groupby(['MNR_Zweit', 'fachsem'])[['note_m2']].mean().reset_index()
    df_Path5 = df_Path5.rename(columns = {'note_m2' : 'Durchschnittsnote_be'})
    df_Path5 = df_Path5.round({'Durchschnittsnote_be': 1})
    
    df_Path = path.merge(df_Path4, on=['MNR_Zweit', 'fachsem'], how='left')
    df_Path = df_Path.merge(df_Path5, on=['MNR_Zweit', 'fachsem'], how='left')
    df_Path = df_Path[df_Path['semester_date'] != akt_semester]
    
    return df_Path

def show_ects(path, StudStart):
    
    Semesters = [14,13,12,11,10,9,8,7,6,5,4,3,2,1,0]
    #Semesters_2 = [14,13,12,11,10,9,8,7,6,5,4,3,2]
    df_ECTS = StudStart[['MNR_Zweit', 'bestanden']]
    for semester in Semesters:
        df_semester = path.loc[path.fachsem == semester, ['MNR_Zweit', 'bonus']]
        df_semester = df_semester.astype({'MNR_Zweit': int})
        df_semester = df_semester.rename(columns={'bonus':'Sem_ects_'+str(semester)})
        df_ECTS = df_ECTS.merge(df_semester, on = ['MNR_Zweit'], how='left')
    
    df_ECTS.Sem_ects_0 = df_ECTS.Sem_ects_0.fillna(0)
    df_ECTS.Sem_ects_1 = df_ECTS.Sem_ects_1 + df_ECTS.Sem_ects_0
    df_ECTS = df_ECTS.drop(columns = 'Sem_ects_0')
    
    
    # add all ECTS
    df_ECTS['Sem_ects_sum_1'] = df_ECTS['Sem_ects_1']
    df_ECTS.loc[df_ECTS.Sem_ects_sum_1.isna(), 'Sem_ects_sum_1'] = 0
    #fs = 2
    for fs in range(2,15):
        df_ECTS.loc[df_ECTS['Sem_ects_' + str(fs)] == 0, 'Sem_ects_' + str(fs)] = np.nan
    
    for fs in range(2,15):
        df_ECTS['Sem_ects_sum_' + str(fs)] = df_ECTS['Sem_ects_' + str(fs)]
        for na in range(2,fs):
            df_ECTS.loc[(df_ECTS['Sem_ects_' + str(fs)].notna()) & (df_ECTS['Sem_ects_' + str(na)].isna()), 'Sem_ects_sum_' + str(na)] = 0
    
    for fs in range(2,15):
        df_ECTS['Sem_ects_sum_' + str(fs)] = df_ECTS['Sem_ects_sum_' + str(fs)] + df_ECTS['Sem_ects_sum_' + str(fs-1)]    
    
    for fs in range(2,15): 
        df_ECTS.loc[(df_ECTS.bestanden == 'bestanden') &
                    (df_ECTS['Sem_ects_sum_' + str(fs)] == 0) &
                    (df_ECTS['Sem_ects_sum_' + str(fs-1)] != 0), 'Sem_ects_sum_' + str(fs-1)] = 180  
    
        
    for fs in range(1,15):  
        
        if fs <= 5:
            df_ECTS.loc[(df_ECTS['Sem_ects_sum_' + str(fs)].notna()) & (df_ECTS['Sem_ects_sum_' + str(fs)] < fs*10), 'Sem_ects_agg_' + str(fs)] = 'weniger als ' + str(fs*10) + ' ECTS'
            df_ECTS.loc[(df_ECTS['Sem_ects_sum_' + str(fs)].notna()) & (df_ECTS['Sem_ects_sum_' + str(fs)] >= fs*10), 'Sem_ects_agg_' + str(fs)] = 'mindestens ' + str(fs*10) + ' ECTS'
            df_ECTS.loc[(df_ECTS['Sem_ects_sum_' + str(fs)].notna()) & (df_ECTS['Sem_ects_sum_' + str(fs)] >= fs*20), 'Sem_ects_agg_' + str(fs)] = 'mindestens ' + str(fs*20) + ' ECTS'
            df_ECTS.loc[(df_ECTS['Sem_ects_sum_' + str(fs)].notna()) & (df_ECTS['Sem_ects_sum_' + str(fs)] >= fs*30), 'Sem_ects_agg_' + str(fs)] = 'mindestens ' + str(fs*30) + ' ECTS'
        else:
            df_ECTS.loc[(df_ECTS['Sem_ects_sum_' + str(fs)].notna()) & (df_ECTS['Sem_ects_sum_' + str(fs)] < 60), 'Sem_ects_agg_' + str(fs)] = 'weniger als 60 ECTS'
            df_ECTS.loc[(df_ECTS['Sem_ects_sum_' + str(fs)].notna()) & (df_ECTS['Sem_ects_sum_' + str(fs)] >= 60), 'Sem_ects_agg_' + str(fs)] = 'mindestens 60 ECTS'
            df_ECTS.loc[(df_ECTS['Sem_ects_sum_' + str(fs)].notna()) & (df_ECTS['Sem_ects_sum_' + str(fs)] >= 120), 'Sem_ects_agg_' + str(fs)] = 'mindestens 120 ECTS' 
            df_ECTS.loc[(df_ECTS['Sem_ects_sum_' + str(fs)].notna()) & (df_ECTS['Sem_ects_sum_' + str(fs)] >= 180), 'Sem_ects_agg_' + str(fs)] = 'bestanden'
    
    # add quantitative status_final
    df_ECTS['bestanden_num'] = 600
    df_ECTS.loc[df_ECTS.bestanden == 'EN', 'bestanden_num'] = 700
    df_ECTS.loc[df_ECTS.bestanden == 'BE', 'bestanden_num'] = 500
    df_ECTS.loc[df_ECTS.bestanden == 'BE', 'bestanden'] = 'bestanden'
    df_ECTS.loc[df_ECTS.bestanden == 'PV', 'bestanden'] = 'noch im Studium'
    df_ECTS.loc[df_ECTS.bestanden == 'EN', 'bestanden'] = 'nicht bestanden'
    for fs in range(2,15):    
        df_ECTS.loc[df_ECTS['Sem_ects_agg_' + str(fs)].isna(), 'Sem_ects_agg_' + str(fs)] = df_ECTS['bestanden']
        
    # finalize sequence
    for fs in range(1,15): 
        df_ECTS['Sem_ects_sum_' + str(fs)].fillna(0, inplace = True)
    
    
    
    df_ECTS = df_ECTS.sort_values(by=['bestanden_num', 'Sem_ects_sum_14', 'Sem_ects_sum_13', 'Sem_ects_sum_12', 'Sem_ects_sum_11', 'Sem_ects_sum_10', 'Sem_ects_sum_9',
                                      'Sem_ects_sum_8', 'Sem_ects_sum_7', 'Sem_ects_sum_6', 'Sem_ects_sum_5', 'Sem_ects_sum_4', 'Sem_ects_sum_3',
                                      'Sem_ects_sum_2', 'Sem_ects_sum_1'], ascending = [True, True, True, True, True, True, True, True, 
                                                                                       True, True, True, True, True, True, False])
    df_ECTS = df_ECTS.reset_index(drop=False)
    df_ECTS['Reihenfolge'] = df_ECTS.index   

    return df_ECTS

# load data

### TO DO ###

#test = clean_exam(df_PrufData)
concated_data = concate_all_data(clean_exam(df_PrufData), df_StudData)
df_StudStart = stud_data(concated_data, 20212)
df_next = getting_next_study(df_StudStart, df_Master_Stud)
df_Studies, df_StudStart, df_next = delete_personal_data(concated_data, df_StudStart, df_next)
df_demo = demo_data(df_Studies, df_stadt)
path_preparation = path_preparation(df_Studies)
df_layers = get_exam_data(df_Studies, df_StudStart, df_Stud_struc)
df_Path = path_final(path_preparation, df_layers, 20212)
df_ECTS = show_ects(df_Path, df_StudStart)
