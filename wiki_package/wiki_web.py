import json
import multiprocessing
import os
import random
import re
import time
import bs4
import numpy as np
import requests
from tqdm import tqdm

from wiki_package import constants
from wiki_package import util
from wiki_package.util import path_check


def clean_category_list(start_list, if_unique=True, remove_prepositions=None, remove_words=None):
    """Function to remove irrelevant categories.

    :param start_list: source list of categories
    :param if_unique: bool, True to remove repetitions categories, otherwise False (def. True).
    :param remove_prepositions: list of prepositions. If a categories contains a prepositions from this list,
    it will be removed.
    :param remove_words: list of words. If a categories contains a word from this list, it will be removed.
    :return: list of categories after removing irrelevant categories
    """

    return_list = start_list[:]

    if remove_prepositions is not None:
        for cat in start_list:
            if any(' ' + prepos + ' ' in cat.lower() for prepos in remove_prepositions):
                return_list.remove(cat)

    if remove_words is not None:
        for cat in start_list:
            if any(word in cat.lower() for word in remove_words) and (cat in return_list):
                return_list.remove(cat)

    if if_unique:
        return_list = list(set(return_list))
    return return_list


def run_clean_category_list_setting(start_list):
    """Function for quick start of function "clean_category_list".

    :param start_list: list of categories from which the irrelevant categories will be removed.
    :return: list of categories after removing irrelevant categories
    """
    return clean_category_list(start_list=start_list,
                               if_unique=True,
                               remove_prepositions=constants.REMOVE_PREPOSITION,
                               remove_words=constants.REMOVE_WORDS)


def get_subcategories(category, n_max=500, category_titles_only=True):
    """Finds subcategories of a category.

    :param category: str, category whose subcategories will be searched.
    :param n_max:int, the number of subcategories to return (def. all but no more than 500 items)
    :param category_titles_only: bool, if true, then only titles of subcategories will be returned, otherwise a list of
                                       dictionaries with 3 keys ('pageid', 'ns', 'title') will be returned
    :return: list of subcategories

    Ex.                  Cat_1
           Cat_1.1       Cat_1.2                Car_1.3
           Cat_1.1.1     Cat_1.2.1  Cat_1.2.2
                         Cat_1.2.1.1
    get_categories('Cat_1') -> ['Cat_1.1 ', 'Cat_1.2', 'Car_1.3']
    """
    s = requests.Session()
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "cmtitle": f'Category:{category}',
        "cmlimit": n_max,
        "list": "categorymembers",
        'cmtype': 'subcat',
        "format": "json",
    }

    r = s.get(url=url, params=params)
    data = r.json()

    return [page_info['title'][9:] for page_info in data['query']['categorymembers']] \
        if category_titles_only else data['query']['categorymembers']


def from_parent_categories_to_child_categories(list_of_parent_categories):
    """Find subcategories of categories from a list
    Ex.                  Cat_1
           Cat_1.1       Cat_1.2                Car_1.3
           Cat_1.1.1     Cat_1.2.1  Cat_1.2.2
                         Cat_1.2.1.1
    get_categories(['Cat_1.1', 'Cat_1.2']) -> ['Cat_1.1.1', 'Cat_1.2.1', 'Cat_1.2.2']

    :param list_of_parent_categories: list of srt, categories whose subcategories will be searched.
    :return: list of subcategory titles
    """
    list_of_child_categories = []
    for parent_category in list_of_parent_categories:
        child_categories = get_subcategories(parent_category, category_titles_only=True)
        list_of_child_categories.extend(child_categories)
    return list_of_child_categories


def get_all_subcategories_under_main_category(main_category, max_level):
    """Finds all subcategories of a category.

    :param main_category: str, category whose subcategories will be searched.
    :param max_level: int
    :return: list of all subcategories

    Ex.                  Cat_1                                leval 0
           Cat_1.1       Cat_1.2                Car_1.3       leval 1
           Cat_1.1.1     Cat_1.2.1  Cat_1.2.2                 leval 2
                         Cat_1.2.1.1                          leval 3
    get_categories('Cat_1', 3) ->
    ['Cat_1.1 ', 'Cat_1.2', 'Car_1.3', 'Cat_1.1.1', 'Cat_1.2.1', 'Cat_1.2.2', 'Cat_1.2.1.1']
    """
    cur_leval = 0
    cur_subcat = [main_category]
    subcat_list = []

    while cur_leval < max_level:
        new_cur_subcat = []
        for subcat in cur_subcat:
            new_subcat = get_subcategories(subcat)
            subcat_list.extend(new_subcat)
            new_cur_subcat.extend(new_subcat)

        cur_subcat = new_cur_subcat[:]
        cur_leval += 1
    return subcat_list


def generate_categories_for_selection(initial_categories, max_level=3, max_num=10000, clean_param=None, save_path=None):
    """

    :param initial_categories: list of categories whose subcategories will be searched.
    (e.g. ['Main Topic classifications'])
    :param max_level: int
    :param max_num: int, maximum number of categories (def. 10000)
    :param clean_param: if True, then will use the default settings for clean_category_list function
                        if False or None, then no categories will be removed
                        Otherwise it should a dict with keys:
                         'if_unique' : bool, 'remove_prepositions' : list, 'remove_words': list
                         (see function clean_category_list for more details)
    :param save_path: the path to the directory where the list of categories files will be saved
    (def. None, mean do not save)
    :return: list of categories
    """
    cur_categories = initial_categories
    cur_level = 0
    while len(cur_categories) < max_num and cur_level < max_level:
        cur_categories = from_parent_categories_to_child_categories(cur_categories)
        cur_level += 1
    if clean_param:
        clean_param = {
            'if_unique': True,
            'remove_prepositions': constants.REMOVE_PREPOSITION,
            'remove_words': constants.REMOVE_WORDS
        }
    if clean_param is not None:
        cur_categories = clean_category_list(start_list=cur_categories,
                                             if_unique=clean_param['if_unique'],
                                             remove_prepositions=clean_param['remove_prepositions'],
                                             remove_words=clean_param['remove_words']
                                             )
    if save_path is not None:
        util.save_data(cur_categories,
                  os.path.join(save_path, f'categories_list_level_{cur_level}_{len(cur_categories)}.txt'))

    return cur_categories


def choose_category(n_1, n_2, n_c, categories_choose):
    """This function randomly selects [n_1], [n_2] and [n_c] categories from [categories_choose].

    :param n_1: int
    :param n_2: int
    :param n_c: int
    :param categories_choose: list of categories
    :return: 3 lists of size [n_1], [n_2] and [n_c].
    """
    random.shuffle(categories_choose)
    return categories_choose[0:n_1], categories_choose[n_1:n_1 + n_2], categories_choose[n_1 + n_2:n_1 + n_2 + n_c]


