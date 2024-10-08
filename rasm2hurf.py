import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense, Reshape, Lambda
from sklearn.model_selection import train_test_split
import pickle
import pandas as pd
import matplotlib.pyplot as plt

# todo
# and-or graph network (based on tabulated LCS?)
# or perhaps a leaf node is a set of path with +/-1 variation

PHI= 1.6180339887498948482 # ppl says this is a beautiful number :)

# Generate random data
np.random.seed(42)

# Parameters
num_samples = 1000
min_length= 2
max_length = 12  # Max length of the strings
num_classes = 40  # Number of classes
tokenizer = tf.keras.preprocessing.text.Tokenizer(char_level=True)

# data
source = pd.read_csv('coba.csv')
#random_strings=pd.concat([source['2bfs'], source['2alpha-bfsdfs']])
#random_labels=pd.concat([source['label'], source['label']])
random_strings=pd.concat([source['rasm']])
random_labels=pd.concat([source['val']])


# Tokenize the strings
tokenizer.fit_on_texts(random_strings)
sequences = tokenizer.texts_to_sequences(random_strings)
padded_sequences = tf.keras.preprocessing.sequence.pad_sequences(sequences, padding='post')

# Convert labels to one-hot encoding
labels = tf.keras.utils.to_categorical(random_labels, num_classes=num_classes)

# Split data into training and testing sets
train_sequences, test_sequences, train_labels, test_labels = train_test_split(
    padded_sequences, labels, test_size=0.2, random_state=38)

# Parameters for the model
vocab_size = len(tokenizer.word_index) + 1  # +1 for padding token
embedding_dim = 50  # Dimension of the embedding vector

# Define the model
model = Sequential([
    Embedding(input_dim=vocab_size, output_dim=embedding_dim, input_length=max_length),
    LSTM(64),
    Dense(64, activation='relu'),
    Dense(64, activation='relu'),
    Dense(max_length, activation='softmax'),
    Dense(num_classes, activation='sigmoid'),
    Lambda(lambda x: x * 8)            # Scale the output to range [0, 8]
])

# Compile the model
model.compile(optimizer='adam',
              loss='categorical_crossentropy',
              metrics=['accuracy'])

# Print model summary
model.summary()

# Train the model
epochs = 8000
batch_size = 32
#model.fit(train_sequences, train_labels, epochs=epochs, batch_size=batch_size, validation_split=0.2)
history = model.fit(train_sequences, train_labels, 
                    epochs=epochs, 
                    batch_size=batch_size, 
                    validation_split=0.2)

