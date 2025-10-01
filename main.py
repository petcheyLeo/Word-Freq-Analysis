import pandas as pd
import os
import ebooklib
from ebooklib import epub
import collections
import re
from bs4 import BeautifulSoup
import numpy as np
import time
from pathlib import Path

from ebooklib.utils import debug
# Defining necessary variables
# Corpus info from: English Fiction Version 20200217
# https://storage.googleapis.com/books/ngrams/books/20200217/eng-fiction/eng-fiction-1-ngrams_exports.html

#TODO create with loop
corpus_ngram_data_folder_paths = (r"Corpus Data/1-gram Data",
                                  r"Corpus Data/2-gram Data",
                                  r"Corpus Data/3-gram Data")
refined_corpus_ngram_data_file_paths = (r"Corpus Data/Refined Data/refined 1-gram data file",
                                        r"Corpus Data/Refined Data/refined 2-gram data file",
                                        r"Corpus Data/Refined Data/refined 3-gram data file")
corpus_counts_path = r"Corpus Data/Total Counts"
epub_path = r"Input Documents"
initialSearchYear = 2010
finalSearchYear = 2019

# Opens an epub file and returns the text from each chapter as a single string
def epub_to_str(epub_filepath):
    book = ebooklib.epub.read_epub(epub_filepath)
    chapter_strings = []
    for chapter in book.get_items_of_type(ebooklib.ITEM_DOCUMENT): #TODO Identify chapters better
        html = BeautifulSoup(chapter.get_body_content(), "html.parser")
        text = [paragraph.get_text() for paragraph in html.find_all("p")]
        string = ' '.join(text)
        chapter_strings.append(string)
    book_string = ' '.join(chapter_strings)
    book_string = ' '.join(book_string.split())         # Removes any double spaces or other whitespace characters
    return book_string

# Takes a string of words and outputs a dictionary of the form {word: frequency}. The dictionary is case-insensitive and
# the frequencies for all the cases are summed. The form that appears most frequently is used as the key
def str_to_counted_data(string):
    word_list = re.findall(r"\b[a-zA-Z][a-zA-Z-'’]*s['’]|[a-zA-Z][a-zA-Z-'’]*\b", string)
    #word_list = re.findall(r"\b\w+(?:['’]\w+)*\b", string)
    #word_list = re.findall(r"\b(([a-zA-Z-'’])+s['’]|([a-zA-Z-'’])+\b)", string)
    proper_nouns = re.findall(r"(?<![.!?] )\b[A-Z][a-z'’-]*\b", string) #TODO can't handle words of the form "Foo-Bar", Dr.

    full_word_freqs = collections.Counter(word_list)
    proper_noun_freqs = collections.Counter(proper_nouns)
    proper_noun_freqs.pop("I", None)

    filtered_word_freqs = full_word_freqs.copy()
    for word in proper_noun_freqs:
        filtered_word_freqs[word] = full_word_freqs[word] - proper_noun_freqs[word]
        if filtered_word_freqs[word] == 0:
            del filtered_word_freqs[word]

    #TODO figure out quote/apostrophe merging
    merged_full_word_freqs = merge_dict(full_word_freqs)
    merged_filtered_word_freqs = merge_dict(filtered_word_freqs)

    #potential_proper_nouns = [words for words in merged_counted_words.keys() if re.match(r"[A-Z][a-z'’-]*", words)]
    # TODO consider harsh + lenient proper noun removal
    return merged_full_word_freqs, merged_filtered_word_freqs, proper_noun_freqs

# Takes a dictionary (of the form {word: frequency}) and then sums the values of keys which differ by only case.
# The key in the output is determined by the most frequent form
def merge_dict(word_freqs):
    word_freqs = {word: freq for word, freq in sorted(word_freqs.items(), key=lambda item: item[1], reverse=True)}
    merged_word_freqs = {}
    temp_word_list = []
    for word in word_freqs:
        if word.casefold() in temp_word_list:
            word_index = temp_word_list.index(word.casefold())
            case_variant = list(merged_word_freqs)[word_index]
            merged_word_freqs[case_variant] += word_freqs[word]
        else:
            merged_word_freqs.update({word: word_freqs[word]})
            temp_word_list.append(word.casefold())
    return merged_word_freqs

