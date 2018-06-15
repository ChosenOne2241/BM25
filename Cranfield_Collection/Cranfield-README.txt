About the Cranfield Collection
------------------------------

The Cranfield document collection is a classic data set for IR experiments. This file briefly explains the files that are included in the collection.

The file ``cranfield_collection.txt'' contains the document collection itself. It consists of
1400 documents, with the following format:

- Lines beginning with .I mark the beginning of a document. The number after .I is the document ID.
- Lines following .T are part of the title of the document.
- Lines following .A contain the author(s) of the document.
- Lines following .B contain the bibliographic reference of the document.
- Lines following .W contain the document itself (up to the next .I, or the end of the file).


The file ``cranfield_queries.txt'' contains some standard queries that researchers have created
relevance judgments for. The format is as follows:

- Lines beginning with .I mark the beginning of a query. The number after .I is the query ID.
- Lines following .W contain the query itself (up to the next .I, or the end of the file).


The file ``cranfield_relevance.txt'' contains relevance judgments for each of the standard queries.
Each line has three parts:

1. A query ID.
2. A document ID.
3. A relevance score for that document in relation to that query.

The explanation of the relevance scores is as follows (these are the original explanations):

1. References which are a complete answer to the question.     
2. References of a high degree of relevance, the lack of which
    either would have made the research impracticable or would
    have resulted in a considerable amount of extra work.
3. References which were useful, either as general background
    to the work or as suggesting methods of tackling certain aspects
    of the work.
4. References of minimum interest, for example, those that have been
   included from an historical viewpoint.
5. References of no interest.

Relevance judgments with a score of 5 were not included in the file (i.e. for each query, any
document that does not appear in the cranfield_relevance.txt file has a score of 5.