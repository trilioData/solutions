import re
import datetime
import os

from lib.utility import (setup_logger,
                         file_manager,
                         connect_db
                         )


def drop_and_alter_fk(records, curr):

    for record in records:
        constraint_name = record['constraint_name']
        fkey_table_name = record['fkey_table_name']
        delete_rule = record['delete_rule']

        try:
            if delete_rule != "RESTRICT":
                log_before_fkey_modify.info("Modifying {} set on {} with Rule {} NOT required \n".format(constraint_name, fkey_table_name, delete_rule))
            else:
                query = "show create table " + fkey_table_name
                log_show_create_table.info("<=======Before dropping {} from {} definition =======>".format(constraint_name, fkey_table_name))
                curr.execute(query)
                log_show_create_table.info("{} \n".format(curr.fetchall()))

                fk_def = get_constraint_def(fkey_table_name, curr, constraint_name)

                new_fk_def = fk_def + " ON DELETE CASCADE"
                drop_fk_query = 'alter table ' + fkey_table_name + ' drop FOREIGN KEY ' + constraint_name
                new_fk_query = 'alter table ' + fkey_table_name + ' add ' + new_fk_def
                log_before_fkey_modify.info("Dropping {} from {} \n".format(constraint_name, fkey_table_name))
                curr.execute(drop_fk_query)
                curr.execute(new_fk_query)
                log_after_fkey_modify.info("<=======After modifying {} from {} modified definition =======>".format(constraint_name, fkey_table_name))
                modified_fk_def = get_constraint_def(fkey_table_name, curr, constraint_name)
                log_after_fkey_modify.info("{} \n".format(modified_fk_def))
        except Exception as err:
            log_gen.exception(err)


def get_constraint_def(table_name, curr, constraint):
    query = "show create table " + table_name
    try:
        curr.execute(query)
        temp = cursor.fetchall()[0][1]
        lines = temp.splitlines()
        match_pattern = constraint
        for line in lines:
            if re.search(r'\b{}\b'.format(match_pattern), line):
                return str(line.replace("`", "").replace(',', '')).strip()
    except Exception as err:
        log_gen.exception(err)
        raise err


def get_db_data(curr):
    context = []
    try:
        conn_details = file_manager('config/connection.json', log_gen)
        table_schema = conn_details['database']
        query = """
                SELECT r.CONSTRAINT_NAME, r.DELETE_RULE, r.TABLE_NAME,
                GROUP_CONCAT(k.COLUMN_NAME SEPARATOR ', ') AS constraint_columns,
                r.REFERENCED_TABLE_NAME, k.REFERENCED_COLUMN_NAME FROM
                information_schema.REFERENTIAL_CONSTRAINTS r JOIN
                information_schema.KEY_COLUMN_USAGE k USING
                (CONSTRAINT_CATALOG, CONSTRAINT_SCHEMA, CONSTRAINT_NAME) where
                k.TABLE_SCHEMA = '{table_schema}' GROUP BY
                r.CONSTRAINT_CATALOG,r.CONSTRAINT_SCHEMA,r.CONSTRAINT_NAME
                """.format(table_schema=table_schema)
        curr.execute(query)
        col_len = len(curr.description)
        if col_len:
            table_col_data = file_manager('lib/table_col.json', log_gen)
            col_names = [cursor.description[i][0] for i in range(col_len)]
            for row in cursor:
                fKeyData = dict(zip(col_names, row))
                fkey_table_name = fKeyData['TABLE_NAME']
                constraint_column = fKeyData['constraint_columns']

                if fkey_table_name in table_col_data and table_col_data[fkey_table_name] == constraint_column:
                    context.append(
                        {'constraint_name': fKeyData['CONSTRAINT_NAME'],
                         'referenced_table_name': fKeyData['REFERENCED_TABLE_NAME'],
                         'referenced_col_name': fKeyData['REFERENCED_COLUMN_NAME'],
                         'constraint_column': constraint_column,
                         'fkey_table_name': fkey_table_name,
                         'delete_rule': fKeyData['DELETE_RULE']
                         }
                    )

    except Exception as err:
        log_gen.exception(err)
    return context


if __name__ == '__main__':
    
    conn = None
    cursor = None

    dir_name = 'enable-physical-delete-' + datetime.datetime.now().strftime('%b-%d-%Y-%H:%M:%S')
    log_dir = os.path.join(os.getcwd(), 'log', dir_name)
    os.makedirs(log_dir)
    before_fkey_modify = log_dir + '/before-fkey-modify.log'
    after_fkey_modify = log_dir + '/after-fkey-modify.log'
    enable_physical_delete = log_dir + '/enable-physical-delete.log'
    show_create_table = log_dir + '/show-create-table.log'
    log_before_fkey_modify = setup_logger('before-fkey-modify', before_fkey_modify)
    log_after_fkey_modify = setup_logger('after-fkey-modify', after_fkey_modify)
    log_gen = setup_logger('enable-physical-delete', enable_physical_delete)
    log_show_create_table = setup_logger('show_create_table', show_create_table)

    try:
        conn, cursor = connect_db(log_gen)
        if cursor:
            db_data = get_db_data(cursor)
            if db_data:
                drop_and_alter_fk(db_data, cursor)

            else:
                log_gen.info("Database is Empty")

    except Exception as err:
        log_gen.exception(err)

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            log_gen.info("connection closed")







