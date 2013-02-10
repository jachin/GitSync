#!/usr/bin/env python

import os
import subprocess
import argparse
import pprint
import logging
import string
import yaml
import socket

from signal import pause

from fabric.api import *
from fabric.utils import *
from fabric.contrib.console import confirm
from fabric.contrib.files import *
from fabric.colors import *

from fsevents import Observer
from fsevents import Stream

import gntp
import gntp.notifier
from gntp.notifier import mini

# These are a bunch of constants that identify different type of file system
#  events and the fsevents library uses.
kFSEventStreamEventFlagNone              = 0x00000000
kFSEventStreamEventFlagMustScanSubDirs   = 0x00000001
kFSEventStreamEventFlagUserDropped       = 0x00000002
kFSEventStreamEventFlagKernelDropped     = 0x00000004
kFSEventStreamEventFlagEventIdsWrapped   = 0x00000008
kFSEventStreamEventFlagHistoryDone       = 0x00000010
kFSEventStreamEventFlagRootChanged       = 0x00000020
kFSEventStreamEventFlagMount             = 0x00000040
kFSEventStreamEventFlagUnmount           = 0x00000080
kFSEventStreamEventFlagItemCreated       = 0x00000100 #256
kFSEventStreamEventFlagItemRemoved       = 0x00000200
kFSEventStreamEventFlagItemInodeMetaMod  = 0x00000400
kFSEventStreamEventFlagItemRenamed       = 0x00000800
kFSEventStreamEventFlagItemModified      = 0x00001000
kFSEventStreamEventFlagItemFinderInfoMod = 0x00002000
kFSEventStreamEventFlagItemChangeOwner   = 0x00004000
kFSEventStreamEventFlagItemXattrMod      = 0x00008000
kFSEventStreamEventFlagItemIsFile        = 0x00010000
kFSEventStreamEventFlagItemIsDir         = 0x00020000
kFSEventStreamEventFlagItemIsSymlink     = 0x00040000

@task
def init_remote_master_repository( remote_path, local_branch, git_ignore_lines ):

    puts("Setting up %s" % remote_path)

    if not exists( remote_path ):
        abort("The remote path does not exist: %s" % remote_path)

    git_repo = get_remote_git_repo( remote_path )

    if exists ( git_repo ):
        puts("The git repo already exist: %s" % git_repo)
    else:
        with cd ( remote_path ):
            run( "git init" )

        update_git_ignore_file( remote_path, git_ignore_lines )

        with cd ( remote_path ):
            run( "git add .gitignore" )
            run( "git commit -m 'Inital Commit'" )
            run( "git add ." )
            run( "git commit -m 'add project'" )


@task
def update_git_ignore_file( remote_path, git_ignore_lines ):
    with cd ( remote_path ):
        for line in git_ignore_lines:
            if not contains( '.gitignore_new', line ):
                append( '.gitignore_new', line )

        run('mv .gitignore_new .gitignore', shell=False)


@task
def remote_has_modified_files( remote_path ):
    with cd( remote_path ):
        with settings( warn_only=True ):
            with hide('running', 'status', 'warnings', 'stderr', 'stdout'):

                git_status_output = run( "git status --porcelain ." )

                if not git_status_output:
                    puts(cyan("%s (remote) is clean." % remote_path))
                    return False
                else:
                    puts(
                        cyan(
                            " %s (remote) has uncommitted changes."
                            % remote_path
                        )
                    )
                    return True


@task
def local_has_modified_files ( local_path ):
    with lcd ( local_path ):
        with settings( warn_only=True ):
            with hide('running', 'status', 'warnings', 'stderr', 'stdout'):

                git_status_output = local( "git status --porcelain .", capture=True )

                if not git_status_output:
                    puts( cyan("%s (local) is clean." % local_path ) )
                    return False
                else:
                    puts(
                        cyan( "%s (local) has uncommitted changes." % local_path )
                    )
                    return True


@task
def get_remote_git_repo ( remote_path ):
    git_repo = os.path.join( remote_path, '.git' )
    return git_repo


@task
def get_local_git_clone ( remote_path, local_path ):
    local( "git clone ssh://%s/%s %s" % ( env.host, remote_path, local_path ) )


@task
def commit_remote_modified_files ( remote_path ):
    if not remote_has_modified_files( remote_path ):
        return True
    with cd( remote_path ):
        run( "git add ." )
        run( "git commit -a -m 'committing all changes from %s'" % (remote_path) )
        return True


@task
def push_remote_master ( remote_path, local_branch ):

    remote_has_local_branch( remote_path, local_branch )

    with cd ( remote_path ):
        run( "git push origin %s" % (local_branch) )
        return True


def remote_has_local_branch ( remote_path, local_branch ):
    with cd ( remote_path ):
        git_branches = run ( 'git branch' )
        puts( cyan( git_branches ) )


@task
def commit_and_push_remote ( remote_path ) :
    commit_amm_modified_files( amm_name )
    push_amm_master( amm_name )


@task
def pull_local ( local_path ):
    with lcd ( local_path ):
        local ( 'git fetch origin' )


@task
def merge_local_master ( local_path ):
    with lcd ( local_path ):
        local ( 'git merge origin/master' )


@task
def pull_and_merge_local ( local_path ):
    pull_local( local_path )
    merge_local_master( local_path )


@task
def commit_local_modified_files ( local_path ):
    with lcd ( local_path ):
        if local_has_modified_files( local_path ):
            local( "git add ." )
            local(
                "git commit -a -m 'committing all changes from a local machine'"
            )
    return True


