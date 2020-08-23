import pathlib
import ast
import json

def merge():
    partialIndexFile = []
    buffer = {}
    done = 0
    startswith = ""
    indexforindex = {}
    seekIndex = 0

    pathlib.Path("IndexForIndex").mkdir(parents=True, exist_ok=True)

    for file in pathlib.Path("partial_index").glob("*.txt"):
        partialIndexFile.append(file.open(mode='r'))

    for i in range(len(partialIndexFile)):
        line = next(partialIndexFile[i])
        index = line.find(":")
        key = line[:index]
        value = ast.literal_eval(line[index+1:])
        if key in buffer:
            buffer[key][0].extend(value)
            buffer[key][1].append(i)
        else:
            buffer[key] = [value, [i]]

    fullInvertedIndex = pathlib.Path("InvertedIndex.txt").open(mode="w")

    while done < len(partialIndexFile):
        smallestTerm = sorted(buffer)[0]
        if smallestTerm[0] != startswith:
            if startswith:
                with pathlib.Path(f"IndexForIndex/Index{startswith}.json").open(mode="w") as f:
                    json.dump(indexforindex, f)
                print(f"Done with {startswith}")
            startswith = smallestTerm[0]
            indexforindex.clear()
        indexforindex[smallestTerm] = seekIndex
        # stringToWrite = f"{smallestTerm}:{str(sorted(buffer[smallestTerm][0]))}\n"
        stringToWrite = json.dumps({smallestTerm: sorted(buffer[smallestTerm][0])}) + "\n"
        seekIndex += (len(stringToWrite) + 1)
        fullInvertedIndex.write(stringToWrite)
        for i in buffer[smallestTerm][1]:
            try:
                line = next(partialIndexFile[i])
                index = line.find(":")
                key = line[:index]
                value = ast.literal_eval(line[index + 1:])
                if key in buffer:
                    buffer[key][0].extend(value)
                    buffer[key][1].append(i)
                else:
                    buffer[key] = (value, [i])
            except StopIteration:
                done += 1
                partialIndexFile[i].close()
        del buffer[smallestTerm]
    with pathlib.Path(f"IndexForIndex/Index{startswith}.json").open(mode="w") as f:
        json.dump(indexforindex, f)
    print(f"Done with {startswith}")
    fullInvertedIndex.close()

if __name__ == "__main__":
    merge()