def generate_categories(initial_categories, type_initial_cat, language_1, language_2,
                        variation_num_cat=None, weights_num_cat=None,
                        variation_num_cat_lang1=None, variation_num_cat_lang2=None, variation_num_cat_common=None,
                        max_level=3, max_num=1000):
    """This function generates categories that will only occur in one language ([language_1] or [language_2]) and in
    both languages.
    :param initial_categories: see the description of the 'type_initial_cat' parameter.
    :param type_initial_cat: Possible options:
                            'cat2gen': the categories for select will be generated by
                            [generate_categories_for_selection] function, and will be subcategories of the categories
                            from [initial_categories]. The [initial_categories] parameter must be a list of categories.
                            'cat2choose': the categories for select are the categories from [initial_categories]
                             parameter. The [initial_categories] parameter must be a list of categories.
                            'download': the categories for select will be downloaded from the file. The path to the
                            file is specified in the [initial_categories] parameter.
    :param language_1: str, language of the first part of the corpus (ex. 'en', 'fr')
    :param language_2: str, language of the first part of the corpus (ex. 'en', 'fr')
    :param variation_num_cat: list of possible number of categories for each type
                            (occurs only in  [language_1], only in [language_2], in both languages). (def. None)
    :param weights_num_cat: list of probabilities to choose a number from [variation_num_cat] list.
                            Must have to have the same size as [variation_num_cat]. (def. None).
    :param max_level: int, (def. 3).
    :param max_num: int, maximum number of categories (def. 10000)
    :param variation_num_cat_lang2: list of possible number of categories which occurs only in  [language_2].
    :param variation_num_cat_lang1: list of possible number of categories which occurs only in  [language_1].
    :param variation_num_cat_common: list of possible number of categories which occurs in both languages.
    :return: dictionary with categories grouped by type.
            (Ex. {'only_en': {'category': ["Sports",  "Science"], 'language': ['en']},
                  'only_fr': {'category': ["Law"], 'language': ['fr']},
                  'common': {'category': ["Information", "Military", "Engineering"], 'language': ['en', 'fr']},
            })
    """
    if type_initial_cat == 'cat2gen':
        categories_for_selection = generate_categories_for_selection(initial_categories, max_level, max_num)
    elif type_initial_cat == 'cat2choose':
        categories_for_selection = initial_categories
    elif type_initial_cat == 'download':
        categories_for_selection = util.read_data(initial_categories)
    else:
        print('The parameter type_initial_cat has an unexpected value. Unable to define categories for selection.')
        categories_for_selection = None

    if variation_num_cat is None:
        variation_num_cat = np.random.randint(1, 5, size=5)
        weights_num_cat = None

    n1 = random.choice(variation_num_cat_lang1) if variation_num_cat_lang1 is not None else \
        random.choices(variation_num_cat, weights=weights_num_cat, k=1)[0]
    n2 = random.choice(variation_num_cat_lang2) if variation_num_cat_lang2 is not None else \
        random.choices(variation_num_cat, weights=weights_num_cat, k=1)[0]
    nc = random.choice(variation_num_cat_common) if variation_num_cat_common is not None else \
        random.choices(variation_num_cat, weights=weights_num_cat, k=1)[0]
    # n1, n2, nc = random.choices(variation_num_cat, weights=weights_num_cat, k=3)

    if n1 + n2 + nc > len(categories_for_selection):
        print('Total number of selected categories (n1, n2, nc) to select is greater then the number categories '
              'to select (categories_for_selection). Total number of selected categories will be reduced.')
        delta = (n1 + n2 + nc - len(categories_for_selection)) // 3 + 1
        n1, n2, nc = n1 - delta, n2 - delta, nc - delta
    cat_1, cat_2, cat_common = choose_category(n1, n2, nc, categories_for_selection)
    return {
        f'only_{language_1}': {'category': cat_1, 'language': [language_1]},
        f'only_{language_2}': {'category': cat_2, 'language': [language_2]},
        'common': {'category': cat_common, 'language': [language_1, language_2]},
    }


def mapping_subcategories_to_categories(initial_categories, type_initial_cat, save_path=None, max_level=10,
                                        save_name=None, if_backup=True):
    """ this function finds all subcategories () of categories from [initial_categories] and matches them with
    the category from which they were founded.

    Ex.                  Cat_1                  Cat_2         leval 0
           Cat_1.1       Cat_1.2                Car_2.1       leval 1
           Cat_1.1.1     Cat_1.2.1  Cat_1.2.2                 leval 2
    mapping_subcategories_to_categories(['Cat_1', 'Cat_2'], 'cat2map',None, 2)
    -> {
    'Cat_1.1': 'Cat_1',
    'Cat_1.2': 'Cat_1',
    'Car_2.1': 'Cat_2',
    'Cat_1.1.1': 'Cat_1',
    'Cat_1.2.1': 'Cat_1',
    'Cat_1.2.2': 'Cat_1',
    }

    :param initial_categories: see the description of the 'type_initial_cat' parameter.
    :param type_initial_cat: Possible options:
                            'download': the list of main categories will be downloaded from the file. The path to the
                            file is specified in the [initial_categories] parameter.
                            'cat2map': the list of main categories  are the categories from [initial_categories]
                             parameter. The [initial_categories] parameter must be a list of categories.
    :param save_path: the path to the directory where the list of categories files will be saved
                      (def. None, mean do not save)
    :param max_level: int, number of iterations of the subcategory search (def. 10).
    :param save_name: str, (def. None)
    :param if_backup: bool, whether intermediate data will be saved (def. True).
    :return: dictionary with subcategories (it is keys) and category from which they were found (it is value).
    """
    if save_path is not None and not os.path.exists(save_path):
        # Create a new directory because it does not exist
        os.makedirs(save_path)
        print(f"The directory {save_path} is created!")

    if type_initial_cat == 'download':
        list_of_cat = util.read_data(initial_categories)
        start_level = initial_categories[initial_categories.find('level_') + len('level_')]
    elif type_initial_cat == 'cat2map':
        list_of_cat = initial_categories
        start_level = len(initial_categories)
    else:
        print('The parameter type_initial_cat has an unexpected value. Unable to define categories for selection.')
        list_of_cat = None
        start_level = None

    save_name = f'{start_level}+{max_level}' if save_name is None else save_name

    subcat2cat = {constants.BAD_NAME_CAT: constants.BAD_NAME_CAT}
    cat_power = {constants.BAD_NAME_CAT: 0}
    level = 0

    for cat in list_of_cat:
        subcat2cat[cat] = cat
        cat_power[cat] = level

    while level < max_level:
        for cat in tqdm([c for c, l in cat_power.items()
                         if l == level and subcat2cat[c] != constants.BAD_NAME_CAT]):
            subcat_list = get_subcategories(cat)
            for subcat in subcat_list:
                if subcat not in subcat2cat.keys():
                    subcat2cat[subcat] = subcat2cat[cat]
                    cat_power[subcat] = cat_power[cat] + 1
                else:
                    if cat_power[cat] + 1 == cat_power[subcat]:
                        subcat2cat[subcat] = constants.BAD_NAME_CAT
        if if_backup:
            util.save_data({subcat_b: [subcat2cat[subcat_b], level_b] for subcat_b, level_b in cat_power.items()
                       if level_b == level},
                      os.path.join(save_path, f'back_up_map_subcat_to_cat_{save_name}_level_{level}.txt'))
        level += 1

    if save_path is not None:
        util.save_data(subcat2cat,
                  os.path.join(save_path, f'map_subcat_to_cat_{save_name}.txt'))
        util.save_data(cat_power,
                  os.path.join(save_path, f'cat_power_{save_name}.txt'))

    return subcat2cat, cat_power


def create_wikipedia_tree(root_categories=None, save_path=None, start_level=0, max_level=30, add_name = '',
                          if_backup=True):
    """Function for creating Wikipedia tree.

    :param root_categories: list of string, list of root categories (Ex. ['Main topic classifications'])
                                            or path to the file
    :param save_path: the path to the directory where the list of categories files will be saved
                      (def. None, mean do not save)
    :param start_level: int, the level from which the wikipedia tree construction will be started.
                             If the tree is not created from level 0, variable [root_categories] must contain
                             the path to the file that contains the tree from level 0 to that level. (def. 0)
    :param max_level: int, number of iterations of the subcategory search (def. 30)
    :param if_backup: bool, whether intermediate data will be saved (def. True).
    :return: dictionary, A dictionary whose keys are category, and whose value is a leaf of 3 values:
                         level in the tree, category type and parent category.
    """
    util.path_check(path=save_path, if_create=True)

    if save_path is None and if_backup:
        print('Intermediate data will be saved in the current directory.')
        save_path = ''

    backup_path = os.path.join(save_path, 'backup') if if_backup else None
    if if_backup:
        util.path_check(path=backup_path, if_create=True)

    if start_level == 0:
        cur_level = 0
        if root_categories is None:
            root_categories = [constants.ROOT_CATEGORY]
        wikipedia_tree = {root_category: [0, constants.SGFNT_CAT_NAME, root_category]
                          for root_category in root_categories}
    elif os.path.exists(root_categories):
        cur_level = start_level
        wikipedia_tree = util.read_data(root_categories)
    else:
        print('Variables start_level and root_categories don\'t math. The algorithm will run on default settings')
        cur_level = 0
        root_categories = [constants.ROOT_CATEGORY]
        wikipedia_tree = {root_category: [0, constants.SGFNT_CAT_NAME, root_category]
                          for root_category in root_categories}

    while cur_level < max_level:
        cur_categories = [cat for cat, cat_info in wikipedia_tree.items() if cat_info[0] == cur_level and
                          cat_info[1] == constants.SGFNT_CAT_NAME]
        if len(cur_categories) == 0:
            print('The previous level does not have any significant categories.')
            break
        cur_wikipedia_tree = {}
        cur_level += 1
        for cur_category in tqdm(cur_categories):
            cur_subcategories = [subcat for subcat in get_subcategories(cur_category)
                                 if subcat not in wikipedia_tree.keys()]
            sgfnt_subcategories = run_clean_category_list_setting(cur_subcategories)

            for subcategory in cur_subcategories:
                if subcategory in sgfnt_subcategories:
                    if subcategory in cur_wikipedia_tree.keys():
                        parent_categories = (cur_wikipedia_tree[subcategory][2]
                                             if type(cur_wikipedia_tree[subcategory][2]) == list
                                             else [cur_wikipedia_tree[subcategory][2]]) + [cur_category]
                        cur_wikipedia_tree[subcategory] = [cur_level, constants.OUT_CAT_NAME, parent_categories]
                    else:
                        cur_wikipedia_tree[subcategory] = [cur_level, constants.SGFNT_CAT_NAME, cur_category]

                else:
                    cur_wikipedia_tree[subcategory] = [cur_level, constants.INSGFNT_CAT_NAME, cur_category]
        wikipedia_tree.update(cur_wikipedia_tree)

        print(f'level={cur_level} '
              f' {constants.SGFNT_CAT_NAME}='
              f'{len([cat for cat, cat_info in cur_wikipedia_tree.items() if cat_info[1] == constants.SGFNT_CAT_NAME])}'
              f' {constants.INSGFNT_CAT_NAME}='
              f'{len([c for c, cat_info in cur_wikipedia_tree.items() if cat_info[1] == constants.INSGFNT_CAT_NAME])}'
              f' {constants.OUT_CAT_NAME}='
              f'{len([cat for cat, cat_info in cur_wikipedia_tree.items() if cat_info[1] == constants.OUT_CAT_NAME])}'
              )

        if if_backup:
            util.save_data(cur_wikipedia_tree,
                      os.path.join(backup_path, f'back_up_wikipedia_tree_{add_name}_level_{cur_level}.json'))

    if save_path is not None:
        util.save_data(wikipedia_tree, os.path.join(save_path, f'wikipedia_tree_{add_name}_levels_0-{cur_level}.json'))

    print('Wikipedia tree has been successfully created. Intermediate files will be deleted')
    for root, dirs, files in os.walk(backup_path):
        for f in files:
            if f'back_up_wikipedia_tree_{add_name}_level_' in f:
                os.remove(os.path.join(root, f))
    #os.rmdir(backup_path)

    return wikipedia_tree


