#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Description: Build a structural data from orginial Cranfield collection and
#              implement the BM25 alogrithm information retrieval;
#              also 5 evaluation methods (precision, recall, MAP, P at N and
#              NDCG at N) are applied.
#              Tested under Python 3.5 on Ubuntu 16.04.
# Author: '(Yungchen J.)
# Date created: 2018-05-07

# Here are some Python standard modules used in the script.
import argparse
# Used to parse program arguments.
# More details are here: https://docs.python.org/3/library/argparse.html
import readline
# Used to create a typing history buffer.
# More details are here: https://docs.python.org/3/library/readline.html
import json # Create a human-readable JSON file for index information and the like.
import string # Used to do some regex operations.
import math
import os

# Here are some Python libraries that places locally.
import porter

STOP_WORDS_PATH = "stopwords.txt"
DOCUMENT_PATH = "./cran/cran.all.1400"
QUERY_PATH = "./cran/cran.qry"
RELEVANCE_PATH = "./cran/cranqrel"
INDEX_PATH = "index.json"
EVALUATION_PATH = "evaluation_output.txt"

# Labels in `cran.all.1400` and `cranqrel` text files.
ID = ".I"
TITLE = ".T"
AUTHORS = ".A"
BIBLIOGRAPHY = ".B"
WORDS = ".W"
LABELS = [ID, TITLE, AUTHORS, BIBLIOGRAPHY, WORDS]
CONTENTS = [AUTHORS, BIBLIOGRAPHY, WORDS]

MOST_RELEVANT = 15 # At most return top `MOST_RELEVANT` results for each query.
USER_STOP_WORD = "QUIT"
# When user types `USER_STOP_WORD`, the program ends; it is case-sensitive.
RELEVANCE_SCORE_THRESHOLD = 4
# Filter out ones with relevance score larger than `RELEVANCE_SCORE_THRESHOLD`.
# The default value is 4 (-1, 1, 2, 3, 4).
RELEVANCE_SCORE_FIX = 5
# It is a number used as minuend to convert original relevance scores to
# NDCG-friendly ones.

# Constants used in BM25 model.
K = 1.0
B = 0.75
# A constant used in Precision at N and NDCG (Normalised Discounted Cumulated Gain) at N.
# If `MOST_RELEVANT` is equal to `N`, precision will be the same as P at N for Cranfield collection.
# N.B.: `N` cannot be larger than `MOST_RELEVANT`.
N = 10

def is_number(word):
	""" A helper function to check if a string can be converted to an integer.
        Used to process documents and queries.
	"""
	try:
		int(word)
		return True
	except ValueError:
		return False

def is_valid(word):
	""" A helper function to check if a string is valid.
        Used to process documents and queries.
	"""
	if word != "" and word not in stop_words and not is_number(word):
		return True
	else:
		return False

def get_arguments():
	parser = argparse.ArgumentParser(description = "A script used to build BM25 model and relative evaluation methods. If the index JSON file is not available, just type `python3 bm25.py` without any extra arguments to generate one in the working directory.")
	parser.add_argument("-m", required = False, choices = ["manual", "evaluation"], default = "manual", help = "mode selection; `manual` mode is chosen by default if it is not specified")
	parser.add_argument("-o", required = False, nargs = "?", const = EVALUATION_PATH, metavar = "FILE NAME", help = "evaluation result output; if `FILE NAME` is not given, the default output file name is `evaluation_output.txt`")
	return parser.parse_args()

def load_stop_words():
	stop_words = set()
	with open(STOP_WORDS_PATH, "r") as fp:
		for line in fp:
			stop_words.add(line.rstrip())
	return stop_words

