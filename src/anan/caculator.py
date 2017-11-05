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


def average(values):
    return int(sum(values) / len(values))


class BasePlayer(object):

    def __init__(self, redis_pool, graph_path):
        self.redis_pool = redis_pool
        self.graph_path = graph_path
        self.last_collect_time = None

    @property
    def _conn(self):
        return redis.Redis(connection_pool=self.REDIS_POOL)

    def get_graph_path(self):
        return self.graph_path


class QpsPlayer(BasePlayer):

    def __init__(self, redis_pool,
                 graph_path, collect_target,
                 collect_interval, rotate_value):
        super(QpsPlayer, self).__init__(redis_pool, graph_path)
        self.collect_target = collect_target
        self.collect_interval = collect_interval
        self.last_collect_value = None
        self.rotate_value = rotate_value

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
        elif self.last_collect_time + self.collect_interval >= int(time.time()):
            self.last_collect_time = int(time.time())
            if self.last_collect_value >= self.rotate_value:
                return self._get_value_and_rotate()
            else:
                return self._get_value()
        else:
            return None

    def get_metrics(self):
        ret = []
        value = self.get_value()
        timestamp = self.last_collect_time
        if value is not None:
            ret.append((self.get_graph_path(), (timestamp, value)))
        return ret


class AggregationPlayer(BasePlayer):

    AGGREGATION_METHOD = {'max': max, 'min': min,
                          'avg': average}

    def __init__(self, redis_pool, graph_path,
                 collect_target, collect_interval,
                 aggregation_length, aggregation_types):
        super(AggregationPlayer, self).__init__(redis_pool, graph_path)
        self.collect_target = collect_target
        self.collect_interval = collect_interval
        self.aggregation_length = aggregation_length
        self.values = []
        self.methods = filter(lambda x: x in self.AGGREGATION_METHOD,
                              aggregation_types.strip().split(','))

    @return_when_crash(None)
    def get_values(self):
        ret = []
        if (self.last_collect_time is None) or\
                (self.last_collect_time +
                 self.collect_interval >= int(time.time())):
            self.last_collect_time = int(time.time())
            r = self._conn
            current_value = int(r.get())
            self.values.append(current_value)
        if len(self.values) >= self.aggregation_length:
            ret = self.values
            self.values = []
            return ret
        return ret

    def get_metrics(self):
        base_path = self.get_graph_path()
        metrics = []
        values = self.get_values()
        if values:
            for method in self.methods:
                path = '%s.%s' % (base_path, method)
                timestamp = self.last_collect_time
                value = self.methods[method](values)
                metrics.append((path, (timestamp, value)))
        return metrics
