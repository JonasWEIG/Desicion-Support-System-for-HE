# -*- coding: utf-8 -*-
"""
Created on Fri Feb  4 13:52:56 2022

@author: ba42pizo
"""
import argparse


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--student_data', type=str, default='../../data/external/20102021_WISO-Studierendendaten_3_BA_20212.csv',
                    help='path to bachelor student data')

    parser.add_argument('--exam_data_ba', type=str, default='../../data/external/20102021_WISO-Leistungsdaten_BA_20212.csv',
                    help='path to  bachelor exam data')

    parser.add_argument('--next_master_study_ba', type=str, default='../../data/external/20102021_WISO-Studierendendaten_3_MA_20212.csv',
                    help='path to  master student data for identifiing next study')    
    
    parser.add_argument('--exam_regulation_ba', type=str, default='../../data/external/po_bachelor_sose21.csv',
                    help='obligatory modules')    
    
    parser.add_argument('--city_names', type=str, default='../../data/external/stadtnamen_by.csv',
                    help='city names for classifying HZB type')    
    
    parser.add_argument('--current semester', type=int, default=20212,
                        help='current semester')
    
    

    return parser.parse_args()