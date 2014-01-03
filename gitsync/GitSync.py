#!/usr/bin/env python

import os
import argparse
import yaml

from fabric.api import *
from fabric.utils import puts
from fabric.contrib.files import exists
from fabric.colors import cyan

from signal import pause

from fsevents import Observer
from fsevents import Stream

from GitNotified import GitNotified

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


class GitSync:

    local_path = ''
    local_branch = ''
    remote_path = ''
    remote_host = ''
    remote_user = ''
    git_ignore_lines = ''
    #observer
    #stream

    def __init__(self, config, notify):

        self.notify = notify

        self.local_path = config['local_path']
        self.local_branch = config['local_branch']
        self.remote_path = config['remote_path']
        self.remote_host = config['remote_host']
        self.remote_user = config['remote_user']
        self.git_ignore_lines = config['git_ignore']
        self.observer = Observer()

        # Sort the git ignore lines.
        self.git_ignore_lines = sorted(self.git_ignore_lines)

        if self.remote_user:
            self.remote_host = self.remote_user + '@' + self.remote_host

        # Start watching the directory
        self.stream = Stream(self.callback, self.local_path, file_events=True)
        self.observer.schedule(self.stream)

    def start(self):
        self.run_initial_sync()
        self.observer.start()

    @task
    def init_remote_master_repository(self, remote_path, local_branch, git_ignore_lines):

        puts("Setting up %s" % remote_path)

        if not exists(remote_path):
            abort("The remote path does not exist: %s" % remote_path)

        git_repo = self.get_remote_git_repo(self, remote_path)

        if exists(git_repo):
            puts("The git repo already exist: %s" % git_repo)
        else:
            with cd(remote_path):
                run("git init")

            self.update_git_ignore_file(self, remote_path, git_ignore_lines)

            with cd(remote_path):
                run("git add .gitignore")
                run("git commit -m 'Inital Commit'")
                run("git add .")
                run("git commit -m 'add project'")

    @task
    def update_git_ignore_file(self, remote_path, git_ignore_lines):

        puts("Updating ignore files.")

        with cd(remote_path):
            with hide('running'):

                cmd = []
                for line in git_ignore_lines:
                    cmd.append("echo '{0}' >> .gitignore_new".format(line))

                run(';'.join(cmd))

                run('mv .gitignore_new .gitignore', shell=False)

    @task
    def remote_has_modified_files(self, remote_path):
        with cd(remote_path):
            with settings(warn_only=True):
                with hide('running', 'status', 'warnings', 'stderr', 'stdout'):

                    git_status_output = run("git status --porcelain .")

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
    def local_has_modified_files(self, local_path):
        with lcd(local_path):
            with settings(warn_only=True):
                with hide('running', 'status', 'warnings', 'stderr', 'stdout'):

                    git_status_output = local("git status --porcelain .", capture=True)

                    if not git_status_output:
                        puts(cyan("%s (local) is clean." % local_path))
                        return False
                    else:
                        puts(
                            cyan("%s (local) has uncommitted changes." % local_path)
                        )
                        return True

    @task
    def get_remote_git_repo(self, remote_path):
        git_repo = os.path.join(remote_path, '.git')
        return git_repo

    @task
    def get_local_git_clone(self, remote_path, local_path):
        local("git clone ssh://%s/%s %s" % (env.host, remote_path, local_path))

    @task
    def commit_remote_modified_files(self, remote_path):
        if not self.remote_has_modified_files(self, remote_path):
            return True
        with cd(remote_path):
            run("git add .")
            run("git commit -a -m 'committing all changes from %s'" % (remote_path))
            return True

    @task
    def push_remote_master(self, remote_path, local_branch):

        self.remote_has_local_branch(self, remote_path, local_branch)

        with cd(remote_path):
            run("git push origin %s" % (local_branch))
            return True

    def remote_has_local_branch(self, remote_path, local_branch):
        with cd(remote_path):
            git_branches = run('git branch')
            puts(cyan(git_branches))

    @task
    def pull_local(self, local_path):
        with lcd(local_path):
            local('git fetch origin')

    @task
    def merge_local_master(self, local_path):
        with lcd(local_path):
            local('git merge origin/master')

    @task
    def pull_and_merge_local(self, local_path):
        self.pull_local(self, local_path)
        self.merge_local_master(self, local_path)

    @task
    def commit_local_modified_files(self, local_path):
        with lcd(local_path):
            if self.local_has_modified_files(self, local_path):
                local("git add .")
                local(
                    "git commit -a -m 'committing all changes from a local machine'"
                )
        return True

    @task
    def push_local_to_remote(self, local_path, local_branch):
        if not self.local_has_local_branch(local_path, local_branch):
            self.local_create_local_branch(local_path, local_branch)

        with lcd(local_path):
            local("git push origin %s" % (local_branch))

    def local_create_local_branch(self, local_path, local_branch):
        with lcd(local_path):
            local('git branch %s' % (local_branch), capture=True)

    def local_has_local_branch(self, local_path, local_branch):

        puts(cyan(local_path))

        with lcd(local_path):
            git_branches = local('git branch', capture=True)
            for branch in git_branches.split():
                if branch == local_branch:
                    return True
            return False

    @task
    def merge_local_to_remote(self, remote_path, local_branch):
        with cd(remote_path):
            run('git merge %s' % (local_branch))

    @task
    def send_local_changes_to_remote(self, remote_path, local_path, local_branch):
        self.commit_local_modified_files(self, local_path)
        self.push_local_to_remote(self, local_path, local_branch)
        self.merge_local_to_remote(self, remote_path, local_branch)

    @task
    def send_remote_changes_to_local(self, remote_path, local_path):
        self.commit_remote_modified_files(self, remote_path)
        self.pull_and_merge_local(self, local_path)

    @task
    def sync(self, remote_path, local_path, local_branch, git_ignore_lines):

        if not os.path.exists(local_path):
            self.init(self, remote_path, local_path, local_branch, git_ignore_lines)

        if self.remote_has_modified_files(self, remote_path):
            self.send_remote_changes_to_local(self, remote_path, local_path)

        self.send_local_changes_to_remote(self, remote_path, local_path, local_branch)

    def initial_sync(self, remote_path, local_path, local_branch, git_ignore_lines):
        if not os.path.exists(local_path):
            self.init(self, remote_path, local_path, local_branch, git_ignore_lines)
        else:
            self.update_git_ignore_file(self, remote_path, git_ignore_lines)

        self.send_remote_changes_to_local(self, remote_path, local_path)
        self.send_local_changes_to_remote(self, remote_path, local_path, local_branch)

    @task
    def init(self, remote_path, local_path, local_branch, git_ignore_lines):
        self.init_remote_master_repository(self, remote_path, local_branch, git_ignore_lines)
        self.get_local_git_clone(self, remote_path, local_path)
        self.local_create_local_branch(local_path, local_branch)
        with lcd(local_path):
            local("git checkout %s" % (local_branch))

    def run_remote_has_modified_files(self):
        result = execute(
            self.remote_has_modified_files,
            self.remote_path,
            host=self.remote_host,
            remote_path=self.remote_path
        )
        return result[self.remote_host]

    def run_send_remote_changes_to_local(self):
        result = execute(
            self.send_remote_changes_to_local,
            self,
            host=self.remote_host,
            remote_path=self.remote_path,
            local_path=self.local_path
        )
        return result[self.remote_host]

    def run_send_local_changes_to_remote(self):
        result = execute(
            self.send_local_changes_to_remote,
            self,
            host=self.remote_host,
            remote_path=self.remote_path,
            local_path=self.local_path,
            local_branch=self.local_branch
        )
        return result[self.remote_host]

    def run_initial_sync(self):
        self.notify.sync_start(self.local_path, self.remote_path, self.remote_host)
        execute(
            self.initial_sync,
            host=self.remote_host,
            remote_path=self.remote_path,
            local_path=self.local_path,
            local_branch=self.local_branch,
            git_ignore_lines=self.git_ignore_lines
        )
        self.notify.sync_done(self.local_path, self.remote_path, self.remote_host)

    def callback(self, event):

        if event.mask == kFSEventStreamEventFlagItemCreated:
            # Sublime Text Seems to trigger a lot of these and they don't seem to
            #  warrant a new sync, so lets skip these for now.
            return

        filename = event.name
        git_dir = os.path.join(self.local_path, '.git')

        if git_dir in filename:
            #Skip sync for file change that are in the .git directory.
            return

        self.notify.sync_start(self.local_path, self.remote_path, self.remote_host)

        try:
            if self.run_remote_has_modified_files():
                # Stop observing.
                self.observer.unschedule(self.stream)
                self.observer.stop()

                self.run_send_remote_changes_to_local()

                # Start observing again.
                self.observer = Observer()
                self.observer.schedule(self.stream)
                self.observer.start()

            self.run_send_local_changes_to_remote()

        except Exception as inst:
            print("sync failed.")
            print(type(inst))
            print(inst.args)
            print(inst)
            self.notify.sync_failed()
            raise
        else:
            self.notify.sync_done(self.local_path, self.remote_path, self.remote_host)

    def stop(self):
        self.observer.unschedule(git_sync.stream)
        self.observer.stop()


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


def main():
    global git_sync
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

if __name__ == '__main__':
    main()
