import mysql.connector
from datetime import datetime
from mysql.connector import errorcode
import MySQLdb
import MySQLdb.cursors
import MySQLdb.converters
import pdb
import tools


# from decimal import Decimal
# from mysql.connector import MySQLConnection, Error


def __create_connection_for_insert_delete():
    """
    I used out parameter in my stored procedures and it is not supported in MySQLdb. So for now I will use mysql.connector for insert and delete. In order to use MySQLdb I need to use select stateent instead of out variable in the stored procedures. Overll, that will be a lot of changes that I dont have time for now.

    Compatibility note: PEP-249 specifies that if there are OUT or INOUT parameters, the modified values are to be returned. This is not consistently possible with MySQL. Stored procedure arguments must be passed as server variables, and can only be returned with a SELECT statement. Since a stored procedure may return zero or more result sets, it is impossible for MySQLdb to determine if there are result sets to fetch before the modified parmeters are accessible.

    :return:
    """
    return mysql.connector.connect(user='babak', password='123',
                                   host='10.18.75.100',
                                   database='MLScheduler')


def __str_args(args):
    ret = []

    for value in args:

        if isinstance(value, basestring) and len(value) > 60:
            value = value[0: 60] + "..."
        ret.append(value)
    return str(ret)


def __create_connection_for_get():
    conv = MySQLdb.converters.conversions.copy()
    conv[246] = float  # convert decimals to floats
    conv[10] = str  # convert dates to strings

    return MySQLdb.connect(user='babak', passwd='123', host='10.18.75.100', db='MLScheduler', conv=conv)


def __execute_delete_procedure(name, args):
    try:
        conn = __create_connection_for_insert_delete()

        cursor = conn.cursor()

        output = cursor.callproc(name, args)

        conn.commit()

        tools.log("PROCEDURE CALLED [DELETE]: %s args-output: %s" % (name, __str_args(args)), insert_db=False)

    except mysql.connector.Error as err:
        tools.log(
            type="ERROR",
            code="db",
            file_name="database.py",
            function_name="__execute_delete_procedure",
            message="ARGS: %s" % args,
            exception=err)

    finally:

        cursor.close()
        conn.close()


def execute_get_procedure_dictionary(name, args=()):
    try:
        conn = __create_connection_for_get()

        cursor = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)

        cursor.callproc(name, args)

        result_sets = []

        while True:
            result_set = cursor.fetchall()

            if result_set != ():
                result_sets.append(result_set)

            try:
                if cursor.nextset() is None:
                    break
            except MySQLdb.Error as err:
                tools.log(
                    type="ERROR",
                    code="db",
                    file_name="database.py",
                    function_name="execute_get_procedure_dictionary",
                    message="ERROR in [] on cursor.nextset(). ARGS: %s\n" % (args),
                    exception=err)

                break

        tools.log("PROCEDURE CALLED [GET]: %s ARGS: %s result_sets LEN: %i" %
                  (name, __str_args(args), len(result_sets)), insert_db=False)

        if len(result_sets) == 1:
            result_sets = result_sets[0]

        return result_sets

    except MySQLdb.Error as err:

        tools.log(
            type="ERROR",
            code="db",
            file_name="database.py",
            function_name="execute_get_procedure_dictionary",
            message="",
            exception=err)

    finally:

        cursor.close()
        conn.close()


def execute_get_procedure_tuple(name, args=()):
    try:
        conn = __create_connection_for_get()

        cursor = conn.cursor(cursorclass=MySQLdb.cursors.Cursor)

        cursor.callproc(name, args)

        result_sets = []

        while True:
            if cursor.description is None:
                break

            result_set = ()

            field_names = tuple([i[0] for i in cursor.description])

            result_set = result_set + (field_names,)

            fall = cursor.fetchall()

            result_set = result_set + fall

            result_sets.append(result_set)

            cursor.nextset()

        tools.log("PROCEDURE CALLED [GET]: %s ARGS: %s OUTPUT result_sets Length: %s" %
                  (name, __str_args(args), len(result_sets)), insert_db=False)

        if len(result_sets) == 1:
            result_sets = result_sets[0]

        return result_sets

    except MySQLdb.Error as err:

        tools.log(
            type="ERROR",
            code="db",
            file_name="database.py",
            function_name="execute_get_procedure_tuple",
            message="ARGS: %s" % args,
            exception=err)

    finally:

        cursor.close()
        conn.close()


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

        conn = __create_connection_for_insert_delete()

        cursor = conn.cursor()

        output = cursor.callproc(name, args)

        conn.commit()

        output = list(output)
        insert_id = output[len(output) - 1]

        tools.log("PROCEDURE CALLED: %s OUTPUT: %s" %
                  (name, __str_args(output)), insert_db=False)

        return insert_id

    except MySQLdb.Error as err:
        tools.log(
            type="ERROR",
            code="db",
            file_name="database.py",
            function_name="__execute_insert_procedure",
            message="ARGS: %s" % args,
            exception=err)

    finally:

        cursor.close()
        conn.close()


def delete_volume(
        id,  # VARCHAR(36),
        cinder_id,  # VARCHAR(36),
        is_deleted,
        delete_clock,  # INT(11),
        delete_time  # INT(11),
):
    args = (
        id,
        cinder_id,
        is_deleted,
        delete_clock,
        delete_time
    )

    return __execute_delete_procedure("delete_volume", args)


