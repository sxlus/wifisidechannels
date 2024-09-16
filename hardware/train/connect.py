from pathlib import Path
from typing import Any, ClassVar, List, Optional, Tuple, Union
import paramiko
import socket

"""
Example usage:
        self.ssh_conn = SSHConnector(ip="10.2.3.56",
                                port=22,
                                username="physec",
                                password="PhySec2018")
        self.ssh_conn.run_command('sudo pkill -9 -f IRS_control.py')
        self.ssh_conn.run_command_background(
            f'sudo python3 MA_simon/IRS_control.py -s /dev/ttyACM0 -R {R:.2f} -P {P:.2f} -f {f:d}')
"""

class SSHConnector:
    """
    Abstraction layer for SSH and SFTP commands

    :param ip: IP of the SSH-server
    :param port: Port of the SSH-server
    :param username: username for the SSH-server
    :param password: password, either to open the keyfile or for username+password login
    :param keyfile: Private key file
    """

    def __init__(
        self,
        ip: str = "127.0.0.1",
        port: int = 22,
        username: Optional[str] = None,
        password: Optional[str] = None,
        keyfile: Optional[Path] = None,
        hot: Optional[bool] = False
    ) -> None:

        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.keyfile = keyfile
        """
        if not self.host_key_file.exists():
            self.logger.warning("Host keys is missing, creating empty file")
            self.host_key_file.parent.mkdir(parents=True, exist_ok=True)
            self.host_key_file.touch()

        host_key_filename = str(self.host_key_file)
        """
        try:
            client = paramiko.SSHClient()
            """
            try:
                client.load_host_keys(host_key_filename)
            except IOError:
                self.logger.warning("Could not load host keys")
            """
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if hot:
                try:
                    client.connect(
                        hostname=ip,
                        port=port,
                        username=username,
                        password=password,
                        key_filename=str(keyfile) if keyfile else None,
                        look_for_keys=False,
                    )
                except paramiko.SSHException as e:
                    if not password:
                        client.get_transport().auth_none(username)
                    else:
                        raise e
        except TimeoutError:
            raise ConnectionError(f"Can not establish SSH Connection to {ip}")
        except paramiko.ssh_exception.AuthenticationException:
            raise Exception(
                f"Username ({username}) or password or private key file for host {ip} are invalid"
            )
        self.ssh_client = client
        #self.sftp_client = client.open_sftp()

    def identify(self) -> str:
        """
        Return a simple indentifier: <classname>:<user>@<ip>:<port>

        :returns: Identifier
        """
        return f"{type(self).__name__}:{self.username}@{self.ip}:{self.port}"

    def run_command_background(self, command: str):
        """
        Runs a shell command on the participant.
        Does not wait for it to finish and returns the stdout and stderr channels

        :param command: ssh command to execute
        :return: stdout and stderr ssh channels
        """
        #self.logger.debug(f'{self.ip} running "{command}"')
        # the timeout applies to socket operations, not waiting for an exit code
        _, stdout, stderr = self.ssh_client.exec_command(command, timeout=15)
        return stdout, stderr

    def run_command_channel(self, command : str):
        transport = self.ssh_client.get_transport()
        channel = transport.open_session(timeout=0.5)
        channel.settimeout(0.5)
        try:
            channel.exec_command(command)
        except socket.timeout:
            pass

    def run_command(
        self, command: str, error_msg: Optional[str] = None
    ) -> Tuple[int, List[str], List[str]]:
        """
        Runs a shell command on the participant and waits for the command to finish.

        :param command: ssh command to execute
        :param error_msg: When specified, causes exit codes!=0
            to throw an exception with this as message

        :raises UnexpectedBashError: When the command fails and `error_msg` is set

        :returns: Exit code, STDOUT lines, STDERR lines
        """
        stdout, stderr = self.run_command_background(command)
        exit_code = stdout.channel.recv_exit_status()
        out_lines = stdout.readlines()
        err_lines = stderr.readlines()
        if error_msg and exit_code:
            raise Exception(
                f"{error_msg} on {self.ip}\n"
                + f'"{command}" returned code {exit_code}\n'
                + f'STDOUT:\n{"".join(out_lines)}STDERR:\n{"".join(err_lines)}'
            )
        return exit_code, out_lines, err_lines

    def upload_file(
            self, filename_local: str, filename_remote: str
    ) -> None:
        sftp = self.ssh_client.open_sftp()
        sftp.put(filename_local, filename_remote)
        sftp.close()

    def download_file(
            self, filename_remote: str, filename_local: str
    ) -> bool:
        sftp = self.ssh_client.open_sftp()
        try:
            sftp.stat(filename_remote)
        except IOError:
            return False

        sftp.get(filename_remote, filename_local)
        sftp.close()
        return True

    def close(self) -> None:
        """
        Close the ssh & sftp connections
        Paramiko prevents the garbage collection from doing this, so it must be done
        manually (see https://github.com/paramiko/paramiko/pull/891)

        This is especially important if you have long-running scripts that constantly
        create APUParticipants, as you may hit ram/sockets/... limits.
        """
        #self.sftp_client.close()
        self.ssh_client.close()

    def is_open(self) -> bool:
        """
        Checks if both SSH and SFTP client are still open

        :returns: If the connector is still open
        """
        return (
            #self.sftp_client.get_channel().get_transport() is not None
            #and
            self.ssh_client.get_transport() is not None
        )