def process_documents():
	""" Build vectors of each term and calculate lengths of each documents.
	"""
	def add_new_word(word):
	# A helper function to add a new word in `term_vectors`.
		if word not in stemming:
			stemming[word] = stemmer.stem(word)
		stemmed_word = stemming[word]
		if stemmed_word not in term_vectors:
			term_vectors[stemmed_word] = {}
		if document_ID in term_vectors[stemmed_word]:
			(term_vectors[stemmed_word])[document_ID] += 1
		else:
			term_vectors[stemmed_word].update({document_ID : 1})

	stemming = {}
	term_vectors = {}
	# `term_vectors` structure: {[Key] Term : [Value] {[Key] Document ID : [Value] Appearance Times}}.
	document_lengths = {}
	average_length = 0.0
	num_of_documents = 0
	with open(DOCUMENT_PATH, "r") as fp:
		document_ID = 0
		length = 0.0
		for line in fp:
			current_section = line[0:2]
			if current_section in LABELS:
				if current_section == ID:
					document_lengths[document_ID] = math.sqrt(length)
					# Calculate the previous document length and start a new one.
					# The empty entry for document 0 is also created although
					# in Cranfield collection, document ID begins from 001.
					average_length += document_lengths[document_ID]
					document_ID += 1
					# Ignore original document IDs, which is the numbers followed by ".I",
					# since they may not be consecutive.
					num_of_documents += 1
					length = 0.0
				section = current_section
				continue # Update and go to next line immediately.

			if section in CONTENTS:
				line = line.translate(removing_punctuation_map)
				line = line.replace("--", " ")
				# Also, treat two consecutive hyphens as a space.
				for term in line.split():
				# Split according to whitespace characters and deal with two special cases:
				# abbreviations with "." and hyphenated compounds.
					term = term.replace(".", "")
					# Remove full stops in one term, used to convert abbreviations
					# like "m.i.t." (line 1222) / "u.s.a." (line 32542) into "mit" / "usa".
					# In the meantime, something like "..e.g.at" (line 17393),
					# "i.e.it" (line 17287), "trans.amer.math.soc.33" (line 31509),
					# or "studies.dash" (line 516) will not be handled as expected.
					# All float-point numbers like "3.2x10" (line 18799), "79.5degree"
					#  (line 20026) will be converted into integers by just removing dots.
					# And similarly, phrases like "m. i. t." (line 36527) and
					# "i. e." (line 11820) will be ignored.
					# "r.m.s." (line 20241) will become "rm" stored in the dictionary after stemming.

					compound = term.replace("-", "")
					if is_valid(compound):
						add_new_word(compound)
						if section == WORDS:
							length += 1.0
							# Treat a compound word as one word; words in `AUTHORS`
							# and `BIBLIOGRAPHY` section will not be counted.
						term_split = term.split("-")
						if len(term_split) > 1:
						# If only one item in `term_split`, which means there is no hyphen in this word.
						# There may exist a term with an ending hyphens like
						# "sub- and" (line 14632), which causes an extra empty string is created
						# and makes term_split look like ["sub", ""].
							for element in term_split:
							# Deal with each part of compound words like "two-step" (line 38037) or
							# type names like "75s-t6" (line 28459) or "a52b06" (line 25717).
								if is_valid(element):
									add_new_word(element)
									# Filter out all pure integers; for example, for "f8u-3" (line 35373),
									# both "f8u" and "f8u3" will be saved, but not "3".

	# Calculate the last length since Cranfield collection does not have ending symbols.
	document_lengths[document_ID] = math.sqrt(length)
	# Skip the document with index 0 from document length vector.
	del document_lengths[0]
	average_length = (document_lengths[document_ID] + average_length) / num_of_documents
	for document in document_lengths.keys():
		document_lengths[document] = document_lengths[document] / average_length
		# Now document_lengths stores a normalised length for each document.

	# A dictionary for stemming is also returned for further use.
	return stemming, term_vectors, document_lengths

def process_single_query(query):
	def add_new_word(word):
	# A helper function to add a new word in `query_terms`.
		if word not in stemming:
			stemming[word] = stemmer.stem(word)
		stemmed_word = stemming[word]
		if stemmed_word not in query_terms:
			query_terms.append(stemmed_word)

	query_terms = []
	query = query.strip() # Remove leading and trailing whitespaces.
	query = query.translate(removing_punctuation_map)
	query = query.replace("--", " ")
	for term in query.split():
		term = term.replace(".", "").lower()
		compound = term.replace("-", "")
		if is_valid(compound):
			add_new_word(compound)
			term_split = term.split("-")
			if len(term_split) > 1:
				for element in term_split:
					if is_valid(element):
						add_new_word(element)
	return query_terms

def process_queries():
	with open(QUERY_PATH, "r") as fp:
		query_list = {}
		query = []
		query_ID = 0
		for line in fp:
			current_section = line[0:2]
			if current_section in LABELS:
				if current_section == ID:
					query_list[query_ID] = query
					query = []
					query_ID += 1
					# Ignore original query IDs, which is the numbers followed by ".I",
					# since they are not consecutive.
				if current_section == WORDS:
					section = current_section
				continue
			if section in CONTENTS:
				if query == []:
					query = process_single_query(line)
				else:
					query += process_single_query(line)
		query_list[query_ID] = query # Add the last entry.
		del query_list[0] # Skip the first one.
	return query_list