def map_subcategories_to_categories_from_wiki_tree(wikipedia_tree=None, initial_level=2, max_level=100,
                                                   save_path=None):
    """

    :param wikipedia_tree: dictionary, A dictionary whose keys are category, and whose value is a leaf of 3 values:
                                       level in the tree, category type and parent category.
    :param initial_level: int, the level in [wikipedia_tree] on which the mapping will be based (def. 2).
                                All categories in [wikipedia_tree] will be mapped to categories from this level.
    :param max_level: int, number of iterations of the subcategory search (def. 100)
    :param save_path: the path to the directory where the list of categories files will be saved
                      (def. None, mean do not save)
    :return: dictionary, the keys are the subcategories, and the values are  the categories to which these
    subcategories belong.
    """
    util.path_check(save_path)
    if wikipedia_tree is None:
        print('Wikipedia tree is nor defined.')
        wikipedia_tree = create_wikipedia_tree(root_categories=constants.ROOT_CATEGORY,
                                               save_path=constants.SAVE_TREE_PATH,
                                               start_level=0)
    elif type(wikipedia_tree) == str:
        wikipedia_tree = util.read_data(wikipedia_tree)
    sub2cat = {}

    for category, [cat_level, cat_type, _] in wikipedia_tree.items():
        if cat_level > max_level:
            continue
        if cat_level < initial_level:
            sub2cat[category] = constants.GLOB_CAT_NAME
            continue
        if cat_type != constants.SGFNT_CAT_NAME:
            sub2cat[category] = cat_type
            continue

        cur_parent = category
        while wikipedia_tree[cur_parent][0] > initial_level:
            cur_parent = wikipedia_tree[cur_parent][2]

        sub2cat[category] = cur_parent

    primary_categories = list(set(sub2cat.values()) - set(constants.EXCLUDED_CATS))

    if save_path is not None:
        max_real_level = max(max_level, max([cat_info[0] for cat_info in wikipedia_tree.values()]))
        util.save_data(sub2cat, os.path.join(save_path, f'map_subcat_to_cat_{max_real_level}->{initial_level}.txt'))
        util.save_data(primary_categories,
                  os.path.join(save_path, f'categories_list_level_{initial_level}_{len(primary_categories)}.txt'))

    return sub2cat, primary_categories


def get_category_pages(category_name, n_max=500, return_type='all'):
    """This function requests information from thr category page and return all pages in that category.
    if there are not enough of pages, that after that more subcategory pages are returned.

    :param category_name: str, name of category (Ex. 'Culture')
    :param n_max: int, maximum number of pages or/and subcategories returned (def. 500)
    :param return_type: Possible options:
                        'all': return all pages and subcategories
                        'pages': return only pages
                        'subcat': return only subcategories
    :return: list of dictionary with 3 keys: 'pageid', 'ns', 'title'.
    """
    s = requests.Session()
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "cmtitle": f'Category:{category_name}',
        "cmlimit": n_max,
        "list": "categorymembers",
        "format": "json"
    }

    r = s.get(url=url, params=params)
    data = r.json()

    if return_type == 'all':
        output = data['query']['categorymembers']
    elif return_type == 'pages':
        output = [page_info for page_info in data['query']['categorymembers'] if page_info['ns'] == 0]
    elif return_type == 'subcat':
        output = [page_info for page_info in data['query']['categorymembers'] if page_info['ns'] == 14]
    else:
        output = None
    return output


def get_pages_from_categories(list_of_categories, only_pageid=False):
    """ This function requests information from each category page from [list_of_categoris] and return all pages
    in those categories.

    :param list_of_categories: list of categories
    :param only_pageid: bool, whether only pageid should be returned (def. False).
    :return: list of pageid (if only_pageid is True) or list of list of dictionary with 3 keys: 'pageid', 'ns', 'title'.
    """
    return [page['pageid'] if only_pageid else page
            for cat in list_of_categories
            for page in get_category_pages(category_name=cat, return_type='pages')
            ]


def get_page_soup_from_page(page_id=None, page_name=None, page_link=None):
    """ Function for obtaining a page source code by pageid or page title.

    :param page_id: int, Wikipedia page id (def. None)
    :param page_name: str, Wikipedia page title (def. None)
    :param page_link: str, Wikipedia weblink (Ex. 'https://en.wikipedia.org/wiki/Main_Page') (def.None)
    :return:BeautifulSoup, page source
    """
    if all(param is None for param in [page_id, page_name, page_link]):
        print('All parameters are None, there is no possibility to identify the page.')
        return None
    if page_link is None:
        page_link = 'https://en.wikipedia.org/?curid=' + str(page_id) if page_id is not None else \
            'https://en.wikipedia.org/wiki/' + page_name

    try:
        html_text = requests.get(page_link).text
    except requests.exceptions.ChunkedEncodingError:
        print(page_link)
        html_text = ''
    return bs4.BeautifulSoup(html_text, features="html.parser")


def get_pageid_from_page_soup(page_soup):
    """Find page id in page source.

    :param page_soup: BeautifulSoup, page source
    :return: int, page id
    """
    return json.loads(page_soup.find('script').get_text().split(';')[1].split('=')[1])['wgArticleId']


def get_pageid_from_page_name(page_name):
    """Find page id from page title.

    :param page_name: str, page title.
    :return: int, page id
    """
    return get_pageid_from_page_soup(get_page_soup_from_page(page_name=page_name))


def get_interlanguage_link_from_page_soup(page_soup, page_id=None, if_title=False):
    """Finds interlanguage link of the page source.

    :param page_soup: BeautifulSoup object, which represents the page source.
    :param page_id:int, Wikipedia page id (def. None)
    :param if_title: bool, whether titles should be returned (def. False).
    :return: dictionary: {language: {'href': <link>, ['title':str]}}
    """

    if page_id is None:
        page_id = get_pageid_from_page_soup(page_soup)

    interlanguage_links = {'en': {'href': 'https://en.wikipedia.org/?curid=' + str(page_id)}}
    # page_soup.find('link', rel="canonical").get('href')
    try:
        list_of_language_soup = page_soup.select('li[class*="interlanguage"]')
        # page_soup.find_all('ul', class_="vector-menu-content-list")[-1].find_all('li')
    except (IndexError, AttributeError):
        # print(f"lang:{page_id}", end='->')
        list_of_language_soup = []

    for language_soup in list_of_language_soup:
        language_info = language_soup.find('a')
        interlanguage_links[language_info.get('lang')] = {'href': language_info.get('href')}
        if if_title:
            interlanguage_links[language_info.get('lang')]['title'] = language_info.get('title')
    return interlanguage_links


