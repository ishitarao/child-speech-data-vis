import spacy
import pandas
import re
from collections import defaultdict
import seaborn as sns
import matplotlib.pyplot as plt

'''
Bug report 1: "I want open that" - spacy reads 'that' as a nominal subject
'''

nlp = spacy.load('en_core_web_sm')


# checks if the sentence is an Active Declarative Sentence
def is_ads(sentence):
    doc = nlp(sentence)
    is_subj = False
    is_verb = False
    is_obj = False

    for token in doc:
        # bad hard coding
        if token.text == 'Pooh':
            is_subj = True
        if token.dep_ == 'nsubj':
            is_subj = True
        if token.pos_ == 'VERB' or token.pos_ == 'AUX':
            if is_subj is False:
                return False
            else:
                is_verb = True
        if 'obj' in token.dep_:
            if is_verb is False:
                return False
            else:
                is_obj = True
                break

    return is_subj and is_obj and is_verb


# checks if the sentence is a copula: USES CODES
def is_copula(sentence):
    return re.search("\\[SC:\\d\\]", sentence) is not None


# Cleans the sentence of any mazes and codes
def clean_sentence(sentence):
    # Clean the C at the beginning of the sentence
    sentence = re.sub("^C ", '', sentence)

    # Clean mazes
    sentence = re.sub('\\(.+\\)\\s', '', sentence)

    # Clean pipes (the word before the pipe)
    sentence = re.sub('\\s\\w*?\\|', ' ', sentence)

    # Clean slashes (this doesn't work, will probably change it
    sentence = re.sub('/\\*.*?\\s|\\.', ' ', sentence)

    # Clean asterisks (the entire word)
    sentence = re.sub('\\*.*?\\s', '', sentence)

    # Clean overlap markers < and >
    sentence = re.sub('<', '', sentence)
    sentence = re.sub('>', '', sentence)

    # Clean braces { }
    sentence = re.sub('\\{.*\\}', '', sentence)

    # Clean brackets [ ]
    sentence = re.sub('\\[.*?\\]', '', sentence)

    return sentence


# FIRST OCCURRENCE
def get_token_with_dep(doc, dep):
    for token in doc:
        if token.dep_ == dep:
            return token.text
    return None


# does NOT count copulas
def get_lemma_with_pos(doc, pos):
    for token in doc:
        if token.pos_ == pos and token.lemma_ != 'be':
            return token.lemma_
    return None


# Parses through the given sentence and returns a dict containing the subject and the verb
def parse_sentence(sentence):
    doc = nlp(sentence)
    subject = get_token_with_dep(doc, 'nsubj')
    # bad hard coding
    if subject is None:
        subject = 'Pooh'
    verb = get_lemma_with_pos(doc, 'VERB')
    if verb is None:
        verb = get_lemma_with_pos(doc, 'AUX')

    # obj = get_token_with_dep(doc, 'dobj')
    # if obj is None:
    #     obj = get_token_with_dep(doc, 'obj')
    #
    # svo = {'subject': subject, 'verb': verb, 'object': obj}

    # WARNING: Really bad hardcoding incoming
    if verb == 'nee':
        verb = 'need'
    if verb == 'will':
        verb = 'get'
    sv = {'subject': subject, 'verb': verb}
    return sv


def nested_dict(n, type):
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: nested_dict(n-1, type))


def count_subject_verbs(svo_list):
    sv_count = nested_dict(2, int)
    for svo in svo_list:
        sv_count[svo['subject']][svo['verb']] += 1

    return sv_count


# convert the array we got to a list, since lists are more convenient
def to_list(array):
    sentences_list = []
    for column in array:
        col_as_list = column.tolist()
        for sentence in col_as_list:
            sentences_list.append(sentence)

    return sentences_list


def read_file(loc):
    dataframe = pandas.read_excel(loc)
    dataframe = dataframe.iloc[6:] # 6
    dataframe = dataframe.drop(dataframe.columns[[0, 2]], axis=1)
    dataframe = dataframe.drop_duplicates()
    sentences_array = []

    # add the first x sentences of the excel file to work with
    for (cname, columnData) in dataframe.head(92).iteritems():
        sentences_array.append(columnData.values)

    return to_list(sentences_array)


def classify_text(sentences_list):
    # an array containing SV dicts
    sv_list = []
    for sentence in sentences_list:
        sentence = clean_sentence(sentence)
        if is_copula(sentence) or not is_ads(sentence):
            continue

        sv_list.append(parse_sentence(sentence))
        # sv = parse_sentence(sentence)
        # if not sv_list.__contains__(sv):
        #     sv_list.append(sv)
        # else:
        #     continue

    sv_count = count_subject_verbs(sv_list)
    df = pandas.DataFrame.from_dict(sv_count).fillna(0)
    return df


def create_graph(df):
    sns.heatmap(df, annot=True, fmt="g", cmap='viridis').set(xlabel='Subject', ylabel='Verb')
    # plt.savefig('Child-sentence-Heatmap.png', dpi=400)
    plt.show()

# ----------------------------------------------End function definitions---------------------------------------------- #


location = "/Users/ishita/PycharmProjects/APL-child-sentences-data-vis/data/childsentences.xlsx"
sentences = read_file(location)
data_frame = classify_text(sentences)
create_graph(data_frame)
