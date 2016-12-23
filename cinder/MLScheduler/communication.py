import os
import requests
import log_tools
import urllib
from datetime import datetime
import json
import pdb

# must not import log because this file is imported in the openstack scheduler classes and will mess everything

__server_url = 'http://CinderDevelopmentEnv:8888/'
__server_url = 'http://10.18.75.100:8888/'
__java_service_url = "http://10.254.252.4:81/"  # http://10.254.252.4:81/?reset

"""
1	Accepted
2	rejected capacity
3	rejected read iops
4	rejected write iops
5	rejected read & write iops
6	rejected unknown reason
"""


class AssessmentPolicy:
    @staticmethod
    def strict_qos():
        return "strict_qos"

    @staticmethod
    def qos_first():
        return "qos_first"

    @staticmethod
    def efficiency_first():
        return "efficiency_first"

    @staticmethod
    def max_efficiency():
        return "max_efficiency"

    @staticmethod
    def parse(s):
        if s == "max_efficiency":
            return AssessmentPolicy.max_efficiency()

        if s == "efficiency_first":
            return AssessmentPolicy.efficiency_first()

        if s == "qos_first":
            return AssessmentPolicy.qos_first()

        if s == "strict_qos":
            return AssessmentPolicy.strict_qos()


class ScheduleResponseType:
    @staticmethod
    def accepted(): return 1

    @staticmethod
    def rejected_capacity(): return 2

    @staticmethod
    def rejected_read_iops(): return 3

    @staticmethod
    def rejected_write_iops(): return 4

    @staticmethod
    def rejected_read_write_iops(): return 5

    @staticmethod
    def rejected_unknown(): return 6

    @staticmethod
    def rejected_no_weighed_host(): return 7


class Communication:
    _current_experiment = None
    __server_url = 'http://10.18.75.100:8888/'

    @staticmethod
    def get_config(key):

        return Communication.get_current_experiment()["config"][key]

    @staticmethod
    def get_current_experiment():
        if Communication._current_experiment is not None:
            return Communication._current_experiment

        try:
            ex = requests.get(Communication.__server_url + "get_current_experiment")
        except Exception as err:
            log_tools.log("CANNOT CONNECT TO SERVER_HANDLER to get the CURRENT EXPERIMENT")
            return None

        try:
            ex = json.loads(ex.text)

            ex["config"] = json.loads(ex["config"])
        except Exception as err:
            log_tools.log("ERROR [get_current_experiment] cannot load the experiment 'config'")
            return None

        Communication._current_experiment = ex

        return Communication._current_experiment

    @staticmethod
    def get_assessment_policy():
        return AssessmentPolicy.parse(Communication.get_config("assessment_policy"))

    @staticmethod
    def get_training_experiment_id():
        return Communication.get_config("training_experiment_id")

    @staticmethod
    def get_config(key):

        return Communication.get_current_experiment()["config"][key]

    @staticmethod
    def reload():

        try:
            ex = requests.get(Communication.__server_url + "get_current_experiment")
        except Exception as err:
            log_tools.log("RELOAD FAILED. CANNOT CONNECT TO SERVER_HANDLER to get the CURRENT EXPERIMENT")
            return None

        try:
            ex = json.loads(ex.text)

            ex["config"] = json.loads(ex["config"])
        except Exception as err:
            log_tools.log("RELOAD FAILED. ERROR [get_current_experiment] cannot load the experiment 'config'")
            return None

        Communication._current_experiment = ex


def insert_volume(
        experiment_id,
        cinder_id,
        backend_cinder_id,
        host_address,
        schedule_response,
        capacity,
        create_clock=0,
        create_time=None):
    if create_time is None:
        create_time = datetime.now()

    create_clock = volume_clock_calc(create_time)

    data = {
        "experiment_id": experiment_id,
        "cinder_id": cinder_id,
        "backend_cinder_id": backend_cinder_id,
        "host_address": host_address,
        "schedule_response_id": schedule_response,
        "capacity": capacity,
        "create_clock": create_clock,
        "create_time": create_time
    }

    return _parse_response(requests.post(__server_url + "insert_volume", data=data))


def insert_backend(
        cinder_id,
        experiment_id,
        capacity,
        is_online=1,
        Description='',
        ML_model_Path='',
        create_clock=0,
        create_time=None):
    if create_time is None:
        create_time = datetime.now()

    create_clock = volume_clock_calc(create_time)

    data = {
        "cinder_id": cinder_id,
        "experiment_id": experiment_id,
        "capacity": capacity,
        "is_online": is_online,
        "Description": Description,
        "ML_model_Path": ML_model_Path,
        "create_clock": create_clock,
        "create_time": create_time
    }

    return _parse_response(requests.post(__server_url + "insert_backend", data=data))


