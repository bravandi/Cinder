import argparse
from cmath import exp
import tools
import os
import communication
import time
import json
import sys
import json
import pdb
import numpy as np


class Experiment:
    experiment = None

    def __init__(self, add_new_experiment, config, print_output_if_have_error=False,
                 print_output=False, debug_run_only_one_server=False, debug_server_ip=None):

        self.debug_server_ip = debug_server_ip
        self.print_output_if_have_error = print_output_if_have_error
        self.print_output = print_output
        self.servers = []
        self.debug_run_only_one_server = debug_run_only_one_server

        if add_new_experiment:

            ex_id = communication.insert_experiment(
                comment='',
                scheduler_algorithm='',
                config=config
            )

            for backend_name in tools.get_cinder_backends():
                communication.insert_backend(
                    experiment_id=ex_id,
                    cinder_id=backend_name,
                    capacity=100,
                )

            tools.log("Create new experiment.")

        Experiment.experiment = communication.Communication.get_current_experiment()

        if Experiment.experiment is not None:
            tools.log("Experiment id: %s" % str(Experiment.experiment["id"]))

        nova = tools.get_nova_client()
        for server in nova.servers.list():

            if server.status != 'ACTIVE':
                continue

            try:
                server_ip = server.networks['provider'][0]

                if self.debug_run_only_one_server:

                    if server_ip != self.debug_server_ip:
                        continue
                else:
                    if server_ip == self.debug_server_ip:
                        continue

                tools.log("Connecting via ssh to %s" % (server_ip))

                ssh_client = Experiment._create_ssh_clients(server_ip)

                self.servers.append({
                    "id": server.id,
                    "ssh": ssh_client,
                    "ip": server_ip,
                    "name": server.name
                })

            except Exception as ex:
                tools.log("Error -> canot create SSH client for %s\nError message -> %s"
                          % (server_ip, ex.message))

    def close_all_ssh_client(self):

        for server in self.servers:
            ssh_client = server["ssh"]
            ssh_client.close()

    def initialize_commands(self):

        for server in self.servers:

            ret = self._run_command(server, "ls ~")

            if "fio-2.0.9\n" not in ret["out"]:
                self._run_command(server, "sudo wget https://github.com/Crowd9/Benchmark/raw/master/fio-2.0.9.tar.gz")
                self._run_command(server, "sudo tar xf ~/fio-2.0.9.tar.gz")
                self._run_command(server, "sudo make -C ~/fio-2.0.9")

            ret = self._run_command(server, "sudo cat /etc/hosts")
            if server["name"] not in str(ret["out"]):
                self._run_command(
                    server,
                    "echo '%s\t%s' | sudo tee --append /etc/hosts" % (server["ip"], server["name"]))

            self._run_command(server, "sudo rm -r -d ~/MLSchedulerAgent/")
            ret = self._run_command(server, 'sudo git clone https://github.com/bravandi/MLSchedulerAgent.git')
            if ret["retval"] == 128:
                self._run_command(server,
                                  "sudo git -C ~/MLSchedulerAgent/ reset --hard; sudo git -C ~/MLSchedulerAgent/ pull")

            self._run_command(server, "sudo echo '%s' > ~/tenantid" % server["id"])

            self._run_command(server, "sudo echo '%s@%s' > ~/tenant_description" % (server["name"], server["ip"]))

            self._run_command(server, "sudo mkdir /media/")

    def _run_command(self, server, command):

        if self.print_output:
            print ("{EXECUTE %s} %s\n" % (server["ip"], command))

        ret = server["ssh"].execute(command)

        if (not self.print_output) and self.print_output_if_have_error and ret["retval"] > 0:
            print ("{EXECUTED %s} %s\n" % (server["ip"], command))
            print ("     [RESPONSE %s] OUT: %s\n     RETVAL:%s   ERR:%s \n" %
                   (server["ip"], ret["out"], ret["retval"], ret["err"]))

        if self.print_output:
            print ("     [RESPONSE %s] OUT: %s\n     RETVAL:%s   ERR:%s \n" %
                   (server["ip"], ret["out"], ret["retval"], ret["err"]))

        return ret

    def start_workload_generators(self, arguments):

        max_number_volumes = json.loads(arguments["--max_number_volumes"].replace('"', ''))
        val = int(np.random.choice(max_number_volumes[0], 1, max_number_volumes[1]))

        arguments["--max_number_volumes"] = '"[[1], [1.0]]"'

        args = []
        for k, v in arguments.iteritems():
            args.append(str(k))
            args.append(str(v))

        for i in range(val):

            self._run_command_on_all_servers(
                "sudo nohup python ~/MLSchedulerAgent/workload_generator.py start %s >~/workload_%s.out 2>~/workload_%s.err &" % (
                    " ".join(args), str(i), str(i))
            )

    def start_performance_evaluators(self, arguments):

        args = []
        for k, v in arguments.iteritems():
            args.append(str(k))
            args.append(str(v))

        self._run_command_on_all_servers(
            "sudo nohup python ~/MLSchedulerAgent/performance_evaluation.py %s >~/performance_evaluation.out 2>~/performance_evaluation.err &" % (
                " ".join(args)))

    def kill_performance_evaluators(self):
        self._run_command_on_all_servers(
            "ps -ef | grep performance_evaluation | grep -v grep | awk '{print $2}' | xargs sudo kill -9")

    def kill_workload_generator_all_servers(self):
        self._run_command_on_all_servers(
            "ps -ef | grep workload_generator | grep -v grep | awk '{print $2}' | xargs sudo kill -9")

    def _run_command_on_all_servers(self, command):

        for server in self.servers:
            self._run_command(server, command)

    def detach_delete_all_servers_volumes(self):
        self._run_command_on_all_servers(
            "sudo nohup python ~/MLSchedulerAgent/workload_generator.py det-del >~/detach_delete_all_servers_volumes.out 2>~/detach_delete_all_servers_volumes.err &")

    @staticmethod
    def _create_ssh_clients(server_ip):
        f = open(
            os.path.join(
                os.path.expanduser('~'),
                "keys",
                "vm-test",
                "vm-test.pem"
            ), 'r')

        s = f.read()

        client = tools.SshClient(
            host=server_ip,
            port=22,
            key=s,
            username='ubuntu',
            password='')

        return client


