import logging
from logging import Handler
from pydantic import BaseModel, ValidationError, Field
from typing import Optional
from datetime import datetime
from sqlalchemy import create_engine, Table, Column, String, MetaData, DateTime
from sqlalchemy.orm import sessionmaker

class LogRecord(BaseModel):
    username: str
    action: str
    created: Optional[datetime] = Field(default_factory=datetime.now)

    class Config:
        validate_assignment = True

    @classmethod
    def validate_created(cls, v):
        return v or datetime.now()

class AuditPostgresHandler(Handler):
    def __init__(self, connection_string, audit_table_name):
        super().__init__()
        self.connection_string = connection_string
        self.audit_table_name = audit_table_name
        self.engine = create_engine(self.connection_string)
        self.Session = sessionmaker(bind=self.engine)
        self.metadata = MetaData()
        self.audit_table = Table(
            self.audit_table_name, self.metadata,
            Column('username', String, primary_key=True),
            Column('action', String),
            Column('action_timestamp', DateTime, default=datetime.now)
        )
        self.metadata.create_all(self.engine)

    def emit(self, record):
        try:
            # Assuming the message is a dictionary containing username and action
            log_message = record.msg
            if isinstance(log_message, dict) and 'username' in log_message and 'action' in log_message:
                log_record = LogRecord(username=log_message['username'], action=log_message['action'])
                with self.Session() as session:
                    ins = self.audit_table.insert().values(
                        username=log_record.username,
                        action=log_record.action,
                        action_timestamp=log_record.created
                    )
                    session.execute(ins)
                    session.commit()
            else:
                raise ValueError("Log message must be a dictionary containing 'username' and 'action'")
        except ValidationError as e:
            print("Validation error occurred while logging to PostgreSQL:", e)
        except Exception as e:
            print("Error occurred while logging to PostgreSQL:", e)

def setup_audit_logging(connection_string, audit_table_name, logger_name=None, level=logging.INFO):
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    audit_postgres_handler = AuditPostgresHandler(connection_string, audit_table_name)
    logger.addHandler(audit_postgres_handler)
    return logger

# Example usage
if __name__ == "__main__":
    connection_string = "postgresql://username:password@localhost/mydatabase"
    audit_table_name = "audit_logs"

    logger = setup_audit_logging(connection_string, audit_table_name)
    logger.info({"username": "test_user", "action": "login"})