def get_interlanguage_link_from_page(page_id=None, page_name=None, page_soup=None):
    """Finds interlanguage link of the page.

    :param page_id: int, wikipedia page id.
    :param page_name: str, wikipedia page title (Ex. 'Culture', 'Category:Culture').
    :param page_soup: BeautifulSoup object, which represents the page source.
    :return: dictionary: {language: {'href': <link>, ['title':str]}}
    """
    if page_soup is None:
        page_soup = get_page_soup_from_page(page_id, page_name)
    return get_interlanguage_link_from_page_soup(page_soup, page_id=page_id)


def get_category_from_page_soup(page_soup, if_show_hidden_categories=True):
    """Finds categories of the page from page source.

    :param page_soup: BeautifulSoup object, which represents the page source.
    :param if_show_hidden_categories: bool, whether to show hidden categories (def. True).
    :return: 2 lists: main categories and hided categories.
    """
    soup_cat_main = page_soup.find('div', class_='mw-normal-catlinks')
    soup_cat_hide = page_soup.find('div', class_='mw-hidden-catlinks mw-hidden-cats-hidden')
    if if_show_hidden_categories:
        return [line.text for line in soup_cat_main.find_all('li')] if soup_cat_main is not None else [None], \
               [line.text for line in soup_cat_hide.find_all('li')] if soup_cat_hide is not None else [None]
    else:
        return [line.text for line in soup_cat_main.find_all('li')] if soup_cat_main is not None else [None]


def get_categories_from_page(page_id=None, page_name=None, page_soup=None, hidden_categories=True):
    """Finds categories of the page from page.

    :param page_id: int, wikipedia page id.
    :param page_name: str, wikipedia page title (Ex. 'Culture', 'Category:Culture').
    :param page_soup: BeautifulSoup object, which represents the page source.
    :param hidden_categories: bool, whether to show hidden categories (def. True).
    :return: 2 lists: main categories and hided categories.
    """
    if page_soup is None:
        page_soup = get_page_soup_from_page(page_id, page_name)
    return get_category_from_page_soup(page_soup, if_show_hidden_categories=hidden_categories)


def remove_cite(text):
    """Removes cites from text.

    Ex. 'habits of the individuals in these groups.[1]' -> 'habits of the individuals in these groups.'

    :param text: str, text
    :return: str, text without cites
    """
    return re.sub('\[\d+\]', '', text)


def remove_nl(text):
    """Removes newline character ('\n').

    :param text: str, text
    :return: str, text without newline characters
    """
    return text.replace('\n', '')


def get_text_from_page_soup(page_soup, if_cite=True):
    """Finds the body text of the page from page source.

    :param page_soup: BeautifulSoup object, which represents the page source.
    :param if_cite: bool, whether cites should be removed from the text (def. True)
    :return: str, the body text of the page.
    """
    text = ' '.join([line.text for line in page_soup.find_all('p')])
    if if_cite:
        text = remove_cite(text)
    return remove_nl(text)


def get_text_from_page(page_id=None, page_name=None, page_soup=None):
    """Finds the body text of the page.

    :param page_id: int, wikipedia page id.
    :param page_name: str, wikipedia page title (Ex. 'Culture', 'Category:Culture').
    :param page_soup: BeautifulSoup object, which represents the page source.
    :return: str, the body text of the page.
    """
    if page_soup is None:
        page_soup = get_page_soup_from_page(page_id, page_name)
    return get_text_from_page_soup(page_soup)


def get_texts_by_languages_from_page_id(page_id, list_of_languages, main_page_soup=None):
    """Finds the body text of the page in several languages.

    :param page_id: int, wikipedia page id.
    :param list_of_languages: list og languages (Ex. ['en', 'fr']).
    :param main_page_soup: BeautifulSoup object, which represents the page source in English.
    :return: a dictionary in which the keys are the language and the value is a text in that language.
            Ex. {'en': en_text, 'fr': fr_text}
    """
    data_text = {}
    page_soup_en = get_page_soup_from_page(page_id=page_id) if main_page_soup is None else main_page_soup
    link_base = get_interlanguage_link_from_page_soup(page_soup=page_soup_en, page_id=page_id, if_title=False)
    for lang in list_of_languages:
        if lang not in link_base.keys():
            # print(f'Page {page_id}  not represented in the language(s): {lang}')
            data_text[lang] = 'NO DATA'
    links = {lang: link_base[lang]['href'] for lang in list_of_languages if lang in link_base.keys()}
    for lang, link in links.items():
        page_soup = page_soup_en if lang == 'en' else get_page_soup_from_page(page_link=link)
        data_text[lang] = get_text_from_page_soup(page_soup)
    return data_text


def get_texts_from_pageids(list_of_page_id, list_of_languages):
    """Finds the body text of the pages in several languages.

    :param list_of_page_id: list of wikipedia page ids.
    :param list_of_languages: list of language (ex. ['en', 'fr']).
    :return: a list of  dictionaries with 2 keys: 'id' and 'text'.
            See also the description of the output in the 'get_texts_by_languages_from_page_id' function.
            Ex. [{'id': id_1, 'text': {'en': en_text_1, 'fr': fr_text_1}},
                 {'id': id_2, 'text': {'en': en_text_2, 'fr': fr_text_2}}]
    """
    return [{'id': page_id, 'text': get_texts_by_languages_from_page_id(page_id, list_of_languages)}
            for page_id in list_of_page_id]


def convert_subcat_into_categories(list_of_subcat, subcat2cat, if_del_none=False, excluded_categories=False):
    """The function mappings the subcategories to the initial categories.

    :param list_of_subcat: list of subcategories
    :param subcat2cat: dictionary, The keys are the subcategories, and the values are the categories to which these
                       subcategories belong.
    :param if_del_none: bool, whether to delete subcategories that are not matched with categories (def. False)
    :param excluded_categories: list or bool, a list of irrelevant categories (this category will be ignored when
                                extracting categories from the wikipedia page) or True if use the default list
                                or False if want to consider all categories (def. False).
    """
    new_cat = set([subcat2cat.get(subcategory, None) for subcategory in list_of_subcat])

    if excluded_categories is True:
        excluded_categories = constants.EXCLUDED_CATS

    if type(excluded_categories) is list:
        new_cat -= set(excluded_categories)
    if if_del_none:
        new_cat.discard(None)
    return list(new_cat)


def get_labels_from_page(page_id=None, page_name=None, page_soup=None, hidden_categories=True,
                         convert_categories=None, del_none=False, excluded_categories=False):
    """

    :param page_id: int, wikipedia page id.
    :param page_name: str, wikipedia page title (Ex. 'Culture', 'Category:Culture').
    :param page_soup: BeautifulSoup object, which represents the page source.
    :param hidden_categories: bool, whether to show hidden categories (def. True).
    :param convert_categories: dictionary, The keys are the subcategories, and the values are the categories
                                           to which these subcategories belong.
    :param del_none: bool, whether to delete subcategories that are not matched with categories (def. False)
    :param excluded_categories: list or bool, a list of irrelevant categories (this category will be ignored when
                                extracting categories from the wikipedia page) or True if use the default list
                                or False if want to consider all categories (def. False).
    :return: list of categories
    """
    categories = get_categories_from_page(page_id=page_id, page_name=page_name, page_soup=page_soup,
                                          hidden_categories=hidden_categories)
    return categories if convert_categories is None else \
        convert_subcat_into_categories(
            list_of_subcat=categories[0] + categories[1] if hidden_categories else categories,
            subcat2cat=convert_categories,
            if_del_none=del_none,
            excluded_categories=excluded_categories)


def get_info_from_page(page_id=None, page_name=None, convert_categories=None,
                       del_none=False, excluded_categories=False):
    """Returns pageid, languages in which this page is written and its categories about a page.

    :param page_id: int, wikipedia page id.
    :param page_name: str, wikipedia page title
    :param convert_categories: None or dict of mapping subcat to cat (def. None).
                               (see output of function mapping_subcategories_to_categories)
    :param del_none: bool, whether to delete subcategories that are not matched with categories (def. False)
    :param excluded_categories: list or bool, a list of irrelevant categories (this category will be ignored when
                                extracting categories from the wikipedia page) or True if use the default list
                                or False if want to consider all categories (def. False).
    :return: a dictionary with 3 keys: 'pageid', 'language', 'categories'.
    """
    page_soup = get_page_soup_from_page(page_id, page_name)
    return {
        'pageid': get_pageid_from_page_soup(page_soup) if page_id is None else page_id,
        'language': list(get_interlanguage_link_from_page_soup(page_soup, page_id=page_id, if_title=False).keys()),
        'categories': get_labels_from_page(page_soup=page_soup, hidden_categories=False,
                                           convert_categories=convert_categories,
                                           del_none=del_none, excluded_categories=excluded_categories)
    }


