import tools
import os
import communication
import sys

class Experiment:

    experiment = None

    def __init__(self, add_new_experiment, print_stderr = False):

        self.print_stderr = print_stderr
        self.servers = []

        if add_new_experiment:

            experiment_id = communication.insert_experiment(
                workload_id=1,
                comment='',
                scheduler_algorithm='',
                config=''
            )

        Experiment.experiment = communication.get_current_experiment()

        tools.log("New wxperiment id: %s" % str(Experiment.experiment["id"]))

        nova = tools.get_nova_client()
        for server in nova.servers.list():
            server_ip = server.networks['provider'][0]
            ssh_client = Experiment._create_ssh_clients(server_ip)

            self.servers.append({
                "id": server.id,
                "ssh": ssh_client,
                "ip": server_ip
            })

    def close_all_ssh_client(self):

        for server in self.servers:

            ssh_client = server["ssh"]
            ssh_client.close()

    def initialize_commands(self):

        for server in self.servers:

            ret = self._run_command(server, 'git clone https://github.com/bravandi/MLSchedulerAgent.git')

            if ret["retval"] == 128:

                self._run_command(server, "git -C ~/MLSchedulerAgent/ pull")

            self._run_command(server, "echo '%s' > ~/tenantid" % server["id"])

            self._run_command(server, "source ~/MLSchedulerAgent/other/fio_install.sh")

            self._run_command(server, "source ~/MLSchedulerAgent/other/custom_commands.sh")

            self._run_command(server, "c_killPerformanceEvaluation")

            self._run_command(server, "c_killWorkloadGenerator", show_full_output=True)

            self._run_command(server, "")

            return

    def _run_command(self, server, command, show_full_output=False):

        print ("{RUNNING %s} %s\n" % (server["ip"], command))

        ret = server["ssh"].execute(command)

        stderr = ""
        if self.print_stderr or show_full_output:
            stderr = "ERR: %s" % ret["err"]

        print ("     [RESPONSE %s] OUT: %s\n     RETVAL:%s %s \n" %
               (server["ip"], ret["out"], ret["retval"], stderr))

        return ret

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
    if "new-exp" in sys.argv:
        add_new_experiment = True

    e = Experiment(
        add_new_experiment=add_new_experiment
    )

    e.initialize_commands()

    e.close_all_ssh_client()

