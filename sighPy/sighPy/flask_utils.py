from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData
import pandas as pd
import os.path


def db_initialize(db_name="flask_app.db", track_modif=False):
    app = Flask(__name__)
    engine_name = 'sqlite:///' + db_name
    app.config['SQLALCHEMY_DATABASE_URI'] = engine_name
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = track_modif
    db = SQLAlchemy(app)
    if os.path.isfile(db_name):
        engine = create_engine(engine_name)
        return engine
    else:
        db.create_all()
        engine = create_engine(engine_name)
        return engine


def update_table(db_engine, table_names: list, user_dfs: list) -> None:
    name_str_check = all([isinstance(n, str) for n in table_names])
    if not name_str_check:
        raise ValueError("Non string type in table_names list-like.")
    user_df_check = all([isinstance(d, pd.core.frame.DataFrame) for d in user_dfs])
    if not user_df_check:
        raise ValueError("Non DataFrame type in user_dfs list-like.")
    if len(table_names) != len(user_dfs):
        raise ValueError("Invalid or mismatched table_names and user_dfs list-likes.")
    db_metadata = MetaData(bind=db_engine, reflect=True)
    metadata_table = db_metadata.tables
    is_exists_list = [(t in metadata_table) for t in table_names]
    for table_name, user_df, is_exists in zip(table_names, user_dfs, is_exists_list):
        if is_exists:
            table_column_object = metadata_table[table_name].c
            table_columns = [col.key for col in table_column_object]
            dataframe_xdim = len(list(user_df))
            if len(table_columns) != dataframe_xdim:
                raise ValueError("Supplied columns mismatched to known table columns: %s" % table_columns)
            user_df.columns = table_columns
            user_df.to_sql(name=table_name, con=db_engine,
                           if_exists='append', index=False)
        else:
            user_df.to_sql(name=table_name, con=db_engine,
                           if_exists='fail', index=False)


def result_to_json(db_engine, table_name: str, id_column: str = None, sql_string: str = None):
    db_metadata = MetaData(bind=db_engine, reflect=True)
    metadata_table = db_metadata.tables
    is_exists = table_name in metadata_table
    if not is_exists:
        raise ValueError("Supplied result_table not found: %s" % table_name)
    table_column_object = metadata_table[table_name].c
    table_columns = [col.key for col in table_column_object]
    key_index = None
    if id_column:
        key_index = table_columns.index(id_column)
    if sql_string is None:
        sql_string = "SELECT * FROM " + table_name
    result_list = db_engine.execute(sql_string).fetchall()
    output_dict = {}
    if key_index is not None:
        parent_key_index = 0
    for result in result_list:
        if key_index is not None:
            child_keys = [c for c in table_columns if c != table_columns[key_index]]
            child_values = [r for r in result if r != result[key_index]]
            item_append = dict(zip(child_keys, child_values))
        else:
            item_append = dict(zip(table_columns, result))
        if key_index is not None:
            output_dict[result[key_index]] = item_append
            continue
        output_dict[parent_key_index] = item_append
    return output_dict


def json_to_html(user_dict: dict, file_name: str):
    from static import html_temp
    from string import Template
    html_template = Template(html_temp)
    filled_template = html_template.substitute(result_json=user_dict)
    if ".html" not in file_name:
        raise ValueError("file_name not passed as .html, i.e. %s.html" % file_name)
    with open(file_name, "w", encoding='utf-8') as file:
        file.write(filled_template)
    return filled_template


def result_to_df(db_engine, table_name: str, sql_string: str = None):
    db_metadata = MetaData(bind=db_engine, reflect=True)
    metadata_table = db_metadata.tables
    is_exists = table_name in metadata_table
    if not is_exists:
        raise ValueError("Supplied result_table not found: %s" % table_name)
    table_column_object = metadata_table[table_name].c
    table_columns = [col.key for col in table_column_object]
    if sql_string is None:
        sql_string = "SELECT * FROM " + table_name
    result_list = db_engine.execute(sql_string).fetchall()
    out_frame = pd.DataFrame(result_list, columns=table_columns)
    return out_frame
