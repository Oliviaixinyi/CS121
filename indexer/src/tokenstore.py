import math
from collections import Generator

from redis import Redis

from job import Job
from poolqueue import PoolQueue


class TokenStore:

    @staticmethod
    def decode(s):
        return s.decode('utf-8')

    def __init__(self, prefix='t'):
        self._prefix = prefix
        self._redis = Redis(host='127.0.0.1', port=6379, db=0)

    def store_token(self, token: str, page: str, amount=1) -> None:
        """
        push the token, page to redis with the amount
        :param token: a word from the document
        :param page: path + url of the document
        :param amount: the times of that token showed in the document
        :return: None or RuntimeError if not pushed successfully
        """
        if not self._redis.zincrby(self.prefixed(token), page, amount=amount):
            raise RuntimeError("Error: Failed to storeIndex(token: {}, page: {})!".format(token, page))

    def tokens(self) -> Generator:
        """
        :return: Generator of all tokens saved in the redis
        """
        return (self.decode(x) for x in self._redis.scan_iter(self.prefixed("*")))

    def token_occurrence_pairs(self):
        for token in self.tokens():
            yield token, map(lambda x: (self.decode(x[0]), x[1]),
                             self._redis.zrange(token, 0, -1, withscores=True))

    def prefixed(self, token: str) -> str:
        """
        prefix token with the format of self._prefix:token
        :param token: a word from the document
        :return: formatted token string
        """
        return "{}:{}".format(self._prefix, token)

    def get_tokens_on_page(self, page: str) -> Generator:
        """
        :param page: path + url of the document
        :return: Generator of all tokens of the page saved in the redis
        """
        return (key for key, val in self.token_occurrence_pairs() if str(page) in map(lambda x: x[0], val))

    def occurrences(self) -> Generator:
        return (list(pair[1]) for pair in self.token_occurrence_pairs())

    def pages_count(self, token: str) -> int:
        """
        :param token: a word from the document
        :return:
        """
        return self._redis.zcard(self.prefixed(token))

    def tf(self, token: str, page: str) -> float:
        """
        :param token: a word from the document
        :param page: path + url of the document
        :return: tf value(term frequency) of the specific token in the specific document
        """
        return int(self._redis.zscore(self.prefixed(token), page))

    def idf(self, token: str) -> float:
        """
        :param token: a word from the document
        :return: idf(inverse document frequency) value of the specific token
        """
        return math.log10(self.get_document_count() / self.pages_count(token))

    def increment_document_count(self) -> None:
        """
        increment the total number of documents stored in the database
        """
        self._redis.incr("document_count")

    def get_document_count(self) -> int:
        """
        :return: the number of the documents stored in the databse
        """
        return int(self._redis.get("document_count") or 0)

    def zrevrange(self, token: str) -> list:
        """
        :param token: a word from the document
        :return: a list of urls contains the specific token and sorted by the token's occurenece
        """
        return self._redis.zrevrange(self.prefixed(token), 0, -1, withscores=True)

    def deduplicate(self) -> None:
        """
        delete unfinished documents from _redis to prevent duplications.
        :return: None
        """
        print("Searching for unfinished jobs...")
        active_jobs = list(map(Job.bytes_to_job, self._redis.lrange(PoolQueue.ACTIVE, 0, -1)))
        if not active_jobs:
            print("No unfinished jobs!")
            return
        pipeline = self._redis.pipeline()
        self.delete_pages((job.path for job in active_jobs), pipeline)

        for _ in active_jobs:
            self._redis.rpoplpush(PoolQueue.ACTIVE, PoolQueue.IDLE)
        self._redis.delete(PoolQueue.ACTIVE)
        pipeline.execute()
        print("Done deduplicating.")

    def delete_pages(self, pages: Generator, pipeline):
        """
        delete unfinished pages
        :param pages:
        :param pipeline:
        :return:
        """
        for token in self.tokens():
            for page in pages:
                print("deleting", page)
                pipeline.zrem(token, page)

    def get_idle(self):
        return self._redis.lrange(PoolQueue.IDLE, 0, -1)

    def tf_idf(self, token: str, page: str) -> float:
        return (1 + math.log10(self.tf(token, page))) * self.idf(token)
