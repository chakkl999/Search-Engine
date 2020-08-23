from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer
import re
import pathlib
import json
from sys import getsizeof
from timeit import default_timer
from MergeIndex import merge
from urllib.parse import urlparse
import hashlib
from math import log10

def tokenize(soup: BeautifulSoup) -> list:
    token = []
    # token = word_tokenize(re.sub("^[^a-zA-Z0-9]*", "", re.sub("[^a-zA-Z0-9]*$", "", soup.get_text())))
    for t in soup.find_all(["p", "li", "label", "span", "legend", "td", "option", "b", "i", "em", "mark", "small", "a"]):
        token.extend(word_tokenize(re.sub("^[^a-zA-Z0-9]*", "", re.sub("[^a-zA-Z0-9]*$", "", t.text))))
    for t in soup.find_all(["strong", "title", re.compile("^h[1-6]$")]):
        temp = word_tokenize(re.sub("^[^a-zA-Z0-9]*", "", re.sub("[^a-zA-Z0-9]*$", "", t.text)))
        token.extend(temp * 10)
    i = 0
    finalResult = []
    while i < len(token):
        if re.match("^[^a-zA-Z0-9]+$", token[i]):
            i += 1
            continue
        if token[i] == "n't":
            finalResult.append("not")
        elif token[i] == "'ll" or token[i] == "wo":
            finalResult.append("will")
        elif token[i] == "'ve":
            finalResult.append("have")
        elif token[i] == "'re":
            finalResult.append("are")
        elif token[i] == "'s":
            finalResult.append("is")
        else:
            finalResult.append(token[i])
        i += 1
    return finalResult

def countFreq(tokens: list) -> dict:
    p = SnowballStemmer("english")
    freq = {}
    for t in tokens:
        word = p.stem(re.sub("^[^a-zA-Z0-9]*", "", re.sub("[^a-zA-Z0-9]*$", "", t)).lower())
        if isWordValid(word):
            if word not in freq:
                freq[word] = 1
            else:
                freq[word] += 1
    return freq

def dumpIndex(index: dict, partial_index: int) -> int:
    pathlib.Path("partial_index").mkdir(parents=True, exist_ok=True)
    try:
        with pathlib.Path(f"partial_index/Partial{partial_index}.txt").open(mode='w') as f:
            for key in sorted(index):
                f.write(f"{key}:{str(index[key])}\n")
    except Exception as e:
        print(f"Error in write partial index {partial_index}: {e}")
    return partial_index+1

def cleanSoup(soup):
    for s in soup.find_all("script"):
        s.decompose()
    for sidebar in soup.find_all("div", class_="grid_4 omega sidebar"):
        sidebar.decompose()
    for fragment in soup.find_all("a"):
        fragment.decompose()
    for f in soup.find_all("footer"):
        f.decompose()
    for login in soup.find_all(attrs={"id": (re.compile("login"), re.compile("fancybox"))}):
        login.decompose()

def isWordValid(word: str) -> bool:
    if re.search("[^a-z0-9\-/']+", word):
        return False
    return True

def cleanURL(url: str) -> str:
    try:
        if re.match("//.+", url):
            url = ("https:" + url)
        url = re.sub("#.*", "", url)
    except:
        pass
    return url

def isURLValid(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in set(["http", "https"]):
        return False
    if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpe?g|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|sql"
            + r"|thmx|mso|arff|rtf|jar|csv|ff"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|ipynb|war|ps.z|eps.z|h|java|py|ppsx)$", parsed.path.lower()):
        return False
    if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpe?g|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|sql"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|ipynb|war|ps.z|eps.z|h|java|py|ppsx|m|mat)$", parsed.query.lower()):
        return False
    if re.match(
            r".*/(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|raw-attachment|zip-attachment"
            + r"|thmx|mso|arff|rtf|jar|csv|~eppstein/pix|uploads|video|pub"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|ipynb)+/.*", parsed.path.lower()):
        return False
    return True

def createFingerPrint(frequency):
    size = 128
    v = [0] * size
    for key, value in frequency.items():
        hash = int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16)
        for i in range(size):
            if((hash & (1 << (size-1-i))) != 0):
                v[i] += value
            else:
                v[i] -= value
    fingerprint = 0
    for i in range(size):
        if(v[i] > 0):
            fingerprint = (fingerprint | (1 << (size-1-i)))
    return fingerprint

def compareFingerPrint(f1, f2):
    if f2 == 0:
        return 0
    similarity = [0]*128
    xor = int(bin(f1 ^ f2), 2)
    for i in range(128):
        if xor & (1 << 128-1-i) == 0:
            similarity[i] = 0
        else:
            similarity[i] = 1
    return int(similarity.count(0) / 128 * 100)

def main ():
    invertedIndex = {}
    n = 0
    partial_index = 0
    docIndex = {}
    fingerPrints = []
    CHECK_EVERY = 100
    start = default_timer()
    for f in pathlib.Path("./DEV").glob("**/*.json"):
        try:
            with f.open() as doc:
                content = json.load(doc)
                url = cleanURL(content["url"])
                if url in docIndex.values() or not isURLValid(url):
                    print(f"[Invalid] {url} is not valid or already parsed.")
                    continue
                print(f"[Info] Processing {url} - Size: {str(round(f.stat().st_size / 1024.0, 2))} KB")
                soup = BeautifulSoup(content["content"], "html.parser", from_encoding=content["encoding"])
                cleanSoup(soup)
                freq = countFreq(tokenize(soup))
                fingerPrint = createFingerPrint(freq)
                similar = False
                for f in fingerPrints:
                    if compareFingerPrint(fingerPrint, f) > 90:
                        similar = True
                        break
                if similar:
                    print(f"[Invalid] {url} has similar content as other page(s). Ignoring this page.")
                    print()
                    continue
                print()
                fingerPrints.append(fingerPrint)
                docIndex[n] = url
                for word, frequency in freq.items():
                    if word in invertedIndex:
                        invertedIndex[word].append([n, round(1+log10(frequency), 2)])
                    else:
                        invertedIndex[word] = [[n, round(1+log10(frequency), 2)]]
                if n % CHECK_EVERY == 0:
                    size = getsizeof(str(invertedIndex))
                    print(f"[Info] Size: {size}")
                    if size > 10000000:
                        print(f"[File] Dumping partial index{partial_index}.")
                        partial_index = dumpIndex(invertedIndex, partial_index)
                        invertedIndex.clear()
                    print()
                n += 1
        except Exception as e:
            print(f"Error with opening ID:{n} - {str(f.as_posix())}: {e}")
    try:
        with pathlib.Path("documentIndex.json").open(mode='w') as f:
            json.dump(docIndex, f)
    except Exception as e:
        print(f"Error in saving document index: {e}")

    print("Finished indexing, dumping the remaining index.")
    if invertedIndex:
        dumpIndex(invertedIndex, partial_index)
    total = int(default_timer() - start)
    print(f"Indexing: {int(total/60/60)} hours, {int(total/60%60)} minutes, {total%60} seconds")
    print("Merging partial index...")
    start = default_timer()
    merge()
    total = int(default_timer() - start)
    print(f"Merging: {int(total/60/60)} hours, {int(total/60%60)} minutes, {total%60} seconds")

if __name__ == "__main__":
    main()