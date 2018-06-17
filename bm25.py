#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Description: Build a structural data from orginial Cranfield collection and
#              implement the BM25 alogrithm information retrieval;
#              also several evaluation methods (precision, recall, P at 10, MAP, NDCG at 10)
#              are applied.
#              Tested under Python 3.5 on Ubuntu 16.04.
# Author: '(Yungchen J.)
# Date created: 2018-05-07

# Here are some Python standard modules used in the script.
import argparse
# Used to parse program arguments.
# More details are here: https://docs.python.org/3/library/argparse.html
import readline
# Used to read and write history files from the Python interpreter.
# More details are here: https://docs.python.org/3/library/readline.html
import json # Create a human-readable .json file for index information.
import string # Used by some regex operations.
import math
import os

# Here are some Python libraries that places locally.
import porter

STOP_WORDS_PATH = "stopwords.txt"
DOCUMENT_PATH = "./Cranfield_Collection/cranfield_collection.txt"
QUERY_PATH = "./Cranfield_Collection/cranfield_queries.txt"
RELEVANCE_PATH = "./Cranfield_Collection/cranfield_relevance.txt"
INDEX_PATH = "index.json"

# Labels in `cranfield_collection.txt` and `cranfield_queries.txt` files.
ID = ".I"
TITLE = ".T"
AUTHORS = ".A"
BIBLIOGRAPHY = ".B"
WORDS = ".W"
LABELS = [ID, TITLE, AUTHORS, BIBLIOGRAPHY, WORDS]
CONTENTS = [AUTHORS, BIBLIOGRAPHY, WORDS]

MOST_SIMILAR = 15 # At most return top `MOST_SIMILAR` results.
USER_STOP_WORD = "QUIT"
# When user types `USER_STOP_WORD`, the program ends; it is case-sensitive.

# Constants in BM25 model.
K = 1.0
B = 0.75

N = 10
# A constant used in Precision at n and NDCG (Normalised Discounted Cumulated Gain).

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
	parser = argparse.ArgumentParser(description = "A script used to build BM25 model and relative evaluation methods. If the index .json file is not available, just type `python3 bm25.py` without any extra arguments to generate one in the working directory; if it is available and `-m` option is not offered, `manual` mode is chosen by default.")
	parser.add_argument("-m", required = False, help = "mode selection", choices = ["manual", "evaluation"], default = "manual")
	return parser.parse_args()

def load_stop_words(stop_words_path):
	stop_words = set()
	with open(stop_words_path, "r") as fp:
		for line in fp:
			stop_words.add(line.rstrip())
	return stop_words

def process_documents(document_path):
	""" Build vectors of each term and calculate lengths of each documents.
	"""
	def add_new_word(word):
	# A helper function to add a new word in `term_vectors`.
		if word not in stemming:
			stemming[word] = stemmer.stem(word)
		stemmed_word = stemming[word]
		if stemmed_word not in term_vectors:
			term_vectors[stemmed_word] = {}
		if document_ID not in term_vectors[stemmed_word]:
			term_vectors[stemmed_word].update({document_ID : 1})
		else:
			(term_vectors[stemmed_word])[document_ID] += 1

	stemming = {}
	term_vectors = {}
	# `term_vectors` structure: {[Key] Term : [Value] {[Key] Document ID : [Value] Appearance Times}}.
	document_lengths = {}
	average_length = 0.0
	num_of_documents = 0
	with open(document_path, "r") as fp:
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
	query = query.strip() # Remove leading and trailing whitespace.
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

def process_queries(query_path):
	with open(query_path, "r") as fp:
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
	''' Using `query`, return a descending list with top `MOST_SIMILAR` pairs
	    based on BM25 to calculate similarities.
        Pair structure is (Document ID, Similarity).
	'''
	similarities = []
	for index in range(0, nums_of_documents):
		document_ID = str(index + 1)
		# Keys in key/value pairs of JSON are always of the type `str`.
		similarity = 0.0
		for term in query:
			if term in term_vectors and document_ID in term_vectors[term]:
				frequency = (term_vectors[term])[document_ID]
				n_i = len(term_vectors[term])
				idf = math.log((nums_of_documents - n_i + 0.5) / (n_i + 0.5), 2)
				similarity += frequency * (1.0 + K) / (frequency + K * ((1.0 - B) + B * document_lengths[document_ID])) * idf
		pair = (int(document_ID), similarity)
		similarities.append(pair)

	# Sort results in desceding order and return the top `MOST_SIMILAR` ones.
	sorted_similarities = sorted(similarities, key = lambda x : x[1], reverse = True)
	return sorted_similarities[0:MOST_SIMILAR]

def manual_mode():
	while True:
		user_query = input("Enter query: ")
		if user_query == USER_STOP_WORD:
			break
		query_terms = process_single_query(user_query)
		print("Results for query " + str(query_terms))
		rank = 1
		for result in bm25_similarities(query_terms):
			print("{0} {1} {2}".format(str(rank), result[0], str(result[1])), end = "\n")
			rank += 1

