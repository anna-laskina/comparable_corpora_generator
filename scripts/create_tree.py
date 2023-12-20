import argparse
import glob
import os

from wiki_package import constants
from wiki_package.wiki_web import create_wikipedia_tree, map_subcategories_to_categories_from_wiki_tree

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wikipedia tree creation.")

    parser.add_argument("-ml", "--max_level", type=int, default=25,
                        help="Number of iterations of the subcategory search")
    parser.add_argument("-pl", "--primary_level", type=int, default=2,
                        help="The level in Wikipedia Tree on which the mapping will be based.")
    parser.add_argument("-rc", "--root_categories", type=str, default='main_topic_classifications',
                        help="Root categories")
    parser.add_argument("-ot", "--only_tree", action='store_true',
                        help="Run only wikipedia tree creation.")
    parser.add_argument("-om", "--only_map", action='store_true',
                        help="Run only associations of categories with topics. Should be installed only "
                             "if the wikipedia tree has already been created and it is only necessary to change "
                             "the number of possible tops and the association of categories with these topics.")
    parser.add_argument("-spt", "--save_path_tree", type=str, default=constants.SAVE_TREE_PATH,
                        help="save tree path")
    args = parser.parse_args()

    list_of_root_categories = args.root_categories.replace('_', ' ').split('+')
    if args.only_map:
        dirl = glob.glob(os.path.join(args.save_path_tree, f'wikipedia_tree_*levels_0-*.json'))

        if len(dirl) > 1:
            print('There are several trees. Please choose which one to use. '
                  f'Enter a number between 1 and {len(dirl) +  1} representing the tree number in the list below.')
            print('\n'.join(dirl))
            num = input()
            if num not in range(1, len(dirl) + 1):
                print('The number is incorrect.')
                exit()
            num -= 1
        elif len(dirl) == 1:
            num = 0
        else:
            print('No wikipedia tree found. Check if the path is correct or run a program without -om.')
            exit()
        wikipedia_tree = dirl[num]
    else:
        wikipedia_tree = create_wikipedia_tree(
            root_categories=list_of_root_categories,
            save_path=args.save_path_tree,
            start_level=0,
            max_level=args.max_level,
            add_name=''.join([cat[0] for cat in list_of_root_categories]),
            if_backup=True,
        )

    if not args.only_tree:
        converted_categories, primary_categories = map_subcategories_to_categories_from_wiki_tree(
            wikipedia_tree=wikipedia_tree,
            initial_level=args.primary_level,
            save_path=args.save_path_tree
        )
