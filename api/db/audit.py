# pylint: disable=protected-access


from sqlalchemy import Column, String, event, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from db import AuditedMixin, Base, DictifiableMixin, QueryMethodsMixin
from db.types.nested import NestedMutableDict

_TABLE_NAME = "data_changes"
FUNC_NAME = "audit"


class DataChanges(Base, DictifiableMixin, AuditedMixin, QueryMethodsMixin):
    __tablename__ = _TABLE_NAME

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    schema = Column(String)
    table_name = Column(String)
    operation = Column(String)
    new = Column(JSONB)
    old = Column(JSONB)


@event.listens_for(Base.metadata, "before_create")
def create_audit_trigger(_target, connection, **_):
    connection.execute(text(f"""
CREATE OR REPLACE FUNCTION {FUNC_NAME}() RETURNS trigger AS $$
    BEGIN
        IF TG_OP = 'INSERT'
        THEN
            INSERT INTO {_TABLE_NAME} (table_name, schema, operation, new)
            VALUES (TG_RELNAME, TG_TABLE_SCHEMA, TG_OP, row_to_json(NEW));
            RETURN NEW;
        ELSIF TG_OP = 'UPDATE'
        THEN
            INSERT INTO {_TABLE_NAME} (table_name, schema, operation, new, old)
            VALUES (TG_RELNAME, TG_TABLE_SCHEMA, TG_OP, row_to_json(NEW), row_to_json(OLD));
            RETURN NEW;
        ELSIF TG_OP = 'DELETE'
        THEN
            INSERT INTO {_TABLE_NAME} (table_name, schema, operation, old)
            VALUES (TG_RELNAME, TG_TABLE_SCHEMA, TG_OP, row_to_json(OLD));
            RETURN OLD;
        END IF;
    END;
$$ LANGUAGE 'plpgsql'
"""))


@event.listens_for(Base.metadata, "after_drop")
def drop_audit_trigger(_target, connection, **_):
    connection.execute(text(f"DROP FUNCTION IF EXISTS {FUNC_NAME}"))


def setup_trigger(table):
    trigger_name = f"{table.__tablename__}_audit"

    trigger_desc = f"""
    CREATE TRIGGER {trigger_name}
    BEFORE
        INSERT OR UPDATE OR DELETE
    ON
        {table.__tablename__}
    FOR EACH ROW
    EXECUTE PROCEDURE {FUNC_NAME}()
    """

    @event.listens_for(table.__table__, "after_create")
    def create_trigger(_target, connection, **_):  # pylint: disable=unused-variable
        connection.execute(text(trigger_desc))

    @event.listens_for(table.__table__, "before_drop")
    def drop_trigger(_target, connection, **_):  # pylint: disable=unused-variable
        connection.execute(text(f"DROP TRIGGER IF EXISTS {trigger_name} ON {table.__tablename__}"))


class Audit(Base, DictifiableMixin, QueryMethodsMixin, AuditedMixin):
    __tablename__ = "audit"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    type = Column(String, nullable=False)
    content = Column(NestedMutableDict.as_mutable(JSONB))
