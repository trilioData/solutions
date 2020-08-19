import os
import datetime
from lib.utility import (setup_logger,
                         file_manager,
                         connect_db
                         )


def delete_workload(curr, conn, workload_ids):
    for workload_id in workload_ids:
        try:
            workload_exists = "SELECT EXISTS(SELECT * FROM workloads WHERE id = %s)"
            curr.execute(workload_exists, (workload_id,))
            temp = curr.fetchall()[0][0]
            if temp == 1:
                Log_wlm_delete.info("workload_id: %s Exists" % workload_id)
                query = "DELETE FROM workloads WHERE id = %s"
                curr.execute(query, (workload_id,))
                Log_wlm_delete.info("workload_id: %s removed \n" % workload_id)
            else:
                Log_wlm.info("workload_id: %s doesn't Exist \n" % workload_id)
            conn.commit()

        except Exception as err:
            Log_wlm.exception(err)
            raise err


if __name__ == '__main__':

    conn = None
    cursor = None

    dir_name = 'log/workloadmgr-' + datetime.datetime.now().strftime('%b-%d-%Y-%H:%M:%S')
    log_dir = os.path.join(os.getcwd(), dir_name)
    os.makedirs(log_dir)
    workload_gen = log_dir + '/workloadmgr-workloads.log'
    workload_del = log_dir + '/workloadmgr-workloads-delete.log'
    Log_wlm = setup_logger('workloadmgr', workload_gen)
    Log_wlm_delete = setup_logger('workloadmgr_del', workload_del)
    try:
        conn, cursor = connect_db(Log_wlm)
        if cursor:
            workload_ids = file_manager('config/workload_ids.txt', Log_wlm, file_type='text', mode='r')
            delete_workload(cursor, conn, workload_ids)

    except Exception as err:
        Log_wlm.exception(err)

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            Log_wlm.info("connection closed \n")

