import imp


def can_load_pync():
    try:
        imp.find_module('pync')
        found = True
    except ImportError:
        found = False

    return found


class PyncNotifier:

    def notify(self, msg, title='GitSync'):
        from pync import Notifier
        Notifier.notify(msg, title)


class TerminalNotifier:

    def notify(self, msg, title='GitSync'):
        print(msg)


class GitNotified:

    notifier = None

    def __init__(self):

        if can_load_pync():
            self.notifier = PyncNotifier()
        else:
            self.notifier = TerminalNotifier()

    def sync_failed(self):
        self.notifer.notify('Sync Failed')

    def sync_start(self, local_path, remote_path, remote_host):
        self.notifer.notify(
            "Starting to sync %s and %s on %s" % (
                local_path,
                remote_path,
                remote_host,
            ),
            title='GitSync'
        )

    def sync_done(self, local_path, remote_path, remote_host):
        self.notifer.notify(
            "Completed sync of %s and %s on %s" % (
                local_path,
                remote_path,
                remote_host,
            ),
            title='GitSync'
        )