# Takes a word as an input and puts it into a "standardised form" to help search for it within the corpus data
def standardise_word(word):
    standard_word = str(word).casefold()
    standard_word = standard_word.replace("’", "'")
    if standard_word == "ain't":
        standard_word = "is not"
    elif standard_word == "can't" or standard_word == "cannot":
        standard_word = "can not"
    elif standard_word == "shan't":
        standard_word = "shall not"
    elif standard_word == "won't":
        standard_word = "will not"
    standard_word = standard_word.replace("n't", " not")
    standard_word = standard_word.replace("'", " '") #TODO "o'clock" is not separated
    standard_word = standard_word.replace("-", " - ")
    standard_word = " ".join(standard_word.split())
    return standard_word

# Takes a dataframe of corpus data (with tabs as the separators) and outputs the total word frequencies for all the
# words between the selected years (inclusive)
def get_corpus_freqs(corpus_df, initial_year, final_year):
    corpus_df = corpus_df.T
    corpus_df[1:] = corpus_df[1:].map(extract_freq, initial_year=initial_year, final_year=final_year, na_action="ignore")

    words_series = corpus_df.iloc[0]
    summed_freqs = corpus_df[1:].sum(axis=0)

    word_freqs_df = pd.concat([words_series, summed_freqs], axis=1)
    word_freqs_df.columns = ["Standard Word", "Corpus Frequency"]
    word_freqs_df["Standard Word"] = word_freqs_df["Standard Word"].map(lambda word: standardise_word(word))
    word_freqs_df = word_freqs_df.groupby(["Standard Word"], as_index=False).sum()
    return word_freqs_df

# Takes a non-word entry from the corpus data and if this entry was between the initial and finals years (inclusive),
# then it returns the frequency from this entry
def extract_freq(data_entry, initial_year, final_year):
    year = data_entry[:4]
    if initial_year <= int(year) <= final_year:
        return int(data_entry.split(",")[1])
    else:
        return np.nan

# Takes a filepath for corpus data and a list/set/dict of words. It finds the sum of the frequencies,
# between the given years, for all of these words that appear in the file (case-insensitive). It outputs
# a dataframe with columns "Standard Word", "Corpus Freq"
def refine_corpus_file_data(filepath, word_list, initial_year, final_year):
    standard_word_set = set([standardise_word(word) for word in word_list])
    diff = collections.Counter([standardise_word(word) for word in word_list]) #TODO can't and cannot

    # Initially, we only look at the words that appear in the file to identify which rows contain useful information
    corpus_words_df = pd.read_table(filepath, usecols=[0], names=["Word"], header=None,     #TODO store as own file?
                                    quoting=3, keep_default_na=False, dtype=str)
    corpus_words_df["Word"] = corpus_words_df["Word"].map(lambda word: standardise_word(word))
    indices = corpus_words_df.index[(corpus_words_df["Word"].isin(standard_word_set))]
    num_of_words = corpus_words_df.size
    skip_indices = [int(nums) for nums in list(range(num_of_words)) if nums not in indices]

    col_names = list(range(600))        # Creates excess rows to ensure all data is collected from the file
    refined_corpus_df = pd.read_table(filepath, header=None, names=col_names,
                                      skiprows=skip_indices, nrows=num_of_words, dtype=str)
    word_freqs_df = get_corpus_freqs(refined_corpus_df, initial_year, final_year)
    return word_freqs_df

