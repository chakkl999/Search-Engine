from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer
from nltk.corpus import stopwords
import pathlib
import json
import timeit
import re
import cosinesimilarity
import tfidf
import sys

def getInput() -> str:
    return str(input("Search: "))

def getFirstDocID(posting: dict) -> int:
    return next(iter(posting))

def convertToList(posting: str) -> list:
    return list(json.loads(posting).values())[0]

def separateIntoDict(userInput: list) -> dict:
    temp = {}
    stopword = set(stopwords.words("english"))
    numOfStopword = 0
    for word in userInput:
        if word in stopword:
            numOfStopword += 1
    stop = numOfStopword/len(userInput) < 0.3
    for q in userInput:
        if stop:
            if q in stopword:
                continue
        if q[0] in temp:
            if q not in temp[q[0]]:
                temp[q[0]][q] = 1
            else:
                temp[q[0]][q] += 1
        else:
            temp[q[0]] = {q: 1}
    return temp

def getPosting(InvertedIndex, IndexForIndex, query: dict) -> dict:
    wordPosting = {}
    df = {}
    for startChar, queryDict in query.items():
        index = json.load(IndexForIndex[startChar])
        IndexForIndex[startChar].seek(0)
        for word in queryDict.keys():
            seekIndex = index.get(word, -1)
            if seekIndex < 0:
                wordPosting[word] = []
                continue
            InvertedIndex.seek(seekIndex)
            line = InvertedIndex.readline()
            wordPosting[word] = convertToList(line)
            df[word] = len(wordPosting[word])
    return wordPosting, df

def findIntersection(posting: dict) -> dict:
    buffer = {}
    result = {}
    lowestDocID = []
    for post in posting.values():
        try:
            lowestDocID.append(post[-1][0])
        except:
            return None
    lowestDocID = min(lowestDocID)
    x = iter(posting)
    for i in range(len(posting)):
        nextTerm = next(x)
        while True:
            try:
                p = posting[nextTerm].pop(0)
                if p[0] > lowestDocID:
                    break
                if p[0] in buffer:
                    buffer[p[0]].append((nextTerm, p[1]))
                else:
                    buffer[p[0]] = [(nextTerm, p[1])]
            except IndexError:
                break
    numTerm = len(posting)
    for docID, post in buffer.items():
        if len(post) == numTerm:
            for word, df in post:
                if word in result:
                    result[word].append((docID, df))
                else:
                    result[word] = [(docID, df)]
    return result

def reorderResult(query: dict, result: list) -> list:
    temp = {}
    stem = SnowballStemmer("english")
    delimiter = re.compile("[^a-zA-Z0-9]")
    for link in result:
        matching = 0
        linkList = list(map(stem.stem, delimiter.split(link.lower())))
        for wordList in query.values():
            for word in wordList:
                if word in linkList:
                    matching += 1
        if matching in temp:
            temp[matching].append(link)
        else:
            temp[matching] = [link]
    returnResult = []
    for num in sorted(temp, reverse=True):
        returnResult.extend(temp[num])
    return returnResult

def getNumQuery(query: dict) -> int:
    num = 0
    for querydict in query.values():
        for query in querydict.values():
            num += query
    return num

def search(docIndex: dict, InvertedIndex, IndexForIndex, n = 10) -> bool:
    stem = SnowballStemmer("english")
    userQuery = getInput()
    if not userQuery:
        return False
    start = timeit.default_timer()
    originalQuery = [query.lower() for query in word_tokenize(userQuery) if not re.search("[^a-zA-Z0-9\-/']", query)]
    if not originalQuery:
        print("Invalid input.")
        print()
        return True
    userInput = sorted([stem.stem(query) for query in originalQuery])
    query = separateIntoDict(userInput)
    posting, df = getPosting(InvertedIndex, IndexForIndex, query)
    intersection = findIntersection(posting)
    if not intersection:
        print(f"Took {int((timeit.default_timer() - start) * 1000)} ms")
        print("Cannot find any page(s) with provided query.")
        print()
        return True
    if getNumQuery(query) > 1:
        topDoc = cosinesimilarity.getTopXDoc(docIndex, intersection, df, query, n)
    else:
        topDoc = tfidf.getTopXDoc(docIndex, intersection, df, n)
    topDoc = reorderResult(query, topDoc)
    print(f"Took {int((timeit.default_timer() - start) * 1000)} ms")
    for i in range(len(topDoc)):
        print(f"{i+1}. {topDoc[i]}")
    print()
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
            if(n < 1):
                print("Please enter a number greater than 0, defaulting to 10.")
                n = 10
        except:
            print("Error in getting the argument, defaulting to 10.")
            print("Format: python3 search.py [number of result]")
            n = 10
    else:
        print("No argument provided, defaulting to 10 results.")
        print("Format: python3 search.py [number of result]")
        n = 10
    print(f"Displaying {n} result(s).")
    InvertedIndex = pathlib.Path("InvertedIndex.txt").open(mode="r")
    with pathlib.Path("documentIndex.json").open(mode="r") as f:
        docIndex = json.load(f)
    IndexForIndex = {}
    for index in pathlib.Path("IndexForIndex").glob("*.json"):
        IndexForIndex[str(index)[-6:-5]] = index.open(mode="r")
    continues = search(docIndex, InvertedIndex, IndexForIndex, n)
    while continues:
        continues = search(docIndex, InvertedIndex, IndexForIndex)
    InvertedIndex.close()
    for file in IndexForIndex.values():
        file.close()

