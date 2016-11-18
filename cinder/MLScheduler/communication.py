import requests
from datetime import datetime
import json

__server_url = 'http://CinderDevelopmentEnv:8888/'

"""
1	Accepted
2	rejected capacity
3	rejected read iops
4	rejected write iops
5	rejected read & write iops
6	rejected unknown reason
"""
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


def insert_volume(
        experiment_id,
        cinder_id,
        backend_cinder_id,
        schedule_response,
        capacity,
        create_clock=0,
        create_time=None):

    if create_time is None:
        create_time = datetime.now()

    data = {
        "experiment_id": experiment_id,
        "cinder_id": cinder_id,
        "backend_cinder_id": backend_cinder_id,
        "schedule_response_id": schedule_response,
        "capacity": capacity,
        "create_clock": create_clock,
        "create_time": create_time
    }

    return _parse_response(requests.post(__server_url + "insert_volume", data=data))


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


def _parse_response(response):

    return int(response.content)


def get_current_experiment():
    ex = requests.get(__server_url + "get_current_experiment")

    return json.loads(ex.text)


if __name__ == "__main__":

    pass
