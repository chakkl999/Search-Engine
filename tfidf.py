from math import log10, sqrt

def getTopXDoc(docIndex: dict, posting: dict, df: dict, n: int) -> list:
    print("Using tf-idf")
    topn = {}
    numOfDoc = len(docIndex)
    for word, post in posting.items():
        for doc in post:
            tfidf = doc[1]*log10(numOfDoc/df[word])
            if doc[0] in topn:
                topn[doc[0]].append(tfidf)
            else:
                topn[doc[0]] = [tfidf]
    for doc, tfidf in topn.items():
        topn[doc] = sum(topn[doc])
    topn = sorted(topn.items(), key=lambda items: items[1], reverse=True)
    x = iter(topn)
    topnDocID = []
    for i in range(n):
        try:
            topnDocID.append(next(x))
        except StopIteration:
            break
    return [docIndex[str(docId[0])] for docId in topnDocID]
