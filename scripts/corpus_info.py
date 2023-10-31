import argparse

from wiki_package import constants
from wiki_package.wiki_tool import visualize_wikipedia_corpus

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wikipedia corpus information.")

    parser.add_argument("-n", "--name", type=str, required=True,
                        help="A name to identify several versions of the corpus. Ex. v0_0.")

    parser.add_argument("-s", "--stat", action='store_true',
                        help = 'Show information about the number of documents and labels.')
    parser.add_argument("-b", "--bar", action='store_true',
                        help = 'Build a bar plot.')
    parser.add_argument("-m", "--heatmap", action='store_true',
                        help = 'Build a heatmap plot.')

    parser.add_argument("-min_s", "--min_size_label", type=int, default=0,
                        help="The minimum number of pages in a category, so that it is shown on the bar.")
    parser.add_argument("-ss", "--size_show", type=int, default=50,
                        help="The number categories, so that it is shown on the heatmap ")
    parser.add_argument("-max_s", "--max_size_label", type=int, default=100,
                        help="Number of pages to which the number of pages in a category pair will be cut "
                             "to build a heatmap.")

    parser.add_argument("-cp", "--corpus_path",  type=str, default=constants.SAVE_PATH,
                        help="Path where the corpus files are located.")
    parser.add_argument("-sp", "--save_path",  type=str, default=constants.SAVE_PATH,
                        help="Path where plot will be saved.")

    args = parser.parse_args()

    visualize_wikipedia_corpus(corpus_id=args.name,
                               corpus_path=args.corpus_path,
                               save_path=args.save_path,
                               show_stat=args.stat,
                               plot_bar=args.bar,
                               min_size_label=args.min_size_label,
                               plot_heatmap=args.heatmap,
                               size_show=args.size_show,
                               max_size_label=args.max_size_label)