def bm25_similarities(query):
	""" Using `query`, return a descending list with at most top `MOST_RELEVANT` pairs
	    based on BM25 to calculate similarities.
        Pair structure is (Document ID, Similarity).
	"""
	similarities = []
	for document_ID in range(1, nums_of_documents + 1):
	# Document ID begins from 1.
		similarity = 0.0
		for term in query:
			if term in term_vectors and document_ID in term_vectors[term]:
				frequency = (term_vectors[term])[document_ID]
				n_i = len(term_vectors[term])
				idf = math.log((nums_of_documents - n_i + 0.5) / (n_i + 0.5), 2)
				similarity += frequency * (1.0 + K) / (frequency + K * ((1.0 - B) + B * document_lengths[document_ID])) * idf
		if similarity > 0.0: # Ignore the one with similarity score 0.
			pair = (document_ID, similarity)
			similarities.append(pair)
	# Sort results in desceding order.
	similarities = sorted(similarities, key = lambda x : x[1], reverse = True)
	if len(similarities) > MOST_RELEVANT:
		return similarities[0:MOST_RELEVANT]
	else:
		return similarities

def manual_mode():
	while True:
		print("********************************************************************************")
		# Use 80 asterisks to fill the default width of terminal window.
		user_query = input("Enter query (type \"QUIT\" to terminate): ")
		if user_query == USER_STOP_WORD:
			break
		query_terms = process_single_query(user_query)
		print("Results for query " + str(query_terms))
		print("Rank\tID\tScore")
		rank = 1
		for result in bm25_similarities(query_terms):
			print("{0}\t{1}\t{2}".format(str(rank), result[0], str(result[1])), end = "\n")
			rank += 1

def load_relevance_scores():
	relevance_scores = {}
	# `relevance_scores` structure: {[KEY] query ID : [Value] [(Document ID, Relevance Score)]}
	with open(RELEVANCE_PATH, "r") as fp:
		for line in fp:
			fields = line.split()
			query_ID = int(fields[0])
			pair = (int(fields[1]), int(fields[2]))
			if query_ID in relevance_scores:
				relevance_scores[query_ID].append(pair)
				# It guarantees no repetition of document IDs for each query.
			else:
				relevance_scores[query_ID] = [pair]

	for query_ID in relevance_scores:
	# Sort pairs in ascending order for each query; the less the relevance
	# score is, the more relevant the document is.
		relevance_scores[query_ID] = sorted(relevance_scores[query_ID], key = lambda x : x[1])
	return relevance_scores

def make_query_results():
	""" It returns possible relevant documents for each query based on BM25 model.
	"""
	query_list = process_queries()
	query_results = {}
	for query_ID in query_list:
		rank = 1
		query_results[query_ID] = []
		for pair in bm25_similarities(query_list[query_ID]):
			query_results[query_ID].append((pair[0], rank))
			rank += 1
	return query_results

def make_relevance_set(query_ID): # Relevant documents (Rel).
	relevance_set = set()
	for pair in relevance_scores[query_ID]:
		if pair[1] <= RELEVANCE_SCORE_THRESHOLD:
		# We only include queries whose relevance scores are less than or equal
		# to `RELEVANCE_SCORE_THRESHOLD` here.
			relevance_set.add(pair[0])
	return relevance_set

def make_retrieval_set(query_ID): # Retrieval documents (Ret).
	retrieval_set = set()
	for pair in query_results[query_ID]:
		retrieval_set.add(pair[0])
	return retrieval_set

def precision():
	precision = 0.0
	for query_ID in relevance_scores:
		relevance_set = make_relevance_set(query_ID)
		retrieval_set = make_retrieval_set(query_ID)
		appearance_times = 0
		for document_ID in retrieval_set:
			if document_ID in relevance_set:
				appearance_times += 1
		precision += appearance_times / len(retrieval_set)
	precision = precision / len(relevance_scores)
	# Calculate arithmetic mean of precisions for all queries.
	return precision

def recall():
	recall = 0.0
	for query_ID in relevance_scores:
		relevance_set = make_relevance_set(query_ID)
		retrieval_set = make_retrieval_set(query_ID)
		appearance_times = 0
		for document_ID in relevance_set:
			if document_ID in retrieval_set:
				appearance_times += 1
		recall += appearance_times / len(relevance_set)
	recall = recall / len(relevance_scores)
	# Calculate arithmetic mean of recalls for all queries.
	return recall

def p_at_n(n):
	p_at_n = 0.0
	for query_ID in relevance_scores:
		relevance_set = make_relevance_set(query_ID)
		appearance_times = 0
		for pair in query_results[query_ID]:
			if pair[0] in relevance_set and pair[1] <= n:
				appearance_times += 1
		p_at_n += appearance_times / n
	p_at_n = p_at_n / len(query_results)
	return p_at_n

