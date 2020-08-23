from math import log10, sqrt

def getNormalizedQueryWeight(numOfDoc: int, df: dict, query: dict) -> dict:
    normalize = 0
    weight = {}
    for queryDict in query.values():
        for word, wt in queryDict.items():
            weight[word] = (1+log10(wt))*log10(numOfDoc/df[word])
            normalize += weight[word]**2
    normalize = sqrt(normalize)
    for word in weight.keys():
        weight[word] = weight[word]/normalize
    return weight

def getTopXDoc(docIndex: dict, posting: dict, df: dict, query: dict, n: int) -> list:
    print("Using cosine similarity.")
    topn = {}
    query = getNormalizedQueryWeight(len(docIndex), df, query)
    normalize = {}
    for word, post in posting.items():
        for doc in post:
            if doc[0] in topn:
                normalize[doc[0]] += (doc[1]**2)
                topn[doc[0]].append([word, doc[1]])
            else:
                normalize[doc[0]] = doc[1]**2
                topn[doc[0]] = [[word, doc[1]]]
    for doc, tfidf in normalize.items():
        normalize[doc] = sqrt(tfidf)
    for doc, tfidf in topn.items():
        score = 0
        for word, wt in tfidf:
            score += ((wt/normalize[doc]) * query[word])
        topn[doc] = score
    topn = sorted(topn.items(), key=lambda items: items[1], reverse=True)
    x = iter(topn)
    topnDocID = []
    for i in range(n):
        try:
            topnDocID.append(next(x))
        except StopIteration:
            break
    return [docIndex[str(docId[0])] for docId in topnDocID]