def get_data_from_page(page_id=None, page_name=None, page_soup=None, list_of_language=None,
                       if_show_hidden_categories=False, convert_categories=None, del_none=False,
                       excluded_categories=False):
    """Returns information from page.

    :param page_id: int, wikipedia page id.
    :param page_name: str, wikipedia page title
    :param page_soup: BeautifulSoup object, which represents the page source.
    :param list_of_language: list of language (ex. ['en', 'fr']).
    :param if_show_hidden_categories: bool, whether to show hidden categories (def. False).
    :param convert_categories: dictionary, The keys are the subcategories, and the values are the categories to which
                                           these subcategories belong.
    :param del_none: bool, whether to delete subcategories that are not matched with categories (def. False)
    :param excluded_categories: list or bool, a list of irrelevant categories (this category will be ignored when
                                extracting categories from the wikipedia page) or True if use the default list
                                or False if want to consider all categories (def. False).
    :return:  a dictionary with 3 keys: 'pageid', 'text', 'categories'.
    """
    if page_soup is None:
        page_soup = get_page_soup_from_page(page_id, page_name)
    if list_of_language is None:
        list_of_language = ['en']
    return {
        'pageid': page_id,
        'text': get_texts_by_languages_from_page_id(page_id, list_of_language, page_soup),
        'categories': get_labels_from_page(page_soup=page_soup, hidden_categories=if_show_hidden_categories,
                                           convert_categories=convert_categories,
                                           del_none=del_none, excluded_categories=excluded_categories)
    }


def get_data_from_pages(list_of_page_ids, list_of_language, convert_categories=None,
                        del_none=False, excluded_categories=False):
    """Returns information from pages.

    :param list_of_page_ids: list of wikipedia page id.
    :param list_of_language: list of language (ex. ['en', 'fr']).
    :param convert_categories: dictionary, The keys are the subcategories, and the values are the categories to which
                                           these subcategories belong.
    :param del_none: bool, whether to delete subcategories that are not matched with categories (def. False)
    :param excluded_categories: list or bool, a list of irrelevant categories (this category will be ignored when
                                extracting categories from the wikipedia page) or True if use the default list
                                or False if want to consider all categories (def. False).
    :return: list of a dictionary with 3 keys: 'pageid', 'text', 'categories'.
    """
    return [get_data_from_page(page_id=doc_id,
                               list_of_language=list_of_language,
                               if_show_hidden_categories=False,
                               convert_categories=convert_categories,
                               del_none=del_none,
                               excluded_categories=excluded_categories)
            for doc_id in list_of_page_ids]


def check_pageid(pageid, list_of_languages, forbidden_cat, map_subcat2cat=None, min_num_cat=1,  max_num_cat=100,
                 if_del_none=True, excluded_categories=True):
    """Function to check the page for the following conditions:
    1. whether the page exists in all languages from [list_of_languages]
    2. the page does not belong to any of the forbidden categories from [forbidden_cat]
    3. the total number of categories of this page does not exceed [max_num_cat]

    :param pageid: int, wikipedia page id
    :param list_of_languages: list of language (ex. ['en', 'fr']).
    :param forbidden_cat: list of forbidden categories.
    :param map_subcat2cat: dictionary, the keys are the subcategories, and the values are the categories to which these
                          subcategories belong (def. None).
    :param max_num_cat: int, the maximum number of categories a page can contain (def. 100).
    :param if_del_none: bool, whether to delete subcategories that are not matched with categories (def. False)
    :param excluded_categories: list or bool, a list of irrelevant categories (this category will be ignored when
                                extracting categories from the wikipedia page) or True if use the default list
                                or False if want to consider all categories (def. False).
    :return: bool, whether the page satisfies these conditions or not.
    """
    try:
        main_page_data = get_info_from_page(page_id=pageid, convert_categories=map_subcat2cat,
                                            del_none=if_del_none, excluded_categories=excluded_categories)

    except:
        return False
    return all(ll in main_page_data['language'] for ll in list_of_languages) and \
        all(ll not in main_page_data['categories'] for ll in forbidden_cat) and \
        min_num_cat <= len(main_page_data['categories']) <= max_num_cat


def choose_relevant_pages_from_candidates(candidate_pages, required_num,
                                          required_languages, list_of_forbidden_categories,
                                          min_num_cat=1, max_num_cat=100,
                                          map_subcat2cat=None, if_del_none=True, excluded_categories=True):
    """A function for choosing pages that satisfy the following conditions:
        1. whether the page exists in all languages from [required_languages]
        2. the page does not belong to any of the forbidden categories from [list_of_forbidden_categories]
        3. the total number of categories of this page does not exceed [max_num_cat]

    :param candidate_pages: list of wikipedia page id
    :param required_num: int, the number of pages that we need
    :param required_languages:  list of required language (ex. ['en', 'fr']).
    :param list_of_forbidden_categories: list of forbidden categories.
    :param max_num_cat: int, the maximum number of categories a page can contain (def. 100).
    :param map_subcat2cat: dictionary, the keys are the subcategories, and the values are the categories to which these
                          subcategories belong (def. None).
    :param if_del_none: bool, whether to delete subcategories that are not matched with categories (def. False)
    :param excluded_categories:  list or bool, a list of irrelevant categories (this category will be ignored when
                                extracting categories from the wikipedia page) or True if use the default list
                                or False if want to consider all categories (def. False).

    :return: list of relevant pages.
    """
    relevant_pages = []
    for candidate in candidate_pages:
        if check_pageid(pageid=candidate,
                        list_of_languages=required_languages,
                        forbidden_cat=list_of_forbidden_categories,
                        map_subcat2cat=map_subcat2cat,
                        min_num_cat=min_num_cat,
                        max_num_cat=max_num_cat,
                        if_del_none=if_del_none,
                        excluded_categories=excluded_categories):
            relevant_pages.append(candidate)
            if len(relevant_pages) == required_num:
                break
    return relevant_pages


def find_pages_under_category(main_category, category_size,
                              required_languages, forbidden_category, forbidden_pages,
                              min_num_cat=1, max_num_cat=5, max_level=22, if_print=False,
                              subcat2cat=None, if_del_none=True, excluded_categories=True):
    """Function for finding pages that belong to a category ([main_category]) and satisfy several conditions.

    :param main_category: str, the name of the category for which the pages will be searched for.
    :param category_size: int, the number of pages to be found.
    :param required_languages: list of required language (ex. ['en', 'fr']).
    :param forbidden_category: list of forbidden categories.
    :param forbidden_pages: list of exclude pages from the search.
    :param max_num_cat: int, the maximum number of categories a page can contain (def. 5).
    :param max_level: int, how many times will the algorithm go to a subcategory to find more pages (def. 20)
    :param if_print: bool, whether intermediate prints are necessary (def. False)
    :param subcat2cat: dictionary, the keys are the subcategories, and the values are the categories to which these
                          subcategories belong (def. None).
    :param if_del_none: bool, whether to delete subcategories that are not matched with categories (def. False)
    :param excluded_categories:  list or bool, a list of irrelevant categories (this category will be ignored when
                                extracting categories from the wikipedia page) or True if use the default list
                                or False if want to consider all categories (def. False).
    :return: list of pages
    """
    final_pages = []
    reviewed_pages = set(forbidden_pages)

    cur_list_of_observed_categories = [main_category]
    cur_level = 0
    if if_print:
        print(f'Start {main_category}')
        start_cat_time = time.perf_counter()
    while len(final_pages) < category_size and cur_level < max_level:
        if if_print:
            print(f'level={cur_level}, cur_size={len(final_pages)}, cur_len_cat={len(cur_list_of_observed_categories)}',
                  end=' ')

        cur_all_pages = list(set(get_pages_from_categories(cur_list_of_observed_categories, only_pageid=True)) -
                             reviewed_pages)
        if if_print:
            print(f'size_cur_all_pages={len(cur_all_pages)}')
        random.shuffle(cur_all_pages)
        relevant_pages = choose_relevant_pages_from_candidates(candidate_pages=cur_all_pages,
                                                               required_num=category_size - len(final_pages),
                                                               required_languages=required_languages,
                                                               list_of_forbidden_categories=forbidden_category,
                                                               min_num_cat=min_num_cat,
                                                               max_num_cat=max_num_cat,
                                                               map_subcat2cat=subcat2cat,
                                                               if_del_none=if_del_none,
                                                               excluded_categories=excluded_categories)

        final_pages.extend(relevant_pages)
        reviewed_pages.update(cur_all_pages)
        if subcat2cat is not None:
            cur_list_of_observed_categories = [
                candidate for candidate in from_parent_categories_to_child_categories(cur_list_of_observed_categories)
                if subcat2cat.get(candidate, '') == main_category]
        else:
            cur_list_of_observed_categories = run_clean_category_list_setting(
                start_list=from_parent_categories_to_child_categories(cur_list_of_observed_categories))
        cur_level += 1
        if len(cur_list_of_observed_categories) == 0:
            if if_print:
                print('The category have no more subcategories')
            break

    if if_print:
        print(f'level={cur_level}, cur_size={len(final_pages)}, cur_len_cat={len(cur_list_of_observed_categories)}')
        finish_cat_time = time.perf_counter()
        dur = util.sec2hms(finish_cat_time - start_cat_time)
        print(f'Finished {main_category}, time = {dur}')
    return final_pages


