import pandas as pd
import os
import ebooklib
from ebooklib import epub
import collections
import re
from bs4 import BeautifulSoup


# Defining necessary variables
# Corpus info from: English Fiction Version 20200217
# https://storage.googleapis.com/books/ngrams/books/20200217/eng-fiction/eng-fiction-1-ngrams_exports.html

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

def refine_corpus_data(words_data):
    standardised_words = [standardise_word(word) for word in list(words_data)]
    word_list_1_grams = [words for words in standardised_words if len(words.split()) == 1]
    word_list_2_grams = [words for words in standardised_words if len(words.split()) == 2]
    word_list_3_grams = [words for words in standardised_words if len(words.split()) == 3]
    word_n_gram_tuple = (word_list_1_grams, word_list_2_grams, word_list_3_grams)
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

def standardise_word(word):
    standard_word = word.casefold()
    standard_word = standard_word.replace("’", "'")
    if standard_word == "ain't":
        standard_word = "is not"
    elif standard_word == "can't":
        standard_word = "can not"
    elif standard_word == "shan't":
        standard_word = "shall not"
    elif standard_word == "won't":
        standard_word = "will not"
    standard_word = standard_word.replace("n't", " not")
    standard_word = standard_word.replace("'", " '")
    standard_word = standard_word.replace("-", " - ")
    return standard_word


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



# def refine_corpus_data(book_word_counts, corpus_words_df, corpus_data_filepath):
#     refined_corpus_data_filepath = 'refined_corpus_data_file'
#
#     book_word_list = [word.casefold() for word in list(book_word_counts)]
#     refined_corpus_indices = corpus_words_df.index[(corpus_words_df["Word"].str.casefold().isin(book_word_list))]
#
#     refined_corpus_words_df = corpus_words_df.iloc[refined_corpus_indices]
#
#     with open(corpus_data_filepath, 'r', encoding='utf-8') as data, open(refined_corpus_data_filepath, 'w', encoding='utf-8') as refined_data:
#         for i, line in enumerate(data):
#             if i in refined_corpus_indices:
#                 refined_data.write(line)
#
#     refined_corpus_words_df = refined_corpus_words_df.reset_index(drop=True)
#
#     return refined_corpus_words_df, refined_corpus_data_filepath

#Given a word, it first finds all the indices matching this word (case-insensitive), next it reads the data
#corresponding to each of these indices and sums the frequencies of the word from initialSearchYear to finalSearchYear.
#It returns the sum of all these frequencies
def corpus_word_freq(input_word, corpus_word_indices_df_triple):
    total_word_freq = 0
    standard_input_word = standardise_word(input_word)
    n = len(standard_input_word.split())
    if n not in [0,1,2]:
        return 0, 1
    else:
        corpus_word_indices_df = corpus_word_indices_df_triple[n-1]
        corpus_data_filepath = refined_corpus_ngram_data_file_paths[n-1]

        word_indices = corpus_word_indices_df.index[(corpus_word_indices_df["Word"].str.casefold() == standard_input_word)]
        col_names = list(range(1000))       # Creates excess columns to ensure all the data is extracted

        num_of_words = list(range(len(corpus_word_indices_df.index)))
        skip_indices = [nums for nums in num_of_words if nums not in word_indices]

        word_data = pd.read_table(corpus_data_filepath, header=None, quoting=3, names=col_names,
                                  skiprows=skip_indices, nrows=len(word_indices), index_col=0, dtype=str)
        word_data = word_data.dropna(axis=1, how='all')
        word_data = word_data.T

        for col in word_data:  #TODO rename variables
            temp_word_data = word_data[col].dropna()

            word_data_selected_years = temp_word_data[(temp_word_data.str[:4].astype(int).ge(initialSearchYear) &
                                                  temp_word_data.str[:4].astype(int).le(finalSearchYear))]
            word_freq_selected_years = word_data_selected_years.str.split(",").str[1].astype(int)
            word_freq = sum(word_freq_selected_years)
            total_word_freq += word_freq

        print("Word =", input_word, "and count =", total_word_freq)
        return total_word_freq, n

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
    book_string = ' '.join(book_string.split())
    return book_string

#Takes a list of words and outputs an ordered dictionary of the form {word: frequency}. Words (and their corresponding
# frequencies) that differ only by case are merged. The form that appears most frequently is used as the key.
def str_to_counted_data(book_string):
    word_list = re.findall(r"\b[a-zA-Z][a-zA-Z-'’]*s['’]|[a-zA-Z][a-zA-Z-'’]*\b", book_string)
    #word_list = re.findall(r"\b\w+(?:['’]\w+)*\b", string)
    #word_list = re.findall(r"\b(([a-zA-Z-'’])+s['’]|([a-zA-Z-'’])+\b)", string)
    proper_nouns = re.findall(r"(?<![.!?] )\b[A-Z][a-z'’-]*\b", book_string) #TODO can't handle words of the form "Foo-Bar"

    full_counted_words = collections.Counter(word_list)
    counted_proper_nouns = collections.Counter(proper_nouns)
    counted_proper_nouns.pop("I", None)

    filtered_counted_words = full_counted_words.copy()
    for key in counted_proper_nouns:
        filtered_counted_words[key] = full_counted_words[key] - counted_proper_nouns[key]
        if filtered_counted_words[key] == 0:
            del filtered_counted_words[key]

    #TODO figure out quote/apostrophe merging
    merged_full_counted_words = merge_word_data(full_counted_words)
    merged_filtered_counted_words = merge_word_data(filtered_counted_words)

    #potential_proper_nouns = [words for words in merged_counted_words.keys() if re.match(r"[A-Z][a-z'’-]*", words)]
    return merged_full_counted_words, merged_filtered_counted_words, counted_proper_nouns

