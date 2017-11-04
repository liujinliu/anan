# -*- coding: utf-8 -*-
import time
import redis
import logging


def return_when_crash(default_ret):
    def never_crash(func):
        def wrapper(self):
            try:
                return func()
            except Exception as e:
                logging.debug(e, exc_info=True)
                return default_ret
        return wrapper
    return never_crash


class QpsPlayer(object):

    def __init__(self, redis_pool, collect_target,
                 collect_interval, rotate_value,
                 graph_path):
        self.collect_target = collect_target
        self.collect_interval = collect_interval
        self.last_collect_value = None
        self.last_collect_time = None
        self.redis_pool = redis_pool
        self.rotate_value = rotate_value
        self.graph_path = self.graph_path

    @property
    def _conn(self):
        return redis.Redis(connection_pool=self.REDIS_POOL)

    def _get_value_init(self):
        r = self._conn
        current_value = int(r.get())
        self.last_collect_value = current_value
        return None

    def _get_value_and_rotate(self):
        p = self._conn.pipeline()
        p.get(self.collect_target)
        p.set(self.collect_target, 0)
        r = p.execute()
        ret = int(r[0]) - self.last_collect_value
        self.last_collect_value = 0
        return ret

    def _get_value(self):
        r = self._conn
        current_value = int(r.get())
        ret = current_value - self.last_collect_value
        self.last_collect_value = current_value
        return ret

    @return_when_crash(0)
    def get_value(self):
        if self.last_collect_time is None:
            self.last_collect_time = int(time.time())
            return self._get_value_init()
        elif self.last_collect_time + self.collect_interval > int(time.time()):
            self.last_collect_time = int(time.time())
            if self.last_collect_value >= self.rotate_value:
                return self._get_value_and_rotate()
            else:
                return self._get_value()
        else:
            return None

    def get_metric(self):
        value = self.get_value()
        timestamp = self.last_collect_time
        return timestamp, value

    def get_graph_path(self):
        return self.graph_path