def categories2labels(categories, convert_categories=None, del_none=True, excluded_categories=True,
                      label2cat=None):
    if convert_categories is not None:
        categories = [convert_subcat_into_categories(list_of_subcat=list_of_cat,
                                                     subcat2cat=convert_categories,
                                                     if_del_none=del_none,
                                                     excluded_categories=excluded_categories)
                      for list_of_cat in categories]
    if label2cat is None:
        label2cat = list(set(cat for list_of_cat in categories for cat in list_of_cat))
    else:
        label2cat.extend(list(set(cat for list_of_cat in categories
                                  for cat in list_of_cat
                                  if cat not in label2cat)))

    cat2label = {cat: i for i, cat in enumerate(label2cat)}

    labels = [[cat2label[cat] for cat in list_of_cat if cat in label2cat] for list_of_cat in categories]
    return labels, label2cat, cat2label


def get_labels_and_cats(wiki_pages_by_type, if_labels_separately, subcat2cat, if_del_none, excluded_categories):
    label2cat = None
    cat2label = None
    label_name = 'label' if if_labels_separately else 'categories'
    for var_cat, list_of_data in wiki_pages_by_type.items():
        for i, doc in enumerate(list_of_data):
            [wiki_pages_by_type[var_cat][i][label_name]], label2cat, cat2label = \
                categories2labels(categories=[wiki_pages_by_type[var_cat][i]['categories']],
                                  convert_categories=subcat2cat,
                                  del_none=if_del_none,
                                  excluded_categories=excluded_categories,
                                  label2cat=label2cat)
    return wiki_pages_by_type, label2cat, cat2label


def collect_wikidata(categories_set, variation_cat_size, weights_cat_size=None, max_level_search_pageid=20,
                     min_num_of_cat_on_page=1, max_num_of_cat_on_page=10, subcat2cat=None, num_cpu=1,
                     if_labels_separately=False, if_del_none=True, excluded_categories=True,
                     iteration=None, if_reversed=False, if_without_intersections_within_datatype=False,
                     if_display_find_alg=True, save_path=None):
    """Function to collect data for wikipedia corpus.

    :param if_without_intersections_within_datatype:
    :param categories_set: dictionary with categories grouped by type.
            (Ex. {'only_en': {'category': ["Sports",  "Science"], 'language': ['en']},
                  'only_fr': {'category': ["Law"], 'language': ['fr']},
                  'common': {'category': ["Information", "Military", "Engineering"], 'language': ['en', 'fr']},
            })
    :param variation_cat_size: list of variations of how many pages there should be for each category.
    :param weights_cat_size: list of weights for [variation_cat_size].
    :param max_level_search_pageid: int, how many times will the algorithm go to a subcategory to find more pages.
    :param max_num_of_cat_on_page: int, the maximum number of categories a page can contain.
    :param subcat2cat: dictionary, the keys are the subcategories, and the values are the categories to which these
                          subcategories belong.
    :param num_cpu: int, number of CPU which will be used for finding pages (def. 1)
    :param if_labels_separately: bool,
    :param if_del_none: bool, whether to delete subcategories that are not matched with categories (def. False)
    :param excluded_categories:  list or bool, a list of irrelevant categories (this category will be ignored when
                                extracting categories from the wikipedia page) or True if use the default list
                                or False if want to consider all categories (def. False).
    :param iteration: list of elements, which correspond to the keys of the 'categories_set', in some order.
                      EX: ['en', 'fr', 'common'] or ['common', 'fr', 'en'] (def. None).
    :param if_reversed: bool, whether corpus collection starts from the end of the [categories_set] (def. True)
                              (True: en->fr->common; False: common->fr->en)
    :param if_display_find_alg: bool, whether intermediate prints are necessary (def. False)
    :param save_path: the path to the directory where data will be saved
    :return:
    """

    if if_without_intersections_within_datatype and num_cpu > 1:
        print('Parameter "if_without_intersections_within_datatype" cannot be True '
              'if Parameter "num_cpu" is greater than 1. Parameter "num_cpu" will be equal 1.')
        num_cpu = 1
    all_categories = set(j for sub_info in categories_set.values() for j in sub_info['category'])
    wiki_pages_by_type = {key: [] for key in categories_set.keys()}
    additional_categories = set()
    if iteration is None:
        iteration = reversed(categories_set.items()) if if_reversed else categories_set.items()
    else:
        iteration = [(k, categories_set[k]) for k in iteration]
    for var_cat, d_cat in iteration:
        type_cat = 'Monolingual' if len(d_cat['language']) == 1 else 'Bilingual'
        type_cat += f' {var_cat[5:]} clusters' if len(d_cat['language']) == 1 else ' clusters'
        print(type_cat, end = ', ')
        list_of_categories = d_cat['category']
        forbidden_cat = (set(all_categories) | additional_categories) - set(list_of_categories)
        forbidden_cat_within_datatype = set()
        list_of_land = d_cat['language']
        list_of_size = random.choices(variation_cat_size, weights=weights_cat_size, k=len(list_of_categories))
        used_pages = []
        print('number of pages per cluster:', *list_of_size)
        start_time = time.perf_counter()
        if num_cpu > 1:
            pool = multiprocessing.Pool(num_cpu)
            page_id_list_by_cat = pool.starmap(find_pages_under_category, [(cat, cat_size,
                                                                            list_of_land,
                                                                            forbidden_cat,
                                                                            used_pages,
                                                                            min_num_of_cat_on_page,
                                                                            max_num_of_cat_on_page,
                                                                            max_level_search_pageid,
                                                                            if_display_find_alg,
                                                                            subcat2cat)
                                                                           for cat, cat_size in
                                                                           tqdm(zip(list_of_categories, list_of_size))])
            used_pages = set()
            for i, page_id_list in enumerate(page_id_list_by_cat):
                page_id_list_by_cat[i] = list(set(page_id_list) - used_pages)
                used_pages.update(page_id_list)
            used_pages = list(used_pages)
            data = list(np.concatenate(pool.starmap(
                get_data_from_pages, [(page_id_list, list_of_land, subcat2cat, if_del_none, excluded_categories)
                                      for page_id_list in page_id_list_by_cat])).flat)
            wiki_pages_by_type[var_cat].extend(data)
        else:
            inter = zip(list_of_categories, list_of_size) if if_display_find_alg else tqdm(zip(list_of_categories, list_of_size))
            for cat, cat_size in inter:
                if if_without_intersections_within_datatype:
                    forbidden_cat -= set(list_of_categories)
                    forbidden_cat.update(forbidden_cat_within_datatype)
                    forbidden_cat.update(set(list_of_categories))
                    forbidden_cat.discard(cat)
                page_id_list = find_pages_under_category(main_category=cat,
                                                         category_size=cat_size,
                                                         required_languages=list_of_land,
                                                         forbidden_category=forbidden_cat,
                                                         forbidden_pages=used_pages,
                                                         min_num_cat=min_num_of_cat_on_page,
                                                         max_num_cat=max_num_of_cat_on_page,
                                                         max_level=max_level_search_pageid,
                                                         if_print=if_display_find_alg,
                                                         subcat2cat=subcat2cat)
                data = get_data_from_pages(page_id_list, list_of_land, subcat2cat, if_del_none, excluded_categories)
                wiki_pages_by_type[var_cat].extend(data)
                used_pages.extend(page_id_list)
                if if_without_intersections_within_datatype:
                    forbidden_cat_within_datatype.update(
                        set(category for doc_info in data for category in doc_info['categories']))
        finish_time = time.perf_counter()
        print(f"{type_cat} finished in {util.sec2hms(finish_time - start_time)}")
        additional_categories.update(set(category for doc_info in wiki_pages_by_type[var_cat]
                                         for category in doc_info['categories']) - set(list_of_categories))
        if save_path is not None:
            util.save_data(wiki_pages_by_type[var_cat], os.path.join(save_path, f'wiki_{var_cat}_bk.json'))

    wiki_pages_by_type, label2cat, cat2label = get_labels_and_cats(wiki_pages_by_type=wiki_pages_by_type,
                                               if_labels_separately=if_labels_separately,
                                               subcat2cat=subcat2cat,
                                               if_del_none=if_del_none,
                                               excluded_categories=excluded_categories)
    return wiki_pages_by_type, label2cat, cat2label




