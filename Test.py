import pandas as pd
import csv



csv.field_size_limit(2147483647)


corpusDataFilepath = "1-00000-of-00001"
word_indices_df = pd.read_table(corpusDataFilepath, header=None,  quotechar='\x07', usecols=[0], nrows=138918)
print(word_indices_df)

row_index = [2,4,6]
break_index = max(row_index) + 1

with open(corpusDataFilepath, 'r', encoding='utf-8') as f,open('betterData', 'w') as f_out:
    reader = csv.reader(f)
    writer = csv.writer(f_out)
    for i, row in enumerate(reader, start=0):
        if i in row_index:
            writer.writerows(row)
        elif i >= break_index:
            break


