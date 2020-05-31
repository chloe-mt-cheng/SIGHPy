from .file_parser import file_parser
from .flask_utils import db_initialize, update_table


def fetch_to_db(filepath: str, file_tables: list, to_db: str = None, create_new: list = None, db_tables: list = None):
    nest_check = [isinstance(tab_name, list) for tab_name in file_tables]

    def nester(tab, truth):
        if truth:
            return tab
        else:
            return [tab]

    file_tables = list(map(nester, file_tables, nest_check))
    dfs, keys, _ = file_parser(filepath, file_tables, create_new)

    if to_db:
        engine = db_initialize(db_name=to_db)
    else:
        engine = db_initialize()

    if not db_tables:
        db_tables = []
        [db_tables.append(k[0].replace("/", "_")) for k in keys]

    return update_table(engine, db_tables, dfs)
