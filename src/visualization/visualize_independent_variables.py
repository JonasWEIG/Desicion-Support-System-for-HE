# -*- coding: utf-8 -*-
"""
Created on Mon Feb  7 16:00:56 2022

@author: ba42pizo
"""

from build_features import *
#### visualisation of independent variables

df_studstart = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_studstart.pkl'))
df_Path = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_path.pkl'))
df_demo = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_demo.pkl'))
prepare_final_files(1, df_studstart, df_Path, df_demo)
semesters = [2,3,4,5]
for semester in semesters:
    df_Studstart = prepare_final_files(semester, df_Studstart, df_Path, df_demo)

prepare_final_files()
for f in list(Final.iloc[:,3:].columns.values):
    sns.countplot(x = f, data = Final, hue = 'final')
    plt.show()