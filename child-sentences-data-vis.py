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
def is_ads(doc):
    is_subj = False
    is_verb = False
    is_obj = False

    for token in doc:
        if token.dep_ == 'nsubj':
            is_subj = True
        if token.pos_ == 'VERB' or token.pos_ == 'AUX':
            if is_subj is False:
                return False
            else:
                is_verb = True
        if token.dep_ == 'advmod' and is_verb is False:
            continue
        if 'obj' in token.dep_ or 'advmod' == token.dep_:
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
    if re.search('^C', sentence) is None:
        return 'Not a child sentence :('
    # Clean the C at the beginning of the sentence
    sentence = re.sub("^C ", '', sentence)

    # Clean mazes
    sentence = re.sub('\\(.+?\\)\\s', '', sentence)

    # Clean pipes (the word before the pipe)
    sentence = re.sub('\\s\\w*?\\|', ' ', sentence)

    # Clean slashes
    sentence = sentence.replace('/*3', '')
    stops = ['p', 'b', 't', 'd']
    for ch in stops:
        sentence = sentence.replace(ch + '/ing', ch + ch + 'ing')
        sentence = sentence.replace(ch + '/ed', ch + ch + 'ed')

    sentence = sentence.replace('/ing', 'ing')
    sentence = sentence.replace('/ed', 'ed')
    sentence = sentence.replace('/s', 's')

    # Clean asterisks (the entire word)
    sentence = re.sub('\\*.*?\\s', '', sentence)

    # Clean overlap markers < and >
    sentence = re.sub('<', '', sentence)
    sentence = re.sub('>', '', sentence)

    # Clean braces { }
    sentence = re.sub('\\{.*\\}', '', sentence)

    # Clean brackets [ ]
    sentence = re.sub('\\[.*?\\]', '', sentence)

    # Clean any accidental double spaces
    sentence = sentence.replace('  ', ' ')

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


def find_verb_uncoded(doc):
    verb = get_lemma_with_pos(doc, 'VERB')
    if verb is None:
        verb = get_lemma_with_pos(doc, 'AUX')
    return verb


# Uses codes
def find_verb_coded(sentence):
    verb_codes = ['[0]', '/ed', '/ing', '[i3:o]']
    needed_code = ''
    for code in verb_codes:
        if code in sentence:
            needed_code = code
            break

    if needed_code == '':
        return ':('

    words_list = sentence.split()
    for word in words_list:
        if needed_code in word:
            return word.split(needed_code)[0]

    return ':('


# Uses codes
def find_subject(sentence):
    words_list = sentence.split()
    for word in words_list:
        if re.search('\\[SV:\\dP?\\]', word) is not None:
            return word.split('[')[0].replace('/', '')

    return ':('


# Returns a nested dict given a base type and number of nests
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


def find_given_child_sentences(dataframe, child_id):
    # find starting point
    count = 0
    for value in dataframe.iloc[:, 0]:
        count += 1
        if value == child_id:
            dataframe = dataframe.iloc[count:]
            break

    # find ending point
    count = 0
    for value in dataframe.iloc[:, 0]:
        count += 1
        if value == 'Total Frequency':
            dataframe = dataframe.iloc[:count]
            break

    # remove the unneeded columns, duplicates, and NaN values
    dataframe = dataframe.drop(dataframe.columns[[0, 2]], axis=1)
    dataframe = dataframe.drop_duplicates().dropna()

    return dataframe


def read_file(loc, child_id):
    dataframe = pandas.read_excel(loc)
    dataframe = find_given_child_sentences(dataframe, child_id)
    sentences_array = []

    for (cname, columnData) in dataframe.iteritems():
        sentences_array.append(columnData.values)

    return to_list(sentences_array)


def classify_text(sentences_list):
    # an array containing SV dicts
    sv_list = []
    for sentence in sentences_list:
        if is_copula(sentence):
            continue

        subject = find_subject(sentence)
        if subject == ':(':
            continue

        verb = find_verb_coded(sentence)

        sentence = clean_sentence(sentence)
        doc = nlp(sentence)
        if not is_ads(doc):
            print(doc)
            continue

        if verb == ':(':
            verb = find_verb_uncoded(doc)

        sv_list.append({'subject': subject, 'verb': verb})

    sv_count = count_subject_verbs(sv_list)
    df = pandas.DataFrame.from_dict(sv_count).fillna(0)
    return df


def create_graph(df, child_id):
    sns.heatmap(df, annot=True, fmt="g", cmap='viridis').set(xlabel='Subject', ylabel='Verb')

    # uncomment this line if you want to save the graph to file:
    # plt.savefig(child_id + '_heatmap.png', dpi=400)
    plt.show()

# ----------------------------------------------End function definitions---------------------------------------------- #


location = "/Users/ishita/PycharmProjects/sv-diversity-data-vis/data/childsentences.xlsx"
child_id = 'JTGTP44B 30P.SLT'
sentences = read_file(location, child_id)
data_frame = classify_text(sentences)
print(data_frame)
create_graph(data_frame, child_id)