def mean_average_precision():
	mean_average_precision = 0.0
	for query_ID in relevance_scores:
		relevance_set = make_relevance_set(query_ID)
		appearance_times = 0
		current_map = 0.0
		for pair in query_results[query_ID]:
			if pair[0] in relevance_set:
				appearance_times += 1
				current_map += appearance_times / pair[1]
		mean_average_precision += current_map / len(relevance_set)
	mean_average_precision = mean_average_precision / len(query_results)
	return mean_average_precision

def ndcg_at_n(n):
	""" It yields a list of NDCGs (from 1 to at most N) of each query separately.
	"""
	for query_ID, score_list in relevance_scores.items():
		relevance_set = make_relevance_set(query_ID)
		score_list_dict = dict(score_list)
		# Convert a list of pairs to dictionary for convienence.
		gain_vector = []
		for pair in query_results[query_ID]:
			if pair[0] in relevance_set:
				gain_vector.append(RELEVANCE_SCORE_FIX - score_list_dict[pair[0]])
				# Convert original ranking scores to NDCG-usable scores.
			else:
				gain_vector.append(0)
		dcg = [gain_vector[0]]
		# Discounted Cumulated Gain; put the first item in `dcg`.
		for i in range(1, len(gain_vector)):
			dcg.append(gain_vector[i] / math.log(i + 1, 2) + dcg[-1])
		# Ideal NDCG.
		ideal_gain_vector = []
		for pair in score_list:
			ideal_gain_vector.append(RELEVANCE_SCORE_FIX - score_list_dict[pair[0]])
		query_results_length = len(query_results[query_ID])
		ideal_gain_vector_length = len(ideal_gain_vector)
		ideal_dcg = [ideal_gain_vector[0]]
		for i in range(1, len(ideal_gain_vector)):
			ideal_dcg.append(ideal_gain_vector[i] / math.log(i + 1, 2) + ideal_dcg[-1])
		ndcg_at_n = []
		for pair in zip(dcg, ideal_dcg):
			ndcg_at_n.append(pair[0] / pair[1])
		if len(ndcg_at_n) > n:
		# Yield at most `n` results for each query.
			yield query_ID, ndcg_at_n[0:n]
		else:
			yield query_ID, ndcg_at_n

def print_evaluation_results():
	print("Evaluation Results:")
	print("Precision: {0}".format(precision()), end = "\n")
	print("Recall: {0}".format(recall()), end = "\n")
	print("P@{0}: {1}".format(N, p_at_n(N)), end = "\n")
	print("Mean Average Precision: {0}".format(mean_average_precision()), end = "\n")
	for query_ID, ndcg in ndcg_at_n(N):
		print("NDCG@{0} <Query {1}>: {2}".format(N, query_ID, ndcg), end = "\n")

if __name__ == "__main__":
	stemmer = porter.PorterStemmer()
	stop_words = load_stop_words()
	punctuation = string.punctuation[0:12] + string.punctuation[14:]
	removing_punctuation_map = dict((ord(character), " ") for character in punctuation)
	# Remove all punctuations except full stops and hyphens.
	args = get_arguments()

	if os.path.exists(INDEX_PATH):
		print("[Loading BM25 index from file.]")
		with open(INDEX_PATH, "r") as fp:
			stemming, term_vectors, document_lengths = json.load(fp)

		# Waring: unlike Python, `dict` type in JSON cannot have `int` key;
		# therefore a conversion is of necessity.
		document_lengths = {int(ID) : length for ID, length in document_lengths.items()}
		for term, vector in term_vectors.items():
			term_vectors[term] = {int(ID) : appearance_times for ID, appearance_times in vector.items()}
		nums_of_documents = len(document_lengths)
		# It is used in `bm25_similarities()` function.

		if args.m == "manual":
			manual_mode()
		elif args.m == "evaluation":
			relevance_scores = load_relevance_scores()
			query_results = make_query_results()
			print_evaluation_results()
			if args.o is not None: # If `-o` option is available.
				with open(args.o, "w") as fp:
					for query_ID, pair_list in query_results.items():
						for entry in pair_list:
							fp.write("{0} {1} {2}\n".format(query_ID, pair[0], pair[1]))
	else:
	# For first-time running, it creates an index JSON file and exit.
		print("[Generating the index file.]")
		with open(INDEX_PATH, "w") as fp:
			json.dump(process_documents(), fp)
