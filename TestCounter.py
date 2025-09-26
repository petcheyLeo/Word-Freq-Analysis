import re
import os




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

for file in folder:
    print(file)

x1 = 2
x2 = 3
x3 = 7


for n in range(1,4):
    print(n)

test = "aAbt't-rw’f G"
print(test.casefold().split())
print(type("bob".split()))


list1 = [1,2,4]
list2 = [1,2,4]

print(list1 == list2)

def add(a,b):
    result = int(a)+int(b)
    return result

print(add(1,1))

Fun = (add(1,2), add(4,7))
print(Fun)

n = 5

print("Bob" + str(n+1))

dictionary = {"Car": "Broken", "Age": 10}
for key in dictionary.keys():
    print(key)

k = "Don't"
k = k.replace("D","W")
print(k)






