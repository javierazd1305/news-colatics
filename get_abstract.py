import urllib3
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import progressbar
import pandas as pd
import re
import nltk
from nltk.tokenize import sent_tokenize
import numpy as np
from nltk.corpus import stopwords
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
import networkx as nx
from gensim.summarization.summarizer import summarize

# nltk.download('punkt') # one time execution
# nltk.download('stopwords')

def loadingGlove100d(path):
    word_embeddings = {}
    f = open(path, encoding='utf-8')
    for line in f:
        values = line.split()
        word = values[0]
        coefs = np.asarray(values[1:], dtype='float32')
        word_embeddings[word] = coefs
    f.close()
    return word_embeddings

def remove_stopwords(sen):
    sen_new = " ".join([i for i in sen if i not in stop_words])
    return sen_new

def pageRankAlgorithm(paragraph, word_embeddings, stop_words,ns=10):
    sentences = []
    sentences = sent_tokenize(paragraph)
    no_repeated_sentences = list(set(sentences))
    no_repeated_sentences_formatted  = no_repeated_sentences.copy()
    for index, sentence in enumerate(no_repeated_sentences_formatted):
        formatted_sentence = re.sub(r'\[[0-9]*\]',' ', sentence)
        formatted_sentence = re.sub(r'\s+',' ', formatted_sentence)
        formatted_sentence = re.sub(r'[^a-zA-Z]',' ', formatted_sentence)
        formatted_sentence = formatted_sentence.lower()
        formatted_sentence = formatted_sentence.replace("  "," ")
        no_repeated_sentences_formatted[index] = formatted_sentence

    clean_sentences = [remove_stopwords(r.split()) for r in no_repeated_sentences_formatted]
    sentence_vectors = []

    for i in clean_sentences:
      if len(i) != 0:
        v = sum([word_embeddings.get(w, np.zeros((100,))) for w in i.split()])/(len(i.split())+0.001)
      else:
        v = np.zeros((100,))
      sentence_vectors.append(v)

    sim_mat = np.zeros([len(no_repeated_sentences_formatted), len(no_repeated_sentences_formatted)])
    for i in range(len(no_repeated_sentences_formatted)):
      for j in range(len(no_repeated_sentences_formatted)):
        if i != j:
          sim_mat[i][j] = cosine_similarity(sentence_vectors[i].reshape(1,100), sentence_vectors[j].reshape(1,100))[0,0]

    nx_graph = nx.from_numpy_array(sim_mat)
    scores = nx.pagerank(nx_graph)

    ranked_sentences = sorted(((scores[i],s) for i,s in enumerate(no_repeated_sentences)), reverse=True)
    result = []
    for i in range(ns):
      result.append(ranked_sentences[i][1])
    return result

def getNewsData(sheet_name):
    SITE_ROOT = os.path.dirname(os.path.realpath('__file__'))
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(SITE_ROOT + '/client_secret.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1k-ersaEgGhnAXU3Xah715J8BKdZtrJHdOdwMuwqFgzQ/edit#gid=0")
    sheet_ = sheet.worksheet(sheet_name)
    data = sheet_.get_all_records()
    df_data = pd.DataFrame(data)
    return df_data

def getParagraph(url):
    http_pool = urllib3.connection_from_url(url)
    r = http_pool.urlopen('GET',url)
    soup = BeautifulSoup(r.data.decode('utf-8'), 'html.parser')
    text = soup.findAll('p')
    paragraph = ""
    for i in text:
        paragraph += i.text
    return paragraph

def textRankAlgorithm(paragraph):
    summary = summarize(paragraph,word_count=100)
    return summary



# df_hbr = getNewsData("HBR")
# df_mckinsey = getNewsData("McKinsey")
# glove_100d_we = loadingGlove100d('glove.6B.100d.txt')
# stop_words = stopwords.words('english')
# url = df_mckinsey.iloc[8]["url"]
# url
# paragraph = getParagraph(url)
# print(len(paragraph))
# summarized_tr = textRankAlgorithm(paragraph)
# summarized_tr
# summarized_pr = pageRankAlgorithm(paragraph, glove_100d_we, stop_words)
# summarized_pr[0]
