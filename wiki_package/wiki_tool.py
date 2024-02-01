import glob
import os

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from wiki_package import constants
from wiki_package.util import path_check
from wiki_package.wiki_corpora import WikiCorpus


def visualize_wikipedia_corpus(corpus_id, corpus_path=constants.SAVE_PATH, save_path=constants.SAVE_PATH,
                               target_type='secondary',
                               show_stat=True, plot_bar=True, min_size_label=0, plot_heatmap=True, size_show=50,
                               max_size_label=100, fill2size=True, TD_count=True, min_dt=100, plot_td=True):
    """Function for visualize wikipedia corpus.

    :param corpus_id: str, A name to identify several versions of the corpus. Ex. v0_0.
    :param corpus_path: str, Path where the corpus files are located.
    :param save_path: str, Path where plot will be saved.
    :param show_stat:  Bool, Show information about the number of documents and labels.
    :param plot_bar: Bool, Whether to build a bar plot (def. True)
    :param min_size_label: int, the minimum number of pages in a category, so that it is shown on the bar (def. 0).
    :param plot_heatmap: Bool, Whether to build a heatmap plot (def. True)
    :param size_show: int, The number categories, so that it is shown on the heatmap (def. 50).
    :param max_size_label: int, Number of pages to which the number of pages in a category pair will be cut
     to build a heatmap (def. 100).
    :return: None
    """
    # corpus_path = os.path.join(corpus_path, f'dataset_{corpus_id}')
    save_path = os.path.join(save_path, f'dataset_{corpus_id}')
    path_check(path=os.path.join(save_path), if_create=True)
    langs = [path_name[-len(f'_{corpus_id}.json') - 5:-len(f'_{corpus_id}.json')].split('-') for path_name in
             glob.glob(os.path.join(corpus_path,
                                    f'dataset_{corpus_id}/wikipedia_categories_main_??-??_{corpus_id}.json'))]
    if len(langs) == 0:
        langs = [path_name[-len(f'_{corpus_id}.json') - 5:-len(f'_{corpus_id}.json')].split('-') for path_name in
                 glob.glob(os.path.join(corpus_path,
                                        f'dataset_{corpus_id}/wikipedia_categories_all_??-??_{corpus_id}.json'))]
    corpus = WikiCorpus(corpus_id=corpus_id, language_1=langs[0][0], language_2=langs[0][1],
                        load_label_info=True, set_cluster_info=True, info_path=corpus_path,
                        load_primary_labels=True if target_type == 'primary' else False)
    if target_type == 'primary':
        corpus.target = corpus.primary_target
        corpus.set_cluster_types()
        corpus_id += '_prime'
    if show_stat:
        print('DOC', f'Total = {len(corpus.dataset)}, '
                     f'In {corpus.language_1} = {corpus.lang_mask.count(0)}, '
                     f'In {corpus.language_2} = {corpus.lang_mask.count(1)}, '
                     f'Common = {corpus.type_mask.count(1)}, '
                     f'Only in {corpus.language_1} = {corpus.type_mask.count(0)}, '
                     f'Only in {corpus.language_2} = {corpus.type_mask.count(2)}.')

        print('LABELS', f'Total = {len(corpus.mono1_clusters) + len(corpus.mono2_clusters) + len(corpus.bi_clusters)}, '
                        f'In {corpus.language_1} = {len(corpus.mono1_clusters) + len(corpus.bi_clusters)}, '
                        f'In {corpus.language_2} = {len(corpus.mono2_clusters) + len(corpus.bi_clusters)}, '
                        f'Common = {len(corpus.bi_clusters)}, '
                        f'Only in {corpus.language_1} = {len(corpus.mono1_clusters)}, '
                        f'Only in {corpus.language_2} = {len(corpus.mono2_clusters)}.')

    if plot_bar:
        label_count = {label: [0, 0] for label in range(corpus.n_clusters)}
        for i in range(corpus.n_docs):
            for label in corpus.target[i]:
                label_count[label][corpus.lang_mask[i]] += 1

        label_count = {k: v for k, v in label_count.items() if sum(v) >= min_size_label}
        label_count = {k: v for k, v in
                       sorted(label_count.items(), key=lambda item: sum(item[1]), reverse=True)}
        dataframe = pd.DataFrame({
            corpus.language_1: [v[0] for v in label_count.values()],
            corpus.language_2: [v[1] for v in label_count.values()]},
            index=[corpus.label2cat[i] for i in label_count.keys()]
        )
        axis = dataframe.plot.bar(figsize=(20, 10))
        plt.savefig(os.path.join(save_path, f'wikipedia_{corpus_id}_bar{min_size_label}.png'))
        plt.show()

    if plot_heatmap:
        fig, axs = plt.subplots(1, 3, figsize=(15, 5))
        map = np.zeros((corpus.n_clusters + 1, corpus.n_clusters + 1))
        label2index = {label: i for i, label in enumerate(list(set([l for ls in corpus.target for l in ls])))}

        for i in range(corpus.n_docs):
            for label_1 in corpus.target[i]:
                for label_2 in corpus.target[i]:
                    map[label2index[label_1], label2index[label_2]] += 1
        for i in range(corpus.n_clusters):
            for j in range(corpus.n_clusters):
                if map[i, j] > max_size_label:
                    map[i, j] = max_size_label

        for i, clusters in enumerate([corpus.mono1_clusters, corpus.bi_clusters, corpus.mono2_clusters]):
            list_of_labels = np.array(list(clusters))
            cluster_sizes = np.array([map[label2index[label], label2index[label]] for label in list_of_labels])
            index = np.array([label2index[label]
                              for label in list_of_labels[(-cluster_sizes).argsort()[:size_show]].astype(int)])
            if fill2size and len(index) < size_show:
                index = np.append(index,np.array([corpus.n_clusters] * (size_show - len(index))))
            sub_map = map[index][:, index]

            sns.heatmap(sub_map,
                        # xticklabels=index, yticklabels=index,
                        cmap="YlGnBu", ax=axs[i], vmax=max_size_label)
            axs[i].set_title([f'monolingual {corpus.language_1}', 'bilingual', f'monolingual {corpus.language_2}'][i])
            # axs[i].set(xlabel="Label id", ylabel="Label id")
        plt.savefig(os.path.join(save_path, f'wikipedia_{corpus_id}_heatmap{size_show}-{max_size_label}.png'))
        plt.show()

    if TD_count == True:
        target_d1 = [label for labels in corpus.target for label in labels]
        label_count = {label: target_d1.count(label) for label in set(target_d1)}
        relevant_labels = [k for k, v in label_count.items() if v >= min_dt]
        relevant_labels_set = set(relevant_labels)
        topic_count_per_doc = {}
        for labels in corpus.target:
            relevant_topic_num = len(set(labels) & relevant_labels_set)
            topic_count_per_doc[relevant_topic_num] = topic_count_per_doc.get(relevant_topic_num, 0) + 1
        topic_count_per_doc = dict(sorted(topic_count_per_doc.items()))
        n_relevant_doc = sum([v for k, v in topic_count_per_doc.items() if k != 0])
        docs_per_relevant_cluster = [label_count[label] for label in relevant_labels]
        print(f'If only labels with at least {min_dt} documents are considered.')
        print(f'Docs: {n_relevant_doc:5d} Labels:{len(relevant_labels):3d} Labels per Doc: {sum([k * v for k, v in topic_count_per_doc.items() if k != 0])/n_relevant_doc:.2f} Docs per label {np.mean(docs_per_relevant_cluster):.2f}')
        print('Number of topics and number of documents with this number of topics:', topic_count_per_doc)
        if plot_td:
            if 0 in topic_count_per_doc.keys():
                del topic_count_per_doc[0]
            x, y = zip(*topic_count_per_doc.items()) # unpack a list of pairs into two tuples
            plt.plot(x, y)
            plt.xlabel('Number of topics')
            plt.ylabel('Number of documents')
            plt.savefig(os.path.join(save_path, f'wikipedia_{corpus_id}_plot_topics_per_doc_{min_dt}.png'))
            plt.show()



if __name__ == "__main__":
    print('ok')
