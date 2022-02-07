# -*- coding: utf-8 -*-
"""
Created on Mon Feb  7 15:59:44 2022

@author: ba42pizo
"""

#### finalize dataframe
Final2 = Final.iloc[:,15:]
Final3 = Final2.drop(['hzb_erwerbsort', 'hzbart', 'hzbdatum', 'immadat', 'HZB_bis_Imma', 
                      'HZB_art', 'semester_date', 'fachsem', 'final', 'Status', 'Status_EN'], axis = 1)
Final3.loc[Final3.hzbnote.isna(),'hzbnote'] = Final3.hzbnote.mean()
Final3.loc[Final3.Durchschnittsnote.isna(),'Durchschnittsnote'] = 5
normalized_df=(Final3-Final3.min())/(Final3.max()-Final3.min())

y = Final.final
'''
import statsmodels.api as sm

model = sm.Logit(y, normalized_df)
result =model.fit()
result.summary2()
'''
normalized_df['Durchschnittsnote'].corr(normalized_df['hzbnote'])