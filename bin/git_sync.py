#!/usr/bin/env python

import argparse
import yaml

from signal import pause

from gitsync import GitNotified, GitSync


def parse_config():
    # Setup Parser
    parser = argparse.ArgumentParser(
        description='Use git to sync a site on a server to your local machine.'
    )

    parser.add_argument(
        'config_file',
        nargs='?',
        type=argparse.FileType('r')
    )

    args = parser.parse_args()

    # Read in config file.
    return yaml.safe_load(args.config_file)


config = parse_config()
notifier = GitNotified()

git_sync = GitSync(config, notifier)
git_sync.start()

try:
    while 1:
        pause()
except KeyboardInterrupt:
    git_sync.stop()

git_sync.observer.join()
