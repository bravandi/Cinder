import tools
import os
import communication
import sys


class Experiment:

    experiment = None

    def __init__(self, add_new_experiment, print_output_if_have_error=False, print_output=False):

        self.print_output_if_have_error = print_output_if_have_error
        self.print_output = print_output
        self.servers = []

        if add_new_experiment:

            experiment_id = communication.insert_experiment(
                workload_id=1,
                comment='',
                scheduler_algorithm='',
                config=''
            )

        Experiment.experiment = communication.get_current_experiment()

        tools.log("Experiment id: %s" % str(Experiment.experiment["id"]))

        nova = tools.get_nova_client()
        for server in nova.servers.list():
            server_ip = server.networks['provider'][0]
            ssh_client = Experiment._create_ssh_clients(server_ip)

            if server_ip == '10.18.75.170':
                continue

            self.servers.append({
                "id": server.id,
                "ssh": ssh_client,
                "ip": server_ip,
                "name": server.name
            })

    def close_all_ssh_client(self):

        for server in self.servers:

            ssh_client = server["ssh"]
            ssh_client.close()

    def initialize_commands(self):

        for server in self.servers:

            ret = self._run_command(server, "sudo cat /etc/hosts")
            if server["name"] not in str(ret["out"]):
                self._run_command(
                    server,
                    "echo '%s\t%s' | sudo tee --append /etc/hosts" % (server["ip"], server["name"]))

            ret = self._run_command(server, 'sudo git clone https://github.com/bravandi/MLSchedulerAgent.git')

            if ret["retval"] == 128:

                self._run_command(server, "sudo git -C ~/MLSchedulerAgent/ reset --hard; sudo git -C ~/MLSchedulerAgent/ pull")

            self._run_command(server, "sudo echo '%s' > ~/tenantid" % server["id"])

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

    def start_workload_generators(self):

        pass

    def start_performance_evaluators(self):

        pass

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

if __name__ == '__main__':

    add_new_experiment = False
    if "new" in sys.argv:
        add_new_experiment = True

    e = Experiment(
        add_new_experiment=add_new_experiment,
        print_output_if_have_error=True,
        print_output=False
    )

    e.initialize_commands()

    if "workload" in sys.argv:
        e.start_workload_generators()

    if "performance" in sys.argv:
        e.start_performance_evaluators()

    e.close_all_ssh_client()

