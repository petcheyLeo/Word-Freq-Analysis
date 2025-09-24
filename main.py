import pandas as pd
import csv
import ebooklib
from ebooklib import epub
import collections
import re
from bs4 import BeautifulSoup


#Defining necessary variables
#Corpus info from https://storage.googleapis.com/books/ngrams/books/20200217/eng-fiction/eng-fiction-1-ngrams_exports.html
corpusDataFilepath = "1-00000-of-00001"
corpusCountFilepath = "totalcounts-1"
epubFilepath1 = "short_fiction_story.epub"
epubFilepath2 = "Waybound Cradle Book 12 Will Wight Z-Library.epub"
epubFilepath3 = "pg76268-images-3.epub"
initialSearchYear = 2010
finalSearchYear = 2019


def get_corpus_data(corpus_data_filepath, corpus_count_filepath):
    # Assigns an index to each word in the data, allows us to find the position of words in the full dataframe while being
    # much smaller than the full dataframe
    corpus_words_df = pd.read_table(corpus_data_filepath, usecols=[0], header=None, names=["Word"], quoting=3, dtype=str)
    #TODO possibly change quote character to quotechar='\x07'

    # Reads the total counts data and find the total number of words that appeared from initialSearchYear to finalSearchYear
    total_counts_df = pd.read_csv(corpus_count_filepath, header=None, lineterminator="\t", dtype=int,
                                  names=["Year", "Word_Count", "Page_Count", "Volume_Count"])
    selected_years_counts_df = total_counts_df.loc[total_counts_df["Year"].ge(initialSearchYear) &
                                                   total_counts_df["Year"].le(finalSearchYear), ["Year", "Word_Count"]]
    total_count_value = selected_years_counts_df["Word_Count"].sum()
    return corpus_words_df, total_count_value


def refine_corpus_data(book_word_counts, corpus_words_df, corpus_data_filepath):
    refined_corpus_data_filepath = 'refined_corpus_data_file'

    book_word_list = [word.casefold() for word in list(book_word_counts)]
    refined_corpus_indices = corpus_words_df.index[(corpus_words_df["Word"].str.casefold().isin(book_word_list))]

    refined_corpus_words_df = corpus_words_df.iloc[refined_corpus_indices]

    with open(corpus_data_filepath, 'r', encoding='utf-8') as data, open(refined_corpus_data_filepath, 'w', encoding='utf-8') as refined_data:
        for i, line in enumerate(data):
            if i in refined_corpus_indices:
                refined_data.write(line)

    refined_corpus_words_df = refined_corpus_words_df.reset_index(drop=True)

    return refined_corpus_words_df, refined_corpus_data_filepath

#Given a word, it first finds all the indices matching this word (case-insensitive), next it reads the data
#corresponding to each of these indices and sums the frequencies of the word from initialSearchYear to finalSearchYear.
#It returns the sum of all these frequencies
def corpus_word_freq(input_word, corpus_word_indices_df, corpus_data_filepath):
    total_word_freq = 0
    word_indices = corpus_word_indices_df.index[(corpus_word_indices_df["Word"].str.casefold() == input_word.casefold())]
    for word_index in word_indices: #TODO Try to do without a loop (add 1k names, then remove excess cols?)
        word_data = pd.read_table(corpus_data_filepath, header=None, quoting=csv.QUOTE_NONE,
                                  skiprows=word_index, nrows=1, index_col=0, dtype=str)
        word_data = word_data.iloc[0]
        word_data_selected_years = word_data[(word_data.str[:4].astype(int).ge(initialSearchYear) &
                                              word_data.str[:4].astype(int).le(finalSearchYear))]
        word_freq_selected_years = word_data_selected_years.str.split(",").str[1].astype(int)
        word_freq = sum(word_freq_selected_years)
        print("Index =", word_index,"and word =", corpus_word_indices_df.loc[word_index,"Word"], "and count =", word_freq)
        total_word_freq += word_freq
    return total_word_freq

def chapter_to_word_list(chapter):
    #chapter to string
    html = BeautifulSoup(chapter.get_body_content(), "html.parser")
    text = [paragraph.get_text() for paragraph in html.find_all("p")]
    string = ' '.join(text)
    # test line

    #string to word list (removes punctuation other than apostrophes)
    #word_list = re.findall(r"\b\w+(?:['’]\w+)*\b", string)

    #word_list = re.findall(r"\b(([a-zA-Z-'’])+s['’]|([a-zA-Z-'’])+\b)", string)
    word_list = re.findall(r"\b[a-zA-Z][a-zA-Z-'’]*s['’]|[a-zA-Z][a-zA-Z-'’]*\b", string)
    return word_list

