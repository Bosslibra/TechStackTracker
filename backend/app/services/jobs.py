import json
import os
import tempfile
import threading
from pathlib import Path

_DATA_LOCK = threading.Lock()
DATA_FILE = Path(__file__).resolve().parent.parent / 'jobs.json'


def read_jobs():
    if not DATA_FILE.exists():
        return []

    with _DATA_LOCK:
        with DATA_FILE.open('r', encoding='utf-8') as f:
            data = json.load(f)

    return data if isinstance(data, list) else []


def write_jobs(jobs):
    data = jobs if isinstance(jobs, list) else []

    with _DATA_LOCK:
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            delete=False,
            dir=str(DATA_FILE.parent),
            prefix='jobs_',
            suffix='.tmp'
        ) as tmp_file:
            json.dump(data, tmp_file, indent=2, ensure_ascii=False)
            tmp_path = tmp_file.name

        os.replace(tmp_path, DATA_FILE)
