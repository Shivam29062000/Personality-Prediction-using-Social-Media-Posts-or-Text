import re
import numpy as np
import pandas as pd
import pickle
from bs4 import BeautifulSoup
from sklearn.model_selection import cross_validate
from sklearn.model_selection import StratifiedKFold
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB


def cleanText(text):
    text = BeautifulSoup(text, "lxml").text
    text = re.sub(r'\|\|\|', r' ', text) 
    text = re.sub(r'http\S+', r'<URL>', text)
    return text

train = pd.read_csv('mbti_1.csv')

train['clean_posts'] = train['posts'].apply(cleanText)

kfolds = StratifiedKFold(n_splits=5, shuffle=True, random_state=1)
scoring = {'acc': 'accuracy',
           'neg_log_loss': 'neg_log_loss',
           'f1_micro': 'f1_micro'}

np.random.seed(1)

tfidf2 = CountVectorizer(ngram_range=(1, 1), stop_words='english', lowercase = True, max_features = 5000)

model_nb = Pipeline([('tfidf1', tfidf2), ('nb', MultinomialNB())])

results_nb = cross_validate(model_nb, train['clean_posts'], train['type'], cv=kfolds, scoring=scoring, n_jobs=-1)

model_nb.fit(train['clean_posts'], train['type'])

pickle.dump(model_nb,open('NB-model.pkl','wb'))