def args_load_defaults(args):
    args.debug_run_only_one_server = tools.str2bool(args.debug_run_only_one_server)
    args.print_output_if_have_error = tools.str2bool(args.print_output_if_have_error)
    args.print_output = tools.str2bool(args.print_output)
    args.new = tools.str2bool(args.new)
    args.read_is_priority = tools.str2bool(args.read_is_priority)
    args.performance_show_fio_output = tools.str2bool(args.performance_show_fio_output)

    if args.debug_run_only_one_server:
        if args.debug_server_ip is None:
            args.debug_server_ip = "10.18.75.182"

    if args.performance_fio_test_name is None:
        args.performance_fio_test_name = "resource_evaluation.fio"
    if args.performance_terminate_if_takes is None:
        args.performance_terminate_if_takes = 25
    if args.performance_restart_gap is None:
        args.performance_restart_gap = 25
    if args.performance_restart_gap_after_terminate is None:
        args.performance_restart_gap_after_terminate = 8
    # args.read_is_priority
    # args.performance_show_fio_output

    if args.workload_fio_test_name is None:
        args.workload_fio_test_name = "workload_generator.fio"
    if args.workload_wait_after_volume_rejected is None:
        args.workload_wait_after_volume_rejected = "[[30], [1.0]]"
    if args.workload_request_read_iops is None:
        args.workload_request_read_iops = "[[600, 850, 1100], [0.3, 0.4, 0.3]]"
    if args.workload_request_write_iops is None:
        args.workload_request_write_iops = "[[400, 500, 600], [0.3, 0.4, 0.3]]"
    if args.workload_delay_between_workload_generation is None:
        args.workload_delay_between_workload_generation = "[[2], [1.0]]"
    if args.workload_max_number_volumes is None:
        args.workload_max_number_volumes = "[[6], [1.0]]"
    if args.workload_volume_life_seconds is None:
        args.workload_volume_life_seconds = "[[40], [1.0]]"
    if args.workload_volume_size is None:
        args.workload_volume_size = "[[5], [1.0]]"

    # args.debug_run_only_one_server
    # args.debug_run_only_one_server
    # args.new

    # args.print_output_if_have_error
    # args.print_output
    # args.training_experiment_id
    # performance_show_fio_output
    # is_training
    # workload_args
    # performance_args
    if args.mod_normalized_clock_for_feature_generation is None:
        args.mod_normalized_clock_for_feature_generation = 180
    if args.training_dataset_size is None:
        args.training_dataset_size = 200
        # volume_clock_calc
        # volume_performance_meter_clock_calc


