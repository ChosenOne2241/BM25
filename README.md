# BM25
The script `bm25.py` searches the [Cranfield collection](http://ir.dcs.gla.ac.uk/resources/test_collections/cran/) using the [BM25](https://en.wikipedia.org/wiki/Okapi_BM25), with queries supplied by the user. And also it offers 5 evaluation methods (precision, recall, MAP, P at N and NDCG at N) to measure the efficiency.

For the first time one runs the script by simply typing `python3 bm25.py` (and all extra arguments are ignored), a `.json` file called `index.json` is generated, containing a dictionary with terms and their stemming forms, term vectors, and lengths for each document abstract. From the second times onwards, `index.json` must exist in the same directory and is used to calculate ranks. Mode can be selected by using the `-m` flag; possible options are `manual` and `evaluation` and the default one is `manual`. Selecting `evaluation` will run and evaluate results for all queries in the `cran.qry` file. Also, in `evaluation` mode, an output file of evaluation results is created supposing `-o` option is present; the default value is ``evaluation_output.txt`` if no specific file name is given. For each query, there are exactly 15 results to be returned. Each line in this text file has three fields, separated by spaces, as follows:

1. Query ID.
2. Document ID.
3. Rank (beginning at 1 for each query).

And selecting `manual` will allow users to type queries from keyword until a stop word `QUIT` is entered or KeyboardInterrupt exception is raised. And in `manual` mode, the script maintains a buffer for typing history, which means user can use arrow keys to browse history for current session. For each query, *at most* top 15 relevant documents are printed. Type `python3 bm25.py -h` for more help information.

Here is a list of all files in the repository:

* `bm25.py` is the script to run.
* `stopwords.txt` contains a list of words that one should not bother including in feature vectors.
* `porter.py` is a Python implementation of the Porter stemming algorithm for English, downloaded from [author's main page](https://tartarus.org/martin/PorterStemmer/).
* And in `cran` directory, there are the following files:
  * `cran.all.1400` contains 1400 abstracts of aerodynamics journal articles (the document collection).
    * Lines beginning with .I are ids for the abstracts.
    * Lines following .T are titles.
    * Lines following .A are authors.
    * Lines following .B are some sort of bibliographic notation.
    * Lines following .W are the abstracts.
  * `cran.qry` contains a set of queries numbered 1 through 365 (which contain 225 different queries).
    * Lines beginning with .I are ids for the queries.
    * Lines following .W are the queries.
  * `cranqrel` is an answer key. Each line consists of three numbers separated by a space:
    * the first number is the query id (1 through 225);
    * the second number is the abstract id (1 through 1400);
    * the third number is a number (-1, 1, 2, 3 or 4).
    These numbers represent how related the query is to the given abstract. Unrelated query / abstract pairs are not listed at all (they would get a score of 5): There are 1836 lines in cranqrel. If all combinations were listed, there would be 225 * 1400 = 315,000 lines.
    Here we treat -1 as being the same as 1. We suspect that it means something like "the best choice for the query", but the specifications do not say. We only use ones with relevance score larger than `RELEVANCE_SCORE_THRESHOLD` (here we use 3) and What each score stands for is elaborated in `cranqrel.readme`.
  * `cranqrel.readme` is the original README file to explain `cranqrel` file.

N.B.: the script may contains some tweaks working only on Cranfield collection, which may not be useful for other kinds of documents; for instance, no `str.lower()` operations are applied since actual contents in Cranfield collection are all lowercase.
