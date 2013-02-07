GitSync
=======

This tool allows a developer to work on files on their local machine and have their work synced on a remote system. It uses git to manage the syncing process.

The use case that inspired this tool is web development where the development environment is a remote server. Many of the most useful development tools require (or at least work a lot better) in low latency environments. Since you local file system is about as low latency as it gets there's really where you want to do your work. However if you actually want to run your application you need your code to be on a remote system, this presents a problem. Especially if you do not have a screaming fast connection between your local machine and the remote one.

This tool takes the syncing of your local file system and the remote system "out of band" so there are fewer interruptions.

This tool relies heavily on the git version control system. Before you try to use it I would recommend getting a basic understanding of how git works. This tool should take care of most (if not all) of the work but if you want take advantage of its full power you will need to understand how git works. Here are some places to get started:

 - Git Home http://git-scm.com/

 - Git Tutorial http://www.ralfebert.de/tutorials/git/

 - Understanding Git Conceptually http://www.eecs.harvard.edu/~cduan/technical/git/


OS X Dependencies
-----------------

Skip any steps that install software you already have.

1. Install Homebrew 
   http://mxcl.github.com/homebrew/
2. Install git 
   ```brew install git```
3. Install python
   ```brew install python```
4. Install pip
   ```sudo easy_install pip```
5. Install fabric
   ```sudo pip install fabric```
6. Install the python library of Mac FS Events
   ```sudo pip install MacFSEvents```
7. Install the python binding for growl.
   ```sudo pip install gntp```
8. Install libyaml
   ```brew install libyaml```
9. Install PyYAML
   ```sudo pip install PyYAML```
10. Install Growl 2 (from the app store) http://growl.info/


Remote Dependencies
-------------------

The Remote system needs to be setup with the following things.

1. SSH access.

2. SSH Keys to allow authentication with having to put in passwords.

3. Git needs to be installed.


Configuration
-------------

The assumption git sync makes (right now) is that the latest version of your stuff is on the remote system.

On the first sync it will assume the location on the local file system is empty and the first thing it needs to do is pull down the files from the remote system.

1. Copy the example configuration file (examples/git_sync.yaml) giving it an appropriate name.

2. Set all the values in the config file.
   - local_path: This is the path on your local machine where you want your files to go.
   - local_branch_name: The name of the git branch you want git sync to use.
   - remote_host: The IP or domain name of the remote system you want to use.
   - remote_user: Your username on the remote system
   - remote_path: The path on the remote system with the files in it you want to sync with.
   - git_ignore: A list of patterns you want git to ignore, in this context that means these are files that will not get synced.

Current Git Users: Caution
--------------------------

If you are already using git as a version control system, be careful. This has been take in into account (somewhat) but not really tested been tested yet.


Running git_sync.py
-------------------

In Terminal run the following command:
```python path/to/git_sync.py path/to/your/config/file.yaml```

It should do some setup work. This could take a lot time if this is the initial sync, if there are a lot of changes or if the network connection is slow.

Once it's done start working. Open files. Save files. Create files. Every time you do something that results in a file system event you should see a growl notification that git sync has started and shortly after another one that it is finished.

Once the sync in finished, check on the server, and the changes should have been synced.

License
-------

- [LICENSE](LICENSE) ([MIT License][MIT])

[MIT]: http://www.opensource.org/licenses/MIT "The MIT License (MIT)"