def collect_wikidata_shuffle(categories_set, variation_cat_size, weights_cat_size=None, max_level_search_pageid=20,
                     min_num_of_cat_on_page=1, max_num_of_cat_on_page=10, subcat2cat=None, num_cpu=1,
                     if_labels_separately=False, if_del_none=True, excluded_categories=True,
                     iteration=None, if_reversed=False, if_without_intersections_within_datatype=False,
                     if_display_find_alg=True, save_path=None):
    if if_without_intersections_within_datatype and num_cpu > 1:
        print('Parameter "if_without_intersections_within_datatype" cannot be True '
              'if Parameter "num_cpu" is greater than 1. Parameter "num_cpu" will be equal 1.')
        num_cpu = 1
    all_categories = set(j for sub_info in categories_set.values() for j in sub_info['category'])
    wiki_pages_by_type = {key: [] for key in categories_set.keys()}
    additional_categories = {key: set() for key in categories_set.keys()}
    used_pages = []

    if iteration == 'random':
        iteration_list = [[cat, d_cat['language'], var_cat] for var_cat, d_cat in categories_set.items() for cat in d_cat['category']]
        list_of_size = random.choices(variation_cat_size, weights=weights_cat_size, k=len(all_categories))
        for i, n in enumerate(list_of_size):
            iteration_list[i].append(n)
        random.shuffle(iteration_list)
    else:
        iteration_list = []
        for j, cat_type in enumerate(iteration):
            for i, cat in enumerate(categories_set[cat_type]['category']):
                iteration_list.insert((j + 1) * i + j, [cat, categories_set[cat_type]['language'], cat_type])
        list_of_size = random.choices(variation_cat_size, weights=weights_cat_size, k=len(all_categories))
        for i, n in enumerate(list_of_size):
            iteration_list[i].append(n)

    for cat, cat_langs, var_cat, cat_size in iteration_list:
        type_cat = 'Monolingual' if len(cat_langs) == 1 else 'Bilingual'
        type_cat += f' {var_cat[5:]} cluster ' if len(cat_langs) == 1 else ' cluster '
        type_cat += cat
        print(type_cat, end = ', ')

        list_of_categories = categories_set[var_cat]['category']
        within_type = set(categories_set[var_cat]['category']) | additional_categories[var_cat]
        without_type = set(cat for set_cat in additional_categories.values() for cat in set_cat) | set(all_categories)

        forbidden_cat = without_type - within_type
        forbidden_cat_within_datatype = set()

        list_of_land = cat_langs

        print('number of pages per cluster:', cat_size)
        search_size = cat_size if len(cat_langs) == 1 else cat_size // 2
        start_time = time.perf_counter()

        if if_without_intersections_within_datatype:
            forbidden_cat -= set(list_of_categories)
            forbidden_cat.update(forbidden_cat_within_datatype)
            forbidden_cat.update(set(list_of_categories))
            forbidden_cat.discard(cat)

        page_id_list = find_pages_under_category(main_category=cat,
                                                 category_size=search_size,
                                                 required_languages=list_of_land,
                                                 forbidden_category=forbidden_cat,
                                                 forbidden_pages=used_pages,
                                                 min_num_cat=min_num_of_cat_on_page,
                                                 max_num_cat=max_num_of_cat_on_page,
                                                 max_level=max_level_search_pageid,
                                                 if_print=if_display_find_alg,
                                                 subcat2cat=subcat2cat)
        data = get_data_from_pages(page_id_list, list_of_land, subcat2cat, if_del_none, excluded_categories)
        wiki_pages_by_type[var_cat].extend(data)
        used_pages.extend(page_id_list)
        if if_without_intersections_within_datatype:
            forbidden_cat_within_datatype.update(
                set(category for doc_info in data for category in doc_info['categories']))

        finish_time = time.perf_counter()
        print(f"{cat} finished in {util.sec2hms(finish_time - start_time)}")
        additional_categories[var_cat].update(set(category for doc_info in data
                                         for category in doc_info['categories']) - set(list_of_categories))
        if save_path is not None:
            util.save_data(wiki_pages_by_type[var_cat], os.path.join(save_path, f'wiki_{cat}_bk.json'))

    wiki_pages_by_type, label2cat, cat2label = get_labels_and_cats(wiki_pages_by_type=wiki_pages_by_type,
                                               if_labels_separately=if_labels_separately,
                                               subcat2cat=subcat2cat,
                                               if_del_none=if_del_none,
                                               excluded_categories=excluded_categories)

    return wiki_pages_by_type, label2cat, cat2label


def unimportant_expulsion(collect_data, if_labels_separately, min_doc_num, label2cat):
    label_name = 'label' if if_labels_separately else 'categories'
    label_counter = {}
    for cat_type, data_info in collect_data.items():
        val = 2 if cat_type == 'common' else 1
        for doc_info in data_info:
            for label in doc_info[label_name]:
                label_counter[label] = label_counter.get(label, 0) + val
    cool_labels = set()
    for k, v in label_counter.items():
        if v >= min_doc_num:
            cool_labels.add(k)
    updated_collect_data = {}
    for cat_type, data_info in collect_data.items():
        updated_collect_data[cat_type] = []
        for doc_info in data_info:
            if len(set(doc_info[label_name]) & cool_labels) > 0:
                updated_doc_info = {k: v for k,v in doc_info.items()}
                updated_doc_info[label_name] = set(doc_info[label_name]) & cool_labels
                if if_labels_separately:
                    updated_doc_info['categories'] = [label2cat[ll] for ll in updated_doc_info[label_name]]
                updated_collect_data[cat_type].append(updated_doc_info)
    return updated_collect_data


def structuring_collected_date(collected_date, list_of_languages, if_rename_id=True):
    corpora = {}
    for language in list_of_languages:
        corpora[language] = {corpus_key: [doc[corpus_key] if corpus_key != 'text' else doc[corpus_key][language]
                                          for data_key in [f'only_{language}', 'common']
                                          for doc in collected_date[data_key]]
                             for corpus_key in list(collected_date['common'][0].keys())}
        corpora[language]['language'] = language
        if if_rename_id:
            old_id_name = [name for name in list(collected_date['common'][0].keys()) if 'id' in name.lower()][0]
            corpora[language]['id'] = corpora[language].pop(old_id_name)
    return corpora


