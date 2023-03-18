from nltk.stem.wordnet import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer

import nltk
nltk.download('all')
from nltk.corpus import stopwords
from preprocessing import lemma_tagger as tag

lemmatizer = WordNetLemmatizer()
analyzer = TfidfVectorizer().build_analyzer()
def stemmed_words(doc):
    return (lemmatizer.lemmatize(w,tag.get_wordnet_pos(w)) for w in analyzer(doc) if w not in set(stopwords.words('english')))
