import sqlite3
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
class Command(BaseCommand):
    help='Create a consistent SQLite backup using its online backup API.'
    def add_arguments(self,parser): parser.add_argument('destination')
    def handle(self,*args,**options):
        destination=Path(options['destination']).resolve()
        if destination.exists(): raise CommandError('Destination already exists; choose a new backup filename.')
        with sqlite3.connect(settings.DATABASES['default']['NAME']) as source,sqlite3.connect(destination) as target: source.backup(target)
        self.stdout.write('Backup created: '+str(destination))