def create_words_df(full_merged_word_freqs, filtered_merged_word_freqs, proper_nouns, initial_year, final_year):
    corpus_n_gram_word_freqs = []
    corpus_total_count_list = []
    for n in range(1,4):
        total_counts_filepath = "Corpus Data/Total Counts/totalcounts-" + str(n)
        total_counts_df = pd.read_csv(total_counts_filepath, header=None, lineterminator="\t", dtype=int,
                                      names=["Year", "Word_Count", "Page_Count", "Volume_Count"])
        selected_counts_df = total_counts_df.loc[total_counts_df["Year"].ge(initialSearchYear) &
                                                 total_counts_df["Year"].le(finalSearchYear), ["Year", "Word_Count"]]
        total_count_n_grams = selected_counts_df["Word_Count"].sum()
        corpus_total_count_list.append(total_count_n_grams)

        corpus_n_gram_folder_path = "Corpus Data/" + str(n) + "-gram Data"
        folder = os.scandir(corpus_n_gram_folder_path)
        temp_corpus_n_gram_word_freqs = []
        for file in folder:
            partial_corpus_n_gram_word_freq = refine_corpus_file_data(file, full_merged_word_freqs, initial_year, final_year)
            temp_corpus_n_gram_word_freqs.append(partial_corpus_n_gram_word_freq)
        corpus_n_gram_word_freq = pd.concat(temp_corpus_n_gram_word_freqs, axis=0, ignore_index=True)
        corpus_n_gram_word_freq = corpus_n_gram_word_freq.groupby(["Standard Word"], as_index=False).sum()
        corpus_n_gram_word_freq["Corpus Relative Frequency"] =(corpus_n_gram_word_freq["Corpus Frequency"]*1_000_000)/int(total_count_n_grams)
        corpus_n_gram_word_freqs.append(corpus_n_gram_word_freq)
        print(f"{n}-gram frequencies obtained")

    total_count_book = sum(list(full_merged_word_freqs.values()))

    corpus_word_freqs = pd.concat(corpus_n_gram_word_freqs, axis=0, ignore_index=True)
    corpus_word_freqs = corpus_word_freqs.sort_values(by="Corpus Relative Frequency", ascending=False,
                                                      na_position='last').drop_duplicates(["Standard Word"])

    book_freqs = pd.DataFrame(full_merged_word_freqs, index = ["Book Frequency"]).T
    book_freqs = book_freqs.reset_index()
    book_freqs = book_freqs.rename(columns={"index": "Word"})
    book_freqs.insert(2, "Book Relative Frequency", book_freqs["Book Frequency"].map(lambda freq: (int(freq)*1_000_000)/int(total_count_book)))
    book_freqs.insert(0, "Standard Word", book_freqs["Word"].map(lambda word: standardise_word(word)))
    words_df = book_freqs.set_index("Standard Word").join(corpus_word_freqs.set_index("Standard Word"))     #TODO manually set nan to 0 and inf
    words_df["Relative Frequency Ratio"] = words_df["Book Relative Frequency"] / words_df["Corpus Relative Frequency"]
    words_df = words_df.sort_values(by=["Relative Frequency Ratio", "Word"], ascending=[False, True], na_position="first")
    words_df[["Corpus Frequency", "Corpus Relative Frequency"]] = words_df[["Corpus Frequency", "Corpus Relative Frequency"]].astype(float).fillna(0)

    proper_col_names = {"Book Relative Frequency": "Book Relative Frequency \n(Average occurrences per million words)",
                        "Corpus Relative Frequency": "Corpus Relative Frequency \n(Average occurrences per million words)"}
    words_df = words_df.rename(columns=proper_col_names)
    words_df = words_df.set_index("Word", drop=True)

    # transposed_words_df_data = {}
    # for word, book_freq in full_merged_word_freqs.items():
    #     #book_filtered_freq =
    #     corpus_freq, n, times = corpus_word_freq(word, corpus_words_series_list)
    #     book_relative_freq = book_freq/book_total_count
    #     corpus_relative_freq = corpus_freq/corpus_total_count_list[n-1]
    #     relative_freq_ratio = (book_freq * corpus_total_count_list[n-1])/(corpus_freq * book_total_count)
    #
    #     transposed_words_df_data.update({word: [book_freq, book_relative_freq, corpus_freq,
    #                                            corpus_relative_freq, relative_freq_ratio]})
    #
    #
    # transposed_words_df = pd.DataFrame(transposed_words_df_data, index=["Book Frequency",
    #                                                                     "Book Relative Frequency",
    #                                                                     "Corpus Frequency",
    #                                                                     "Corpus Relative Frequency",
    #                                                                     "Relative Frequency Ratio"])
    # words_df = transposed_words_df.T
    # words_df = words_df.sort_values(by=["Relative Frequency Ratio"], ascending=False, na_position="first")
    return words_df

def df_to_excel(input_df, file_name):
    input_df.to_excel(os.path.join("Output Documents",file_name))
    print(file_name,"successfully created")

def epub_to_excel(epub_filepath):
    print("Obtaining book word list")
    book_string = epub_to_str(epub_filepath)
    print("Obtaining book frequencies")
    merged_full_word_freqs, merged_filtered_word_freqs, proper_noun_freqs = str_to_counted_data(book_string)
    print("Obtaining corpus frequencies")
    words_df = create_words_df(merged_full_word_freqs, merged_filtered_word_freqs, proper_noun_freqs,initialSearchYear, finalSearchYear)
    print("Creating Excel data sheet")
    epub_file_name = Path(epub_filepath).name.removesuffix(".epub")
    df_to_excel(words_df, str(epub_file_name) + " Word Frequencies.xlsx")
    return




def refine_corpus_data(words_data):
    standardised_words = [standardise_word(word) for word in list(words_data)]
    word_list_1_grams = [words for words in standardised_words if len(words.split()) == 1]
    word_list_2_grams = [words for words in standardised_words if len(words.split()) == 2]
    word_list_3_grams = [words for words in standardised_words if len(words.split()) == 3]
    word_n_gram_tuple = (set(word_list_1_grams), set(word_list_2_grams), set(word_list_3_grams))
    for n in range(1,4):
        refine_data_in_folder(word_n_gram_tuple[n-1], n)
        print(f"Refined corpus {n}-gram data")
    return

