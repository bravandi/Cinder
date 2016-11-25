import paramiko
from StringIO import StringIO
import pdb
import os
from keystoneauth1.identity import v3
from keystoneauth1 import session
from novaclient import client as n_client
from cinderclient import client as c_client


def get_session():
    auth = v3.Password(auth_url="http://controller:35357/v3",
                       username='admin',
                       password='ADMIN_PASS',
                       project_name='admin',
                       # user_domain_id = 'default',
                       # project_domain_id = 'default',
                       user_domain_name='default',
                       project_domain_name='default'
                       )

    sess = session.Session(auth=auth, verify='/path/to/ca.cert')

    return sess


# todo design a proper error management when calling openstack services using client API ies
def get_cinder_client():

    return c_client.Client(2, session=get_session())


def get_nova_client():

    return n_client.Client(2, session=get_session())


def delete_volumes_available_error():
    cinder = get_cinder_client()

    for volume in cinder.volumes.list():
        if volume.status == 'available' or volume.status == 'error':

            cinder.volumes.delete(volume.id)

class SshClient:
    "A wrapper of paramiko.SSHClient"
    TIMEOUT = 4

    def __init__(self, host, port, username, password, key=None, passphrase=None):

        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if key is not None:
            key = paramiko.RSAKey.from_private_key(StringIO(key), password=passphrase)

        self.client.connect(host, port, username=username, password=password, pkey=key, timeout=self.TIMEOUT)

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None

    def execute(self, command, sudo=False):
        feed_password = False

        if sudo and self.username != "root":
            command = "sudo -S -p '' %s" % command
            feed_password = self.password is not None and len(self.password) > 0

        stdin, stdout, stderr = self.client.exec_command(command)

        if feed_password:
            stdin.write(self.password + "\n")
            stdin.flush()

        if "apt-get" in command or "pip" in command:
            stdin.write("Y\n")
            stdin.flush()

        return {'out': stdout.readlines(),
                'err': stderr.readlines(),
                'retval': stdout.channel.recv_exit_status()}


def read_file(path):
    with open(os.path.realpath(path), 'r') as myfile:
        data = myfile.read()

    myfile.close()
    return data


def get_cinder_backends():
    cinder = get_cinder_client()

    result = []

    for backend in cinder.pools.list():
        result.append(backend.name)

    return result


def log(message, debug=False):

    print ("\n" + message + "\n")


def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")


if __name__ == '__main__':

    pass