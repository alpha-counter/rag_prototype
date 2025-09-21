from sqlalchemy import create_engine, Table, Column, String, MetaData, select, insert, update
from sqlalchemy.orm import sessionmaker
import re

class SettingsManager:
    def __init__(self, db_connection_string, settings_table_name):
        self.db_connection_string = db_connection_string
        self.settings_table_name = settings_table_name
        self.engine = create_engine(self.db_connection_string)
        self.Session = sessionmaker(bind=self.engine)
        self.metadata = MetaData()
        self.settings_table = Table(
            self.settings_table_name, self.metadata,
            Column('key', String, primary_key=True),
            Column('value', String)
        )
        self.settings = self._load_settings()

    def _load_settings(self):
        settings = {}
        with self.Session() as session:
            query = select([self.settings_table.c.key, self.settings_table.c.value])
            results = session.execute(query).fetchall()
            for row in results:
                settings[row.key] = row.value
        return settings

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def get_int(self, key, default=0):
        try:
            return int(self.settings.get(key, default))
        except ValueError:
            return default

    def get_bool(self, key, default=False):
        value = self.settings.get(key, str(default)).lower()
        return value in ['true', '1', 't', 'yes']

    def set(self, key, value):
        self.settings[key] = value
        self._save_setting(key, value)

    def _save_setting(self, key, value):
        with self.Session() as session:
            query = insert(self.settings_table).values(key=key, value=value).on_conflict_do_update(
                index_elements=['key'],
                set_=dict(value=value)
            )
            session.execute(query)
            session.commit()

    def reload(self):
        self.settings = self._load_settings()

    def validate_key(self, key):
        if not re.match(r'^[A-Za-z0-9_]+$', key):
            raise ValueError("Invalid key name")
