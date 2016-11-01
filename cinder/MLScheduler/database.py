import mysql.connector
from datetime import datetime
from mysql.connector import errorcode
import uuid
import common
# from mysql.connector import MySQLConnection, Error

def __create_connection():

    return mysql.connector.connect(user='babak', password='123',
                                          host='10.18.75.100',
                                          database='MLScheduler')


def __execute_insert_procedure(name, args):
    """
    calls a stored procedure for insert only, must have an out variable to return the inserted id
    :param name:
    :param args:
    :return: inserted id
    """

    try:
        args = list(args)
        args.append(-1)
        args = tuple(args)

        conn = __create_connection()

        cursor = conn.cursor()

        output = cursor.callproc(name, args)

        conn.commit()

        # print out the result
        # for result in cursor.stored_results():
        #     print(result.fetchall())

        output = list(output)
        inser_id = output[len(output) - 1]

        common.log("INSERT Called: %s ID: %s args-output: %s" % (name, inser_id, output), debug=True)

        return inser_id

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
	volume_request_id, #		VARCHAR(36),
    response_id, #		INT(11),
	create_clock, #			    INT(11),
	create_time #	DATETIME
    ):

    args = (
        experiment_id,  # VARCHAR(36),
        volume_request_id,  # VARCHAR(36),
        response_id,  # INT(11),
        create_clock,  # INT(11),
        create_time  # DATETIME
    )

    return __execute_insert_procedure("insert_schedule_response", args)

def insert_volume(
    experiment_id,  #            bigint
    cinder_id,  #                VARCHAR(36)
    backend_cinder_id,  #		VARCHAR(36),
    schedule_response_id,  #		bigint,
    capacity,  #					INT(11),
    create_clock,  # INT(11),
	create_time #	DATETIME
):
    sharp_index = backend_cinder_id.index("#")
    if sharp_index > 0:
        backend_cinder_id = backend_cinder_id[0:sharp_index]

    args = (
        experiment_id,
        cinder_id,
        backend_cinder_id,  # VARCHAR(36),
        schedule_response_id,  # bigint,
        capacity,  # INT(11),
        create_clock,  # INT(11),
        create_time  # datetime
    )

    return __execute_insert_procedure("insert_volume", args)

def insert_volume_performance_meter(
        experiment_id,
        backend_id,
        volume_id,
        read_iops,
        write_iops,
        sla_violation_id,
        io_test_output,
        create_clock,
        create_time):


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

    return __execute_insert_procedure("insert_volume_performance_meter", args)

def insert_volume_request(
    workload_id, #		bigint,
    capacity, #			INT(11),
    type, #				INT(11),
    read_iops, #		INT(11),
    write_iops, #		INT(11),
    create_clock, #		INT(11),
    create_time  # DATETIME
):
    args = (
        workload_id,  # bigint,
        capacity,  # INT(11),
        type,  # INT(11),
        read_iops,  # INT(11),
        write_iops,  # INT(11),
        create_clock,  # INT(11),
        create_time  # DATETIME(6)
    )

    return __execute_insert_procedure("insert_volume_request", args)

def insert_workload(
    comment, #		MEDIUMTEXT,
    generate_method, #			INT(11),
    create_time  # DATETIME
):
    args = (
        comment,  # MEDIUMTEXT,
        generate_method,  # INT(11),
        create_time  # DATETIME
    )

    return __execute_insert_procedure("insert_workload", args)

if __name__ == '__main__':

    # insert_volume(cinder_id='c55', backend_ID=1, schedule_response_ID=1, capacity=1)

    print insert_volume_request(workload_id=1, capacity=1, type=0, read_iops=500, write_iops=500, create_clock=0, create_time=datetime.now())

    pass