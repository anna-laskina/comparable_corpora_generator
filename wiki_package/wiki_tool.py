import os

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from wiki_package import constants
from wiki_package.util import path_check
from wiki_package.wiki_corpora import WikiCorpus


def visualize_wikipedia_corpus(corpus_id, corpus_path=constants.SAVE_PATH, save_path=constants.SAVE_PATH,
                               target_type='secondary_2',
                               show_stat=True, plot_bar=True, min_size_label=None, plot_heatmap=True, size_show=50,
                               max_size_label=100, fill2size=True, TD_count=True, plot_td=True):
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

    corpus = WikiCorpus(corpus_id=corpus_id, info_path=corpus_path,
                        target_type=target_type.split('_')[0], d_min=int(target_type.split('_')[1]))
    corpus_print_name = f'{corpus_id}_{target_type[0]}{target_type.split("_")[1]}'

    if show_stat:
        print('DOC:', f'Total = {corpus.n_docs}, '
                     f'In {corpus.language_1} = {corpus.lang_mask.count(0)}, '
                     f'In {corpus.language_2} = {corpus.lang_mask.count(1)}, '
                     f'Common = {corpus.type_mask.count(1)}, '
                     f'Only in {corpus.language_1} = {corpus.type_mask.count(0)}, '
                     f'Only in {corpus.language_2} = {corpus.type_mask.count(2)}.')

        print('TOPICS:', f'Total = {corpus.n_clusters}, '
                        f'Monolingual {corpus.language_1} = {len(corpus.mono1_clusters)}, '
                        f'Monolingual {corpus.language_2} = {len(corpus.mono2_clusters)}, '
                        f'Bilingual = {len(corpus.bi_clusters)}, '
                        f'Primary = {len(corpus.primary_clusters)}, '
                        f'Secondary = {len(corpus.secondary_clusters)}.')

    if plot_bar:
        if min_size_label is None:
            min_size_label = int(target_type.split('_')[1])
        label2index = {label: i for i, label in enumerate(list(set([l for ls in corpus.target for l in ls])))}
        index2label = {i: label for label, i in label2index.items()}
        label_count = {label: [0, 0] for label in range(corpus.n_clusters)}
        for i in range(corpus.n_docs):
            for label in corpus.target[i]:
                label_count[label2index[label]][corpus.lang_mask[i]] += 1

        label_count = {k: v for k, v in label_count.items() if sum(v) >= min_size_label}
        label_count = {k: v for k, v in
                       sorted(label_count.items(), key=lambda item: sum(item[1]), reverse=True)}
        dataframe = pd.DataFrame({
            corpus.language_1: [v[0] for v in label_count.values()],
            corpus.language_2: [v[1] for v in label_count.values()]},
            index=[corpus.label2topic[index2label[i]] for i in label_count.keys()]
        )
        axis = dataframe.plot.bar(figsize=(20, 10))
        plt.savefig(os.path.join(save_path, f'wikipedia_{corpus_print_name}_bar{min_size_label}.png'))
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
        plt.savefig(os.path.join(save_path, f'wikipedia_{corpus_print_name}_heatmap{size_show}-{max_size_label}.png'))
        plt.show()

    if TD_count == True:
        topic_per_doc = [len(labels) for labels in corpus.target]
        topic_count_per_doc = {num: topic_per_doc.count(num) for num in set(topic_per_doc)}
        topic_count_per_doc = dict(sorted(topic_count_per_doc.items()))

        doc_per_topic = {}
        for labels in corpus.target:
            for label in labels:
                doc_per_topic[label] = doc_per_topic.get(label, 0) + 1

        print(f'Topics per Doc: {np.mean(topic_per_doc):.2f} Docs per topic {np.mean(list(doc_per_topic.values())):.2f}')
        print('Number of topics and number of documents with this number of topics:')
        print(topic_count_per_doc)
        if plot_td:
            x, y = zip(*topic_count_per_doc.items()) # unpack a list of pairs into two tuples
            plt.plot(x, y)
            plt.xlabel('Number of topics')
            plt.ylabel('Number of documents')
            plt.savefig(os.path.join(save_path, f'wikipedia_{corpus_print_name}_plot_topics_per_doc.png'))
            plt.show()


if __name__ == "__main__":
    print('ok')
