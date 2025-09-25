import os
#import gzip
#import shutil
#with gzip.open('file.txt.gz', 'rb') as f_in:
#    with open('file.txt', 'wb') as f_out:
#        shutil.copyfileobj(f_in, f_out)

_2gram_data_folderpath = r"C:\Users\petch\PycharmProjects\WordFreqAnalysis\2-gram_data"
apostrophe_data_filepath = "2-gram_apostrophe_data"

folder = os.scandir(_2gram_data_folderpath)

for file in folder:
    print(file.name)
    counter = 0
    with (open(os.path.join(_2gram_data_folderpath, file), 'r', encoding='utf-8') as data,
          open(apostrophe_data_filepath, 'a', encoding='utf-8') as refined_data):
        for line in data:
            words = line.split()
            if words[1].startswith("'") :
                refined_data.write(line)
                counter += 1
    print("Number of apostrophe words =", counter)