plt.plot(history.history['accuracy'], label='Training Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()


def save_variables(filename, *args):
    with open(filename, 'wb') as f:
        pickle.dump(args, f)
def load_variables(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

save_variables('rasm-lstm.model', model, train_sequences, test_sequences, train_labels, test_labels)
model, train_sequences, test_sequences, train_labels, test_labels= load_variables('rasm-lstm.model')

loss, accuracy = model.evaluate(test_sequences, test_labels)
print(f'Accuracy on test data: {accuracy}')

def predict(string):
    sequence = tokenizer.texts_to_sequences([string])
    padded_sequence = tf.keras.preprocessing.sequence.pad_sequences(sequence, maxlen=max_length, padding='post')
    evals = model.predict(padded_sequence)
    predicted_index = np.argmax(evals)
    return( predicted_index, max(max(evals)) )



# Test the prediction function
# predict("222") # alif

# the hurf lookup
hurf= [''] * 40
hurf[1]= 'ا'
hurf[2]= 'ب'
hurf[3]= 'ت'
hurf[4]= 'ة'
hurf[5]= 'ث'
hurf[6]= 'ج'
hurf[7]= 'چ'
hurf[8]= 'ح'
hurf[9]= 'خ'
hurf[10]= 'د'
hurf[11]= 'ذ'
hurf[12]= 'ر'
hurf[13]= 'ز'
hurf[14]= 'س'
hurf[15]= 'ش'
hurf[16]= 'ص'
hurf[17]= 'ض'
hurf[18]= 'ط'
hurf[19]= 'ظ'
hurf[20]= 'ع'
hurf[21]= 'غ'
hurf[22]= 'ڠ'
hurf[23]= 'ف'
hurf[24]= 'ڤ'
hurf[25]= 'ق'
hurf[26]= 'ک'
hurf[27]= 'ݢ'
hurf[28]= 'ل'
hurf[29]= 'م'
hurf[30]= 'ن'
hurf[31]= 'و'
hurf[32]= 'ۏ'
hurf[33]= 'ه'
hurf[34]= 'ء'
hurf[35]= 'ي'
hurf[36]= 'ی'
hurf[37]= 'ڽ'

# checking the weights Access the final Dense layer
weights, biases = model.layers[-2].get_weights()
for i in range(0,num_classes):
    plt.figure()
    plt.plot(weights[:,i])
    if i==0:
        label= 'space'
    else:
        label= hurf[i]
    plt.text(np.pi, 0, label, fontsize=32, ha='left', va='bottom', color='red')



def stringtorasm_LSTM(strokeorder):
    remainder_stroke= strokeorder
    rasm=''
    while len(remainder_stroke)>=2 and remainder_stroke!='':
        label_best=''
        eval_best=0
        len_best=-1
        len_current=len(remainder_stroke)
        for n in range(min_length, max_length+1):
            if n>len_current:
                break
            tee_string= remainder_stroke[0:n]
            tee_label, tee_eval= predict(tee_string)
            tee_eval *= pow(PHI, n)
            if tee_eval> eval_best:
                eval_best= tee_eval
                label_best= tee_label
                len_best= n
        hurf_best= hurf[label_best]
        rasm+= hurf_best
        if hurf_best=='ا' or hurf_best=='د' or hurf_best=='ذ' or hurf_best=='ر' or hurf_best=='ز' or hurf_best=='و':
            remainder_stroke=''
        else:
            remainder_stroke= remainder_stroke[len_best:]
        if remainder_stroke=='':
            break
    return(rasm)
        

# LCS 
def lcs_tabulate(strings):
    #print(f"len {len(strings)}")
    dict={}
    for string in strings:
        lim= len(string)
        if lim > max_length:
            lim= max_length
        for n in range(min_length, lim+1):
            if string[0:n] not in dict:
                dict[string[0:n]]=1
            else:
                dict[string[0:n]]+=1
    largest_keys = sorted(dict, key=dict.get, reverse=True)[: min_length+int(len(strings)/max_length*pow(PHI,2))]
    return(largest_keys)    


fieldstring= 'rasm'
fieldval= 'val'
LCS = [{} for _ in range(40)]
for i in range(0,40):
    LCS[i]= lcs_tabulate(source[source[fieldval] == i][fieldstring])
           
from fuzzywuzzy import fuzz
#fuzz.ratio("kitten", "sitting")  # Output: Similarity percentage Jaro-Winkler I guess

def jaro_distance(s1, s2):
    if s1 == s2:
        return 1.0

    len_s1 = len(s1)
    len_s2 = len(s2)

    max_dist = int(max(len_s1, len_s2) / 2) - 1

    match = 0

    hash_s1 = [0] * len_s1
    hash_s2 = [0] * len_s2

    for i in range(len_s1):
        for j in range(max(0, i - max_dist), min(len_s2, i + max_dist + 1)):
            if s1[i] == s2[j] and hash_s2[j] == 0:
                hash_s1[i] = 1
                hash_s2[j] = 1
                match += 1
                break

    if match == 0:
        return 0.0

    t = 0
    point = 0

    for i in range(len_s1):
        if hash_s1[i]:
            while hash_s2[point] == 0:
                point += 1
            if s1[i] != s2[point]:
                t += 1
            point += 1

    t /= 2

    return (match / len_s1 + match / len_s2 + (match - t) / match) / 3.0


def jaro_winkler_similarity(s1, s2, p=0.1):
    jaro_dist = jaro_distance(s1, s2)

    prefix = 0
    for i in range(min(len(s1), len(s2))):
        if s1[i] == s2[i]:
            prefix += 1
        else:
            break

    prefix = min(4, prefix)

    return jaro_dist + (prefix * p * (1 - jaro_dist))



def stringtorasm_LCS(strokeorder):
    remainder_stroke= strokeorder
    rasm=''
    while len(remainder_stroke)>=2 and remainder_stroke!='':
        label_best=''
        eval_best=-1
        len_best=-1
        len_current=len(remainder_stroke)
        for n in range(min_length, max_length+1):
            if n>len_current:
                break
            tee_string= remainder_stroke[0:n]
            for i in range(0, len(LCS)):
                for j in range(0, len(LCS[i])):
                    #tee_eval= fuzz.ratio(tee_string, LCS[i][j]) *pow(PHI, len(tee_string))
                    tee_eval= jaro_winkler_similarity(tee_string, LCS[i][j], 0.1) *pow(PHI, len(tee_string))
                    if tee_eval> eval_best:
                        #print(f"length:{n} class:{label_best} score:{eval_best}")
                        eval_best= tee_eval
                        label_best= i
                        len_best= n
        hurf_best= hurf[label_best]
        #print(f"BEST length:{n} class:{label_best} score:{eval_best}")
        rasm+= hurf_best
        if hurf_best=='ا' or hurf_best=='د' or hurf_best=='ذ' or hurf_best=='ر' or hurf_best=='ز' or hurf_best=='و':
            remainder_stroke=''
        else:
            remainder_stroke= remainder_stroke[len_best:]
        if remainder_stroke=='':
            break
    return(rasm)



#-------

from itertools import product
from collections import defaultdict, Counter

def lcs_multiple(strings, min_length=3):
    if not strings:
        return []

    num_strings = len(strings)
    lengths = [len(s) for s in strings]

    # Create a multi-dimensional array to store lengths of LCS and sets of LCS substrings with counts
    dp = {}
    for indices in product(*(range(length + 1) for length in lengths)):
        dp[indices] = (0, defaultdict(int))

    # Build the dp array in bottom-up fashion
    for indices in product(*(range(length + 1) for length in lengths)):
        if all(index == 0 for index in indices):
            continue

        max_length = 0
        max_subseqs = defaultdict(int)
        for i in range(num_strings):
            if indices[i] > 0:
                prev_indices = indices[:i] + (indices[i] - 1,) + indices[i + 1:]
                if dp[prev_indices][0] > max_length:
                    max_length = dp[prev_indices][0]
                    max_subseqs = dp[prev_indices][1].copy()

                elif dp[prev_indices][0] == max_length:
                    for subseq, count in dp[prev_indices][1].items():
                        max_subseqs[subseq] += count

        current_chars = [strings[i][indices[i] - 1] for i in range(num_strings) if indices[i] > 0]
        if len(current_chars) == num_strings and all(char == current_chars[0] for char in current_chars):
            prev_indices = tuple(index - 1 for index in indices)
            new_subseqs = defaultdict(int)
            for subseq, count in dp[prev_indices][1].items() or {("", 1)}:
                new_subseqs[subseq + current_chars[0]] = count

            if dp[prev_indices][0] + 1 > max_length:
                max_length = dp[prev_indices][0] + 1
                max_subseqs = new_subseqs

            elif dp[prev_indices][0] + 1 == max_length:
                for subseq, count in new_subseqs.items():
                    max_subseqs[subseq] += count

        dp[indices] = (max_length, max_subseqs)

    # Combine all substrings and their counts
    all_subseqs = Counter()
    for indices in dp:
        for subseq, count in dp[indices][1].items():
            if len(subseq) >= min_length:
                all_subseqs[subseq] += count

    # Filter out the common substrings (appear in all strings)
    common_subseqs = {subseq: count for subseq, count in all_subseqs.items() if count >= num_strings}

    if len(common_subseqs):
        # If there are common substrings, return them sorted by count (descending) and lexicographically
        return sorted(common_subseqs.items(), key=lambda x: (-x[1], x[0]))
    else:
    # If no common substring, return top 6 substrings sorted by count (descending) and lexicographically
        return sorted(all_subseqs.items(), key=lambda x: (-x[1], x[0]))[:6]


def damerau_levenshtein_freeman_distance(s1, s2):
    d = {}
    len_str1 = len(s1)
    len_str2 = len(s2)

    for i in range(-1, len_str1 + 1):
        d[(i, -1)] = i + 1
    for j in range(-1, len_str2 + 1):
        d[(-1, j)] = j + 1

    for i in range(len_str1):
        for j in range(len_str2):
            #cost = 0 if s1[i] == s2[j] else 1
            diff= abs( ord(s1[i-1])%8-ord(s2[i-1])%8 )
            if diff>4:
                diff= 8-diff
            if s1[i-1] == s2[j-1]:
                cost = 0
            elif diff==1:
                cost = 0.5
            elif diff==4:
                cost = 0.125
            else:
                cost = 1
            
            d[(i, j)] = min(
                d[(i - 1, j)] + 1,  # deletion
                d[(i, j - 1)] + 1,  # insertion
                d[(i - 1, j - 1)] + cost,  # substitution
            )
            if i > 0 and j > 0 and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                d[(i, j)] = min(d[(i, j)], d[i - 2, j - 2] + cost)  # transposition

    return d[len_str1 - 1, len_str2 - 1]


def levenshteinX_distance(s1, s2):
    # Populate the distance matrix with default values
    rows = len(s1) + 1
    cols = len(s2) + 1
    distance_matrix = [[0 for x in range(cols)] for x in range(rows)]
    for i in range(1, rows): distance_matrix[i][0] = i
    for j in range(1, cols): distance_matrix[0][j] = j

    # value assignment    
    for i in range(1, rows):
        for j in range(1, cols):
            diff= abs( ord(s1[i-1])%8-ord(s2[i-1])%8 )
            if diff>4:
                diff= 8-diff
            if s1[i-1] == s2[j-1]:
                cost = 0
            elif diff==1:
                cost = 0.5
            elif diff==4:
                cost = 0.25
            else:
                cost = 1
            distance_matrix[i][j] = min(distance_matrix[i-1][j] + 1,    # Deletion
                                        distance_matrix[i][j-1] + 1,    # Insertion
                                        distance_matrix[i-1][j-1] + cost)  # Substitution
            # may add other variants to accommodate compression

    return distance_matrix[-1][-1]

def fuzzy_substring_matching(template, long_string):
    if long_string!='':
        min_distance = float('inf')
        best_match = None
        best_start_index = -1
        len_template = len(template)
        len_long_string = len(long_string)
        
        for i in range(len_long_string - len_template + 1):
            substring = long_string[i:i + len_template]
            distance = levenshteinX_distance(template, substring) / len_template
            if distance < min_distance:
                min_distance = distance
                best_match = substring
                #best_index = i
        
        #print(f"match: {long_string[:best_index]}")
        #print(f"remainder: {long_string[best_start_index + len_template:]}")
        if best_match is not None: # and perhahps min_distance threshold too
            remainder = long_string[best_start_index + len_template:]
        else:
            remainder = ''
        return best_match, min_distance, remainder



def stringtorasm_LEV(remainder_stroke):
    rasm=''
    while len(remainder_stroke)>=3 and remainder_stroke!='':
        # find the substring with smalesst edit distance
        lev_dist_min=1e9
        hurf_min=''
        template_min=''
        remainder_min=''
        for template, data in hurf.nodes(data=True):
            if len(remainder_stroke)>=3: 
                hurf_temp, lev_dist_temp, remainder_temp= fuzzy_substring_matching(template, remainder_stroke)
                if lev_dist_temp<lev_dist_min:
                    template_min= template
                    hurf_min=data['label']
                    lev_dist_min= lev_dist_temp
                    remainder_min= remainder_temp
                    # adding rules for terminal hurf
            else:
                remainder_stroke=''
                break
        # found the best possible match
        # distance selection can be applied here
        if template_min!='':
            rasm+=hurf_min
        if hurf_min=='ا' or hurf_min=='د' or hurf_min=='ذ' or hurf_min=='ر' or hurf_min=='ز' or hurf_min=='و':
            remainder_stroke=''
        else:
            remainder_stroke= remainder_min
        #print(f"current match: {hurf_min} ({template_min}) from dist {lev_dist_min}, rasm is {rasm}, remainder is {remainder_stroke}")    





# Define the file path (replace 'your_file.txt' with your actual file name)
import sys
file_path = sys.argv[1]

with open(file_path, 'r') as file:
    # Iterate over each line in the file
    for line in file:
        #print(line, end='')  # The 'end' argument avoids adding extra newlines
        print(f"{stringtorasm_LCS(line)} ")
        

