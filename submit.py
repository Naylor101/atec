#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import tensorflow as tf
tfconfig = tf.ConfigProto()
tfconfig.gpu_options.allow_growth = True
session = tf.Session(config=tfconfig)
import sys
import keras
import keras.backend as K
from keras.layers import *
from keras.models import *
from keras.optimizers import *
from keras.callbacks import *
import numpy as np
from keras.activations import softmax
from keras import backend
# Model Load
sys.path.append('utils/')
sys.path.append('feature/')
import config
from Feats import data_2id, add_hum_feats
from CutWord import cut_word
from help import get_X_Y_from_df
import pandas as pd

def load_data(in_path):
    print('load data')
    data = cut_word(in_path, config.cut_char_level)
    data = data_2id(data)  # 2id
    data = add_hum_feats(data, '')  # 生成特征并加入

    return data


def main(in_path, out_path):

    for file in os.listdir('./'):
        if file.endswith('.h5'):
            model_path = file
    data = load_data(in_path)
    X, _ = get_X_Y_from_df(data, False, False)
    if config.feats == []:
        X = X[:2]

    print('load model and predict')
    model = load_model(model_path, custom_objects={"softmax": softmax})
    test_pred = model.predict(X, batch_size=config.batch_size)
    print('save submit file')
    data['label'] = [int(x > 0.5) for x in test_pred[:, 1]]
    data[['id', 'label']].to_csv(out_path, index=False, header=None, sep='\t')


def main_test(model_path):
    in_path = 'submit/a.csv'
    out_path = 'submit/{0}.csv'.format(model_path.split('/')[-1])

    X, _ = get_X_Y_from_df(data, False, False)
    if config.feats == []:
        X = X[:2]
    model = load_model(model_path, custom_objects={"softmax": softmax})
    test_pred = model.predict(X, batch_size=config.batch_size)
    print('save submit file')
    data['label'] = [int(x > 0.5) for x in test_pred[:, 1]]
    data[['id', 'label']].to_csv(out_path, index=False, header=None, sep='\t')


def make_test_cv_data(X_dev, model_name, epoch_nums, kfolds):
    mean_epoch = False
    test_df = pd.DataFrame()
    S_test = np.zeros((X_dev[0].shape[0], epoch_nums))
    for epoch_num in range(epoch_nums):
        for kf in range(1, kfolds + 1):
            print('kf: ', kf)
            print('epoch_num: ', epoch_num + 1)
            model = load_model("stack_data/_%s_%s.h5" %
                               (model_name, epoch_num), custom_objects={"softmax": softmax})
            pred = model.predict(X_dev, batch_size=config.batch_size)

            S_test[:, epoch_num] += pred[:, 1]
        S_test[:, epoch_num] /= kfolds

        test_df['epoch_%s' % (epoch_num)] = S_test[:, epoch_num]
        test_df.to_csv('stack_data/test_%s.csv' % (model_name),
                       index=False,)
        if mean_epoch:
            pred = np.mean(S_test, axis=1)
        else:
            pred = S_test[:,epoch_num]
        return pred


def do_cv_test(in_path, out_path):

    model_name = 'cnn'
    epoch_nums = 2
    kfolds = 3
    data = load_data(in_path)
    X, _ = get_X_Y_from_df(data, False, False)
    if config.feats == []:
        X = X[:2]
    pred = make_test_cv_data(X, model_name, epoch_nums, kfolds)
    data['label'] = [int(x > 0.5) for x in pred]
    data[['id', 'label']].to_csv(out_path, index=False, header=None, sep='\t')


if __name__ == '__main__':
    #main(sys.argv[1], sys.argv[2])
    do_cv_test(sys.argv[1],sys.argv[2])
    # main_test(sys.argv[1])