def build_corpus_from_wikipedia(start_categories_info=None, type_cat_info='cat2gen',
                                variation_num_cat=None, weights_num_cat=None,
                                variation_num_cat_lang1=None, variation_num_cat_lang2=None,
                                variation_num_cat_common=None,
                                language_1='en', language_2='fr',
                                max_level_for_search_categories=3, max_num_initial_categories=3000,
                                mapping_of_subcategories_in_main_category=None,
                                del_none=False, excluded_categories=False,
                                min_num_of_cat_on_page=1,  max_num_of_cat_on_page=10, min_doc_num_per_cat=2,
                                variation_cluster_size=None, weights_cluster_size=None,
                                max_level_for_search_pages=2, num_cpu=1, if_without_intersections_within_datatype=False,
                                if_labels_separately=False, iteration=None, if_reversed=True, if_display_find_alg=True,
                                collect_type='shuffle',
                                save_path=None, add_name=''):
    """Function to collect data for wikipedia corpus.

    :param if_without_intersections_within_datatype:
    :param iteration:
    :param variation_num_cat_lang2: list of possible number of categories which occurs only in  [language_2].
    :param variation_num_cat_lang1: list of possible number of categories which occurs only in  [language_1].
    :param start_categories_info: see the description of the 'type_initial_cat' parameter.
    :param type_cat_info: Possible options:
                            'cat2gen': the categories for select will be generated by
                            [generate_categories_for_selection] function, and will be subcategories of the categories
                            from [initial_categories]. The [initial_categories] parameter must be a list of categories.
                            'cat2choose': the categories for select are the categories from [initial_categories]
                             parameter. The [initial_categories] parameter must be a list of categories.
                            'download': the categories for select will be downloaded from the file. The path to the
                            file is specified in the [initial_categories] parameter.
    :param variation_num_cat:  list of possible number of categories for each type
                            (occurs only in  [language_1], only in [language_2], in both languages).
    :param variation_num_cat_common:  list of possible number of categories which occurs only in both languages.
    :param weights_num_cat: list of probabilities to choose a number from [variation_num_cat] list.
                            Must have  to have the same size as [variation_num_cat].
    :param language_1: str, language of the first part of the corpus (ex. 'en', 'fr')
    :param language_2: str, language of the first part of the corpus (ex. 'en', 'fr')
    :param max_level_for_search_categories:
    :param max_num_initial_categories: int, maximum number of categories (def. 10000)
    :param mapping_of_subcategories_in_main_category: dictionary, the keys are the subcategories, and the values are
                                                      the categories to which these subcategories belong.
    :param del_none: bool, whether to delete subcategories that are not matched with categories (def. False)
    :param excluded_categories: list or bool, a list of irrelevant categories (this category will be ignored when
                                extracting categories from the wikipedia page) or True if use the default list
                                or False if want to consider all categories (def. False).
    :param max_num_of_cat_on_page: int, the maximum number of categories a page can contain. (def. 10)
    :param variation_cluster_size: list of variations of how many pages there should be for each category.
    :param weights_cluster_size: list of weights for [variation_cat_size].
    :param max_level_for_search_pages: int, how many times will the algorithm go to a subcategory to find more pages.
    :param num_cpu: int, number of CPU which will be used for finding pages (def. 1)
    :param if_labels_separately: bool
    :param if_reversed: bool, whether corpus collection starts from the end of the [categories_set] (def. True)
                              (True: en->fr->common; False: common->fr->en)
    :param if_display_find_alg: bool, whether intermediate prints are necessary (def. False)
    :param save_path: the path to the directory where data will be saved
    :param add_name: str, a name to identify several versions of the corpus
    :return: two parts of corpus.

    """
    if save_path is not None:
        data_save_path = os.path.join(save_path, f'dataset_{add_name}')
        if not os.path.exists(data_save_path):
            # Create a new directory because it does not exist
            os.makedirs(data_save_path)
            print("The new directory is created!")
    else:
        data_save_path = save_path

    backup_path = os.path.join(data_save_path, 'backup')
    path_check(path=backup_path, if_create=True)

    if num_cpu > 1:
        if_display_find_alg = False

    if start_categories_info is None:
        start_categories_info = [constants.ROOT_CATEGORY]
        type_cat_info = 'cat2gen'

    name2print = {f'only_{language_1}': f'Monolingual {language_1}',
                  f'only_{language_2}': f'Monolingual {language_2}',
                  'common' : 'Bilingual'
                 }

    print('Category selection process...')
    categories_set = generate_categories(initial_categories=start_categories_info,
                                         type_initial_cat=type_cat_info,
                                         variation_num_cat=variation_num_cat, weights_num_cat=weights_num_cat,
                                         language_1=language_1, language_2=language_2,
                                         variation_num_cat_lang1=variation_num_cat_lang1,
                                         variation_num_cat_lang2=variation_num_cat_lang2,
                                         variation_num_cat_common=variation_num_cat_common,
                                         max_level=max_level_for_search_categories,
                                         max_num=max_num_initial_categories)
    print('Selected categories:')
    for k, v in categories_set.items():

        print(f'{name2print[k]}  categories')
        print(', '.join(f'({i}) {name}' for i, name in enumerate(v['category'])))

    if data_save_path is not None:
        util.save_data(categories_set,
                  os.path.join(data_save_path, f'wikipedia_categories_main_{language_1}-{language_2}_{add_name}.json'))

    if os.path.exists(mapping_of_subcategories_in_main_category):
        subcat2cat = util.read_data(mapping_of_subcategories_in_main_category)
        print('File for mapping subcategories in a category has been successfully downloaded')
    elif mapping_of_subcategories_in_main_category is True:
        print('Started the process of creating a file to mapping subcategories in a category.')
        wikipedia_tree = create_wikipedia_tree(root_categories=constants.ROOT_CATEGORY,
                                               save_path=data_save_path,
                                               start_level=0,
                                               max_level=max_level_for_search_pages,
                                               if_backup=False)
        subcat2cat = map_subcategories_to_categories_from_wiki_tree(wikipedia_tree=wikipedia_tree,
                                                                    initial_level=2,
                                                                    max_level=max_level_for_search_pages)
        if data_save_path is not None:
            util.save_data(wikipedia_tree, os.path.join(data_save_path, f'wikipedia_tree_{add_name}.json'))
            util.save_data(subcat2cat, os.path.join(data_save_path, f'subcat2cat_{add_name}.json'))

        # mapping_subcategories_to_categories(
        # initial_categories=start_categories_info,
        # type_initial_cat='download' if type_cat_info == 'download' else 'cat2map',
        # save_path=save_path,
        # max_level=max_level_for_search_pages + max_level_for_search_categories)
    else:
        print('File for mapping subcategories in a category not provided.')
        subcat2cat = None

    print('Collect data', iteration)
    collect_function = collect_wikidata_shuffle if collect_type == 'shuffle' else collect_wikidata
    collect_data, label2cat, cat2label = collect_function(
        categories_set=categories_set,
        variation_cat_size=variation_cluster_size,
        weights_cat_size=weights_cluster_size,
        max_level_search_pageid=max_level_for_search_pages,
        min_num_of_cat_on_page=min_num_of_cat_on_page,
        max_num_of_cat_on_page=max_num_of_cat_on_page,
        subcat2cat=subcat2cat,
        num_cpu=num_cpu,
        if_labels_separately=if_labels_separately,
        if_del_none=del_none,
        excluded_categories=excluded_categories,
        iteration=iteration,
        if_without_intersections_within_datatype=if_without_intersections_within_datatype,
        if_reversed=if_reversed,
        if_display_find_alg=if_display_find_alg,
        save_path=backup_path)

    collect_data = unimportant_expulsion(collect_data=collect_data,
                                         if_labels_separately=if_labels_separately,
                                         min_doc_num=min_doc_num_per_cat,
                                         label2cat=label2cat)

    collect_data, label2cat, cat2label = get_labels_and_cats(wiki_pages_by_type=collect_data,
                                                                   if_labels_separately=if_labels_separately,
                                                                   subcat2cat=subcat2cat,
                                                                   if_del_none=del_none,
                                                                   excluded_categories=excluded_categories)


    print(f'Number of documents in monolingual {language_1} clusters = {len(collect_data[f"only_{language_1}"])}, '
          f'Number of documents in monolingual {language_2} clusters = {len(collect_data[f"only_{language_2}"])}, '
          f'Number of documents in bilingual clusters = {len(collect_data["common"])}'
          )
    if data_save_path is not None:
        util.save_data(label2cat, os.path.join(data_save_path,
                                          f'wikipedia_categories_all_{language_1}-{language_2}_{add_name}.json'))
        util.save_data(cat2label, os.path.join(data_save_path,
                                          f'wikipedia_labels_{language_1}-{language_2}_{add_name}.json'))

    print('Corpus reorganisation.')
    corpus1, corpus2 = structuring_collected_date(collected_date=collect_data,
                                                  list_of_languages=[language_1, language_2],
                                                  if_rename_id=True).values()

    if data_save_path is not None:
        util.save_data(corpus1, os.path.join(data_save_path, f'wikipedia_{language_1}_{add_name}.json'))
        util.save_data(corpus2, os.path.join(data_save_path, f'wikipedia_{language_2}_{add_name}.json'))

    if os.path.exists(os.path.join(data_save_path, f'wikipedia_{language_1}_{add_name}.json')) and os.path.exists(os.path.join(data_save_path, f'wikipedia_{language_2}_{add_name}.json')):
        print('Corpus has been successfully created. Intermediate files will be deleted')
        for root, dirs, files in os.walk(backup_path):
            for f in files:
                os.remove(os.path.join(root, f))
        os.rmdir(backup_path)

    return corpus1, corpus2

if __name__ == "__main__":
    print('ok')