def make_relevance():
	relevance = {}
	# `relevance` structure: {[KEY] query ID : [Value] [(Document ID, relevance Score)]}
	with open(RELEVANCE_PATH, "r") as fp:
		for line in fp:
			parts = line.split()
			query_ID = int(parts[0])
			if query_ID not in relevance:
				relevance[query_ID] = [(int(parts[1]), int(parts[2]))]
			else:
				relevance[query_ID].append((int(parts[1]), int(parts[2])))
			# It guarantees no repetition of document IDs for each query.
	for query in relevance:
	# Sort pairs in ascending order for each query; the less the relevance
	# score is, the more revelant the document is.
		relevance[query] = sorted(relevance[query], key = lambda x : x[1])
	return relevance

def make_evaluation():
	bm25_similarity_list = {}
	for query_ID in query_list:
		rank = 1
		bm25_similarity_list[query_ID] = []
		for entry in bm25_similarities(query_list[query_ID]):
			bm25_similarity_list[query_ID].append((entry[0], rank))
			rank += 1
	return bm25_similarity_list

def evaluation_results():
	print("Evaluation Results:")
	print("Precision: {0}".format(precision()), end = "\n")
	print("Recall: {0}".format(recall()), end = "\n")
	print("Mean Average Precision: {0}".format(mean_average_precision(N)), end = "\n")
	print("P@10: {0}".format(p_at_n(N)), end = "\n")
	print("NDCG@10: {0}".format(NDCG_at_n(N)), end = "\n")

def precision():
	precision = 0.0
	for query in relevance:
		appearance_times = 0
		relevance_set = set()
		for entry in relevance[query]:
			relevance_set.add(entry[0])
		for entry in bm25_similarity_list[query]:
			if entry[0] in relevance_set:
				appearance_times += 1
		precision += appearance_times / len(bm25_similarity_list[query])
	precision = precision / len(bm25_similarity_list)
	return precision

def recall():
	recall = 0.0
	for query in bm25_similarity_list:
		appearance_times = 0
		bm25_set = set()
		for entry in bm25_similarity_list[query]:
			bm25_set.add(entry[0])
		for entry in relevance[query]:
			if entry[0] in bm25_set:
				appearance_times += 1
		recall += appearance_times / len(relevance[query])
	recall = recall / len(relevance)
	return recall

def mean_average_precision(n):
	mean_average_precision = 0.0
	for query in relevance:
		appearance_times = 0
		current_map = 0.0
		map_set = set()
		for entry in relevance[query]:
			map_set.add(entry[0])
		for entry in bm25_similarity_list[query]:
			if entry[0] in map_set:
				appearance_times += 1
			current_map += appearance_times / entry[1]
		mean_average_precision += current_map / n
	mean_average_precision = mean_average_precision / len(bm25_similarity_list)
	return mean_average_precision

def p_at_n(n):
	p_at_n = 0.0
	for query in relevance:
		appearance_times = 0
		relevance_set = set()
		for entry in relevance[query]:
			relevance_set.add(entry[0])
		for entry in bm25_similarity_list[query]:
			if entry[0] in relevance_set and entry[1] < n:
				appearance_times += 1
		p_at_n += appearance_times / n
	p_at_n = p_at_n / len(bm25_similarity_list)
	return p_at_n

def NDCG_at_n(n):
	NDCG_at_n = 0.0
	return NDCG_at_n

if __name__ == "__main__":
	# These variables are accessed by functions `process_documents` and
	# `process_queries` according to LEGB rule.
	stemmer = porter.PorterStemmer()
	stop_words = load_stop_words(STOP_WORDS_PATH)
	punctuation = string.punctuation[0:12] + string.punctuation[14:]
	removing_punctuation_map = dict((ord(character), " ") for character in punctuation)
	# Remove all punctuations except full stops and hyphens.
	args = get_arguments()

	if os.path.exists(INDEX_PATH):
		print("Loading BM25 index from file; please wait.")
		with open(INDEX_PATH, "r") as fp:
			stemming, term_vectors, document_lengths = json.load(fp)
			# WARNING: JSON does not allow integer keys; key values of variable
			# loaded from .json file are `str`.
		nums_of_documents = len(document_lengths)
		# It is used in `bm25_similarities()` function.

		if args.m == "manual":
			manual_mode()
		elif args.m == "evaluation":
			query_list = process_queries(QUERY_PATH)
			relevance = make_relevance()
			bm25_similarity_list = make_evaluation()
			evaluation_results()
	else:
	# For first-time running, it creates an index .json file and quit.
		with open(INDEX_PATH, "w") as fp:
			json.dump(process_documents(DOCUMENT_PATH), fp)