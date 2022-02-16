# -*- coding: utf-8 -*-
"""
Created on Tue Feb  8 11:29:31 2022

@author: ba42pizo
"""

import pandas as pd
import numpy as np
import os
import pickle

from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score 
import sys
sys.path.append('../features')
from build_features import prepare_final_files


def naive_bayes(x_train, y_train, x_test, y_test):

    from sklearn.naive_bayes import GaussianNB

    modelnb = GaussianNB()
    modelnb.fit(x_train, y_train)
    score = modelnb.score(x_test, y_test)
    y_pred = modelnb.predict(x_test)
    f1 = f1_score(y_test, y_pred, average = 'binary')
    print("NB: acurracy: " + str(score) + "; f1 score: " + str(f1))
    with open(os.path.abspath('../../models/modelnb_pickle'), 'wb') as file:
        pickle.dump(modelnb, file)

def random_forest(x_train, y_train, x_test, y_test):
    
    from sklearn.ensemble import RandomForestClassifier
    
    modelrf = RandomForestClassifier(n_estimators = 1000)
    modelrf.fit(x_train, y_train)
    score = modelrf.score(x_test, y_test)
    y_pred = modelrf.predict(x_test)
    f1 = f1_score(y_test, y_pred, average = 'binary')
    print("RF: acurracy: " + str(score) + "; f1 score: " + str(f1))
    with open(os.path.abspath('../../models/modelrf_pickle'), 'wb') as file:
        pickle.dump(modelrf, file)


def logistic_regression(x_train, y_train, x_test, y_test):
    
    from sklearn.linear_model import LogisticRegression

    logReg = LogisticRegression()

    logReg.fit(x_train, y_train)
    score = logReg.score(x_test, y_test)
    y_pred = logReg.predict(x_test)
    f1 = f1_score(y_test, y_pred, average = 'binary')
    print("LR: acurracy: " + str(score) + "; f1 score: " + str(f1))
    with open(os.path.abspath('../../models/modellr_pickle'), 'wb') as file:
        pickle.dump(logReg, file)

def support_vector_machine(x_train, y_train, x_test, y_test):
    
    from sklearn.svm import SVC

    modelsvm = SVC(kernel = 'rbf')
    modelsvm.fit(x_train, y_train)
    score = modelsvm.score(x_test, y_test)
    y_pred = modelsvm.predict(x_test)
    f1 = f1_score(y_test, y_pred, average = 'binary')
    print("SVM: acurracy: " + str(score) + "; f1 score: " + str(f1))
    with open(os.path.abspath('../../models/modelsvm_pickle'), 'wb') as file:
        pickle.dump(modelsvm, file)

def neural_net(x_train, y_train, x_test, y_test):
    
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense
    from tensorflow.keras.optimizers import Adam

    modelann = Sequential([
        Dense(units = 32, input_shape=(len(x_test.columns),), activation = 'sigmoid'),
        Dense(units = 64, activation = 'sigmoid'),
        Dense(units = 128, activation = 'sigmoid'),
        Dense(units = 256, activation = 'sigmoid'),
        Dense(units = 128, activation = 'sigmoid'),
        Dense(units = 64, activation = 'sigmoid'),
        Dense(units = 32, activation = 'sigmoid'),
        Dense(units = 1, activation = 'sigmoid')])

    modelann.compile(optimizer = Adam(learning_rate=0.001), loss= 'mean_squared_error', metrics=['accuracy'])
    modelann.fit(x_train, y_train, batch_size=64, epochs=100, validation_split=0.2, verbose = 0, callbacks=None, validation_data=None, shuffle=True)
    y_pred = modelann.predict(x_test)
    y_pred = np.where(y_pred >= 0.5, 1, 0)
    #y_test, y_pred = set(1, 2, 4), set(2, 8, 1)
    y = np.asarray(y_test) - y_pred[:,0]
    score = np.count_nonzero(y == 0)/(y_pred[:,0]).size
   #from sklearn.metrics import f1_score, accuracy_score, confusion_matrix
    #cm = confusion_matrix(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average = 'binary')
    print("ANN: acurracy: " + str(score) + "; f1 score: " + str(f1))
    with open(os.path.abspath('C:../../models/modelann_pickle'), 'wb') as file:
        pickle.dump(modelann, file)

if __name__ == '__main__':
    df_StudStart = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_studstart_without_prediction.pkl'))
    df_Path = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_path.pkl'))
    df_demo = pd.read_pickle(os.path.abspath('../../data/interim/bachelor/df_demo.pkl'))
    for semester in range(1,2):
        Final = prepare_final_files(semester, df_StudStart, df_Path, df_demo)[1]
        
        x_train, x_test, y_train, y_test = train_test_split(Final.drop(['MNR_Zweit', 'Startsemester', 'studiengang', 'final'], axis = 1), 
                                                            Final.final, test_size = 0.25, random_state = 0)
        
        logistic_regression(x_train, y_train, x_test, y_test)
        random_forest(x_train, y_train, x_test, y_test)
        naive_bayes(x_train, y_train, x_test, y_test)
        support_vector_machine(x_train, y_train, x_test, y_test)
        neural_net(x_train, y_train, x_test, y_test)

