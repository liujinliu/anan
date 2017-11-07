# -*- coding: utf-8 -*-

import time
import socket
import pickle
import struct
import argparse
import redis
from caculator import QpsPlayer, AggregationPlayer
from config_parse import get_config


parser = argparse.ArgumentParser()
parser.add_argument('--config_file', type=str,
                    default='example.yaml', dest="config_file",
                    help="config file path")
ARGS = parser.parse_args()
CONFIG = get_config(ARGS.config_file)


def socket_create():
    host = CONFIG['graphite']['host']
    port = CONFIG['graphite'].get('pickle', 2004)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    return s


def feeding(s, players):
    while True:
        allmetrics = []
        for p in players:
            tmp_metric = p.get_metrics()
            allmetrics.extend(tmp_metric)
        if allmetrics:
            payload = pickle.dumps(allmetrics, protocol=2)
            header = struct.pack("!L", len(payload))
            message = '%s%s' % (header, payload)
            s.sendall(message)
            print(message)
        time.sleep(1)


def players_get():
    redis_host = CONFIG['redis']['host']
    redis_port = CONFIG['redis']['port']
    redis_db = CONFIG['redis']['db']
    pool = redis.ConnectionPool(host=redis_host, port=redis_port,
                                db=redis_db)
    players = []
    for p in CONFIG['qps_players']:
        players.append(QpsPlayer(pool, p['collect_target'],
                                 p['collect_interval'],
                                 p['rotate_value'], p['graph_path']))
    for p in CONFIG['aggregation_players']:
        players.append(AggregationPlayer(pool, p['collect_target'],
                                         p['collect_interval'],
                                         p['aggregation_length'],
                                         p['aggregation_types']))
    return players


def cruiser_run():
    pass


if __name__ == "__main__":
    s = socket_create()
    players = players_get()
    feeding(s, players)
