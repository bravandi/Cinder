import tools
import os
import communication

class Experiment:

    def __init__(self):
        self.servers = []

        experiment_id = communication.insert_experiment(
            workload_id=1,
            comment='',
            scheduler_algorithm='',
            config=''
        )

        tools.log("New wxperiment id: %s" % str(experiment_id))

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

    def clone_or_pull_agent(self):

        for server in self.servers:

            ret = Experiment._run_command(server, 'git clone https://github.com/bravandi/MLSchedulerAgent.git')

            if ret["retval"] == 128:

                Experiment._run_command(server, "git -C ~/MLSchedulerAgent/ pull")

            Experiment._run_command(server, "echo '%s' > ~/tenantid" % server["id"])

            Experiment._run_command(server, "source ~/MLSchedulerAgent/other/fio_install.sh")

    @staticmethod
    def _run_command(server, command):

        print ("{RUNNING %s} %s\n" % (server["ip"], command))

        ret = server["ssh"].execute(command)

        print ("     [RESPONSE %s] OUT: %s\n     RETVAL:%s ERR: %s \n" %
               (server["ip"], ret["out"], ret["retval"], ret["err"]))

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

    e = Experiment()

    # e.clone_or_pull_agent()

    # e.close_all_ssh_client()

    # client = tools.SshClient(
    #     host='10.18.75.174',
    #     port=22,
    #     key=s,
    #     username='ubuntu',
    #     password='')

    try:
       # ret = client.execute('git clone https://github.com/bravandi/MLSchedulerAgent.git')
       #
       # print "  ".join(ret["out"]), "  E ".join(ret["err"]), ret["retval"]
       #
       # if ret["retval"] == 128:
       #
       #     ret = client.execute("git -C /home/ubuntu/MLSchedulerAgent/ pull")
       #
       # print "  ".join(ret["out"]), "  E ".join(ret["err"]), ret["retval"]




        pass

    finally:
      # client.close()
        pass

    # print communication.insert_experiment(
    #     workload_id=1,
    #     comment='',
    #     scheduler_algorithm='',
    #     config=''
    # )

    pass