if __name__ == '__main__':

    # todo ******* run python experiment.py execute --command "sudo mkdir /media" on the other servers that you shut down
    # todo when create new server make sure dependecies such as numpy are installed -->python experiment.py execute --command "pip install numpy"

    parser = argparse.ArgumentParser(description='Manage experiments.')

    parser.add_argument('commands', type=str, nargs="+",
                        choices=[
                            'start', 'shutdown', 'start-new', 'workload', 'del-avail-err',
                            'performance', 'det-del', 'kill-workload',
                            'kill-performance', 'execute', 'init', 'create-experiment'],
                        help=
                        """
                        Manage experiments.
                        """
                        )

    parser.add_argument('--execute_command_in_bash', metavar='', type=str, required=False,
                        help='execute command on all servers.')

    parser.add_argument('--training_experiment_id', default=0, metavar='', type=int, required=False,
                        help='if set 0 it will use the default scheduler. Other wise will use the given id to generate training dataset and create classification model to perform iops prediction. default=0')

    parser.add_argument('--debug_run_only_one_server', default='False', metavar='', type=str,
                        help='Only run one server for debug purposes. default=False')

    parser.add_argument('--print_output_if_have_error', default='True', metavar='', type=str,
                        help='print output if there is an error in execute command on the hosts. default=False')

    parser.add_argument('--print_output', default='True', metavar='', type=str,
                        help='print output if there is an error in execute command on the hosts. default=False')

    parser.add_argument('--new', default='False', metavar='', type=str,
                        help='Create new experiment otherwise the last created experiment will be used. default=False')

    parser.add_argument('--read_is_priority', default='True', metavar='', type=str,
                        help='Create new experiment otherwise the last created experiment will be used. default=False.')

    parser.add_argument('--mod_normalized_clock_for_feature_generation', default=None, metavar='', type=int,
                        required=False,
                        help='mod the clock ... example=180')

    parser.add_argument('--training_dataset_size', default=None, metavar='', type=int, required=False,
                        help='training dataset size. example=1000')

    parser.add_argument('--debug_server_ip', default=None, metavar='', type=str, required=False,
                        help='for debug only use this server')

    # PERFORMANCE CONFIGURATION
    parser.add_argument("--performance_fio_test_name", default="resource_evaluation.fio", metavar='', type=str,
                        required=False,
                        help='Performance Eval: the fio test will be used for performance evaluation. default="resource_evaluation.fio"')

    parser.add_argument('--performance_terminate_if_takes', default=None, metavar='', type=int, required=False,
                        help='Performance Eval: terminate performance eval process if takes more than xx seconds. example=25')

    parser.add_argument('--performance_restart_gap', default=None, metavar='', type=int, required=False,
                        help='Performance Eval: do Performance Evaluation proccess each xx seconds. example=4')

    parser.add_argument('--performance_restart_gap_after_terminate', default=None, metavar='', type=int, required=False,
                        help='Performance Eval: if performance evaluation failed, wait xx seconds the restart. example=4')

    parser.add_argument('--performance_show_fio_output', default='False', metavar='', type=str,
                        help='Performance Eval: print fio output. default=False')
    # END PERFORMANCE CONFIGURATION

    # WORKLOAD GENERATOR

    parser.add_argument("--workload_fio_test_name", default="workload_generator.fio", metavar='', type=str,
                        required=False,
                        help='Workload: fio test to generate workload. default="workload_generator.fio"')

    parser.add_argument("--workload_wait_after_volume_rejected", default=None, metavar='', type=str,
                        required=False,
                        help='if a volume request is rejected, wait for xx seconds. example="[[30], [1.0]]"')

    parser.add_argument("--workload_request_read_iops", default=None, metavar='',
                        type=str, required=False,
                        help='request iops read random list. example="[[600, 850, 1100], [0.3, 0.4, 0.3]]"')

    parser.add_argument("--workload_request_write_iops", default=None, metavar='',
                        type=str, required=False,
                        help='request iops write random list. example="[[400, 500, 600], [0.3, 0.4, 0.3]]"')

    parser.add_argument("--workload_delay_between_workload_generation", default=None, metavar='',
                        type=str, required=False,
                        help='wait xx seconds between generating workloads. example="[[2], [1.0]]"')

    parser.add_argument("--workload_max_number_volumes", default=None, metavar='',
                        type=str, required=False,
                        help='max number of vilumes to be created. example="[[6], [1.0]]"')

    parser.add_argument("--workload_volume_life_seconds", default=None, metavar='',
                        type=str, required=False,
                        help='life time of a volume. example="[[40], [1.0]]"')

    parser.add_argument("--workload_volume_size", default=None, metavar='',
                        type=str, required=False,
                        help='life time of a volume. example= "[[5], [1.0]]"')

    # END WORKLOAD GENERATOR

    args = parser.parse_args()

    args_load_defaults(args)

    if "shutdown" in args.commands:
        args.commands = ["kill-workload", "kill-performance", "det-del"]
        args.debug_server_ip = ''
        args.new = False

    if "start" in args.commands:
        args.commands = ["init", "workload", "performance"]
        args.new = False

    if "start-new" in args.commands:
        args.commands = ["init", "workload", "performance"]
        args.new = True

    if "create-experiment" in args.commands:
        args.new = True

    if args.debug_run_only_one_server:
        args.commands.remove("init")

    workload_args = {
        "--fio_test_name": args.workload_fio_test_name,

        "--wait_after_volume_rejected": json.dumps(args.workload_wait_after_volume_rejected),
        "--request_read_iops": json.dumps(args.workload_request_read_iops),
        "--request_write_iops": json.dumps(args.workload_request_write_iops),
        '--delay_between_workload_generation': json.dumps(args.workload_delay_between_workload_generation),
        "--max_number_volumes": json.dumps(args.workload_max_number_volumes),
        "--volume_life_seconds": json.dumps(args.workload_volume_life_seconds),
        "--volume_size": json.dumps(args.workload_volume_size)
    }

    performance_args = {
        "--fio_test_name": args.performance_fio_test_name,
        "--terminate_if_takes": args.performance_terminate_if_takes,
        "--restart_gap": args.performance_restart_gap,
        "--restart_gap_after_terminate": args.performance_restart_gap_after_terminate,
        "--show_fio_output": args.performance_show_fio_output,
    }

    if "del-avail-err" in args.commands:
        tools.log("CAUSING ERROR WHILE RUNNING THE SCHEDULER. MIGHT NEED TO REMOVE")
        tools.delete_volumes_available_error()

        sys.exit()

    is_training = True
    if args.training_experiment_id > 0:
        is_training = False

    e = Experiment(
        debug_server_ip=args.debug_server_ip,
        debug_run_only_one_server=args.debug_run_only_one_server,
        add_new_experiment=args.new,
        print_output_if_have_error=args.print_output_if_have_error,
        print_output=args.print_output,
        config=json.dumps({
            "training_experiment_id": args.training_experiment_id,
            "read_is_priority": args.read_is_priority,
            "is_training": is_training,
            "workload_args": workload_args,
            "performance_args": performance_args,
            "mod_normalized_clock_for_feature_generation": args.mod_normalized_clock_for_feature_generation,
            "training_dataset_size": args.training_dataset_size,
            "volume_clock_calc": tools.read_file("script_volume_clock_calc"),
            "volume_performance_meter_clock_calc": tools.read_file("script_volume_performance_meter_clock_calc")
        })
    )

    if "init" in args.commands:
        e.initialize_commands()

    if "workload" in args.commands:
        e.start_workload_generators(workload_args)

    if "performance" in args.commands:
        e.start_performance_evaluators(performance_args)

    if "kill-workload" in args.commands:
        e.kill_workload_generator_all_servers()

        # sleep 4 to make sure all the processes are dead are not going to create new volumes!
        if "det-del" in args.commands:
            time.sleep(3)

    if "kill-performance" in args.commands:
        e.kill_performance_evaluators()

    if "det-del" in args.commands:
        e.detach_delete_all_servers_volumes()
        # tools.delete_volumes_available_error()

    if "execute" in args.commands:
        e._run_command_on_all_servers(args.execute_command_in_bash)

    e.close_all_ssh_client()
