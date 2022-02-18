# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 14:03:47 2021

@author: ba42pizo
"""
import pandas as pd
import numpy as np
import os
from utils import *
import sys
sys.path.append('../features')
from build_features import add_probabilities


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

def getting_last_study(data, bachelordata_stud, bachelordata_pruf):

    # create MNR_neu column and MNR_Zweit & merge
    df_StudData_ba = bachelordata_stud.sort_values(by=['mtknr', 'semester'], ascending = [True, True])
    df_PrufData_ba = bachelordata_pruf.rename(columns = {'psem' : 'semester'})
    df_PrufData_ba = df_PrufData_ba.sort_values(by=['mtknr', 'semester'], ascending = [True, True]) 
    df_PrufData_ba = df_PrufData_ba[df_PrufData_ba.prftitel == 'Gesamtkonto']
    df_PrufData_ba = df_PrufData_ba.astype({'mtknr': int, 'stg': int} )
    df_StudData_ba = df_StudData_ba.astype({'mtknr': int, 'stg': int} )
    df_Studies_ba = df_PrufData_ba.merge(df_StudData_ba, on=['mtknr', 'stg', 'semester'], how='outer')        
    df_Studies_ba = df_Studies_ba.sort_values(by=['mtknr', 'semester'], ascending = [True, True]) 
    df_Studies_ba = df_Studies_ba.reset_index(drop=True)
    
    df_BA_Stud = df_Studies_ba.loc[df_Studies_ba.prftitel == 'Gesamtkonto', ['mtknr', 'studiengang', 'pstatus', 'pnote', 'bonus', 'semester', 'fachsem']]
    
    df_BA_Stud = df_BA_Stud.rename(columns = {'studiengang': 'studiengang_bachelor'})
    #df_BA_Stud = df_BA_Stud[['mtknr', 'studiengang_bachelor']].drop_duplicates(subset = ['mtknr', 'studiengang_bachelor'], keep = 'first')
    # dropduplicates
    df_last = data[['mtknr', 'MNR_Zweit', 'bestanden', 'Endnote', 'studiengang']]
    df_last = df_last.merge(df_BA_Stud, on = ['mtknr'], how = 'left')
    df_last.studiengang_bachelor = 'Bachelor_' + df_last.studiengang_bachelor
    df_last['next_study'] = df_last.studiengang_bachelor
    df_last = df_last.drop(columns = ['studiengang_bachelor'])
    df_last.loc[df_last.next_study.isna(), 'next_study'] = 'extern'
    df_last = df_last.rename(columns = {'pnote': 'Note_ba', 'pstatus': 'Status_ba'})
    
    return df_last

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



def get_exam_data(data, StudStart, structure, typ='bachelor'):
    
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
    if typ == 'bachelor':
        df_layers4.loc[df_layers4.Bereich_1 == 1100, 'GOP_bestanden'] = 'EN'
        df_layers4.loc[(df_layers4.Bereich_1 == 1100) & (df_layers4.bestanden == 'PV') & (df_layers4.bonus_b1 < 60), 'GOP_bestanden'] = 'PV'
        df_layers4.loc[(df_layers4.Bereich_1 == 1100) & (df_layers4.bonus_b1 >= 60), 'GOP_bestanden'] = 'BE'
        df_layers4.loc[df_layers4.Bereich_1 == 1000, 'GOP_bestanden'] = 'EN'
        df_layers4.loc[(df_layers4.Bereich_1 == 1000) & (df_layers4.bestanden == 'PV') & (df_layers4.bonus_b1 < 30), 'GOP_bestanden'] = 'PV'
        df_layers4.loc[(df_layers4.Bereich_1 == 1000) & (df_layers4.bonus_b1 >= 30), 'GOP_bestanden'] = 'BE'
        df_layers4[['note_b1', 'note_b2', 'note_m1', 'note_m2']] = df_layers4[['note_b1', 'note_b2', 'note_m1', 'note_m2']].round(1)
    else:
        df_layers4[['note_b1', 'note_b2']] = df_layers4[['note_b1', 'note_b2']].round(2)
        df_layers4.loc[(df_layers4.pstatus == 'BE') & (df_layers4.pnr == 1999) & (df_layers4.bonus == 20),['bonus_m2', 'bonus_m1', 'bonus_b1', 'bonus_b2']] = 20
        df_layers4.loc[(df_layers4.pstatus == 'BE') & (df_layers4.pnr == 1999) & (df_layers4.bonus == 20),['not_passed_m2']] = 'BE'
        df_layers4.loc[(df_layers4.pstatus == 'BE') & (df_layers4.pnr == 1999) & (df_layers4.bonus == 20),['max_sem_m2', 'max_sem_m1', 'max_sem_b1', 'max_sem_b2']] = df_layers4.fachsem
        df_layers4.loc[(df_layers4.pstatus == 'BE') & (df_layers4.pnr == 1999) & (df_layers4.bonus == 20),['note_m2', 'note_m1', 'note_b1', 'note_b2']] = df_layers4.pnote

    
    
    ############### Add study path analysis #################
    #if ba
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
    
    if typ == 'bachelor':
        add_term(df_layers, 20132, 'International Business Studies', 1100, 'Sprachen 1.1', 1)
        add_term(df_layers, 20202, 'International Business Studies', 1100, 'Foreign languages 1.1', 1)
        add_term(df_layers, 20132, 'Sozialökonomik', 1100, 'Sprachen', 2)
        add_term(df_layers, 20152, 'Sozialökonomik', 1100, 'Sprachen', 2)
        add_term(df_layers, 20162, 'Sozialökonomik', 1100, 'Sprachen', 2)
        add_term(df_layers, 20172, 'Sozialökonomik', 1100, 'Sprachen', 2)
        add_term(df_layers, 20132, 'Sozialökonomik', 1920, 'Sprachen 2.2', 2)
        add_term(df_layers, 20132, 'Wirtschaftswissenschaften', 1100, 'Sprachen', 2)
        
        df_layers.loc[df_layers['Bezeichnung'].notnull(),'final_verlauf'] = df_layers.Plan_sem.astype('Int64').astype(str) + '_' + df_layers.Bezeichnung.astype(str)
    else: 
        df_layers['final_verlauf'] = df_layers.Plan_sem.astype('Int64').astype(str) + '_' + df_layers.Bezeichnung.astype(str)
        df_layers.loc[(df_layers.final_verlauf == 'nan_nan') & (df_layers.Bereich_1 == 1700), 'final_verlauf'] = '2_' + df_layers.modultitel
        df_layers.loc[(df_layers.Bezeichnung.isna()) & (df_layers.Bereich_1 == 1500) & 
                      ((df_layers.studiengang == 'Economics') | (df_layers.studiengang == 'Gesundheitsmanagement und -ökonomie')), 'final_verlauf'] = '2_' + df_layers.modultitel
        df_layers.loc[(df_layers.Bezeichnung.isna()) & (df_layers.Bereich_1 == 1700) & (df_layers.Bereich_2 == 1700) & 
                      (df_layers.studiengang == 'Arbeitsmarkt und Personal'), 'final_verlauf'] = '1_' + df_layers.modultitel     
        df_layers.loc[(df_layers.Bezeichnung.isna()) & (df_layers.Bereich_1 == 1700) & (df_layers.Bereich_2 == 1700) & 
                      (df_layers.studiengang == 'Finance, Auditing, Controlling, Taxation (FACT)'), 'final_verlauf'] = '1_' + df_layers.modultitel 
        df_layers.loc[(df_layers.Bezeichnung.isna()) & (df_layers.Bereich_1 == 1700) & 
                      (df_layers.studiengang == 'International Business Studies'), 'final_verlauf'] = '1_' + df_layers.modultitel 
        df_layers.loc[(df_layers.Bezeichnung.isna()) & (df_layers.Bereich_1.notna()) & 
                      (df_layers.studiengang == 'International Information Systems (IIS)'), 'final_verlauf'] = '1_' + df_layers.modultitel
        df_layers.loc[(df_layers.Bezeichnung.isna()) & (df_layers.Bereich_1 == 1800) & (df_layers.Bereich_2 == 1800) & 
                      (df_layers.studiengang == 'Management'), 'final_verlauf'] = '1_' + df_layers.modultitel
        df_layers.loc[(df_layers.Bezeichnung.isna()) & (df_layers.Bereich_1 == 1700) & (df_layers.Bereich_2 == 1700) & 
                      (df_layers.studiengang == 'Marketing'), 'final_verlauf'] = '1_' + df_layers.modultitel
    
    
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

def show_ects(path, StudStart, typ='bachelor'):
    
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
   
    
   
    if typ == 'bachelor':
        
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
    else:
        for fs in range(1,15):  
            
            if fs <= 5:
                df_ECTS.loc[(df_ECTS['Sem_ects_sum_' + str(fs)].notna()) & (df_ECTS['Sem_ects_sum_' + str(fs)] < fs*10), 'Sem_ects_agg_' + str(fs)] = 'weniger als ' + str(fs*10) + 'ECTS'
                df_ECTS.loc[(df_ECTS['Sem_ects_sum_' + str(fs)].notna()) & (df_ECTS['Sem_ects_sum_' + str(fs)] >= fs*10), 'Sem_ects_agg_' + str(fs)] = 'mindestens ' + str(fs*10) + 'ECTS'
                df_ECTS.loc[(df_ECTS['Sem_ects_sum_' + str(fs)].notna()) & (df_ECTS['Sem_ects_sum_' + str(fs)] >= fs*20), 'Sem_ects_agg_' + str(fs)] = 'mindestens ' + str(fs*20) + 'ECTS'
                df_ECTS.loc[(df_ECTS['Sem_ects_sum_' + str(fs)].notna()) & (df_ECTS['Sem_ects_sum_' + str(fs)] >= fs*30), 'Sem_ects_agg_' + str(fs)] = 'mindestens ' + str(fs*30) + 'ECTS'
            else:
                df_ECTS.loc[(df_ECTS['Sem_ects_sum_' + str(fs)].notna()) & (df_ECTS['Sem_ects_sum_' + str(fs)] < 40), 'Sem_ects_agg_' + str(fs)] = 'weniger als 40 ECTS'
                df_ECTS.loc[(df_ECTS['Sem_ects_sum_' + str(fs)].notna()) & (df_ECTS['Sem_ects_sum_' + str(fs)] >= 40), 'Sem_ects_agg_' + str(fs)] = 'mindestens 40 ECTS'
                df_ECTS.loc[(df_ECTS['Sem_ects_sum_' + str(fs)].notna()) & (df_ECTS['Sem_ects_sum_' + str(fs)] >= 80), 'Sem_ects_agg_' + str(fs)] = 'mindestens 80 ECTS' 
                df_ECTS.loc[(df_ECTS['Sem_ects_sum_' + str(fs)].notna()) & (df_ECTS['Sem_ects_sum_' + str(fs)] >= 120), 'Sem_ects_agg_' + str(fs)] = 'bestanden'


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

def add_percentile (df_StudStart):
    #df_MNR = pd.read_pickle(os.path.abspath('..\\WiSe2122\\pickles\\df_studstart_bachelor_wise21.plk'))
    df_StudStart.loc[df_StudStart.bestanden == 'EN', 'Endnote'] = 5

    cohorts = pd.unique(df_StudStart['Startsemester']).tolist()
    studies = pd.unique(df_StudStart['studiengang']).tolist()
    #cohorts = [20202]
    df_final = pd.DataFrame(columns = ['MNR_Zweit', 'Endnote', 'y', 'percentile'])

    for cohort in cohorts:
        for study in studies:
             df = df_StudStart.loc[(df_StudStart.Endnote != 0) & 
                              (df_StudStart.Startsemester == cohort) & (df_StudStart.studiengang == study), ['MNR_Zweit', 'Endnote']]
             df = df.sort_values(by = ['Endnote'])
             df['y'] = np.arange(1, len(df.Endnote)+1)/len(df.Endnote)
             grades = pd.unique(df['Endnote']).tolist()
             for grade in grades:
                df.loc[df.Endnote == grade, 'percentile'] = df.loc[df.Endnote == grade, 'y'].max()
             df_final = pd.concat([df_final, df], ignore_index=True)
                

    df_StudStart = df_StudStart.merge(df_final[['MNR_Zweit', 'percentile']], on= 'MNR_Zweit', how = 'left')
    
    # save because result is needed for prepare_final_files
    
    if df_StudStart.studiengang.str.contains('Wirtschaftswissenschaften').any():
        df_StudStart.to_pickle(os.path.abspath('../../data/interim/bachelor/df_studstart_without_prediction.pkl'))
        
    else:
        df_StudStart.to_pickle(os.path.abspath('../../data/interim/master/df_studstart_without_prediction.pkl'))
        
    
    
    return df_StudStart


def save_data(typ='bachelor', df_Studies = df_Studies ,df_StudStart = df_StudStart, df_next = df_next,
              df_Path = df_Path, df_layers = df_layers, df_ECTS = df_ECTS, df_demo = df_demo):
    if typ == 'bachelor':
        # save as pickle

        # save as pickle
        df_Studies.to_pickle(os.path.abspath('../../data/interim/bachelor/df_Studies.pkl'))
        df_StudStart.to_pickle(os.path.abspath('../../data/interim/bachelor/df_studstart.pkl'))
        df_next.to_pickle(os.path.abspath('../../data/interim/bachelor/df_next_study.pkl'))
        df_Path.to_pickle(os.path.abspath('../../data/interim/bachelor/df_path.pkl'))
        df_layers.to_pickle(os.path.abspath('../../data/interim/bachelor/df_layers.pkl'))
        df_ECTS.to_pickle(os.path.abspath('../../data/interim/bachelor/df_ects.pkl'))
        df_demo.to_pickle(os.path.abspath('../../data/interim/bachelor/df_demo.pkl'))
        
        # save as csv
        df_layers.to_csv(os.path.abspath('../../data/processed/bachelor/df_layers.csv'), sep=';', decimal=',')
        df_StudStart.to_csv((os.path.abspath('../../data/processed/bachelor/df_studstart.csv')), sep=';', decimal=',')
        df_next.to_csv((os.path.abspath('../../data/processed/bachelor/df_next_study.csv')), sep=';', decimal=',')
        df_Path.to_csv(os.path.abspath('../../data/processed/bachelor/df_path.csv'), sep=';', decimal=',')
        df_ECTS.to_csv(os.path.abspath('../../data/processed/bachelor/df_ects.csv'), sep=';', decimal=',')
        df_demo.to_csv(os.path.abspath('../../data/processed/bachelor/df_demo.csv'), sep=';', decimal=',')
       
    else:

        # save as pickle
        df_Studies.to_pickle(os.path.abspath('../../data/interim/master/df_Studies.pkl'))
        df_StudStart.to_pickle(os.path.abspath('../../data/interim/master/df_studstart.pkl'))
        df_next.to_pickle(os.path.abspath('../../data/interim/master/df_next_study.pkl'))
        df_Path.to_pickle(os.path.abspath('../../data/interim/master/df_path.pkl'))
        df_layers.to_pickle(os.path.abspath('../../data/interim/master/df_layers.pkl'))
        df_ECTS.to_pickle(os.path.abspath('../../data/interim/master/df_ects.pkl'))
        df_demo.to_pickle(os.path.abspath('../../data/interim/master/df_demo.pkl'))
        
        # save as csv
        df_layers.to_csv(os.path.abspath('../../data/processed/master/df_layers.csv'), sep=';', decimal=',')
        df_StudStart.to_csv((os.path.abspath('../../data/processed/master/df_studstart.csv')), sep=';', decimal=',')
        df_next.to_csv((os.path.abspath('../../data/processed/master/df_next_study.csv')), sep=';', decimal=',')
        df_Path.to_csv(os.path.abspath('../../data/processed/master/df_path.csv'), sep=';', decimal=',')
        df_ECTS.to_csv(os.path.abspath('../../data/processed/master/df_ects.csv'), sep=';', decimal=',')
        df_demo.to_csv(os.path.abspath('../../data/processed/master/df_demo.csv'), sep=';', decimal=',')


if __name__ == '__main__':
    args = parse_args()
    
    # load data
    df_PrufData = pd.read_csv(os.path.abspath(args.exam_data_ba), sep=';', engine = 'python', encoding = 'utf-8')
    df_StudData = pd.read_csv(os.path.abspath(args.student_data_ba), sep=';', engine = 'python', encoding = 'utf-8')
    df_Master_Stud = pd.read_csv(os.path.abspath(args.next_master_study_ba), sep=';', engine = 'python', encoding = 'utf-8')
    df_stadt = pd.read_csv(os.path.abspath(args.city_names), sep=';', engine = 'python', encoding = 'windows-1252')
    df_Stud_struc = pd.read_csv(os.path.abspath(args.exam_regulation_ba), sep=';', engine = 'python', encoding = 'windows-1252')
    
    # progress and save
    concated_data = concate_all_data(clean_exam(df_PrufData), df_StudData)
    df_StudStart = stud_data(concated_data, 20212)
    if df_StudStart.studiengang.str.contains('Wirtschaftswissenschaften').any():
        df_next = getting_next_study(df_StudStart, df_Master_Stud)
    else:
        df_next = getting_next_study(df_StudStart, df_Master_Stud)
    df_Studies, df_StudStart, df_next = delete_personal_data(concated_data, df_StudStart, df_next)
    df_StudStart = add_percentile (df_StudStart)
    df_demo = demo_data(df_Studies, df_stadt)
    path_preparation = path_preparation(df_Studies)
    df_layers = get_exam_data(df_Studies, df_StudStart, df_Stud_struc)
    df_Path = path_final(path_preparation, df_layers, 20212)
    df_ECTS = show_ects(df_Path, df_StudStart)

    for semester in range (1,6):
        df_StudStart = add_probabilities(semester, df_StudStart, df_Path, df_demo)
    
    save_data()


