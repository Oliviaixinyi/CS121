import threading

import redis

from job import Job


class PoolQueue:
    IDLE = 'idle'
    ACTIVE = 'active'

    def __init__(self, rhost='127.0.0.1', rport=6379, rdb=0, token_store=None):
        self._redis = redis.Redis(host=rhost, port=rport, db=rdb, decode_responses=True)
        self._token_store = token_store

    def indexer_jobs_completed(self):
        return self._redis.get("indexer:jobs:completed") == 'True'

    def enqueue_idles(self, jobs, queue=IDLE):
        print("Enqueuing jobs...")
        pipeline = self._redis.pipeline()
        for job in jobs:
            pipeline.rpush(queue, job)
        pipeline.execute()

    def get_next_job(self, f=IDLE, t=ACTIVE):
        job_bytes = self._redis.rpoplpush(f, t)
        if job_bytes is None:
            self._redis.set("indexer:jobs:completed", "True")
            print("No more job available!")
        else:
            job = Job.bytes_to_job(job_bytes)
            print(threading.current_thread().getName(), "get Next Job: %s" % job.path)
            return job

    def complete(self, job, queue=ACTIVE):
        print(threading.current_thread().getName(), "completed Job: %s" % job.path)
        self._redis.lrem(queue, job)
