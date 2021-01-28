import logging

import paramiko

from config import interfaces,logger

SSH_TIMEOUT = int(interfaces.get('ssh', 'command_timeout'))

# noinspection PyArgumentList
class SSHConnection:
    class __SSHConnection:
        def __init__(self):
            self.ip = interfaces.get('ssh', 'ip')
            self.port = int(interfaces.get('ssh', 'port'))
            self.username = interfaces.get('ssh', 'username')
            # self.password = ''
            self.session = paramiko.SSHClient()
            # paramiko.util.log_to_file("sshlogs.log")
            self.session.load_system_host_keys()
            self.session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                self.session.connect(self.ip, self.port, username=self.username, timeout = int(interfaces.get('ssh', 'ssh_timeout')), look_for_keys=False, allow_agent=False)
            except Exception as e:
                logger.debug("Fail to connect without password is -- {}".format(e))
                if "No authentication" in str(e):
                    self.session.get_transport().auth_none(self.username)
                else:
                    raise e
            self.channel = self.session.invoke_shell()

    instance = None

    def __init__(self):
        if not SSHConnection.instance:
            SSHConnection.instance = SSHConnection.__SSHConnection()

    def __getattr__(self):
        return getattr(self.instance)

    def get_session(self):
        """
        Gets a session to execute a command on the SSH server.
        Returns:

        """
        try:
            a = SSHConnection.instance.session.exec_command("ls",timeout=2)
            s = SSHConnection.instance.session.exec_command
            return s
        except Exception as e:
            SSHConnection.instance = SSHConnection.__SSHConnection()
            s = SSHConnection.instance.session.exec_command
            return s

    def get_transport_channel(self):
        """
        Open a transport channel for SSH communication
        Returns: Channel created

        """
        try:
            self.transport = SSHConnection.instance.session.get_transport()
            self.transport.set_keepalive(5)
            self.channel = self.transport.open_session(timeout=SSH_TIMEOUT)
            logger.debug("status is --> {}".format(self.transport.is_active()))
            return self.channel
        except Exception as e:
            logger.debug("SSHConnection retry : get_transport_channel -- {}".format(e))
            SSHConnection.instance = SSHConnection.__SSHConnection()
            self.transport = SSHConnection.instance.session.get_transport()
            self.transport.set_keepalive(5)
            self.channel = self.transport.open_session(timeout=SSH_TIMEOUT)
            return self.channel

    def log(self):
        """SSH logs capturing function"""
        paramiko.util.log_to_file("sshlogs.log")
    
    def get_shell(self):
        """
        Start an interactive shell session on the SSH server.
        Returns: Chanel created to run the test

        """
        try:
            if SSHConnection.instance.channel.closed:
                logger.debug("Session is closed, opening a new session")
                SSHConnection.instance = SSHConnection.__SSHConnection()
            # SSHConnection.instance.channel.send("pwd")
            # # time.sleep(2)
            # # logger.debug("Ready status: %s", SSHConnection.instance.channel.recv_ready())
            # while not SSHConnection.instance.channel.recv_ready():
            #     logger.debug("EXIS STATUS")
            #     time.sleep(1)
            # SSHConnection.instance.channel.recv(99999)
            channel =  SSHConnection.instance.channel
        except:
            logger.error("Error during retrieve the session, creating a new one")
            SSHConnection.instance = SSHConnection.__SSHConnection()
            channel =  SSHConnection.instance.channel
        return channel

    def close_shell(self):
        """
        Close the shell instance created in the test
        Returns: None

        """
        SSHConnection.instance.channel.close()
    