def merge_word_data(counted_word_data):
    counted_word_data = {key: value for key, value in sorted(counted_word_data.items(), key=lambda item: item[1], reverse=True)}
    merged_words_data = {}
    temp_key_list = []
    for key in counted_word_data:
        if key.casefold() in temp_key_list:
            word_index = temp_key_list.index(key.casefold())
            word = list(merged_words_data)[word_index]
            merged_words_data[word] += counted_word_data[key]
        else:
            merged_words_data.update({key: counted_word_data[key]})
            temp_key_list.append(key.casefold())
    return merged_words_data

def create_words_df(sorted_words_data,filtered_sorted_words_data):
    corpus_words_df_list = []
    corpus_total_count_list = []
    for n in range(1,4):
        corpus_words_df_list.append(pd.read_table(refined_corpus_ngram_data_file_paths[n-1], usecols=[0], header=None, names=["Word"], quoting=3, dtype=str))
        total_counts_df = pd.read_csv("Corpus Data/Total Counts/totalcounts-" + str(n), header=None, lineterminator="\t", dtype=int,
                                                                         names=["Year", "Word_Count", "Page_Count", "Volume_Count"])
        selected_years_counts_df = total_counts_df.loc[total_counts_df["Year"].ge(initialSearchYear) &
                                                                                          total_counts_df["Year"].le(finalSearchYear), ["Year", "Word_Count"]]
        corpus_total_count_list.append(selected_years_counts_df["Word_Count"].sum())

    book_total_count = sum(list(sorted_words_data.values()))

    #print(corpus_word_indices_df.info())
    #corpus_word_indices_df, corpus_data_filepath = refine_corpus_data(sorted_words_data, corpus_word_indices_df, corpus_data_filepath)
    #print(corpus_word_indices_df.info())

    transposed_words_df_data = {}
    for word, book_freq in sorted_words_data.items():
        #book_filtered_freq =
        corpus_freq, n = corpus_word_freq(word, corpus_words_df_list)
        book_relative_freq = book_freq/book_total_count
        corpus_relative_freq = corpus_freq/corpus_total_count_list[n-1]
        relative_freq_ratio = (book_freq * corpus_total_count_list[n-1])/(corpus_freq * book_total_count)

        transposed_words_df_data.update({word: [book_freq, book_relative_freq, corpus_freq,
                                               corpus_relative_freq, relative_freq_ratio]})
        print(transposed_words_df_data[word])

    transposed_words_df = pd.DataFrame(transposed_words_df_data, index=["Book Frequency",
                                                                        "Book Relative Frequency",
                                                                        "Corpus Frequency",
                                                                        "Corpus Relative Frequency",
                                                                        "Relative Frequency Ratio"])
    words_df = transposed_words_df.T
    words_df = words_df.sort_values(by=["Relative Frequency Ratio"], ascending=False, na_position="first")
    return words_df

def df_to_excel(input_df, file_name):
    input_df.to_excel(file_name)
    print(file_name," successfully created")




def epub_to_excel(epub_filepath):
    print("Starting process")
    book_string = epub_to_str(epub_filepath)
    print("Book word list obtained")
    merged_full_counted_words, merged_filtered_counted_words, counted_proper_nouns = str_to_counted_data(book_string)
    print("Sorted word data obtained")
    refine_corpus_data(merged_full_counted_words)
    print("Corpus data refined")

    final_words_df = create_words_df(merged_full_counted_words, merged_filtered_counted_words)
    df_to_excel(final_words_df, "WordFrequencies3.xlsx")
    print(final_words_df)
    return


epub_to_excel(r"Input Documents/Waybound Cradle Book 12 Will Wight Z-Library.epub")



#TODO fix file names for excel output
#TODO Makes nice plots????

#TODO Send to multiple pages: full data, data w/out inf, data w/out inf and proper nouns (also pages to show proper nouns and inf words)
#TODO consider harsh + lenient proper noun removal
#TODO Read txt files as well as all files from a folder (web scraping?)
#TODO write 2 separate files to preprocess 2/3-grams
#TODO total counts into excel
#TODO Verify filepaths


# Alphabetically sorting keys
#key_list = list(merged_words_data.keys())  # TODO fix sort for capitals
#key_list.sort()
#partial_sorted_words_data = {key: merged_words_data[key] for key in key_list}

# Numerically sorting values
#sorted_words_data = {key: value for key, value in sorted(partial_sorted_words_data.items(),
#                                                         key=lambda item: item[1], reverse=True)}