def refine_data_in_folder(word_list, n_value):
    folder_path = corpus_ngram_data_folder_paths[n_value - 1]
    refined_file_path = refined_corpus_ngram_data_file_paths[n_value - 1]
    if os.path.exists(refined_file_path):
        os.remove(refined_file_path)
    folder = os.scandir(folder_path)
    for file in folder:
        words_df = pd.read_table(file, usecols=[0], header=None, names=["Word"], quoting=3, dtype=str)
        refined_corpus_indices = words_df.index[(words_df["Word"].str.casefold().isin(word_list))]

        with open(file, 'r', encoding='utf-8') as data, open(refined_file_path, 'a', encoding='utf-8') as refined_data:
            for i, line in enumerate(data):
                if i in refined_corpus_indices:
                    refined_data.write(line)
        #
        #     refined_corpus_words_df = refined_corpus_words_df.reset_index(drop=True)
        #
        #     return refined_corpus_words_df, refined_corpus_data_filepath




        # with (open(file, 'r', encoding='utf-8') as data,
        #       open(refined_file_path, 'a', encoding='utf-8') as refined_data):
        #     counter = 0
        #     for line in data:
        #         print(f"Line number {counter}")
        #         word = line.split()[:n_value]
        #         word = [word_part.casefold for word_part in word]
        #         if word in words_list:
        #             refined_data.write(line)
        #         counter += 1


    return

# def get_corpus_data(corpus_data_filepath, corpus_count_filepath):
#     # Assigns an index to each word in the data, allows us to find the position of words in the full dataframe while being
#     # much smaller than the full dataframe
#     corpus_words_df = pd.read_table(corpus_data_filepath, usecols=[0], header=None, names=["Word"], quoting=3, dtype=str)
#     #TODO possibly change quote character to quotechar='\x07'
#
#     # Reads the total counts data and find the total number of words that appeared from initialSearchYear to finalSearchYear
#     total_counts_df = pd.read_csv(corpus_count_filepath, header=None, lineterminator="\t", dtype=int,
#                                   names=["Year", "Word_Count", "Page_Count", "Volume_Count"])
#     selected_years_counts_df = total_counts_df.loc[total_counts_df["Year"].ge(initialSearchYear) &
#                                                    total_counts_df["Year"].le(finalSearchYear), ["Year", "Word_Count"]]
#     total_count_value = selected_years_counts_df["Word_Count"].sum()
#     return corpus_words_df, total_count_value
#



#Given a word, it first finds all the indices matching this word (case-insensitive), next it reads the data
#corresponding to each of these indices and sums the frequencies of the word from initialSearchYear to finalSearchYear.
#It returns the sum of all these frequencies
def corpus_word_freq(input_word, corpus_word_indices_series_triple):
    time_setup = 0
    time_search = 0
    time_read = 0
    time_extract = 0

    start_setup = time.time()
    total_word_freq = 0
    standard_input_word = standardise_word(input_word)
    n = len(standard_input_word.split())
    end_setup = time.time()
    time_setup = end_setup - start_setup
    if n not in [1, 2, 3]:
        return 0, 1
    else:
        start_search = time.time()

        corpus_word_indices_series = corpus_word_indices_series_triple[n - 1]
        corpus_data_filepath = refined_corpus_ngram_data_file_paths[n-1]


        lower_series_location = corpus_word_indices_series.searchsorted(standard_input_word, side='left')
        upper_series_location = corpus_word_indices_series.searchsorted(standard_input_word, side='right')

        word_indices = corpus_word_indices_series.index[lower_series_location:upper_series_location]
        col_names = list(range(600))       # Creates excess columns to ensure all the data is extracted

        num_of_words = list(range(corpus_word_indices_series.size))
        skip_indices = [nums for nums in num_of_words if nums not in word_indices]

        end_search = time.time()
        time_search = end_search - start_search
        start_read = time.time()

        word_data = pd.read_table(corpus_data_filepath, header=None, names=col_names,
                                  skiprows=skip_indices, nrows=len(word_indices), index_col=0, dtype=str)

        end_read = time.time()
        time_read = end_read - start_read

        word_data = word_data.dropna(axis=1, how='all')
        word_data = word_data.set_index(np.arange(word_data.shape[0]))
        word_data = word_data.T



        start_extract = time.time()

        for col in word_data:
            temp_word_data = word_data[col].dropna()

            word_data_selected_years = temp_word_data[(temp_word_data.str[:4].astype(int).ge(initialSearchYear) &
                                                  temp_word_data.str[:4].astype(int).le(finalSearchYear))]
            word_freq_selected_years = word_data_selected_years.str.split(",").str[1].astype(int)
            word_freq = sum(word_freq_selected_years)
            total_word_freq += word_freq

        print("Word =", input_word, "and count =", total_word_freq)

        end_extract = time.time()
        time_extract = end_extract - start_extract
        times = (time_setup, time_search, time_read, time_extract)
        return total_word_freq, n, times












