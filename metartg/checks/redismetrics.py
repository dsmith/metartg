#!/usr/bin/env python
from socket import socket
from time import time
import sys


REDIS_METRICS = {
    'used_memory': 'GAUGE',
    'connected_clients': 'GAUGE',
    'connected_slaves': 'GAUGE',
    'blocked_clients': 'GAUGE',
    'total_connections_received': 'COUNTER',
    'total_commands_processed': 'COUNTER',
}


def readlines(sock):
    buf = ''
    while True:
        data = sock.recv(1024)
        if not data:
            return
        buf += data
        while buf.find('\r\n') != -1:
            line, buf = buf.split('\r\n', 1)
            if line == '':
                return
            yield line


def redis_metrics():
    sock = socket()
    sock.connect(('127.0.0.1', 6379))
    sock.sendall('info\r\n')

    metrics = {}
    now = int(time())
    for line in readlines(sock):
        if not line or line.startswith('$'):
            continue

        field, value = line.split(':', 1)
        if not field in REDIS_METRICS:
            continue

        for field, rrdtype in REDIS_METRICS.iteritems():
            metrics[field] = {
                'type': rrdtype,
                'ts': now,
                'value': int(value),
            }

    sock.sendall('quit\r\n')
    sock.close()
    return metrics


def run_check(callback):
    metrics = redis_metrics()
    callback('redis', metrics)
