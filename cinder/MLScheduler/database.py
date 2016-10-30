import mysql.connector
from datetime import datetime
from mysql.connector import errorcode
import uuid
# from mysql.connector import MySQLConnection, Error

def __create_connection():

    return mysql.connector.connect(user='babak', password='123',
                                          host='10.18.75.100',
                                          database='MLScheduler')


def __execute_procedure(name, args):

    try:
        conn = __create_connection()

        cursor = conn.cursor()

        cursor.callproc(name, args)

        conn.commit()

        # print out the result
        # for result in cursor.stored_results():
        #     print(result.fetchall())

        return 'return not implimented yet'

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

    finally:
        conn.commit()
        cursor.close()
        conn.close()

def insert_schedule_response(
	experiment_id, #			VARCHAR(36),
	volume_request_ID, #		VARCHAR(36),
	rejection_reason_ID, #		INT(11),
	create_clock = 0, #			    INT(11),
	create_time = datetime.now() #	DATETIME
    ):

    args = (
        experiment_id,  # VARCHAR(36),
        volume_request_ID,  # VARCHAR(36),
        rejection_reason_ID,  # INT(11),
        create_clock,  # INT(11),
        create_time  # DATETIME
    )

    return __execute_procedure("insert_schedule_response", args)

def insert_volume(
    cinder_id, #                VARCHAR(36)
    backend_ID, #				bigint,
    schedule_response_ID, #		bigint,
    capacity, #					INT(11),
    is_deleted = 0, #				BIT(1),
    delete_clock = None,  # INT(11),
    delete_time = None,  # datetime,
    create_clock = 0,  # INT(11),
	create_time = datetime.now() #	DATETIME
):

    args = (
        cinder_id,
        backend_ID,  # bigint,
        schedule_response_ID,  # bigint,
        capacity,  # INT(11),
        is_deleted,  # BIT(1),
        delete_clock,  # INT(11),
        delete_time,  # datetime,
        create_clock,  # INT(11),
        create_time  # datetime
    )

    return __execute_procedure("insert_volume", args)

def insert_volume_performance_meter(
        experiment_id,
        backend_id,
        volume_id,
        read_iops,
        write_iops,
        sla_violation_id,
        io_test_output,
        create_clock = 0,
        create_time=datetime.now()):


    args = (
        experiment_id,  # experiment_ID				bigint,
        backend_id,  # backend_ID					bigint,
        volume_id,  # volume_ID					bigint,
        read_iops,  # read_IOPS						int,
        write_iops,  # write_IOPS						int,
        sla_violation_id,  # SLA_violation_ID				int,
        io_test_output,  # io_test_output			    LONGTEXT
        create_clock,  # create_clock					int,
        create_time,  # create_time		DateTime,
    )

    return __execute_procedure("insert_volume_performance_meter", args)

def insert_volume_request(
    workload_ID, #		bigint,
    Capacity, #			INT(11),
    type, #				INT(11),
    read_IOPS, #		INT(11),
    write_IOPS, #		INT(11),
    create_clock = 0, #		INT(11),
    create_time=datetime.now()  # DATETIME
):
    args = (
        workload_ID,  # bigint,
        Capacity,  # INT(11),
        type,  # INT(11),
        read_IOPS,  # INT(11),
        write_IOPS,  # INT(11),
        create_clock,  # INT(11),
        create_time  # DATETIME(6)
    )

    return __execute_procedure("insert_volume_request", args)

def insert_workload(
    comment, #		MEDIUMTEXT,
    generate_method, #			INT(11),
    create_time=datetime.now()  # DATETIME
):
    args = (
        comment,  # MEDIUMTEXT,
        generate_method,  # INT(11),
        create_time  # DATETIME
    )

    return __execute_procedure("insert_workload", args)

if __name__ == '__main__':

    insert_volume(
        cinder_id='c55',
        backend_ID=1,
        schedule_response_ID=1,
        capacity=1
    )
    # pass