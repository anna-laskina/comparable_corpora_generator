import os
from wiki_package import util
from wiki_package import constants


class WikiCorpus:

    def __init__(self, corpus_id=None,  corpus_version=None, corpus_sequence_number=None,
                 language_1='en', language_2='fr', info_path=constants.SAVE_PATH,
                 load_label_info=True, set_cluster_info=True, load_primary_labels=True):

        self.version = corpus_version if corpus_id is None else corpus_id[1: corpus_id.find('_')]
        self.sequence_number = corpus_sequence_number if corpus_id is None else corpus_id[corpus_id.find('_') + 1:]
        self.corpus_id = f'v{self.version}_{self.sequence_number}' if corpus_id is None else corpus_id
        self.language_1 = language_1
        self.language_2 = language_2

        self.dataset = None
        self.target = None
        self.lang_mask = None
        self.type_mask = None
        self.n_clusters = None
        self.n_docs = None

        self.bi_clusters = None
        self.mono1_clusters = None
        self.mono2_clusters = None

        self.cat2label = None
        self.label2cat = None
        self.primary_target = None

        self.read_wikipedia_corpus(path=info_path)
        if load_primary_labels:
            self.def_primary_labels(path=info_path)
        if load_label_info:
            self.load_label2cat(path=info_path)
        if set_cluster_info:
            self.set_cluster_types()

    def read_wikipedia_corpus(self, path):
        self.dataset = []
        self.target = []
        self.lang_mask = []

        for land_id, language in enumerate([self.language_1, self.language_2]):
            wiki_info = util.read_data(
                os.path.join(path, f'dataset_{self.corpus_id}/wikipedia_{language}_{self.corpus_id}.json'))
            n_doc = len(wiki_info['id'])
            self.dataset.extend([{'id': doc_id, 'text': wiki_info['text'][i]}
                                 for i, doc_id in enumerate(wiki_info['id'])])
            self.target.extend(wiki_info['label'])
            self.lang_mask.extend([land_id] * n_doc)
        self.n_clusters = len(set([doc_label for doc_labels in self.target for doc_label in doc_labels]))
        self.n_docs = len(self.dataset)

    def def_primary_labels(self, path):
        try:
            topic_by_type = util.read_data(
                os.path.join(
                    path, f'dataset_{self.corpus_id}/'
                          f'wikipedia_categories_main_{self.language_1}-{self.language_2}_{self.corpus_id}.json'))
            primary_cats = [cat for type_dict in topic_by_type.values() for cat in type_dict['category']]
        except FileNotFoundError:
            print('No primary topics information found!')
            return None

        cat2label = util.read_data(
            os.path.join(path,
                         f'dataset_{self.corpus_id}/'
                         f'wikipedia_labels_{self.language_1}-{self.language_2}_{self.corpus_id}.json'))

        primary_labels = [cat2label[cat] for cat in primary_cats if cat in cat2label.keys()]
        self.primary_target = [[label for label in labels if label in primary_labels] for labels in self.target]
        return self.primary_target

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

    def set_cluster_types(self):
        lang_labels = [set(), set()]

        for i in range(self.n_docs):
            for label in self.target[i]:
                lang_labels[self.lang_mask[i]].add(label)

        self.bi_clusters = set(lang_labels[0] & lang_labels[1])
        self.mono1_clusters = set(lang_labels[0] - lang_labels[1])
        self.mono2_clusters = set(lang_labels[1] - lang_labels[0])
        self.set_type_mask()

    def get_cluster_type(self, label):
        if label in self.bi_clusters:
            return 1
        elif label in self.mono1_clusters:
            return 0
        elif label in self.mono2_clusters:
            return 2
        else:
            return -1

    def load_label2cat(self, path):
        self.label2cat = util.read_data(
            os.path.join(path, f'dataset_{self.corpus_id}/'
                               f'wikipedia_categories_all_{self.language_1}-{self.language_2}_{self.corpus_id}.json'))
        if type(self.label2cat) is dict:
            self.label2cat = {int(k): v for k,v in self.label2cat.items()}

    def label2cat(self, label):
        if self.label2cat is None:
            print('No category information has been uploaded.')
            return None
        return self.label2cat[label]
