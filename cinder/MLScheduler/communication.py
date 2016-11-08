import requests
from datetime import datetime

__server_url = 'http://CinderDevelopmentEnv:8888/'


class ScheduleResponseType:
    @staticmethod
    def accepted(): return 1

    @staticmethod
    def rejected(): return 2

    @staticmethod
    def rejected_capacity(): return 3

    @staticmethod
    def rejected_iops(): return 4

    @staticmethod
    def rejected_capacity_iops(): return 5


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
        workload_id,
        comment,
        scheduler_algorithm,
        config,
        create_time=None):

    if create_time is None:
        create_time = datetime.now()

    data = {
        "workload_id": workload_id,
        "comment": comment,
        "scheduler_algorithm": scheduler_algorithm,
        "config": config,
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

if __name__ == "__main__":
    # print add_volume(
    #     experiment_id=1,
    #     cinder_id=uuid.uuid1(),
    #     backend_cinder_id='block4@lvm#LVM',
    #     schedule_response=1,
    #     capacity=1)

    # print insert_schedule_response(
    #     experiment_id=1,
    #     volume_request_id=1,
    #     response_id=1
    # )

    print insert_experiment(
        workload_id=1,
        comment='',
        scheduler_algorithm='',
        config=''
    )

    pass
