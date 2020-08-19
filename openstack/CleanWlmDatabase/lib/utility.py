import mysql.connector
from mysql.connector import errorcode
import json
import logging


def setup_logger(logger_name, log_file, level=logging.INFO):
    log_setup = logging.getLogger(logger_name)
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setFormatter(formatter)
    log_setup.setLevel(level)
    log_setup.addHandler(file_handler)
    return log_setup


def file_manager(filename, logger, file_type='JSON', mode='r'):
    try:
        if file_type == 'JSON':
            if mode == 'r':
                with open(filename, mode) as f:
                    return json.loads(f.read())

        elif file_type == 'text':
            if mode == 'r':
                with open(filename, mode) as f:
                    return [x.strip() for x in f.readlines()]

    except Exception as err:
        logger.exception(err)
        raise err


def connect_db(logger):
    cursor = None
    try:
        conn_details = file_manager('config/connection.json', logger)
        connection = mysql.connector.connect(**conn_details)
        if connection.is_connected():
            logger.info("DB Connection Established with host %s of database %s \n" %
                         (conn_details['host'], conn_details['database']))
            cursor = connection.cursor()

    except (mysql.connector.Error, Exception) as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logger.error("Bad Credentials for %s \n" % conn_details['database'])
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logger.exception("Database %s does not exist \n" % conn_details['database'])
        else:
            logger.exception(err)
        raise err

    else:
        return connection, cursor


