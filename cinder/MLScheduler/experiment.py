import argparse
import tools
import os
import communication
from multiprocessing import Process
from classification import MachineLearningAlgorithm
import time
import sys
import json
from datetime import datetime
import pdb

_args_commands = None


class RemoteMachine:
    def __init__(self, server_ip):
        self.proc = None
        self.server_ip = server_ip

    def start(self, workload_args, performance_args):
        if self.is_alive() is True:
            return False

        self.proc = Process(
            target=RemoteMachine.start_workload_generator,
            args=(self, workload_args, performance_args))

        # tools.log(app="W_STORAGE_GEN", message="   Start test for volume: %s Time: %s" %
        #           (self.cinder_volume_id, self.last_start_time))
        self.proc.start()

        return True

    def terminate(self):
        if self.proc is None:
            tools.log(
                app="MLScheduler",
                type="ERROR",
                code="exp_null_terminate",
                file_name="experiment.py",
                function_name="terminate",
                message="proc is null cant terminate. maybe RemoteMachine.start() is not called.")

            return False

        self.proc.terminate()

        return True

    def is_alive(self):

        if self.proc is None:
            # todo PROBABLY not a problem. So I comment it.
            # tools.log(
            #     app="MLScheduler",
            #     type="WARNING",
            #     code="exp_null_is_alive",
            #     file_name="experiment.py",
            #     function_name="is_alive",
            #     message="proc is null cant call is_alive(). maybe RemoteMachine.start() is not called.")

            return False

        return self.proc.is_alive()

    @staticmethod
    def start_workload_generator(remote_machine_instance, workload_args, performance_args):

        # def start_workload_generators(self, workload_args, performance_args):

        args = []
        for k, v in workload_args.iteritems():
            args.append(str(k))
            args.append(str(v))

        for k, v in performance_args.iteritems():
            args.append(str(k))
            args.append(str(v))

        # if using 'until' then: command = "sudo python %s start %s >>%s 2>>%s" % \
        command = "sudo python %s start %s >%s 2>%s" % \
                  (
                      tools.get_path_for_tenant("~/MLSchedulerAgent/workload_generator.py"),
                      " ".join(args),
                      tools.get_path_for_tenant("~/workload.out"),
                      tools.get_path_for_tenant("~/workload.err")
                  )

        # todo save the command in database will be handy for running test experiments
        remote_machine_instance.ssh_client = Experiment.create_ssh_clients(remote_machine_instance.server_ip)

        Experiment.run_command(
            ssh_client=remote_machine_instance.ssh_client,
            # command="echo 'until %s; do\n\tcode=\"$?\"\n\techo \"workload_generator crashed with exit code $code.  Respawning..\" >&2\n\tif [ $code = \"137\" ]; then\n\t\techo \"done\"\n\t\tbreak\n\tfi\n\tsleep 1\ndone' > %s.sh" % (
            #     command, tools.get_path_for_tenant("~/command_workload"))
            command="echo '%s' > %s" % (command, tools.get_path_for_tenant("~/command_workload.sh"))
        )

        Experiment.run_command(
            ssh_client=remote_machine_instance.ssh_client,
            command="source command_workload.sh"
        )

        # commented code below is for running multiple workload generators. not gonna work because of detecting current device issue. issue

        # self._run_command_on_all_servers(command)

        # max_number_volumes = json.loads(arguments["--max_number_volumes"].replace('"', ''))
        # val = int(np.random.choice(max_number_volumes[0], 1, max_number_volumes[1]))
        #
        # arguments["--max_number_volumes"] = '"[[1], [1.0]]"'
        #
        # args = []
        # for k, v in arguments.iteritems():
        #     args.append(str(k))
        #     args.append(str(v))
        #
        # for i in range(val):
        #     self._run_command_on_all_servers(
        #         "sudo nohup python %s start %s >%s 2>%s &" %
        #         (
        #             tools.get_path_expanduser("~/MLSchedulerAgent/workload_generator.py"),
        #             " ".join(args),
        #             tools.get_path_expanduser("~/workload.out"),
        #             tools.get_path_expanduser("~/workload.err")
        #         )
        #     )


