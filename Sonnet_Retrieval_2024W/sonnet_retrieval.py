import json
import requests
import os
import re
from porter_stemmer import PorterStemmer


# Part 1: get Shakespeare's sonnets
def load_sonnets(file_name):
    if not os.path.exists(file_name):
        response = requests.get('https://poetrydb.org/author,title/Shakespeare;Sonnet')
        if response.status_code == 200:
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(response.text)
            print(f"Sonnets stored in file: {file_name}")
            return json.loads(response.text)
        else:
            print("Failed to fetch sonnets")
            return []
    else:
        with open(file_name, "r", encoding="utf-8") as file:
            return json.load(file)


# Part 6a: add Document class
class Document:
    stemmer = PorterStemmer()
    def __init__(self, lines: list[str]):
        self.lines = lines

    # Part 3+4: add tokenize method with option to stemming
    def tokenize(self, use_stemming: bool = True) -> list[str]:     # refactored: moved tokenize method to new parent class Document for consistent tokenizing (Sonnet & Query) +set default to True
        """
        Tokenizes the sonnet text, optionally applying stemming with the Porter Stemmer.
        :param use_stemming: Whether to apply Porter Stemming to the tokens.
        :return: List of tokens (stemmed if stemming=True).
        """
        tokens = []
        for line in self.lines:
            clean_line = re.sub(r"[.,':;!?]", "", line).lower()     # remove punctuation and split by whitespace
            tokens.extend(clean_line.split())

        if use_stemming:
            tokens = [self.stemmer.stem(token, 0, len(token) - 1) for token in tokens]       # 0 starting index; len(token -1) end index

        return tokens


# Part 2: convert list of dictionaries to a list of Sonnet instances
class Sonnet(Document):
    def __init__(self, sonnet):
        super().__init__(sonnet["lines"])       # refactored: pass lines to parent class
        self.id = int(sonnet["title"].split(':')[0].split()[-1])
        self.title = sonnet["title"].split(': ')[1]

    def __repr__(self):
        joined_lines = '\n  '.join(self.lines)
        return f"Sonnet {self.id}: {self.title}\n  {joined_lines}\n"

    def __str__(self):
        return self.__repr__()


# Part 6b: add Query class
class Query(Document):
    def __init__(self, query: str):
        super().__init__([query])       # pass a single query string as a list of one line: (lines = [query]) --> compatible with class Document


# Part 5: create the inverted index
class Index(dict[str, set[int]]):
    def __init__(self, documents: list[Sonnet]):
        super().__init__()
        self.documents = documents

        for document in documents:
            self.add(document)

    def add(self, document: Sonnet):
        for token in document.tokenize():
            if token not in self:
                self[token] = set()
            self[token].add(document.id)

    # Part 7: add search method to Index class
    def search(self, query: Query) -> list[Sonnet]:
        """
        Search for sonnets matching the given query.
        :param query: Query object containing the search text.
        :return: List of matching Sonnet objects, sorted by ID.
        """
        query_tokens = query.tokenize()
        if not query_tokens:
            return []       # no valid tokens in the query

        # gather sets of document IDs for each token that exists in the index
        relevant_tokens = [self[token] for token in query_tokens if token in self]
        if not relevant_tokens:
            return []       # none of the tokens extracted from the query exist in the inverted index

        # check if all tokens in the query exist in the index
        if len(relevant_tokens) < len(query_tokens):
            return []       # if any token is missing, return no results

        # find the intersection of sets for all tokens
        matching_ids = set.intersection(*relevant_tokens)

        # convert matching IDs to Sonnet objects and return them sorted by ID
        matching_sonnets = [doc for doc in self.documents if doc.id in matching_ids]
        return sorted(matching_sonnets, key=lambda x: x.id)     # using key=lambda to avoid need for __lt__ method


# Part 8: add user interface
def user_interface(index: Index):
    while True:
        user_input = input("Search for sonnets (enter 'q' to quit): ").strip()
        if user_input == 'q':
            print("Quitting search")
            break
        query = Query(user_input)
        matching_sonnets = index.search(query)

        if not matching_sonnets:
            print(f"No sonnets found for query: \"{user_input}\"")
        else:
            print(
                f"Your search for \"{user_input}\" matched {len(matching_sonnets)} sonnets ({", ".join(str(sonnet.id) for sonnet in matching_sonnets)}): ")
            print("\n".join(str(sonnet) for sonnet in matching_sonnets))


def main():
    file_name = "json_sonnets.json"
    sonnets = load_sonnets(file_name)

    print("Reading sonnets...")
    if not sonnets:
        print("No sonnets found.")
        return

    sonnet_instances = [Sonnet(sonnet) for sonnet in sonnets]
    index = Index(sonnet_instances)
    user_interface(index)


if __name__ == "__main__":
    main()

# ################# Test Section #################
# file_name = "json_sonnets.json"
# sonnets = load_sonnets(file_name)
#
# if not sonnets:
#     print("Failed to load sonnets. Exiting...")
#     exit()
#
# # instantiate Sonnet class for all elements
# sonnet_instances = [Sonnet(sonnet) for sonnet in sonnets]
# print(len(sonnet_instances))
#
# # instantiate Index class with all sonnet_instances
# index = Index(sonnet_instances)
#
# # print varieties of sonnet #32
# print(sonnet_instances[31])
# print(sonnet_instances[31].tokenize(use_stemming=False))
# print(sonnet_instances[31].tokenize())
#
# # test .search method
# query_1 = Query("love hate")
# matching_sonnets_1 = index.search(query_1)
#
# if not matching_sonnets_1:
#     print(f"No matching sonnets found for query: \"{query_1.lines[0]}\"")
# else:
#     print(f"Sonnets matching query \"{query_1.lines[0]}\":")
#     for sonnet in matching_sonnets_1:
#         print(f"Sonnet {sonnet.id}: {sonnet.title}")
#
# # debug: (example Sonnet 1)
# print("Sonnet tokens (stemmed):", sonnet_instances[0].tokenize(use_stemming=True))      # example sonnet tokens
# query_2 = Query("creatures")        # example query tokens
# query_tokens_2 = query_2.tokenize(use_stemming=True)
# print("Query tokens (stemmed):", query_tokens_2)
# # observation: stemmed sonnet tokens and stemmed query tokens identical :)
# ################################################