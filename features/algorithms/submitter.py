from flask import Flask, request
import json
import subprocess
import shlex
import threading

# Initialize the Flask application
app = Flask(__name__)


@app.route('/', methods=['POST'])
def receive_results():
    parsed = json.loads(request.data)
    result_id = parsed['job_id']
    current_jobs[result_id](parsed)
    del current_jobs[result_id]


app.run(port=8001)
current_jobs = {}
job_id = 0
lock = threading.Lock()


def execJob(command, completion):
    lock.aquire()
    current_jobs[job_id] = completion
    args = shlex.split(command)
    args.extend(['-u', app.host, '-i', job_id])
    job_id += 1
    lock.release()
    # Run command
    output = subprocess.run(command, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return output.stdout
