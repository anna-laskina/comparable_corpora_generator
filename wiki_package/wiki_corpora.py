import os
from wiki_package import util
from wiki_package import constants


class WikiCorpus:

    def __init__(self, corpus_id=None,  corpus_version=None, corpus_sequence_number=None, info_path=constants.SAVE_PATH,
                 target_type=None, d_min=2):

        self.version = corpus_version if corpus_id is None else corpus_id[1: corpus_id.find('_')]
        self.sequence_number = corpus_sequence_number if corpus_id is None else corpus_id[corpus_id.find('_') + 1:]
        self.corpus_id = f'v{self.version}_{self.sequence_number}' if corpus_id is None else corpus_id
        self.language_1 = None
        self.language_2 = None

        self.dataset = None
        self.labels = None
        self.target = None
        self.lang_mask = None
        self.type_mask = None
        self.n_clusters = None
        self.n_docs = None

        self.bi_clusters = None
        self.mono1_clusters = None
        self.mono2_clusters = None
        self.primary_clusters = None
        self.secondary_clusters = None
        self.label2topic = None

        self.read_wikipedia_corpus(path=info_path)
        self.set_cluster_info(path=info_path, d_min=d_min)
        self.set_target(target_type=target_type)
        self.set_type_mask()

    def read_wikipedia_corpus(self, path):
        self.dataset = []
        self.labels = []
        self.lang_mask = []

        wiki_info = util.read_data(
            os.path.join(path, f'dataset_{self.corpus_id}/wikicorpus_{self.corpus_id}.json'))

        list_of_languages = sorted(set(doc_info['language'] for doc_info in wiki_info))
        if len(list_of_languages) > 2:
            print('The corpus with more than 2 languages is not supported.')
            exit()

        self.language_1, self.language_2 = list_of_languages

        for doc_info in wiki_info:
            self.dataset.append({'id': doc_info['id'], 'text': doc_info['text']})
            self.labels.append(doc_info['label'])
            self.lang_mask.append(0 if doc_info['language'] == self.language_1 else 1)
        self.n_docs = len(self.dataset)

    def set_cluster_info(self, path, d_min=2):
        topics_info = util.read_data(
            os.path.join(path, f'dataset_{self.corpus_id}/topic_information_{self.corpus_id}.json'))
        self.bi_clusters, self.mono1_clusters, self.mono2_clusters = [], [], []
        self.primary_clusters, self.secondary_clusters = set(), set()
        for topic_info in topics_info.values():
            topic_label = int(topic_info[2])
            if topic_info[0] == 'secondary' and int(topic_info[3]) < d_min:
                continue
            if topic_info[0] == 'primary':
                self.primary_clusters.add(topic_label)
            else:
                self.secondary_clusters.add(topic_label)
            if topic_info[1] == 'bilingual':
                self.bi_clusters.append(topic_label)
            elif topic_info[1] == f'monolingual {self.language_1}':
                self.mono1_clusters.append(topic_label)
            else:
                self.mono2_clusters.append(topic_label)

        self.label2topic = util.read_data(
            os.path.join(path, f'dataset_{self.corpus_id}/label_information_{self.corpus_id}.json'))
        if type(self.label2topic) is dict:
            self.label2topic = {int(k): v for k, v in self.label2topic.items()}

    def set_target(self, target_type='secondary'):
        topic_set = self.primary_clusters\
            if target_type == 'primary' else self.primary_clusters | self.secondary_clusters
        self.target = [list(set(labels) & topic_set) for labels in self.labels]
        self.n_clusters = len(set([doc_label for doc_labels in self.target for doc_label in doc_labels]))

    def set_type_mask(self):
        self.type_mask = []
        for i in range(self.n_docs):
            type_mark = None
            if len(self.target[i]) == 0:
                type_mark = -1
            elif self.target[i][0] in self.mono1_clusters:
                type_mark = 0
            elif self.target[i][0] in self.bi_clusters:
                type_mark = 1
            elif self.target[i][0] in self.mono2_clusters:
                type_mark = 2
            self.type_mask.append(type_mark)

        if None in self.type_mask:
            print('Clusters are not distributed by type correctly.')

    def get_cluster_type(self, label):
        if label in self.bi_clusters:
            return 1
        elif label in self.mono1_clusters:
            return 0
        elif label in self.mono2_clusters:
            return 2
        else:
            return -1

    def get_topic_by_label(self, label):
        if self.label2topic is None:
            print('No category information has been uploaded.')
            return None
        return self.label2topic[label]