@task
def push_local_to_remote ( local_path, local_branch ):
    if not local_has_local_branch( local_path, local_branch ):
        local_create_local_branch( local_path, local_branch )

    with lcd ( local_path ):
        local( "git push origin %s" % ( local_branch ) )


def local_create_local_branch ( local_path, local_branch ):
    with lcd ( local_path ):
        local ( 'git branch %s' % ( local_branch ), capture=True )


def local_has_local_branch ( local_path, local_branch ):

    puts( cyan( local_path ) )

    with lcd ( local_path ):
        git_branches = local ( 'git branch', capture=True )
        for branch in git_branches.split( ):
            if branch == local_branch:
                return True
        return False


@task
def merge_local_to_remote ( remote_path, local_branch ):
    with cd ( remote_path ):
        run ( 'git merge %s' % (local_branch) )


@task
def send_local_changes_to_remote ( remote_path, local_path, local_branch ):
    commit_local_modified_files( local_path )
    push_local_to_remote( local_path, local_branch )
    merge_local_to_remote( remote_path, local_branch )


@task
def send_remote_changes_to_local ( remote_path, local_path ):
    commit_remote_modified_files( remote_path )
    pull_and_merge_local( local_path )


@task
def sync ( remote_path, local_path, local_branch, git_ignore_lines ):

    if not os.path.exists( local_path ):
        init( remote_path, local_path, local_branch, git_ignore_lines )

    if remote_has_modified_files( remote_path ):
        send_remote_changes_to_local( remote_path, local_path )
    
    send_local_changes_to_remote( remote_path, local_path, local_branch )


def initial_sync ( remote_path, local_path, local_branch, git_ignore_lines ):
    if not os.path.exists( local_path ):
        init( remote_path, local_path, local_branch, git_ignore_lines )

    send_remote_changes_to_local( remote_path, local_path )
    send_local_changes_to_remote( remote_path, local_path, local_branch )


@task
def init ( remote_path, local_path, local_branch, git_ignore_lines ):
    init_remote_master_repository( remote_path, local_branch, git_ignore_lines )
    get_local_git_clone( remote_path, local_path )
    local_create_local_branch( local_path, local_branch )
    with lcd( local_path ):
        local( "git checkout %s" % (local_branch) )


# Setup Parser
parser = argparse.ArgumentParser(
    description='Use git to sync a site on pion to your local machine.'
)

parser.add_argument(
    'config_file'
    , nargs='?'
    , type=argparse.FileType('r')
)

args = parser.parse_args()

# Read in config file.
config = yaml.safe_load(args.config_file)

local_path       = config['local_path']
local_branch     = config['local_branch']
remote_path      = config['remote_path']
remote_host      = config['remote_host']
remote_user      = config['remote_user']
git_ignore_lines = config['git_ignore']
observer         = Observer()

# Sort the git ignore lines.
git_ignore_lines = sorted( git_ignore_lines )

if remote_user:
    remote_host = remote_user + '@' + remote_host

def growl_start( ):
    try:
        mini(
            "Starting to sync %s and %s on %s" % (
                local_path,
                remote_path,
                remote_host,
            )
            , applicationName='GitSync'
            , noteType='Message'
            , title='GitSync Starting'
        )
    except socket.error:
        print 'Unable to send growl notification.'
        print 'Growl is probably not running.'
        print 'GitSync Starting'



def growl_done( ):
    try:
        mini(
            "Completed sync of %s and %s on %s" % (
                local_path,
                remote_path,
                remote_host,
            )
            , applicationName='GitSync'
            , noteType='Message'
            , title='GitSync Finished'
        )
    except socket.error:
        print 'Unable to send growl notification.'
        print 'Growl is probably not running.'
        print 'GitSync Finished'


def run_remote_has_modified_files( ):
    result = execute(
        remote_has_modified_files
        , host             = remote_host
        , remote_path      = remote_path
    )
    return result[remote_host]


def run_send_remote_changes_to_local( ):
    result = execute(
        send_remote_changes_to_local
        , host             = remote_host
        , remote_path      = remote_path
        , local_path       = local_path
    )
    return result[remote_host]


def run_send_local_changes_to_remote( ):
    result = execute(
        send_local_changes_to_remote
        , host             = remote_host
        , remote_path      = remote_path
        , local_path       = local_path
        , local_branch     = local_branch
    )
    return result[remote_host]


def run_initial_sync( ):
    growl_start( )
    execute(
        initial_sync
        , host             = remote_host
        , remote_path      = remote_path
        , local_path       = local_path
        , local_branch     = local_branch
        , git_ignore_lines = git_ignore_lines
    )
    growl_done( )


def callback( event ):

    global observer, stream

    if event.mask == kFSEventStreamEventFlagItemCreated:
        # Sublime Text Seems to trigger a lot of these and they don't seem to
        #  warrant a new sync, so lets skip these for now.
        return

    filename = event.name
    git_dir  = os.path.join( local_path, '.git' )
    
    if git_dir in filename:
        #Skip sync for file change that are in the .git directory.
        return

    growl_start( )

    try:
        if run_remote_has_modified_files():
            # Stop observing.
            observer.unschedule(stream)
            observer.stop()

            run_send_remote_changes_to_local()

            # Start observing again.
            observer = Observer()
            observer.schedule(stream)
            observer.start()

        run_send_local_changes_to_remote()

    except Exception as inst:
        print "sync failed."
        print type(inst)
        print inst.args
        print inst
        growl_failed( )
        raise
    else:
        growl_done( )

run_initial_sync( )

# Start watching the directory
stream = Stream(callback, local_path, file_events=True)
observer.schedule(stream)
observer.start()

try:
    while 1:
        pause( )
except KeyboardInterrupt:
    observer.unschedule(stream)
    observer.stop( )
    observer.join( )

