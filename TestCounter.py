
items = ['apple', 'red', 'apple', 'red', 'red', 'pear']


counts = dict()
for i in items:
    print("i is :", i)
    print("counts.get(i, 0) is:", counts.get(i, 0))
    #print("counts[i] is :", counts[i])
    counts[i] = counts.get(i, 0) + 1
    print("counts is :", counts)


    val_based_rev = {k: v for k, v in sorted(d.items(), key=lambda item: item[1], reverse=True)}

