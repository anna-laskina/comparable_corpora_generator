import argparse

from wiki_package import constants
from wiki_package.wiki_web import create_wikipedia_tree, map_subcategories_to_categories_from_wiki_tree

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wikipedia tree creation.")

    parser.add_argument("-ml", "--max_level", type=int, default=25,
                        help="Number of iterations of the subcategory search")
    parser.add_argument("-pl", "--primary_level", type=int, default=2,
                        help="The level in Wikipedia Tree on which the mapping will be based.")
    args = parser.parse_args()

    wikipedia_tree = create_wikipedia_tree(
        root_categories=[constants.ROOT_CATEGORY],
        save_path=constants.SAVE_TREE_PATH,
        start_level=0,
        max_level=args.max_level,
        if_backup=True,
    )

    converted_categories, primary_categories = map_subcategories_to_categories_from_wiki_tree(
        wikipedia_tree=wikipedia_tree,
        initial_level=args.primary_level,
        save_path=constants.SAVE_TREE_PATH
    )
