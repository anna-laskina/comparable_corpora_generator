# Comparable corpora generator
This repository provides the source code for create a comparable corpora based on Wikipedia.


## __How to run the code__

### __Preprocessing__

Before starting to create a dataset, it is necessary to create a Wikipedia tree and associate categories with topics.
For that step the following programme must be run:

```python -m scripts.create_tree  ```

### __Create Wikipedia corpora__

Start the corpus creation process with the following command:

```python -m scripts.build_corpus -n <string> [-l1 <string>] [-l2 <string>] [-verbose] ...```

The meaning of main argument is:
* ``-h``, ``--help``: Show usage.
* ``-n <string>``, ``--name <string>``: A name to identify several versions of the corpus. Ex. v0_0.
* ``-l1 <string>``, ``--language_1 <string>``: A language of the first part of the corpus (ex. 'en', 'fr').
* ``-l2 <string>``, ``--language_2 <string>``: A language of the second part of the corpus (ex. 'en', 'fr').
* ``-verbose``, ``--verbose``: Provides additional details about creation process.

**Example:**
For En-Fr corpora: 

```python -m scripts.build_corpus -n v0_0 -l1 en -l2 fr```