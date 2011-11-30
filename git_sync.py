import os
import subprocess
import ConfigParser
import argparse
import pprint
import logging

from fsevents import Observer
from fsevents import Stream

import gntp
import gntp.notifier

parser = argparse.ArgumentParser(
    description='Use git to sync a site on pion to your local machine.'
)

parser.add_argument(
    'config_file'
    , nargs='?'
    , type=argparse.FileType('r')
    , default="./git_sync.cfg"
)

args = parser.parse_args()

config = ConfigParser.ConfigParser()

config.readfp(args.config_file)

local_path    =  config.get('GitSync', 'local_path')
local_branch  =  config.get('GitSync', 'local_branch')
remote_path   =  config.get('GitSync', 'remote_path')
remote_host   =  config.get('GitSync', 'remote_host')
remote_user   =  config.get('GitSync', 'remote_user')

if remote_user:
    remote_host  =  remote_user + '@' + remote_host

growl = gntp.notifier.GrowlNotifier(
    applicationName = "GitSync",
    notifications = ["Sync Starting", "Sync Done"],
    defaultNotifications = ["Sync Starting","Sync Done"],
    hostname = "localhost",
)

def growl_start( ):
    growl.notify(
        noteType = "Sync Starting",
        title = "Sync is starting",
        description = "Starting to sync local_path and remote_path on remote_host",
    )

def growl_done( ):
    growl.notify(
        noteType = "Sync Done",
        title = "Sync is finished",
        description = "Completed sync of local_path and remote_path on remote_host",
    )

def callback( event ):

    filename = event.name
    git_dir = os.path.join( local_path, '.git' )

    #Skip sync for file change that are in the .git directory.
    if not git_dir in filename:
        growl_start( )
        subprocess.call("fab -H %s sync:remote_path=%s,local_path=%s,local_branch=%s" % ( remote_host, remote_path, local_path, local_branch ), shell=True)
        growl_done( )
        print 'To stop: Ctrl-\\'

# Do an initial sync
growl_start( )
subprocess.call("fab -H %s sync:remote_path=%s,local_path=%s,local_branch=%s" % ( remote_host, remote_path, local_path, local_branch ), shell=True)
growl_done( )
print 'To stop: Ctrl-\\'

# Start watching the directory
observer = Observer()
stream = Stream(callback, local_path, file_events=True)
observer.schedule(stream)
observer.start()