# def epub_to_excel(epub_filepath):
#     print("Starting process")
#     book_string = epub_to_str(epub_filepath)
#     print("Book word list obtained")
#     merged_full_counted_words, merged_filtered_counted_words, counted_proper_nouns = str_to_counted_data(book_string)
#     print("Sorted word data obtained")
#     start = time.time()
#     refine_corpus_data(merged_full_counted_words)
#     end = time.time()
#     print(f"Corpus data refined, {end - start} seconds taken")
#     #final_words_df = create_words_df(merged_full_counted_words, merged_filtered_counted_words)
#     #df_to_excel(final_words_df, "WordFrequenciesFull.xlsx")
#     #print(final_words_df)
#     return

epub_filepath = r"Input Documents/Cradle-Waybound.epub"

epub_to_excel(epub_filepath)


# epub_filepath = r"Input Documents/Waybound Cradle Book 12 Will Wight Z-Library.epub"
#
# start = time.time()
# book_string = epub_to_str(epub_filepath)
# end = time.time()
# print(f"Epub to str, {end - start} seconds taken")
#
# start = time.time()
# merged_full_counted_words, merged_filtered_counted_words, counted_proper_nouns = str_to_counted_data(book_string)
# end = time.time()
# print(f"Words merged, {end - start} seconds taken")
#
# words_set = set(merged_full_counted_words)
#
# col_names = list(range(600))
# start = time.time()
# corpus_df = pd.read_table(r"Corpus Data/1-gram Data/processed_1-00000-of-00001", usecols=[0], names=["Word"], header=None, quoting=3, keep_default_na=False, dtype=str)
# corpus_df["Word"] = corpus_df["Word"].map(lambda word: standardise_word(word))
#
# end = time.time()
# print(f"Corpus data opened, {end - start} seconds taken")
# start = time.time()
#
# indices = corpus_df.index[(corpus_df["Word"].isin(words_set))]
# end = time.time()
# print(f"Indices found, {end - start} seconds taken")
# start = time.time()
#
# num_of_words = list(range(len(indices)))
# skip_indices = [nums for nums in num_of_words if nums not in indices]
#
# word_data = pd.read_table(r"Corpus Data/1-gram Data/processed_1-00000-of-00001", header=None, names=col_names,
#                           skiprows=skip_indices, nrows=len(indices), index_col=0, dtype=str)
# end = time.time()
# print(f"Necessary data opened, {end - start} seconds taken")
#
#
# start = time.time()
#
# word_data = word_data.T
# word_data[1:] = word_data[1:].map(extract_freq, initial_year=2010, final_year=2019, na_action="ignore")
# words_df = word_data.iloc[0]
# words_df = words_df.apply(lambda x: standardise_word(x))
# sums = word_data[1:].sum(axis=0)
# new_df = pd.concat([words_df, sums], axis=1)
# new_df.columns = ["Words", "Total Freq"]
# new_df = new_df.groupby(["Words"])["Total Freq"].sum()
# end = time.time()
# print(f"Data processed, {end - start} seconds taken")



#TODO List of most frequent words that don't appear in text, get words from corpus data using dictionary file,
# preprocess to remove case variants by grouping by word and extracting (year, freq, books) from each cell.
# Store col 0 as separate file as well
#TODO Calculate the average number of times a word appears in a book, given that it is in the book.
# Combine with relative freq ratio to get an "overuse" indicator
#TODO fix file names for excel output
#TODO Makes nice plots????
#TODO Send to multiple pages: full data, data w/out inf, data w/out inf and proper nouns (also pages to show proper nouns and inf words)
#TODO Read txt files as well as all files from a folder (web scraping?)
#TODO total counts into excel
#TODO Verify filepaths


# Alphabetically sorting keys
#key_list = list(merged_words_data.keys())  # TODO fix sort for capitals
#key_list.sort()
#partial_sorted_words_data = {key: merged_words_data[key] for key in key_list}

# Numerically sorting values
#sorted_words_data = {key: value for key, value in sorted(partial_sorted_words_data.items(),
#                                                         key=lambda item: item[1], reverse=True)}