def insert_experiment(
        comment,
        scheduler_algorithm,
        config,
        workload_comment=None,
        workload_generate_method=0,
        workload_id=0,
        create_time=None):
    """

    :param comment:
    :param scheduler_algorithm:
    :param config:
    :param workload_comment:
    :param workload_generate_method:
    :param workload_id: if equal to 0 it create a new workload by capturing the running experiment requests
    :param create_time:
    :return:
    """

    if create_time is None:
        create_time = datetime.now()

    data = {
        "workload_id": workload_id,
        "comment": comment,
        "scheduler_algorithm": scheduler_algorithm,
        "config": config,
        "workload_comment": workload_comment,
        "workload_generate_method": workload_generate_method,
        "create_time": create_time
    }

    return _parse_response(requests.post(__server_url + "insert_experiment", data=data))


def insert_schedule_response(
        experiment_id,
        volume_request_id,
        response_id,
        create_clock=0,
        create_time=None):
    if create_time is None:
        create_time = datetime.now()

    data = {
        "experiment_id": experiment_id,
        "volume_request_id": volume_request_id,
        "response_id": response_id,
        "create_clock": create_clock,
        "create_time": create_time
    }

    return _parse_response(requests.post(__server_url + "insert_schedule_response", data=data))


def get_training_dataset(
        experiment_id,
        training_dataset_size):
    # WRONG PARAMETERS
    params = {
        "experiment_id": experiment_id,
        "training_dataset_size": training_dataset_size
    }

    ex = requests.get("%sget_training_dataset?%s" % (__server_url, urllib.urlencode(params)))

    return json.loads(ex.text)


def get_backends_weights(experiment_id, volume_request_id):
    params = {
        "experiment_id": experiment_id,
        "volume_request_id": volume_request_id
    }

    weights = requests.get("%sget_backends_weights?%s" % (__server_url, urllib.urlencode(params)))

    return json.loads(weights.text)


def get_error_log_count(experiment_id):
    params = {
        "experiment_id": experiment_id
    }

    error_count = requests.get("%sget_error_log_count?%s" % (__server_url, urllib.urlencode(params)))

    return int(error_count.text)


def get_prediction(volume_request_id):
    params = {
        "volume_request_id": volume_request_id
    }

    prediction = requests.get("%sget_prediction?%s" % (__server_url, urllib.urlencode(params)))

    return json.loads(prediction.text)


def get_prediction_from_java_service(clock, volume_request_id, algorithm, training_experiment_id):

    params = {
        "volume_request_id": volume_request_id,
        "clock": clock,
        "algorithm": algorithm,
        "training_experiment_id": training_experiment_id,
        "experiment_id": Communication.get_current_experiment()["id"]
    }

    prediction = requests.get("%s?%s" % (__java_service_url, urllib.urlencode(params)))

    return json.loads(prediction.text)


def reset_java_service():
    params = {
        "reset": ""
    }

    prediction = requests.get("%s?%s" % (__java_service_url, urllib.urlencode(params)))

    return prediction.text


def volume_clock_calc(t):
    return t.strftime("%s")


try:
    # define the function from the database
    exec (Communication.get_current_experiment()["config"]["volume_clock_calc"])
except Exception as err:

    log_tools.log(
        "ERROR on dynamic add of [volume_clock_calc]. IGNORE, if running ['shutdown', 'ServiceHandler']. ERR:%s" % str(
            err))
    # sys.exit(1)


def get_volume_performance_meter_clock_calc(t=datetime.now()):
    if os.name == 'nt':
        return 50

    exec (Communication.get_current_experiment()["config"]["volume_performance_meter_clock_calc"])

    return volume_performance_meter_clock_calc(t)


try:
    # define the function from the database
    exec (Communication.get_current_experiment()["config"]["volume_performance_meter_clock_calc"])
except Exception as err:
    log_tools.log(
        "ERROR on dynamic add of [get_volume_performance_meter_clock_calc]. IGNORE, if running ['shutdown', 'ServiceHandler']. ERR:%s" % str(
            err))
    # sys.exit(1)


def _parse_response(response):
    return int(response.content)


if __name__ == "__main__":

    print (get_error_log_count(0))

    # http://10.254.252.6:81/?volume_request_id=1490&clock=100&algorithm=j48

    # from classification import MachineLearningAlgorithm
    #
    # predictions_list = get_prediction_from_java_service(
    #     volume_request_id=1490,
    #     clock=100,
    #     algorithm=MachineLearningAlgorithm.J48()
    # )
    #
    # read_candidates = []
    # write_candidates = []
    #
    # for backend_prediction in predictions_list:
    #     print ("\n\ncinder-->" + backend_prediction["cinder_id"])
    #
    #     print ("read_predictions: " + str(backend_prediction["read_predictions"]))
    #
    #     print ("write_predictions: " + str(backend_prediction["write_predictions"]))

    pass
