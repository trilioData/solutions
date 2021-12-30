import os
import datetime
from lib.utility import (setup_logger,
                         file_manager,
                         connect_db
                         )


def delete_snapshots(curr, conn, snapshots_ids):
    for snapshot_id in snapshot_ids:
        try:
            snapshot_exists = "SELECT EXISTS(SELECT * FROM snapshots WHERE id = %s AND deleted = 1 AND status = \"deleted\")"
            curr.execute(snapshot_exists, (snapshot_id,))
            temp = curr.fetchall()[0][0]
            if temp == 1:
                Log_wlm_delete.info("snapshot_id: %s Exists" % snapshot_id)
                query = "DELETE FROM snapshots WHERE id = %s"
                curr.execute(query, (snapshot_id,))
                Log_wlm_delete.info("snapshot_id: %s removed \n" % snapshot_id)
            else:
                Log_wlm.info("snapshot_id: %s doesn't Exist \n" % snapshot_id)
            conn.commit()

        except Exception as err:
            Log_wlm.exception(err)
            raise err


if __name__ == '__main__':

    conn = None
    cursor = None

    dir_name = 'log/snapshotmgr-' + datetime.datetime.now().strftime('%b-%d-%Y-%H:%M:%S')
    log_dir = os.path.join(os.getcwd(), dir_name)
    os.makedirs(log_dir)
    snapshot_gen = log_dir + '/snapshotmgr-snapshot.log'
    snapshot_del = log_dir + '/snapshotmgr-snapshot-delete.log'
    Log_wlm = setup_logger('snapshotmgr', snapshot_gen)
    Log_wlm_delete = setup_logger('snapshotmgr_del', snapshot_del)
    try:
        conn, cursor = connect_db(Log_wlm)
        if cursor:
            snapshot_ids = file_manager('config/snapshot_ids.txt', Log_wlm, file_type='text', mode='r')
            delete_snapshots(cursor, conn, snapshot_ids)

    except Exception as err:
        Log_wlm.exception(err)

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            Log_wlm.info("connection closed \n")

