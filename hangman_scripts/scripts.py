import math
from collections import defaultdict
import numpy as np

################################################################################
# Checks if the given string matches the filter. █ represents wildcard char.   #
################################################################################
def matchesFilter(str, filter, used_letters):
    if len(str) != len(filter): return False
    
    for letter in used_letters:
        if letter in filter: continue
        if letter in str: return False
    
    for i in range(len(str)):
        if filter[i] == "█": 
            if str[i] in used_letters: return False
            continue
        
        if filter[i] != str[i]: return False
    return True

################################################################################
# Returns a filtered list of all viable words given a wordlist and used chars. #
################################################################################
def getFilteredList(filter, wordlist, used_letters):
    return [word for word in wordlist if matchesFilter(word, filter, used_letters)]
    
################################################################################
# Retrieves the entropy of a list. filtered_list is a probability array.       #
################################################################################
def getEntropy(filtered_list):
    entropy = 0
    total = 0

    for freq in filtered_list:
        if freq != 0:
            entropy -= freq * math.log2(freq)
            total += freq
    if total == 0:
        print("Impossible sequence found.")
        return 0
    entropy /= total
    entropy += math.log2(total)

    return entropy

################################################################################
# Calculates the entropy of wordlist with respective probability array p.      #
################################################################################
def calculate(filter, wordlist, used_letters, p):

    # calculate the current entropy of all possible items
    currentEntropy = getEntropy(p)

    alphabetList = defaultdict(lambda: defaultdict(lambda: 0))
    entropyList = defaultdict(lambda: defaultdict(lambda: 0))
    infoList = defaultdict(lambda: currentEntropy)
    
    # sum up frequencies
    for i in range(len(wordlist)):
        
        k = wordlist[i]
        v = p[i]
        
        if v == 0: continue
        # iterate through only unique characters
        for letter in set(k):
            # calculate the filter for that letter
            pattern = ''.join([letter if letter == otherLetter else "█" for otherLetter in k])

            # add the frequency value to this pattern to find total.
            alphabetList[letter][pattern] += v

            # initial calculation. need to divide by total and add log of total.
            entropyList[letter][pattern] -= v * math.log2(v)

    for letter, dictionary in alphabetList.items():

        if letter in used_letters: continue

        # sum of the totals for the letter
        total = sum(dictionary.values())

        expected_present_entropy = 0

        for pattern, freq in dictionary.items():
            if freq == 0: continue
            # completes the entropy calculation.
            entropyList[letter][pattern] /= freq
            entropyList[letter][pattern] += math.log2(freq)
            expected_present_entropy += freq / total * entropyList[letter][pattern]

        # we've found expected entropy if the letter exists, now we must consider if it does not
        temp_used_letters = used_letters + [letter]
        absent_filtered_list = getFilteredList(filter, wordlist, temp_used_letters)
        ap = np.zeros((len(absent_filtered_list)), dtype=float)
        
        count = 0
        for i in range(len(wordlist)):
            if wordlist[i] in absent_filtered_list:
                ap[count] = p[i]
                count += 1
        ap /= sum(ap)

        expected_absent_entropy = 0
        if absent_filtered_list:
            expected_absent_entropy = getEntropy(ap)

        # set the values for expected information gained
        infoList[letter] -= expected_present_entropy * total + expected_absent_entropy * (1 - total)

    return infoList