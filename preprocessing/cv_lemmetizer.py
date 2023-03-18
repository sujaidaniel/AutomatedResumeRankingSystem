from nltk.stem.wordnet import WordNetLemmatizer

import nltk
nltk.download('all')
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from preprocessing import lemma_tagger as tag


lemmatizer = WordNetLemmatizer()
analyzer = CountVectorizer().build_analyzer()
def stemmed_words(doc):
    return (lemmatizer.lemmatize(w,tag.get_wordnet_pos(w)) for w in analyzer(doc) if w not in set(stopwords.words('english')))