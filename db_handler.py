import logging.config

import mysql.connector

LOG = logging.getLogger(__name__)

class DBHandler:
    def __init__(self, db_options):
        self.db_options = db_options
        self.db_object = mysql.connector.connect(
            host=self.db_options["host"],
            port=self.db_options["port"],
            database=self.db_options["database"],
            user=self.db_options["user"],
            password=self.db_options["password"]
        )
        self.cursor = self.db_object.cursor()

    def execute_query(self, query):
        self.cursor.execute(query)
        result = self.cursor.fetchall()
        LOG.info("Query - "+query+" executed")
        return result

    def close_connection(self):
        self.db_object.close()
        LOG.info("DB connection closed")