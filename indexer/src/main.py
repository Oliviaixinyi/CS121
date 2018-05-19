from indexer import Indexer
from searchengine import SearchEngine
from tokenstore import TokenStore
import re

def command_line():
    command = input("Please type in what do you want to search: ").lower()
    command = re.sub("[^A-Za-z0-9]+","",command)
    valid = False
    while valid != True:
        if len(command) > 32:
            print("the query is too long, please shorten the search word")
        else:
            valid = True
    return command

if __name__ == '__main__':
    store = TokenStore()
    indexer = Indexer(store)

    book_file = open("WEBPAGES_RAW/bookkeeping.json")
    #indexer.run(book_file)

    search_engine = SearchEngine(store)
    search_query = command_line()

    search_engine.show_search(search_query)