class Experiment:
    experiment = None

    def __init__(self, add_new_experiment, config, print_output_if_have_error=False,
                 print_output=False, debug_run_only_one_server=False, debug_server_ip=None, is_shutdown=False):

        self.debug_server_ip = debug_server_ip
        self.print_output_if_have_error = print_output_if_have_error
        self.print_output = print_output
        self.servers = []
        self.remote_machine_list = []
        self.debug_run_only_one_server = debug_run_only_one_server
        self.is_shutdown = is_shutdown

        if add_new_experiment:

            ex_id = communication.insert_experiment(
                comment='',
                scheduler_algorithm='',
                config=config
            )

            communication.Communication.reload()

            try:
                communication.reset_java_service()
            except:
                raise Exception("Cannot communicate with the java service handler.")

            tools.log("Created a new experiment. id: " + str(ex_id), code="created-new-experiment", insert_db=False)

        Experiment.experiment = communication.Communication.get_current_experiment()

        # database wont add duplicates
        for backend_name in tools.get_cinder_backends():
            communication.insert_backend(
                experiment_id=Experiment.experiment["id"],
                cinder_id=backend_name,
                capacity=100,
            )

        if Experiment.experiment is None:
            tools.log(
                type="ERROR", code="", file_name="experiment.py", function_name="Experiment",
                message="cannot create new experiment. insert record to db maybe.")

            raise Exception("cannot create new experiment. insert record to db maybe.")

        if add_new_experiment is True:
            tools.log(
                type="INFO", code="start", file_name="experiment.py", function_name="Experiment",
                message="Create new experiment. Experiment id: %s" % str(Experiment.experiment["id"]))

        if is_shutdown:
            tools.log(
                type="INFO", code="shutdown", file_name="experiment.py", function_name="Experiment",
                message="Shutdown experiment. Experiment id: %s" % str(Experiment.experiment["id"]))

        if add_new_experiment is False and is_shutdown is False:
            tools.log(
                type="INFO", code="resume", file_name="experiment.py", function_name="Experiment",
                message="Resume experiment. Experiment id: %s" % str(Experiment.experiment["id"]))

        number_of_servers_to_start_simulation = 0

        nova = tools.get_nova_client()
        for server in nova.servers.list():

            if (
                            "start" in _args_commands or "start-new" in _args_commands
            ) and number_of_servers_to_start_simulation >= communication.Communication.get_config(
                "number_of_servers_to_start_simulation"):

                break

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

                tools.log("Connecting via ssh to %s" % (server_ip), code="connecting-via-ssh", insert_db=False)

                ssh_client = Experiment.create_ssh_clients(server_ip)

                if "start-new" in _args_commands or "start" in _args_commands:
                    result = ssh_client.execute("sudo ps aux | grep workload_generator")
                    if len(result["out"]) > 2:  # one is for grep another is for ssh

                        for out in result["out"]:
                            if "workload_generator.py" in out:
                                ssh_client.close()
                                tools.log(
                                    type="WARNING",
                                    code="start_exp_already_running",
                                    file_name="experiment.py",
                                    function_name="__init__",
                                    message="server %s is already running at least one workload_generator.py instance." % server_ip)
                                continue

                result = ssh_client.execute("sudo fdisk -l")

                if len(result["err"]) > 0 and "Input/output error" in result["err"][0]:
                    result_2 = ssh_client.execute(
                        "sudo python /home/centos/MLSchedulerAgent/workload_generator.py det-del")
                    tenant_id = ssh_client.execute("cat /home/centos/tenantid")["out"][0]
                    result_2 = tools.run_command2("openstack server delete " + tenant_id, get_out=True)
                    ssh_client.close()
                    continue

                tenant = nova.servers.get(server.id)

                self.servers.append({
                    "id": server.id,
                    "ssh": ssh_client,
                    "ip": server_ip,
                    "name": server.name,
                    "hypervisor": tenant.to_dict()['OS-EXT-SRV-ATTR:hypervisor_hostname']
                })

                number_of_servers_to_start_simulation = number_of_servers_to_start_simulation + 1

            except Exception as err:
                tools.log(
                    type="ERROR",
                    code="ssh",
                    file_name="experiment.py",
                    function_name="__init__",
                    message="can not create SSH client for %s" % server_ip,
                    exception=err)

    def close_all_ssh_client(self):

        for server in self.servers:
            ssh_client = server["ssh"]
            ssh_client.close()

    def initialize_commands(self):

        for server in self.servers:

            ret = self._run_command(server, "ls " + tools.get_path_for_tenant("~"))

            # if "fio-2.0.9\n" not in ret["out"]:
            #     self._run_command(server, "sudo wget https://github.com/Crowd9/Benchmark/raw/master/fio-2.0.9.tar.gz")
            #     self._run_command(server, "sudo tar xf %s" % tools.get_path_expanduser("~/fio-2.0.9.tar.gz"))
            #     self._run_command(server, "sudo make -C %s" % tools.get_path_expanduser("~/fio-2.0.9"))

            ret = self._run_command(server, "sudo cat /etc/hosts")

            if server["name"] not in str(ret["out"]):
                ret = self._run_command(
                    server,
                    "echo '%s\t%s' | sudo tee --append /etc/hosts" % (server["ip"], server["name"]))

            # why remove
            # self._run_command(server, "sudo rm -r -d %s" % tools.get_path_expanduser("~/MLSchedulerAgent/"))

            ret = self._run_command(server, 'sudo git clone https://github.com/bravandi/MLSchedulerAgent.git')
            if ret["retval"] == 128:
                self._run_command(
                    server,
                    # "sudo git -C %s reset --hard; sudo git -C %s pull" %
                    "cd %s; sudo git reset --hard" % tools.get_path_for_tenant("~/MLSchedulerAgent")
                    # % (tools.get_path_expanduser("~/MLSchedulerAgent/"), tools.get_path_expanduser("~/MLSchedulerAgent/"))
                )

                self._run_command(
                    server,
                    "cd %s; sudo git pull" % tools.get_path_for_tenant("~/MLSchedulerAgent")
                )

            self._run_command(server, "sudo echo '%s' > %s" % (server["id"], tools.get_path_for_tenant("~/tenantid")))

            self._run_command(server, "sudo echo '%s@%s@%s' > %s" %
                              (server["hypervisor"], server["ip"], server["name"],
                               tools.get_path_for_tenant("~/tenant_description")))

            # self._run_command(server, "sudo mkdir /media/")

            self._run_command(server, "sudo rm -r -d /media/*")

            self._run_command(server, "sudo rm %s;sudo rm %s" %
                              (tools.get_path_for_tenant("*.err"),
                               tools.get_path_for_tenant("*.out")))

    def _run_command(self, server, command):
        return Experiment.run_command(
            command=command,
            ssh_client=server["ssh"],
            print_output=self.print_output,
            print_output_if_have_error=self.print_output_if_have_error
        )

    @staticmethod
    def run_command(ssh_client, command, print_output=True, print_output_if_have_error=True):

        if print_output:
            print ("{EXECUTE %s} %s\n" % (ssh_client.host, command))

        ret = ssh_client.execute(command)

        if (not print_output) and print_output_if_have_error and ret["retval"] > 0:
            print ("{EXECUTED %s} %s\n" % (ssh_client.host, command))
            print ("     [RESPONSE %s] OUT: %s\n     RETVAL:%s   ERR:%s \n" %
                   (ssh_client.host, ret["out"], ret["retval"], ret["err"]))

        if print_output:
            print ("     [RESPONSE %s] OUT: %s\n     RETVAL:%s   ERR:%s \n" %
                   (ssh_client.host, ret["out"], ret["retval"], ret["err"]))

        return ret

    def kill_workload_generator_all_servers(self):
        self.run_command_on_all_servers(
            "ps -ef | grep python | grep -v grep | awk '{print $2}' | xargs sudo kill -9"
            # "ps -ef | grep workload_generator | grep -v grep | awk '{print $2}' | xargs sudo kill -9"
        )

    def run_command_on_all_servers(self, command):

        for server in self.servers:
            self._run_command(server, command)

    def detach_delete_all_servers_volumes(self):
        self.run_command_on_all_servers(
            "sudo nohup python %s det-del >%s 2>%s &" %
            (
                tools.get_path_for_tenant("~/MLSchedulerAgent/workload_generator.py"),
                tools.get_path_for_tenant("~/detach_delete_all_servers_volumes.out"),
                tools.get_path_for_tenant("~/detach_delete_all_servers_volumes.err"),
            )
        )

    def start_workload_generators(self, workload_args, performance_args):

        try:
            command = ["sudo", "rm", "/root/exp_*"]
            out, err, p = tools.run_command(command)
            tools.log(
                type="INFO2",
                code="rm_root_exp*",
                file_name="experiment.py",
                function_name="start_workload_generators",
                message="%s @@ %s" % (" ".join(command), out),
                exception=err)
        except Exception as err:
            pass

        number_of_servers_running = 0

        for server in self.servers:
            remote_machine = RemoteMachine(server_ip=server["ip"])

            self.remote_machine_list.append(remote_machine)

            remote_machine.start(workload_args=workload_args, performance_args=performance_args)

            number_of_servers_running = number_of_servers_running + 1

            print ("number of servers currently running: " + str(number_of_servers_running))

        last_bad_vol_count = 0

        while True:

            current_bad_vol_count = communication.get_error_log_count(experiment_id=self.experiment["id"])

            if "start-new" in _args_commands and current_bad_vol_count - last_bad_vol_count >= communication.Communication.get_config(
                    "restart_controller_compute_bad_volume_count_threshold"):

                tools.log(
                    type="WARNING",
                    code="regular_service_restart",
                    file_name="experiment.py",
                    function_name="start_workload_generators",
                    message="restarting compute and controller services to make sure everything will be fine. ever 7 minutes")

                try:
                    tools.run_command2(
                        'sudo python /root/cinder/cinder/MLScheduler/experiment.py execute-controller --command "service keystone restart; service nova-api restart; service nova-cert restart; service nova-consoleauth restart; service nova-scheduler restart; service nova-conductor restart; service nova-novncproxy restart; service neutron-server restart; service memcached restart" > /root/exp_controller_restart_err_count.out',
                        get_out=True
                    )

                    tools.run_command2(
                        'python /root/cinder/cinder/MLScheduler/experiment.py execute-compute --command "service nova-compute restart; service neutron-linuxbridge-cleanup restart; service neutron-linuxbridge-agent restart" > /root/exp_computes_restart_err_count.out',
                        get_out=True
                    )

                    tools.run_command2("python ~/cinder/cinder/MLScheduler/experiment.py del-err", get_out=True)

                    last_bad_vol_count = last_bad_vol_count + current_bad_vol_count
                except Exception as err:
                    tools.log(
                        type="ERROR",
                        code="error_count_limit_failed",
                        file_name="experiment.py",
                        function_name="start_workload_generators",
                        message="failed restarting services. will wait for 10 seconds",
                        exception=err)

            is_all_remote_machines_done = True

            for remote_machine in self.remote_machine_list:
                is_all_remote_machines_done = is_all_remote_machines_done and remote_machine.is_alive() is False

            if is_all_remote_machines_done is True:
                print ("\n%%%%%%%%%%%%%%All experiments done%%%%%%%%%%%%%%")
                break

            time.sleep(12)

        if (self.debug_server_ip is None or self.debug_server_ip.strip()) == '':
            tools.run_command2(
                'python /root/cinder/cinder/MLScheduler/experiment.py execute-compute --command "service nova-compute restart; service neutron-linuxbridge-cleanup restart; service neutron-linuxbridge-agent restart" > exp_computes_restart_simulation_done.out')

            tools.run_command2(
                'python ~/cinder/cinder/MLScheduler/experiment.py execute --command "sudo reboot" > exp_reboot_hosts_simulation_done.out')

    @staticmethod
    def create_ssh_clients(server_ip):
        f = open(
            os.path.join(
                os.path.expanduser('~'),
                "keys",
                "vm-test",
                "vm-test.pem"
            ), 'r')

        s = f.read()

        uname = "centos"

        if server_ip == "10.18.75.189":
            uname = "ubuntu"

        client = tools.SshClient(
            host=server_ip,
            port=22,
            key=s,
            username=uname,
            password='')

        return client

    @staticmethod
    def execute_compute(command):
        compute_node_ip_list = [
            ("10.18.75.51", "compute1"),
            ("10.18.75.52", "compute2"),
            ("10.18.75.53", "compute3"),
            ("10.18.75.54", "compute4"),
            ("10.18.75.55", "compute5"),
            ("10.18.75.56", "compute6"),
            ("10.18.75.57", "compute7"),
            ("10.18.75.58", "compute8"),
            ("10.18.75.59", "compute9"),
            ("10.18.75.45", "compute10"),
            ("10.18.75.46", "compute11"),
            ("10.18.75.47", "compute12")
            # "10.18.75.48","compute1"),
            # "10.18.75.49","compute1"),
            # "10.18.75.50""compute1"),
        ]

        f = open(os.path.join(os.path.expanduser('~'), "keys", "server.pem"), 'r')
        s = f.read()

        errors = []

        for compute_ip in compute_node_ip_list:
            try:
                client = tools.SshClient(host=compute_ip[0], port=22, key=s, username="root", password='')

                print ("\n\n      [%s] Executing: %s" % (compute_ip, command))

                result = client.execute(command)
                for key, value in result.iteritems():
                    print("[%s]: %s" % (key, value))
            except Exception as err:
                errors.append((compute_ip, str(err)))

        print ("\n*************ERRORS*************")
        for err_server in errors:
            print ("[%s]: %s\n" % err_server)

    @staticmethod
    def execute_controller(command):
        compute_node_ip_list = [
            ("10.18.75.41", "controller")
        ]

        f = open(os.path.join(os.path.expanduser('~'), "keys", "server.pem"), 'r')
        s = f.read()

        errors = []

        for compute_ip in compute_node_ip_list:
            try:
                client = tools.SshClient(host=compute_ip[0], port=22, key=s, username="root", password='')

                print ("\n\n      [%s] Executing: %s" % (compute_ip, command))

                result = client.execute(command)
                for key, value in result.iteritems():
                    print("[%s]: %s" % (key, value))
            except Exception as err:
                errors.append((compute_ip, str(err)))

        print ("\n*************ERRORS*************")
        for err_server in errors:
            print ("[%s]: %s\n" % err_server)

    @staticmethod
    def execute_blocks(command):
        compute_node_ip_list = [
            ("10.18.75.61", "block1"),
            ("10.18.75.62", "block2"),
            ("10.18.75.63", "block3"),
            ("10.18.75.64", "block4"),
            ("10.18.75.65", "block5"),
            ("10.18.75.66", "block6"),
            ("10.18.75.67", "block7"),
            ("10.18.75.68", "block8"),
            ("10.18.75.69", "block9"),
            ("10.18.75.70", "block10")
        ]

        f = open(os.path.join(os.path.expanduser('~'), "keys", "server.pem"), 'r')
        s = f.read()

        errors = []

        for compute_ip in compute_node_ip_list:
            try:
                client = tools.SshClient(host=compute_ip[0], port=22, key=s, username="root", password='')

                print ("\n\n      [%s] Executing: %s" % (compute_ip, command))

                result = client.execute(command)
                for key, value in result.iteritems():
                    print("[%s]: %s" % (key, value))
            except Exception as err:
                errors.append((compute_ip, str(err)))

        print ("\n*************ERRORS*************")
        for err_server in errors:
            print ("[%s]: %s\n" % err_server)