#Opens an epub file and returns a list contain all the words from each chapter
def read_epub(epub_filepath):
    book = ebooklib.epub.read_epub(epub_filepath)
    book_word_list = []
    for chapter in book.get_items_of_type(ebooklib.ITEM_DOCUMENT): #TODO Identify chapters better
        book_word_list += chapter_to_word_list(chapter)
    return book_word_list

#Takes a list of words and outputs an ordered dictionary of the form {word: frequency}. Words (and their corresponding
# frequencies) that differ only by case are merged. The form that appears most frequently is used as the key.
def count_words(book_word_list):
    initial_words_data = collections.Counter(book_word_list)
    merged_words_data = {}
    temp_key_list = []
    for key in initial_words_data:
        if key.casefold() in temp_key_list:
            word_index = temp_key_list.index(key.casefold())
            word = list(merged_words_data)[word_index]
            merged_words_data[word] += initial_words_data[key]
        else:
            merged_words_data.update({key: initial_words_data[key]})
            temp_key_list.append(key.casefold())
    #Alphabetically sorting keys
    key_list = list(merged_words_data.keys())      #TODO fix sort for capitals
    key_list.sort()
    partial_sorted_words_data = {key: merged_words_data[key] for key in key_list}

    #Numerically sorting values
    sorted_words_data = {key: value for key, value in sorted(partial_sorted_words_data.items(),
                                                             key=lambda item: item[1], reverse=True)}
    return sorted_words_data






def create_words_df(sorted_words_data, corpus_data_filepath, corpus_counts_filepath):
    corpus_word_indices_df, corpus_total_count = get_corpus_data(corpus_data_filepath, corpus_counts_filepath)
    print("Corpus data obtained")
    book_total_count = sum(list(sorted_words_data.values()))

    print(corpus_word_indices_df.info())
    corpus_word_indices_df, corpus_data_filepath = refine_corpus_data(sorted_words_data, corpus_word_indices_df, corpus_data_filepath)
    print(corpus_word_indices_df.info())

#DoN'T has index 138917


    transposed_words_df_data = {}
    for key, value in sorted_words_data.items():
        print(key)
        corpus_freq = corpus_word_freq(key, corpus_word_indices_df, corpus_data_filepath)
        book_relative_freq = value/book_total_count
        corpus_relative_freq = corpus_freq/corpus_total_count
        relative_freq_ratio = (value * corpus_total_count)/(corpus_freq * book_total_count)

        transposed_words_df_data.update({key: [value, book_relative_freq, corpus_freq,
                                               corpus_relative_freq, relative_freq_ratio]})
        print(transposed_words_df_data[key])

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




def epub_to_excel(epub_filepath, corpus_data_filepath, corpus_counts_filepath):
    print("Starting process")
    book_word_list = read_epub(epub_filepath)
    print("Book word list obtained")
    sorted_words_data = count_words(book_word_list)
    print("Sorted word data obtained")

    final_words_df = create_words_df(sorted_words_data, corpus_data_filepath, corpus_counts_filepath)
    df_to_excel(final_words_df, "WordFrequencies2.xlsx")
    print(final_words_df)
    return
#

def better_epub_to_excel(epub_filepath):
    book_text = epub_to_text(epub_filepath)
    book_word_list = text_to_word_list(book_text)
    sorted_words_data = count_words(book_word_list)

    final_words_df = create_words_df(sorted_words_data)
    #df_to_excel(final_words_df, "WordFrequencies2.xlsx")
    print(final_words_df)
    return

#corpusWordIndices, corpusTotalCountValue = get_corpus_data("1-00000-of-00001", "totalcounts-1")
#corpus_word_freq("don't", corpusWordIndices)


epub_to_excel(epubFilepath2, corpusDataFilepath, corpusCountFilepath)

#TODO fix file names for excel output and data files



#TODO Makes nice plots????

#TODO Send to multiple pages: full data, data w/out inf, data w/out inf and proper nouns (also pages to show proper nouns and inf words)
#TODO identify proper noun if they only occur capitalised
#TODO Read txt files as well as all files from a folder (web scraping?)
#TODO handle corpus data bigger than 1 file
#TODO words with apostrophes from 2-grams and hyphenated words from 3 grams
#TODO write 2 separate files to preprocess 2/3-grams
#TODO total counts into excel
#TODO Filepaths as inputs
#TODO Verify filepaths



