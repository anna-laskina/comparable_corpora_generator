# Comparable corpora generator
This repository provides the source code for create a clustered bilingual comparable corpora based on Wikipedia.


## __How to run the code__
Access to code launching is facilitated through programs available in the scripts folder. There are three programs in total:
1. A program for creating a category tree
2. A program for creating corpus
3. A program for visualizing obtained corpus.

Below is a detailed description of each program.

### __Create Category Tree__

Before starting to create a corpus, it is necessary to create a category tree and associate categories with topics.
For that step the following programme must be run:

    python -m scripts.create_tree

The category tree creation does not require any parameters and can only be launched once before creating a series of corpora. 
The following additional parameters are available:
* ``-ml <int>``, ``--max_level <int>``: the number of iterations of the subcategory search. It is advisable to change
this value only if it is necessary to speed up the process of building a category tree or if it is desirable to 
consider only the closest descendants to the root. It is not recommended to set the value to less than 5.
* ``-pl <int>``, ``--primary_level <int>``: the level of the category tree, the categories from which will be 
considered as topics to create the corpus.
* ``-rc <string>``, ``--root_categories <string>``: the name of the root category.
* ``-ot``, ``--only_tree``: Run only category tree creation.
* ``-om``, ``--only_map``: Run only associations of categories with topics. Should be installed only if the category
tree has already been created and it is only necessary to change the number of possible topics and the association of 
categories with these topics.
* ``-spt <string>``, ``--save_path_tree <string>``: save tree path.

If some parameters have been changed, when creating a corpus, pay attention to the parameters related to topic 
definition and make the appropriate changes.

### __Create Wikipedia corpora__

Once the  category tree has been generated and the categories have been linked to the topics, a corpus can be created 
by running the _build_corpus.py_ program located in the _scripts_ folder. In a basic configuration, 
this can be achieved by running this command:
    
    python -m scripts.build_corpus -n <string> [-l1 <string>] [-l2 <string>] 

where
* ``-n <string>``, ``--name <string>``: A name to identify several versions of the corpus.
* ``-l1 <string>``, ``--language_1 <string>``: The language code for the first part of the corpus.
* ``-l2 <string>``, ``--language_2 <string>``: The language code for the second part of the corpus.

An example of an English-French corpus would be the following command:

    python -m scripts.build_corpus -n v0_0 -l1 en -l2 fr

In addition to the basic parameters mentioned above, it is available a fine-tuning of a corpus creation. 
In our comparable corpus available three type of clusters: a monolingual l1 (code 0), a bilingual (code 1) and 
a monolingual l2 (code 2) types. The monolingual type assumes that documents with this topic are presented in one 
language only, while the bilingual type assumes that  documents with this topic are presented in both languages. 
The following parameters are available in accordance with this division:

* ``-var_cat <string>``, ``--variation_num_cat <string>``: A list of possible number of topics for any topic type.
Passing values through underscores.
* ``-var_cat_1 <string>``, ``--variation_num_cat_in_lang1 <string>``: A list of possible number of topics which occurs
in monolingual l1 types. Passing values through underscores.
* ``-var_cat_2 <string>``, ``--variation_num_cat_in_lang2 <string>``: A list of possible number of topics which occurs
in monolingual l2 types. Passing values through underscores.
* ``-var_cat_c <string>``, ``--variation_num_cat_in_common <string>``: A list of possible number of topics which occurs 
only in bilingual types. Passing values through underscores.
* ``-svar``, ``--simple_vat_cat``: Considering only _variation_num_cat_ parameter.
* ``-i <string>``, ``--iteration <string>``: An order in which topic types are considered, with seven options:
_12с_, _1с2_, _21c_, _2c1_, _c12_, _c21_ or _r_ (random).
* ``-ct <string>``, ``--collect_type <string>``: A style of considering topic types: _shuffle_ or _by_type_.

Next parameters that apply to presenting documents on topics:

* ``-var_size <string>``, ``--variation_cluster_size <string>``: A list of variations of how many documents there should
be for each topic. Passing values through underscores.
* ``-wiw``, ``--without_inter_within``: No intersections within one topic type (total crise ). 
* ``-min_cp <int>``, ``--min_num_of_cat_on_page <int>``, A minimum number of topics per document.
* ``-max_cp <int>``, ``--max_num_of_cat_on_page <int>``: A maximum number of topics per document.
* ``-min_d <int>``, ``--min_doc_num_per_cat <int>``: A minimum number of documents each topic should contain.


Parameters influencing topic selection in the corpus. 
Three ways of selecting topics are implemented:
the topics for select will be generated (cat2gen), 
the topics for select will be a random selection (cat2choose),
the topics for select will be downloaded (download).

* ``-init_cat_type <string>``, ``--initial_category_type <string>``: A way topics are selected. 
Possible options: 'cat2gen', 'cat2choose', 'download'.
* ``-init_cat_info <string>``, ``--initial_category_information <string>``: 
an information that will be used when selecting topics.
If cat2gen' option was chosen, a list of Wikipedia categories from which subcategories the topics will be selected.
If 'cat2choose' option was chosen, a list of topics to select from. 
If 'download' option was chosen, the path to the file where the topics are stored.

Changing the parameter below is reasonable when the parameters for tree creation and topic selection have been modified.

* ``-map_file <string>``, ``--map_subcat_to_cat_filename <string>``: 
A file name of the file where information about associations of categories with topics is stored. If you are unsure of the file name, navigate to the folder where the trees are stored and search for files beginning with the prefix 'map'.

Finally, additional technical parameters are:
* ``-sp <string>``, ``--save_path <string>``: A path to the directory where the corpus will be saved.
* ``-spt <string>``, ``--save_path_tree <string>``: A path to the directory where the category tree information is stored.
* ``-verbose``, ``--verbose``: To provide additional details about creation process.
* ``-c <int>``, ``--num_cpu <int>``: A number of CPU which will be used for finding pages.

The default values are available via a help message:

    python -m scripts.build_corpus -h

### __View corpus information__

    python -m scripts.corpus_info -n <string> [-s] [-b] [-m] 

The meaning of main argument is:
* ``-h``, ``--help``: Show usage.
* ``-n <string>``, ``--name <string>``: A name to identify several versions of the corpus. Ex. v0_0.
* ``-s``, ``--stat``: Show information about the number of documents and labels.
* ``-b``, ``--bar``: Build a bar plot.
* ``-m``, ``--heatmap``: Build a heatmap plot.

