# -*- coding: utf-8 -*-
"""
Created on Thu Feb 17 17:59:41 2022

@author: ba42pizo
"""

from make_dataset import *
from utils import *
import os
import sys
sys.path.append('../features')
from build_features import add_probabilities, prepare_final_files
sys.path.append('../models')
from apriori import add_association_rules

if __name__ == '__main__':
    args = parse_args()
    
    # load data
    df_PrufData = pd.read_csv(os.path.abspath(args.exam_data_ma), sep=';', engine = 'python', encoding = 'utf-8')
    df_StudData = pd.read_csv(os.path.abspath(args.student_data_ma), sep=';', engine = 'python', encoding = 'utf-8')
    df_Bachelor_Stud = pd.read_csv(os.path.abspath(args.last_bachelor_study_ma), sep=';', engine = 'python', encoding = 'utf-8')
    df_Bachelor_Pruf = pd.read_csv(os.path.abspath(args.exam_data_ba), sep=';', engine = 'python', encoding = 'utf-8')
    df_stadt = pd.read_csv(os.path.abspath(args.city_names), sep=';', engine = 'python', encoding = 'windows-1252')
    df_Stud_struc = pd.read_csv(os.path.abspath(args.exam_regulation_ba), sep=';', engine = 'python', encoding = 'windows-1252')
    
    # progress and save
    concated_data = concate_all_data(clean_exam(df_PrufData), df_StudData)
    df_StudStart = stud_data(concated_data, 20212)
    if df_StudStart.studiengang.str.contains('Wirtschaftswissenschaften').any():
        df_next = getting_next_study(df_StudStart, df_Master_Stud)
    else:
        df_next = getting_last_study(df_StudStart, df_Bachelor_Stud, df_Bachelor_Pruf)
    df_Studies, df_StudStart, df_next = delete_personal_data(concated_data, df_StudStart, df_next)
    df_StudStart = add_percentile (df_StudStart)
    df_demo = demo_data(df_Studies, df_stadt)
    path_preparation = path_preparation(df_Studies)
    df_layers = get_exam_data(df_Studies, df_StudStart, df_Stud_struc, 'master')
    df_Path = path_final(path_preparation, df_layers, 20212)
    df_ECTS = show_ects(df_Path, df_StudStart, 'master')
    
    
    for semester in range (1,6):
        df_StudStart = add_probabilities(semester, df_StudStart, df_Path, df_demo, 'master')
       
    save_data('master')
    
    df_final = add_association_rules(df_layers, df_StudStart, 0.02, 'master')
    df_final.to_pickle(os.path.abspath('../../data/interim/master/df_apriori.pkl'))
    df_final.to_csv(os.path.abspath('../../data/processed/master/df_apriori.csv'), sep=';', decimal=',', encoding = 'utf-8')
