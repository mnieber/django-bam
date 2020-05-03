import glob
import hashlib
import os
import sys

from dbbackup.storage import get_storage
from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from six.moves import input as raw_input


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--restore", action="store_true")
        parser.add_argument("migrate_options", nargs="*")

    def _app_dir(self, app_config):
        app_dir = os.path.dirname(app_config.module.__file__)
        if not settings.BAM_INCLUDE_APP_DIR(app_dir):
            return None
        return app_dir

    def _migrations_dir(self, app_config):
        app_dir = self._app_dir(app_config)
        if not app_dir:
            return None
        return os.path.join(app_dir, "migrations")

    def _hash(self, filename):
        with open(filename) as ifs:
            return hashlib.md5(ifs.read().encode("utf-8")).hexdigest()

    def handle(self, restore, migrate_options, *args, **options):
        hashes = []
        for app_config in apps.get_app_configs():
            migrations_dir = self._migrations_dir(app_config)
            if migrations_dir and os.path.exists(migrations_dir):
                for migration in glob.glob(os.path.join(migrations_dir, "*.py")):
                    if os.path.basename(migration) == "__init__.py":
                        continue
                    hashes.append(self._hash(migration))

        bam_id = (
            "bam-" + hashlib.md5("".join(sorted(hashes)).encode("utf-8")).hexdigest()
        )

        storage = get_storage()
        has_backup = bam_id in storage.list_directory()

        if restore:
            if has_backup:
                call_command("reset_db")
                call_command("migrate")
                call_command("dbrestore", "-i", bam_id)
            else:
                print("No backup for the current set of migrations exists")
        else:
            if has_backup:
                if query_yes_no(
                    "A backup (%s) for the current set of migrations" % bam_id +
                    " already exists, continue?"
                ):
                    storage.delete_file(bam_id)
                else:
                    return

            call_command("migrate", *migrate_options)
            call_command("dbbackup", "-o", bam_id)
