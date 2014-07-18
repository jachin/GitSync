import unittest
from pprint import pprint

from fabric.api import env, local, run, execute, task
from fabric.context_managers import lcd, cd, settings, hide
from fabric.contrib.files import append

host = '10.10.10.11'

text_1 = """Nullam id dolor id nibh ultricies vehicula ut id elit.
Aenean eu leo quam. Pellentesque ornare sem lacinia quam venenatis vestibulum.
"""

text_2 = """Sed posuere consectetur est at lobortis. Integer posuere erat a
ante venenatis dapibus posuere velit aliquet. """

text_3 = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras
justo odio, dapibus ac facilisis in, egestas eget quam. Vivamus sagittis lacus
vel augue laoreet rutrum faucibus dolor auctor. Etiam porta sem malesuada
magna mollis euismod. Nullam id dolor id nibh ultricies vehicula ut id elit.
"""

config_yaml = """
local_path: /vagrant/scratch
local_branch: unittesting
remote_host: {0}
remote_user: vagrant
remote_path: /home/vagrant/scratch
""".format(host)

@task
def setup_remote_repo():
    delete_remote_repo()
    run( 'mkdir /home/vagrant/scratch' );
    with cd('/home/vagrant/scratch'):
        run("touch one.txt")
        run("touch two.txt")
        run("touch three.txt")

        append('one.txt', text_1)
        append('two.txt', text_2)
        append('three.txt', text_3)


@task
def delete_remote_repo():
    run("rm -Rf /home/vagrant/scratch")

@task
def update_yaml():
    with lcd('/vagrant'):
        local("echo '{0}' > scratch.yaml".format(config_yaml));


class GitSyncTest(unittest.TestCase):

    def setUp(self):
        execute(
            setup_remote_repo,
            hosts=[host],
        )

    def tearDown(self):
        execute(
            delete_remote_repo,
            hosts=[host],
        )

    @task
    def simple_change(self):
        with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
            with cd('/home/vagrant/scratch'):
                self.assertTrue(True)
                self.assertTrue(run("ls one.txt").succeeded)
                self.assertTrue(run("ls not_real.txt").failed)

    @task
    def init_git_sync(self):
        with lcd('/vagrant'):
            local("echo '{0}' > scratch.yaml".format(config_yaml));

    def test_simple_change(self):
        update_yaml()
        execute(self.simple_change,self,hosts=[host],)

if __name__ == '__main__':
    unittest.main()