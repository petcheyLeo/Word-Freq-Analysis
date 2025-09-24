import pandas as pd
import csv



#csv.field_size_limit(2147483647)


corpusDataFilepath = "1-00000-of-00001"
#word_indices_df = pd.read_table(corpusDataFilepath, header=None,  quotechar='\x07', usecols=[0], nrows=138918)
#print(word_indices_df)

row_index = [3,6]
break_index = max(row_index) + 1




#corpus_words_df = pd.read_table("1-00000-of-00001", usecols=[0], header=None, names=["Word"], quoting=csv.QUOTE_NONE, dtype=str)

num_lines = 4608325
print(num_lines)

to_exclude = [i for i in range(num_lines) if i not in row_index]


#for chunk in pd.read_table("1-00000-of-00001", header=None, quoting=csv.QUOTE_NONE, dtype=str, chunksize=1, iterator=True):
#    if get_chunk(chunk) in row_index:
#        good_data.to_csv("data_out.csv", sep='\t', mode="a", header = False, index = False)


with open(corpusDataFilepath, 'r', encoding='utf-8') as data:
    with open('EBSD_data_filtered', 'w') as outfile:
        for i, line in enumerate(data):
            if i in row_index:
                outfile.write(line)
                print("Nice")
