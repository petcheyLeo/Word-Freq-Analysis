import re
import os
import requests
from bs4 import BeautifulSoup




items = ['apple', 'red', 'apple', 'red', 'red', 'pear', 'Capital', 'They\'re', 'half-hearted', 'Half-hearted', 'they\'re', 'I', 'I\'m', 'can\'t' ]


counts = dict()
for i in items:
    #print("i is :", i)
    #print("counts.get(i, 0) is:", counts.get(i, 0))
    #print("counts[i] is :", counts[i])
    counts[i] = counts.get(i, 0) + 1
    #print("counts is :", counts)


#    val_based_rev = {k: v for k, v in sorted(d.items(), key=lambda item: item[1], reverse=True)}



print(counts)
key_list = list(counts.keys())
potential_proper_nouns = [words for words in counts.keys() if re.match(r"[A-Z][a-z'’-]*", words)]
print("Potential proper nouns", potential_proper_nouns)


print(key_list)
key_list = [words.replace("’", "'") for words in key_list]
print(key_list)
key_list = [words.replace("n't", " not") for words in key_list]
print(key_list)
key_list = [words.replace("'", " '") for words in key_list]
print(key_list)
key_list = [words.replace("-", " - ") for words in key_list]
print(key_list)


with open(r"Corpus Data\Refined Data\refined_corpus_data_file", 'r') as f:
    print(f.readline())


folder = os.scandir(r"Corpus Data\Total Counts")
url = r"http://storage.googleapis.com/books/ngrams/books/20200217/eng-fiction/eng-fiction-3-ngrams_exports.html"
page = requests.get(url).text


soup = BeautifulSoup(page, 'html.parser')

links = [url + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith('gz')]

print(links)

print(os.path.join("", "corpus data"))

#html = BeautifulSoup(content.get_body_content(), "html.parser")
#print(html)

test = ["dog"]

print(test[0])



