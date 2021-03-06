import re
import signal

from searchengine import SearchEngine
from tokenstore import TokenStore


# Todo: reformat command line interface
def command_line(arg=None):
    while True:
        raw_query = input("Please type in what do you want to search: ").lower()

        if " --" in raw_query and not arg:
            raw_query, arg = raw_query.split(" --")

        query = re.sub("[^A-Za-z0-9 ]+", "", raw_query)

        if len(query) > 32:
            print("the query is too long, please shorten the search word")
        else:
            return query.split(), arg


if __name__ == '__main__':
    store = TokenStore()
    search_engine = SearchEngine(store)

    signal.signal(signal.SIGINT, lambda _s, _f: exit(0))

    while True:
        search_queries, arg = command_line()
        search_engine.search(*[search_queries, False] if arg == "all" else [search_queries])
