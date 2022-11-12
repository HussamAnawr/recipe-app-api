"""
Django management command to wait for database avaliablity
"""
import time
from django.core.management.base import BaseCommand
from django.db.utils import OperationalError
from psycopg2 import OperationalError as Psycopg2Error

class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write('Waiting for database ... ')
        db_up = False
        while db_up is False:
            try:
                self.check(databases=['default'])
                db_up = True
            except (Psycopg2Error, OperationalError):
                self.stdout.write('Database unavailable, wait for one second')
                time.sleep(1)
        
        self.stdout.write(self.style.SUCCESS('Database available'))