def args_load_defaults(args):
    args.assessment_policy = communication.AssessmentPolicy.parse(args.assessment_policy)
    args.learning_algorithm = MachineLearningAlgorithm.parse(args.learning_algorithm)

    args.skip_init = tools.str2bool(args.skip_init)
    args.save_info_logs = tools.str2bool(args.save_info_logs)
    args.debug_run_only_one_server = tools.str2bool(args.debug_run_only_one_server)
    args.print_output_if_have_error = tools.str2bool(args.print_output_if_have_error)
    args.print_output = tools.str2bool(args.print_output)
    args.new = tools.str2bool(args.new)
    args.read_is_priority = tools.str2bool(args.read_is_priority)
    args.performance_show_fio_output = tools.str2bool(args.performance_show_fio_output)

    if args.debug_run_only_one_server:
        if args.debug_server_ip is None:
            args.debug_server_ip = ""

    if args.debug_server_ip is not None and args.debug_server_ip.strip() != '':
        args.debug_run_only_one_server = True
        args.print_output = True
        args.print_output_if_have_error = True
    else:
        args.debug_run_only_one_server = False

    if args.performance_fio_test_name is None:
        args.performance_fio_test_name = "resource_evaluation.fio"
    if args.performance_terminate_if_takes is None:
        args.performance_terminate_if_takes = 15
    if args.performance_restart_gap is None:
        args.performance_restart_gap = 25
    if args.performance_restart_gap_after_terminate is None:
        args.performance_restart_gap_after_terminate = 8
    # args.read_is_priority
    # args.performance_show_fio_output

    if args.volume_attach_time_out is None:
        args.volume_attach_time_out = 40
    if args.workload_fio_test_name is None:
        args.workload_fio_test_name = "workload_generator.fio"
    if args.workload_wait_after_volume_rejected is None:
        args.workload_wait_after_volume_rejected = "[[30], [1.0]]"
    if args.workload_request_read_iops is None:
        args.workload_request_read_iops = "[[600, 850, 1100], [0.3, 0.4, 0.3]]"
    if args.workload_request_write_iops is None:
        args.workload_request_write_iops = "[[400, 500, 600], [0.3, 0.4, 0.3]]"
    if args.workload_delay_between_storage_workload_generation is None:
        args.workload_delay_between_storage_workload_generation = "[[5], [1.0]]"
    if args.workload_delay_between_create_volume_generation is None:
        args.workload_delay_between_create_volume_generation = "[[2], [1.0]]"
    if args.workload_max_number_volumes is None:
        args.workload_max_number_volumes = "[[5], [1.0]]"
    if args.workload_volume_life_seconds is None:
        args.workload_volume_life_seconds = "[[500], [1.0]]"
    if args.workload_volume_size is None:
        args.workload_volume_size = "[[9], [1.0]]"

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

    parser = argparse.ArgumentParser(description='Manage experiments.')

    parser.add_argument('commands', type=str, nargs="+",
                        choices=[
                            "start", "shutdown", "start-new", "workload", "del-avail-err", "del-err",
                            "det-del", "kill-workload", "execute-compute", "execute-controller",
                            "execute", "init", "create-experiment", "execute-blocks"],
                        help=
                        """
                        Manage experiments.
                        """
                        )

    parser.add_argument('--command', metavar='', type=str, required=False,
                        help='execute command on all servers.')

    parser.add_argument('--training_experiment_id', default=0, metavar='', type=int, required=False,
                        help='if set 0 it will use the default scheduler. Other wise will use the given id to generate training dataset and create classification model to perform iops prediction. default=0')

    parser.add_argument('--debug_run_only_one_server', default='False', metavar='', type=str,
                        help='Only run one server for debug purposes. default=False')

    parser.add_argument('--print_output_if_have_error', default='True', metavar='', type=str,
                        help='print output if there is an error in execute command on the hosts. default=False')

    parser.add_argument('--print_output', default='False', metavar='', type=str,
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
    parser.add_argument('--volume_attach_time_out', default=40, metavar='', type=int,
                        required=False,
                        help='volume attach timeout default=40')

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

    parser.add_argument("--workload_delay_between_storage_workload_generation", default=None, metavar='',
                        type=str, required=False,
                        help='wait xx seconds between generating workloads. example="[[2], [1.0]]"')

    parser.add_argument("--workload_delay_between_create_volume_generation", default=None, metavar='',
                        type=str, required=False,
                        help='wait xx seconds between creating new volume request. example="[[5], [1.0]]"')

    parser.add_argument("--workload_max_number_volumes", default=None, metavar='',
                        type=str, required=False,
                        help='max number of vilumes to be created. example="[[6], [1.0]]"')

    parser.add_argument("--workload_volume_life_seconds", default=None, metavar='',
                        type=str, required=False,
                        help='life time of a volume. example="[[40], [1.0]]"')

    parser.add_argument("--workload_volume_size", default=None, metavar='',
                        type=str, required=False,
                        help='life time of a volume. example= "[[5], [1.0]]"')

    parser.add_argument('--save_info_logs', type=str, metavar='', required=False, default='False',
                        help='save INFO logs in database ?')

    parser.add_argument('--description', type=str, metavar='', required=False, default='',
                        help='a description such as: sequential read training')

    parser.add_argument('--assessment_policy', type=str, metavar='', required=False, default='max_efficiency',
                        help="choose within ['max_efficiency', 'efficiency_first', 'qos_first', 'strict_qos']")

    parser.add_argument('--skip_init', type=str, metavar='', required=False, default='True',
                        help='save INFO logs in database ?')

    parser.add_argument('--learning_algorithm', type=str, metavar='', required=False, default='j48',
                        help='J48, RepTree')

    parser.add_argument('--max_number_vols', default=400, metavar='', type=int, required=False,
                        help='stop the experiment when max number of requested volume is reached.')

    is_shutdown = False
    # END WORKLOAD GENERATOR

    args = parser.parse_args()

    print("Experiment run time: " + str(datetime.now()))

    args_load_defaults(args)

    _args_commands = args.commands

    args_has_init_initially = "init" in args.commands

    if "shutdown" in args.commands:
        args.commands = ["kill-workload", "kill-performance", "det-del"]
        args.debug_server_ip = ''
        args.new = False
        is_shutdown = True

    if "start" in args.commands:
        args.commands = ["init", "workload", "start"]
        if args.skip_init is True:
            args.commands.remove("init")
        args.new = False

    if "start-new" in args.commands:
        args.commands = ["init", "workload", "start-new"]
        if "init" in args.commands and args.skip_init is True:
            args.commands.remove("init")
        args.new = True

    if "create-experiment" in args.commands:
        args.new = True

    if args.debug_run_only_one_server and args_has_init_initially is False:
        if "init" in args.commands:
            args.commands.remove("init")

    if args.debug_run_only_one_server is True:
        args.save_info_logs = True

    workload_args = {
        "--fio_test_name": args.workload_fio_test_name,

        "--save_info_logs": str(args.save_info_logs),
        "--wait_after_volume_rejected": json.dumps(args.workload_wait_after_volume_rejected),
        "--request_read_iops": json.dumps(args.workload_request_read_iops),
        "--request_write_iops": json.dumps(args.workload_request_write_iops),
        '--delay_between_storage_workload_generation': json.dumps(
            args.workload_delay_between_storage_workload_generation),
        "--delay_between_create_volume_generation": json.dumps(args.workload_delay_between_create_volume_generation),
        "--max_number_volumes": json.dumps(args.workload_max_number_volumes),
        "--volume_life_seconds": json.dumps(args.workload_volume_life_seconds),
        "--volume_size": json.dumps(args.workload_volume_size)
    }

    performance_args = {
        "--perf_fio_test_name": args.performance_fio_test_name,
        "--perf_terminate_if_takes": args.performance_terminate_if_takes,
        "--perf_restart_gap": args.performance_restart_gap,
        "--perf_restart_gap_after_terminate": args.performance_restart_gap_after_terminate,
        "--perf_show_fio_output": args.performance_show_fio_output,
    }

    if "del-avail-err" in args.commands:
        print ("del-avail-err")
        tools.delete_volumes_available_error(delete_available=True)
        sys.exit()

    if "del-err" in args.commands:
        print ("del-err")
        tools.delete_volumes_available_error(delete_available=False)
        sys.exit()

    if "execute-compute" in args.commands:
        Experiment.execute_compute(args.command)
        sys.exit()

    if "execute-controller" in args.commands:
        Experiment.execute_controller(args.command)
        sys.exit()

    if "execute-blocks" in args.commands:
        Experiment.execute_blocks(args.command)
        sys.exit()

    is_training = True
    if args.training_experiment_id > 0:
        is_training = False

    script_volume_clock_calc = tools.read_file("script_volume_clock_calc.py")
    script_volume_performance_meter_clock_calc = tools.read_file("script_volume_performance_meter_clock_calc.py")

    e = Experiment(
        is_shutdown=is_shutdown,
        debug_server_ip=args.debug_server_ip,
        debug_run_only_one_server=args.debug_run_only_one_server,
        add_new_experiment=args.new,
        print_output_if_have_error=args.print_output_if_have_error,
        print_output=args.print_output,
        config=json.dumps({
            "max_number_vols": args.max_number_vols,
            "learning_algorithm": args.learning_algorithm,
            "restart_controller_compute_bad_volume_count_threshold": 60,
            "number_of_servers_to_start_simulation": 40,

            # ################################ BAYES NET ################################
            # ################################ BAYES NET ################################
            # ############################## READ BAYES NET ################################
            "assess_read_eff_fir_bn": "vol_count == 1 or [v1] >= 0.62 or [v2] >= 0.53 or [v3] >= 0.44",
            "assess_read_qos_fir_bn": "vol_count == 1 or [v1] >= 0.67 or [v2] >= 0.60",
            "assess_read_str_qos_bn": "vol_count == 1 or [v1] >= 0.70 or [v2] >= 0.65",
            # ############################# WRITE BAYES NET ################################
            "assess_write_eff_fir_bn": "vol_count == 1 or [v1] >= 0.65 or [v2] >= 0.55 or [v3] >= 0.47",
            "assess_write_qos_fir_bn": "vol_count == 1 or [v1] >= 0.70 or [v2] >= 0.65",
            "assess_write_str_qos_bn": "vol_count == 1 or [v1] >= 0.63 or [v2] >= 0.68",

            # ################################ TREE  ################################
            # ################################ TREE ################################
            # ############################ READ TREE ################################
            "assess_read_eff_fir": "vol_count == 1 or [v1] >= 0.70 or [v2] >= 0.70 or [v3] > 0.70",
            "assess_read_qos_fir": "vol_count == 1 or [v1] >= 0.70 or [v2] >= 0.67",
            "assess_read_str_qos": "vol_count == 1 or [v1] >= 0.90",
            # ############################# WRITE TREE ################################
            "assess_write_eff_fir": "vol_count == 1 or [v1] >= 0.70 or [v2] >= 0.70 or [v3] > 0.70",
            "assess_write_qos_fir": "vol_count == 1 or [v1] >= 0.73 or [v2] >= 0.70",
            "assess_write_str_qos": "vol_count == 1 or [v1] >= 0.93",

            "assessment_policy": args.assessment_policy,
            "description": args.description,
            "training_experiment_id": args.training_experiment_id,
            "read_is_priority": args.read_is_priority,
            "is_training": is_training,
            "min_required_vpm_records": 150,  # used in [get_training_dataset] stored procedure
            "volume_attach_time_out": args.volume_attach_time_out,
            "wait_volume_status_timeout": 15,

            "workload_args": dict([(z[2:], w) for z, w in workload_args.iteritems()]),
            "performance_args": dict([(z[2:], w) for z, w in performance_args.iteritems()]),

            "mod_normalized_clock_for_feature_generation": args.mod_normalized_clock_for_feature_generation,
            "training_dataset_size": args.training_dataset_size,

            "volume_clock_calc": script_volume_clock_calc,
            "volume_performance_meter_clock_calc": script_volume_performance_meter_clock_calc,

            "assess_read_max_eff": "[v1] >= 0.00 or [v2] >= 0.00 or [v3] >= 0.00 or [v4] >= 0.00",
            "assess_write_max_eff": "[v1] >= 0.00 or [v2] >= 0.00 or [v3] >= 0.00 or [v4] >= 0.00"
        })
    )

    if "init" in args.commands:
        e.initialize_commands()

    if "workload" in args.commands:
        e.start_workload_generators(workload_args, performance_args)

    if "kill-workload" in args.commands:

        e.kill_workload_generator_all_servers()

        # sleep 4 to make sure all the processes are dead are not going to create new volumes!
        if "det-del" in args.commands:
            time.sleep(3)

        e.kill_workload_generator_all_servers()

    if "det-del" in args.commands:
        e.detach_delete_all_servers_volumes()
        tools.delete_volumes_available_error(delete_available=True)

    if "execute" in args.commands:
        e.run_command_on_all_servers(args.command)

    e.close_all_ssh_client()

