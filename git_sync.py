import os
import subprocess
import ConfigParser
import argparse
import pprint
import logging
import string

from fabric.api import *
from fabric.utils import *
from fabric.contrib.console import confirm
from fabric.contrib.files import *
from fabric.colors import *

from fsevents import Observer
from fsevents import Stream

import gntp
import gntp.notifier

@task
def init_remote_master_repository( remote_path, local_branch ):

    puts("Setting up %s" % remote_path)

    if not exists( remote_path ):
        abort("The remote path does not exist: %s" % remote_path)

    git_repo = get_remote_git_repo( remote_path )

    if exists ( git_repo ):
        puts("The git repo already exist: %s" % git_repo)
    else:
        with cd ( remote_path ):
            run( "git init" )
            append( '.gitignore', '.DS_Store' )
            append( '.gitignore', '.svn*' )
            append( '.gitignore', 'data/asset/*' )
            append( '.gitignore', 'data/tmp/*' )
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

        run('rm .gitignore', shell=False)
        run('mv .gitignore_new .gitignore', shell=False)


@task
def remote_has_modified_files( remote_path ):
    puts(blue('remote_has_modified_files'))
    puts(red(env.hosts))
    with cd ( remote_path ):
        with settings( warn_only=True ):
            with hide('running', 'status', 'warnings', 'stderr', 'stdout'):
                git_status_output = run( "git status . " )
                puts(red(git_status_output))
                if "nothing to commit (working directory clean)" in git_status_output:
                    puts(cyan("%s (remote) is clean." % remote_path))
                    return False
                else:
                    puts(cyan("%s (remote) has uncommitted changes." % remote_path))
                    return True


@task
def local_has_modified_files ( local_path ):
    with lcd ( local_path ):
        with settings( warn_only=True ):
            with hide('running', 'status', 'warnings', 'stderr', 'stdout'):
                git_status_output = local( "git status . ", capture=True )
                if "nothing to commit (working directory clean)" in git_status_output:
                    puts(cyan("%s (local) is clean." % local_path))
                    return False
                else:
                    puts(cyan("%s (local) has uncommitted changes." % local_path))
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
    with cd ( remote_path ):
        run( "git add ." )
        run( "git commit -a -m 'committing all changes from %s'" % (remote_path) )
        return True


@task
def push_remote_master ( remote_path, local_branch ):
    with cd ( remote_path ):
        run( "git push origin %s" % (local_branch) )
        return True


@task
def commit_and_push_remote ( remote_path ) :
    commit_amm_modified_files(amm_name)
    push_amm_master(amm_name)


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
    with lcd ( local_path ):
        local( "git push origin %s" % (local_branch) )


@task
def merge_local_to_remote ( remote_path, local_branch ):
    with cd ( remote_path ):
        run ( 'git merge %s' % (local_branch) )


@task
def send_local_changes_to_remote( remote_path, local_path, local_branch ):
    commit_local_modified_files( local_path )
    push_local_to_remote( local_path, local_branch )
    merge_local_to_remote( remote_path, local_branch )


@task
def send_remote_changes_to_local( remote_path, local_path ):
    commit_remote_modified_files( remote_path )
    pull_and_merge_local( local_path )


@task
def sync( remote_path, local_path, local_branch ):
    puts( blue( 'sync' ) )

    if not os.path.exists( local_path ):
        init( remote_path, local_path, local_branch )

    if remote_has_modified_files( remote_path ):
        send_remote_changes_to_local( remote_path, local_path )
    
    send_local_changes_to_remote( remote_path, local_path, local_branch )


@task
def init ( remote_path, local_path, local_branch ):
    init_remote_master_repository( remote_path, local_branch )
    get_local_git_clone ( remote_path, local_path )


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
config = ConfigParser.ConfigParser()

config.readfp(args.config_file)

local_path    =  config.get('GitSync', 'local_path')
local_branch  =  config.get('GitSync', 'local_branch')
remote_path   =  config.get('GitSync', 'remote_path')
remote_host   =  config.get('GitSync', 'remote_host')
remote_user   =  config.get('GitSync', 'remote_user')

git_ignore_lines = []

for (key, value) in config.items( 'GitIgnore' ):
    git_ignore_lines.append(value)


git_ignore_lines = sorted( git_ignore_lines )

if remote_user:
    remote_host  =  remote_user + '@' + remote_host


# Setup Growl notifications.
growl = gntp.notifier.GrowlNotifier(
    applicationName      = "GitSync",
    notifications        = ["Sync Starting", "Sync Done"],
    defaultNotifications = ["Sync Starting","Sync Done"],
    hostname             = "localhost",
)

def growl_start( ):
    growl.notify(
        noteType    = "Sync Starting",
        title       = "Sync is starting",
        description = "Starting to sync %s and %s on %s" % (
            local_path,
            remote_path,
            remote_host,
        ),
    )

def growl_done( ):
    growl.notify(
        noteType    = "Sync Done",
        title       = "Sync is finished",
        description = "Completed sync of %s and %s on %s" % (
            local_path,
            remote_path,
            remote_host,
        ),
    )


def callback( event ):

    filename = event.name
    git_dir  = os.path.join( local_path, '.git' )

    #Skip sync for file change that are in the .git directory.
    if not git_dir in filename:
        growl_start( )
        execute(
            sync
            , host         = remote_host
            , remote_path  = remote_path
            , local_path   = local_path
            , local_branch = local_branch
        )
        growl_done( )
        print 'To stop: Ctrl-\\'

# Do an initial sync
growl_start( )

execute(
    sync
    , host         = remote_host
    , remote_path  = remote_path
    , local_path   = local_path
    , local_branch = local_branch
)

growl_done( )

print 'To stop: Ctrl-\\'

execute(
     update_git_ignore_file
    , host = remote_host
    , remote_path = remote_path
    , git_ignore_lines=git_ignore_lines
)

# Start watching the directory
observer = Observer()
stream = Stream(callback, local_path, file_events=True)
observer.schedule(stream)
observer.start()
