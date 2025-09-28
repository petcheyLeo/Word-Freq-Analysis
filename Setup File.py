import os
import requests
import gzip
import shutil
from bs4 import BeautifulSoup
import time


corpus_ngram_data_folder_paths = (r"Corpus Data/1-gram Data",
                                  r"Corpus Data/2-gram Data",
                                  r"Corpus Data/3-gram Data")
corpus_identifiers = {0: "eng", 1: "eng-us", 2: "eng-gb", 3: "eng-fiction",
                      4: "chi-sim", 5: "fre", 6: "ger", 7: "heb", 8: "ita", 9: "rus", 10: "spa"}
corpus_names = ("English", "American English", "British English", "English Fiction",
                "Chinese (simplified)", "French", "German", "Hebrew", "Italian", "Russian", "Spanish")

def create_file_structure(corpus_name):
    if not os.path.exists("Input Documents"):
        os.mkdir("Input Documents")
    if not os.path.exists("Output Documents"):
        os.mkdir("Output Documents")
    subfolder_path = os.path.join("Corpus Data", corpus_name)
    subfolder_names = ["1-gram Data", "2-gram Data", "3-gram Data", "Refined Data", "Total Counts"]
    for subfolder_name in subfolder_names:
        os.makedirs(os.path.join(subfolder_path, subfolder_name), exist_ok=True)

