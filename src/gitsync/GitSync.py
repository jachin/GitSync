# -*- coding: utf-8 -*-


__version__ = "0.2.0"

import os
import argparse
import yaml

from signal import pause

from fsevents import Observer
from fsevents import Stream

# These are a bunch of constants that identify different type of file system
#  events and the fsevents library uses.
kFSEventStreamEventFlagNone = 0x00000000
kFSEventStreamEventFlagMustScanSubDirs = 0x00000001
kFSEventStreamEventFlagUserDropped = 0x00000002
kFSEventStreamEventFlagKernelDropped = 0x00000004
kFSEventStreamEventFlagEventIdsWrapped = 0x00000008
kFSEventStreamEventFlagHistoryDone = 0x00000010
kFSEventStreamEventFlagRootChanged = 0x00000020
kFSEventStreamEventFlagMount = 0x00000040
kFSEventStreamEventFlagUnmount = 0x00000080
kFSEventStreamEventFlagItemCreated = 0x00000100  # 256
kFSEventStreamEventFlagItemRemoved = 0x00000200
kFSEventStreamEventFlagItemInodeMetaMod = 0x00000400
kFSEventStreamEventFlagItemRenamed = 0x00000800
kFSEventStreamEventFlagItemModified = 0x00001000
kFSEventStreamEventFlagItemFinderInfoMod = 0x00002000
kFSEventStreamEventFlagItemChangeOwner = 0x00004000
kFSEventStreamEventFlagItemXattrMod = 0x00008000
kFSEventStreamEventFlagItemIsFile = 0x00010000
kFSEventStreamEventFlagItemIsDir = 0x00020000
kFSEventStreamEventFlagItemIsSymlink = 0x00040000

import gitsynclib.GitSync

observer = Observer()
notifier = None
stream = None
git_sync = None
config = None


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


def start():
    global observer, git_sync
    git_sync.run_initial_sync()
    observer.start()

def stop():
    global observer
    observer.unschedule(stream)
    observer.stop()
    observer.join()

def callback(event):

    global observer, git_sync

    if event.mask == kFSEventStreamEventFlagItemCreated:
        # Sublime Text Seems to trigger a lot of these and they don't seem to
        #  warrant a new sync, so lets skip these for now.
        return

    filename = event.name
    git_dir = os.path.join(config['local_path'], '.git')

    if git_dir in filename:
        # Skip sync for file change that are in the .git directory.
        return

    if observer:
        # Stop observing.
        observer.unschedule(stream)
        observer.stop()

    git_sync.run_sync()

    # Start observing again.
    observer = Observer()
    observer.schedule(stream)
    observer.start()


def main():

    global config, stream, observer, git_sync, notifier

    config = parse_config()

    stream = Stream(callback, config['local_path'], file_events=True)
    observer.schedule(stream)

    (git_sync, notifier) = gitsynclib.GitSync.setup_git_sync(config)

    git_sync.run_initial_sync()
    observer.start()

    try:
        while 1:
            pause()
    except KeyboardInterrupt:
        stop()

    return 0
