#!/usr/bin/env python3

import subprocess
import os


class cd:
    """Context manager for changing the current working directory"""

    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


BASE_DIR = 'circleci/images'
REPO = 'heisenberg302/'

CONFIGS = [
    dict(
        dockerfile_dir=os.path.join(BASE_DIR, 'extbuilder'),
        image_name=REPO + 'extbuilder',
        command=[
            'docker', 'build',
            '--tag', REPO + 'extbuilder',
            '.'
        ]
    ),
    dict(
        dockerfile_dir=os.path.join(BASE_DIR, 'failtester'),
        image_name=REPO + 'failtester-11',
        command=[
            'docker', 'build',
            '--tag', REPO + 'failtester-11',
            '--build-arg', 'PG_MAJOR=11',
            '.'
        ]
    ),
    dict(
        dockerfile_dir=os.path.join(BASE_DIR, 'failtester'),
        image_name=REPO + 'failtester-10',
        command=[
            'docker', 'build',
            '--tag', REPO + 'failtester-10',
            '--build-arg', 'PG_MAJOR=10',
            '.'
        ]
    ),
    dict(
        dockerfile_dir=os.path.join(BASE_DIR, 'exttester'),
        image_name=REPO + 'exttester-10',
        command=[
            'docker', 'build',
            '--tag', REPO + 'exttester-10',
            '--build-arg', 'PG_MAJOR=10',
            '.'
        ]
    ),
    dict(
        dockerfile_dir=os.path.join(BASE_DIR, 'exttester'),
        image_name=REPO + 'exttester-11',
        command=[
            'docker', 'build',
            '--tag', REPO + 'exttester-11',
            '--build-arg', 'PG_MAJOR=11',
            '.'
        ]
    )
]


for config in CONFIGS:
    with cd(config['dockerfile_dir']):
        subprocess.call(config['command'])
        subprocess.call([
            'docker', 'push',
            config['image_name']
        ])