def insert_tenant(
        experiment_id,  # VARCHAR(36),
        nova_id,  # VARCHAR(36),
        description,  # mediumtext,
        create_time  # DATETIME
):
    args = (
        experiment_id,  # VARCHAR(36),
        nova_id,  # VARCHAR(36),
        description,
        create_time  # DATETIME
    )

    return __execute_insert_procedure("insert_tenant", args)


def insert_schedule_response(
        experiment_id,  # VARCHAR(36),
        volume_request_id,  # VARCHAR(36),
        response_id,  # INT(11),
        create_clock,  # INT(11),
        create_time  # DATETIME
):
    args = (
        experiment_id,  # VARCHAR(36),
        volume_request_id,  # VARCHAR(36),
        response_id,  # INT(11),
        create_clock,  # INT(11),
        create_time  # DATETIME
    )

    return __execute_insert_procedure("insert_schedule_response", args)


def insert_backend(
        cinder_id,  # VARCHAR(36),
        experiment_id,  # bigint,
        capacity,  # INT(11),
        is_online, # bool
        description, # MEDIUMTEXT
        ml_model_Path, # VARCHAR(1000)
        create_clock,  # INT(11),
        create_time  # DATETIME
):
    args = (
        cinder_id,  # VARCHAR(36),
        experiment_id,  # VARCHAR(36),
        capacity,  # INT(11),
        is_online,
        description,
        ml_model_Path,
        create_clock,  # INT(11),
        create_time  # DATETIME
    )

    return __execute_insert_procedure("insert_backend", args)


def insert_volume(
        experiment_id,  # bigint
        cinder_id,  # VARCHAR(36)
        backend_cinder_id,  # VARCHAR(36),
        schedule_response_id,  # bigint,
        capacity,  # INT(11),
        create_clock,  # INT(11),
        create_time  # DATETIME
):
    # sharp_index = backend_cinder_id.index("#")
    # if sharp_index > 0:
    #     backend_cinder_id = backend_cinder_id[0:sharp_index]

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
        tenant_id,
        nova_id,
        backend_id,
        volume_id,
        cinder_volume_id,
        read_iops,
        write_iops,
        duration,
        sla_violation_id,
        io_test_output,
        terminate_wait,
        create_clock,
        create_time):
    args = (
        experiment_id,  # experiment_ID				bigint,
        tenant_id,
        nova_id,  # nova_id         VARCHAR(36)
        backend_id,  # backend_ID					bigint,
        volume_id,  # volume_ID					    bigint,
        cinder_volume_id,  # cinder_volume_id         VARCHAR(36)
        read_iops,  # read_IOPS						int,
        write_iops,  # write_IOPS					int,
        duration,  # duration                        float,
        sla_violation_id,  # SLA_violation_ID		int,
        io_test_output,  # io_test_output		    LONGTEXT
        terminate_wait,  # terminate_wait            int,
        create_clock,  # create_clock				int,
        create_time,  # create_time		            DateTime,
    )

    return __execute_insert_procedure("insert_volume_performance_meter", args)


def insert_experiment(
        workload_id,  # bigint,
        comment,  # MEDIUMTEXT
        scheduler_algorithm,  # MEDIUMTEXT
        config,  # LONGTEXT,
        workload_comment,  # MEDIUMTEXT
        workload_generate_method,  # int
        create_time):
    args = (
        workload_id,  # bigint,
        comment,  # MEDIUMTEXT
        scheduler_algorithm,  # MEDIUMTEXT
        config,  # LONGTEXT,
        workload_comment,  # MEDIUMTEXT
        workload_generate_method,  # int
        create_time
    )

    return __execute_insert_procedure("insert_experiment", args)


def insert_workload_generator(
        experiment_id,
        tenant_id,  # bigint,
        cinder_id,
        nova_id,  # VARCHAR(36)
        duration,  # float,
        read_iops,
        write_iops,
        command,  # LONGTEXT,
        output,  # LONGTEXT,
        create_clock,  # INT(11),
        create_time):
    args = (
        experiment_id,  # experiment_ID				bigint,
        tenant_id,  # bigint,
        cinder_id,
        nova_id,
        duration,  # INT(11),
        read_iops,
        write_iops,
        command,  # INT(11),
        output,  # INT(11),
        create_clock,  # INT(11),
        create_time  # DATETIME(6)
    )

    return __execute_insert_procedure("insert_workload_generator", args)


def insert_volume_request(
        workload_id,  # bigint,
        experiment_id,  # bigint,
        capacity,  # INT(11),
        type,  # INT(11),
        read_iops,  # INT(11),
        write_iops,  # INT(11),
        create_clock,  # INT(11),
        create_time  # DATETIME
):
    args = (
        workload_id,  # bigint,
        experiment_id,
        capacity,  # INT(11),
        type,  # INT(11),
        read_iops,  # INT(11),
        write_iops,  # INT(11),
        create_clock,  # INT(11),
        create_time  # DATETIME(6)
    )

    return __execute_insert_procedure("insert_volume_request", args)


def insert_workload(
        comment,  # MEDIUMTEXT,
        generate_method,  # INT(11),
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

    print insert_volume_request(workload_id=1, capacity=1, type=0, read_iops=500, write_iops=500, create_clock=0,
                                create_time=datetime.now())

    pass