def download_file(url, folder_path):
    local_filename = url.split('/')[-1]
    filepath = os.path.join(folder_path, local_filename)
    with requests.get(url, stream=True) as r:
        with open(filepath, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    return filepath

def download_file2(url):
    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        with open(local_filename, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=1024):
                fd.write(chunk)
    return local_filename

def extract_gz_file(filepath):
    new_filepath = filepath.replace(".gz", "")
    with gzip.open(filepath, 'rb') as f_in:
        with open(new_filepath, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(filepath)
    return new_filepath

def filter_data(filepath, filter_type):
    local_filename = filepath.split('\\')[-1]
    output_folder_path = os.path.dirname(filepath)
    output_filepath = os.path.join(output_folder_path, "processed_" + str(local_filename))
    with open(filepath, 'r', encoding='utf-8') as data:
        with open(output_filepath, 'w', encoding='utf-8') as refined_data:
            for line in data:
                word = " ".join(line.split()[:filter_type])
                if filter_type == 1 and condition_1_gram(word):
                    refined_data.write(line)
                elif filter_type == 2 and condition_2_gram(word):
                    refined_data.write(line)
                elif filter_type == 3 and condition_3_gram(word):
                    refined_data.write(line)
    return output_filepath

#TODO run condition 1 on english words text file to find problems
#TODO "shouldn't've is a 1-gram?"
def condition_1_gram(word): #TODO issues with Mc and change .islower to .lower ==
    if word.isalpha():
        if word.islower() or word.istitle() or word.isupper():
            return True
    return False

def condition_2_gram(word):
    split_word = word.split()
    if len(split_word) == 2:
        if split_word[1].casefold() == "not":       # Words of the form "____ not"
            if split_word[0].isalpha():
                if word.islower() or word.isupper():
                    return True
                elif split_word[0].istitle() and split_word[1].islower():
                    return True

        elif split_word[1].startswith("'"):       # Words of the form "____ '___"
            if split_word[0].isalpha():
                if split_word[1][1:].isalpha() or split_word[1] == "'":
                    if word.islower() or word.isupper() or word.istitle():
                        return True
                    elif split_word[0].istitle() and split_word[1].islower():
                        return True
    return False

def condition_3_gram(word): #TODO allow not as final word I'mn't
    split_word = word.split()
    if len(split_word) == 3:
        if split_word[1] == "-":  # Words of the form "____ - ____"
            if split_word[2].isalpha() and split_word[0].isalpha():
                if word.islower() or word.isupper() or word.istitle():
                    return True
                elif split_word[0].istitle() and split_word[2].islower():
                    return True

        elif split_word[1].casefold() == "not" and split_word[2].startswith("'"):  # Words of the form "____ not '___"
            if split_word[0].isalpha() and split_word[2][1:].isalpha():
                if word.islower() or word.isupper():
                    return True
                elif split_word[0].istitle() and split_word[1].islower() and split_word[2].islower():
                    return True

        elif split_word[1].startswith("'") and split_word[2].startswith("'"):  # Words of the form "____ '___ '___"
            if split_word[0].isalpha():
                if split_word[2][1:].isalpha() or split_word[2] == "'":
                    if split_word[1][1:].isalpha():
                        if word.islower() or word.isupper():
                            return True
                        elif split_word[0].istitle():
                            if split_word[1].istitle() or split_word[1].islower():
                                if split_word[2].istitle() or split_word[2].islower():
                                    return True
    return False





    # elif split_word[0].isalpha() is not True:
    #     return False
    # if split_word[1][0] == "'" or split_word[1].casefold() == "not":
    #     if word.islower():
    #         return True #TODO no need to string slice
    #     elif split_word[0].istitle() and (split_word[1].islower() or (split_word[1][0] == "'" and split_word[1][1:].istitle())):
    #         return True
    #     elif word.isupper():
    #         return True
    #     return False

def download_2020_corpus(corpus_index):
    corpus_identifier = corpus_identifiers[corpus_index]
    corpus_name = corpus_names[corpus_index]
    create_file_structure(corpus_name)
    for n in range(1,4):
        print(f"Obtaining {n}-gram data \n")
        url = (r"http://storage.googleapis.com/books/ngrams/books/20200217/" + str(corpus_identifier)
               + r"/" + str(corpus_identifier) + "-" + str(n) + r"-ngrams_exports.html")
        page = requests.get(url).text
        soup = BeautifulSoup(page, 'html.parser')
        count_links = [node.get('href') for node in soup.find_all('a') if "totalcount" in node.get('href')]
        word_links = [node.get('href') for node in soup.find_all('a') if node.get('href').endswith('gz')]
        num_of_files = len(word_links)


        folder_path = os.path.join("Corpus Data", str(corpus_name))
        download_file(count_links[0],os.path.join(folder_path,"Total Counts"))

        corpus_folder_path = os.path.join(folder_path, str(n) + "-gram Data")
        for counter, link in enumerate(word_links):
            print(f"Downloading file {counter+1} of {num_of_files}")
            start1 = time.time()

            filepath = download_file(link, corpus_folder_path)

            end1 = time.time()
            time_taken1 = end1 - start1
            print(f"Download time was {time_taken1} seconds \n")

            print(f"Extracting {filepath.split('\\')[-1]}")
            start2 = time.time()

            extracted_filepath = extract_gz_file(filepath)

            end2 = time.time()
            time_taken2 = end2 - start2
            print(f"Extraction time was {time_taken2} seconds \n")

            print(f"Processing {extracted_filepath.split('\\')[-1]}")
            start3 = time.time()

            processed_filepath = filter_data(extracted_filepath, n)

            end3 = time.time()
            time_taken3 = end3 - start3
            print(f"Processing time was {time_taken3} seconds \n")
            os.remove(extracted_filepath)
            if os.path.getsize(processed_filepath) == 0:
                os.remove(processed_filepath)
            print(f"Total time taken was {time_taken1 + time_taken2 + time_taken3} seconds \n")



corpus_choice = -1
print("Corpus data available:")
for i in corpus_identifiers:
    print(f"{i}: {corpus_names[i]}")
while corpus_choice not in corpus_identifiers.keys():
    corpus_choice = input("Please enter the number corresponding to the corpus that you would like to download \n")
    try:
        corpus_choice = int(corpus_choice)
        if corpus_choice < min(corpus_identifiers.keys()) or corpus_choice > max(corpus_identifiers.keys()):
            print("Please ensure you enter an integer from 0 to 10 \n")
    except:
        print("Please ensure you enter an integer \n")


#download_file(,r"Corpus Data\1-gram Data")
download_2020_corpus(corpus_choice)


# def download_extract_gz(url):
#     local_filename = url.split('/')[-1]
#     new_filename = local_filename.replace(".gz", "Test")
#     with urllib.request.urlopen(url) as response:
#         with gzip.GzipFile(fileobj=response) as uncompressed:
#             file_content = uncompressed.read()
#
#         # write to file in binary mode 'wb'
#     with open(new_filename, 'wb') as f:
#         f.write(file_content)
#     return new_filename


# def filter_data_2(filename, filter_type):
#     print(f"Processing {filename}")
#     output_folder_path = corpus_ngram_data_folder_paths[filter_type - 1]
#     output_filepath = os.path.join(output_folder_path, "processed_" + str(filename) + "_2")
#
#     words_df = pd.read_table(filename, usecols=[0], header=None, names=["Word"], quoting=3, dtype=str)
#     with open(filename, 'r', encoding='utf-8') as data:
#         with open(output_filepath, 'w', encoding='utf-8') as refined_data:
#             if filter_type == 1:
#                 indices = words_df.index[(words_df["Word"].apply(lambda x: condition_1_gram(str(x))))]
#                 for i, line in enumerate(data):
#                     if i in indices:
#                         refined_data.write(line)
#             elif filter_type == 2:
#                 indices = words_df.index[(words_df["Word"].apply(lambda x: condition_2_gram(str(x))))]
#                 for i, line in enumerate(data):
#                     if i in indices:
#                         refined_data.write(line)
#             elif filter_type == 3:
#                 indices = words_df.index[(words_df["Word"].apply(lambda x: condition_3_gram(str(x))))]
#                 for i, line in enumerate(data):
#                     if i in indices:
#                         refined_data.write(line)






# start1 = time.time()
# file = download_file1(r"http://storage.googleapis.com/books/ngrams/books/20200217/eng-fiction/3-00002-of-00549.gz")
# end1 = time.time()
# print(end1 - start1)
#
# start2 = time.time()
# extracted_filename = extract_gz_file(file)
# end2 = time.time()
# print(end2 - start2)
#
# os.remove(file)
# os.remove(extracted_filename)

# start3 = time.time()
# file = download_extract_gz(r"http://storage.googleapis.com/books/ngrams/books/20200217/eng-fiction/3-00002-of-00549.gz")
# end3 = time.time()
# print(end3 - start3)
# #
# start4 = time.time()
# extracted_filename = extract_gz_file(file)
# end4 = time.time()
# print(end4 - start4)
#
# os.remove(file)
# os.remove(extracted_filename)



# _2gram_data_folderpath = r"C:\Users\petch\PycharmProjects\WordFreqAnalysis\2-gram_data"
# apostrophe_data_filepath = "2-gram_apostrophe_data"
#
# folder = os.scandir(_2gram_data_folderpath)
#
# for file in folder:
#     print(file.name)
#     counter = 0
#     with (open(os.path.join(_2gram_data_folderpath, file), 'r', encoding='utf-8') as data,
#           open(apostrophe_data_filepath, 'a', encoding='utf-8') as refined_data):
#         for line in data:
#             words = line.split()
#             if words[1].startswith("'") :
#                 refined_data.write(line)
#                 counter += 1
#     print("Number of apostrophe words =", counter)




#test_file = r"2-00035-of-00047"
test_file = r"1-00000-of-00001"

# start1 = time.time()
# filter_data(test_file, 1)
# end1 = time.time()
# print(end1 - start1)






