from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import subprocess
import threading
import shlex
import logging
from enum import Enum
from features import tasks


class Algorithms(Enum):
    rar = 0


class AlgoServerHandler(BaseHTTPRequestHandler):
    def send_ok(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('charset', 'utf-8')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        parsed = json.loads(self.rfile.read(content_length).decode('utf-8'))
        result_id = parsed['job_id']

        if result_id == Algorithms['rar'].value:
            tasks.rar_callback(parsed)
        self.send_ok()
        assassin = threading.Thread(target=self.shutdown)
        assassin.daemon = True
        assassin.start()

    def shutdown(self):
        self.server.shutdown()
        self.server.handle_request()

server = HTTPServer(('127.0.0.1', 8001), AlgoServerHandler)


def execJob(command, algorithm):
    args = shlex.split(command)
    args.extend(['-u', ("http://127.0.0.1" + ":8001"), '-i', str(algorithm.value)])
    # Run command
    process = subprocess.Popen(args, shell=True)
    server.serve_forever()
    return process
