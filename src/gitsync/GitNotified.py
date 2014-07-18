from pync import Notifier


class GitNotified:

    def __init__(self):
        self

    def sync_failed(self):
        Notifier.notify('Sync Failed', title='GitSync')

    def sync_start(self, local_path, remote_path, remote_host):
        Notifier.notify(
            "Starting to sync %s and %s on %s" % (
                local_path,
                remote_path,
                remote_host,
            ),
            title='GitSync'
        )

    def sync_done(self, local_path, remote_path, remote_host):
        Notifier.notify(
            "Completed sync of %s and %s on %s" % (
                local_path,
                remote_path,
                remote_host,
            ),
            title='GitSync'
        )
