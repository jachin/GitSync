import os
import pprint

from fabric.api import *
from fabric.utils import *
from fabric.contrib.console import confirm
from fabric.contrib.files import *
from fabric.colors import *

from fsevents import Observer
from fsevents import Stream

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
            run( "git add .gitignore" )
            run( "git commit -m 'Inital Commit'" )
            run( "git add ." )
            run( "git commit -m 'add project'" )
    
    with cd ( remote_path ):
        git_branch_output = run( "git branch" )
        pprint.pprint( git_branch_output )

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
def observe( remote_host, remote_path, local_path, local_branch ):

    def callback( event ):

        filename = event.name
        git_dir = os.path.join( local_path, '.git' )

        #Skip sync for file change that are in the .git directory.
        if not git_dir in filename:
            sync( amm_name, local_path )
            puts(green('To stop: Ctrl-\\'))

    # Do an initial sync
    sync( remote_host, remote_path, local_path, local_branch )

    puts( green( 'Observing: %s' % local_path ) )

    # Start watching the directory
    observer = Observer()
    stream = Stream(callback, local_path, file_events=True)
    observer.schedule(stream)
    observer.start()


@task
def init ( remote_path, local_path, local_branch ):
    init_remote_master_repository( remote_path, local_branch )
    get_local_git_clone ( remote_path, local_path )
