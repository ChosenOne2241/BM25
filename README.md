# BM25
The script `BM25.py` searches the [Cranfield collection](http://ir.dcs.gla.ac.uk/resources/test_collections/cran/) using the [BM25](https://en.wikipedia.org/wiki/Okapi_BM25), with queries supplied by the user. 

For the first time one runs the script by simply typing `python3 bm25.py`, a `.json` file called `index.json` is generated containing a dictionary with words and their stemming forms, term vectors, and lengths for each document abstract. From the second times onwards, `index.json` must exist in the same directory and is used to calculate ranks. Mode can be selected by using the `-m` flag, whose default value is `manual`. Possible options are `manual` and `evaluation`. Selecting `evaluation` will run and evaluate the results for all queries in the `cranfield_queries.txt` file.An output file named ``evaluation_output.txt`` is created. Each line in this file has three fields, separated by spaces, as follows:

1. Query ID.
2. Document ID.
3. Rank (beginning at 1 for each query).

And selecting `manual` will allow users to type queries from keyword until a stop word `QUIT` is entered or KeyboardInterrupt exception is raised. And in `manual` mode, the script maintains a buffer for typing history, which means user can use arrow keys to browse history for current session. Type `python3 BM25.py -h` for more help information.

Here is a list of all files in the repository:

* `bm25.py` is the main function to run.
* `stopwords.txt` is a list to eliminate words that one should not bother including in feature vectors.
* `porter.py` is a Python implementation of the Porter stemming algorithm for English language, downloaded from [author's main page](https://tartarus.org/martin/PorterStemmer/).
* And in `Cranfield_Collection` directory, there are the following documents:
  * `cranfield_queries.txt` contains a set of queries numbered 1 through 365 (which contain 225 individual queries).
    * Lines beginning with .I are ids for the queries.
    * Lines following .W are the queries.
  * `cranfield_collection.txt` contains 1400 abstracts of aerodynamics journal articles (the document collection).
    * Lines beginning with .I are ids for the abstracts.
    * Lines following .T are titles.
    * Lines following .A are authors.
    * Lines following .B are some sort of bibliographic notation.
    * Lines following .W are the abstracts.
  * `cranfield_relevance.txt` is an answer key. Each line consists of three numbers separated by a space:
    * the first number is the query id (1 through 225);
    * the second number is the abstract id (1 through 1400);
    * the third number is a number (-1, 1, 2, 3 or 4).
    These numbers represent how related the query is to the given abstract. Unrelated query/abstract pairs are not listed at all (they would get a score of 5): There are 1836 lines in cranqrel. If all combinations were listed, there would be 225 * 1400 = 315,000 lines.
    We will treat -1 as being the same as 1. We suspect it means something like "the best choice for the query", but the specifications do not say.

N.B.: the script may contains some tweaks working only on Cranfield collection, which may not be useful for other kinds of documents; for instance, no `str.lower()` operations are done since actual contents in Cranfield collection are all lowercase.
