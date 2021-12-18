"""
使用RNN完成文本分类
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import random
import sys

import numpy as np
import pandas as pd
from sklearn import metrics
import tensorflow as tf
from sklearn.model_selection import train_test_split
from tensorflow.contrib.layers.python.layers import encoders



sen = pd.read_csv("temp_filem_ML.csv")['0'].apply(lambda x: tuple(eval(x)))
random.shuffle(sen)
x,y=zip(*sen)
train_data,test_data,train_target,test_target=train_test_split(x, y, random_state=1234)
cate_dic={'like':1,'dislike':0}
y_train = pd.Series(train_target).apply(lambda x:cate_dic[x] , train_target)
y_test = pd.Series(test_target).apply(lambda x:cate_dic[x] , test_target)

"""
基于卷积神经网络的中文文本分类
"""


import argparse
import sys
import numpy as np
import pandas as pd
from sklearn import metrics
import tensorflow as tf

learn = tf.contrib.learn
FLAGS = None
# 文档最长长度
MAX_DOCUMENT_LENGTH = 100
# 最小词频数
MIN_WORD_FREQUENCE = 2
# 词嵌入的维度
EMBEDDING_SIZE = 20
# filter个数
N_FILTERS = 10  # 10个神经元
# 感知野大小
WINDOW_SIZE = 20
# filter的形状
FILTER_SHAPE1 = [WINDOW_SIZE, EMBEDDING_SIZE]
FILTER_SHAPE2 = [WINDOW_SIZE, N_FILTERS]
# 池化
POOLING_WINDOW = 4
POOLING_STRIDE = 2
global n_words


def cnn_model(features, target):
    """
    2层的卷积神经网络，用于短文本分类
    """
    # 先把词转成词嵌入
    # 我们得到一个形状为[n_words, EMBEDDING_SIZE]的词表映射矩阵
    # 接着我们可以把一批文本映射成[batch_size, sequence_length,EMBEDDING_SIZE]的矩阵形式

    target = tf.one_hot(target, 15, 1, 0)  # 对词编码最大选前15个标签,在的为1,不在的为0
    print(target)
    # 把词变成词嵌入, feature 词矩阵, vocab_size输入数据的总词汇量, embed_dim嵌入矩阵的维度大小
    # 输出是 [句子数,词数,嵌入维度数]
    word_vectors = tf.contrib.layers.embed_sequence(features
                                                    , vocab_size=n_words
                                                    , embed_dim=EMBEDDING_SIZE
                                                    , scope='words')
    # 增加一维
    word_vectors = tf.expand_dims(word_vectors, 3)
    print(word_vectors)

    with tf.variable_scope('CNN_Layer1'):
        # 添加卷积层做滤波
        conv1 = tf.contrib.layers.convolution2d(word_vectors
                                                , N_FILTERS
                                                , FILTER_SHAPE1
                                                , padding='VALID')  # 不够了舍弃
        # 添加RELU非线性
        conv1 = tf.nn.relu(conv1)
        # 最大池化
        pool1 = tf.nn.max_pool(conv1
                               , ksize=[1, POOLING_WINDOW, 1, 1]
                               , strides=[1, POOLING_STRIDE, 1, 1]
                               , padding='SAME')  # 不够了填充
        # 对矩阵进行转置，以满足形状
        pool1 = tf.transpose(pool1, [0, 1, 3, 2])

    with tf.variable_scope('CNN_Layer2'):
        # 第2卷积层
        conv2 = tf.contrib.layers.convolution2d(pool1
                                                , N_FILTERS
                                                , FILTER_SHAPE2
                                                , padding='VALID')
        # 抽取特征
        pool2 = tf.squeeze(tf.reduce_max(conv2, 1), squeeze_dims=[1])

    # 全连接层
    logits = tf.contrib.layers.fully_connected(pool2, 15, activation_fn=None)
    loss = tf.losses.softmax_cross_entropy(target, logits)
    # 优化器
    train_op = tf.contrib.layers.optimize_loss(loss
                                               , tf.contrib.framework.get_global_step()
                                               , optimizer='Adam'
                                               , learning_rate=0.01)

    return ({
                'class': tf.argmax(logits, 1),
                'prob': tf.nn.softmax(logits)
            }, loss, train_op)


# 处理词汇
vocab_processor = learn.preprocessing.VocabularyProcessor(MAX_DOCUMENT_LENGTH# 最大长度和最小词频
                                                          ,min_frequency=MIN_WORD_FREQUENCE)
x_train = np.array(list(vocab_processor.fit_transform(train_data)))
x_test = np.array(list(vocab_processor.transform(test_data)))
n_words=len(vocab_processor.vocabulary_)
print('Total words:%d'%n_words)# 不重复的单词数量

# cate_dic={'like':1,'dislike':0}
# y_train = pd.Series(train_target).apply(lambda x:cate_dic[x] , train_target)
# y_test = pd.Series(test_target).apply(lambda x:cate_dic[x] , test_target)

# result_cnn=pd.DataFrame(columns=('step','loss_train','loss_test','score'))
# result_cnn.to_csv("./DL_model/cnn_loss.csv",index=False)
result_cnn = pd.read_csv("./DL_model/cnn_loss.csv")
for i in range(100):
    classifier1=learn.Estimator(model_fn=cnn_model,model_dir='./DL_model/cnn_model')
    #Train and predict
    classifier1_skl = learn.SKCompat(classifier1)
    classifier1_skl.fit(x_train,y_train,steps=100)
    y_predicted=classifier1_skl.predict(x_test)['class']
    score=metrics.accuracy_score(y_test,y_predicted)
    loss_train = classifier1.evaluate(x_train,y_train)
    loss_test = classifier1.evaluate(x_test,y_test)
    result_rnn = result_rnn.append({"loss_test":loss_test["loss"],
                                                        "loss_train":loss_train["loss"],
                                                        "score":score,
                                                        "step":loss_train["global_step"]
                                                        },ignore_index=True)
    result_rnn.to_csv("./DL_model/cnn_loss.csv",index=False)
    print("我存了第%d次"%i)