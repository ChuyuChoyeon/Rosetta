import psycopg
from psycopg import sql
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Creates the database if it doesn't exist (PostgreSQL only)"

    def handle(self, *args, **options):
        db_settings = settings.DATABASES["default"]
        
        # Ensure we are using PostgreSQL
        if "postgresql" not in db_settings["ENGINE"]:
            self.stdout.write(self.style.ERROR("This command only supports PostgreSQL."))
            return

        dbname = db_settings["NAME"]
        user = db_settings["USER"]
        password = db_settings["PASSWORD"]
        host = db_settings["HOST"]
        port = db_settings["PORT"]

        # Connection parameters for the default 'postgres' database
        # We need to connect to 'postgres' to create a new database
        conn_params = {
            "dbname": "postgres",
            "user": user,
            "password": password,
            "host": host,
            "port": port,
            "autocommit": True,
        }

        try:
            self.stdout.write(f"Connecting to 'postgres' database at {host}:{port}...")
            conn = psycopg.connect(**conn_params)
            cursor = conn.cursor()

            # Check if database exists
            self.stdout.write(f"Checking if database '{dbname}' exists...")
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", [dbname])
            exists = cursor.fetchone()

            if not exists:
                self.stdout.write(f"Creating database '{dbname}'...")
                # Use sql.Identifier to safely quote the database name
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
                self.stdout.write(self.style.SUCCESS(f"Database '{dbname}' created successfully."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Database '{dbname}' already exists."))

            cursor.close()
            conn.close()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating database: {e}"))
            exit(1)
