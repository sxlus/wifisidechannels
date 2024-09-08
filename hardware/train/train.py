import hardware.train.connect as connect
import datetime
import time

class Train:
    connection: connect.SSHConnector = None
    m_ip = None
    m_port = None
    m_username = None
    m_password = None

    def __init__(
            self,
            ip="192.168.1.100",
            port=22,
            username="root",
            password="rocktrain"):

        self.connection = connect.SSHConnector(ip=ip, port=port, username=username, password=password, hot=True)
        self.m_ip = ip
        self.m_port = port
        self.m_username = username
        self.m_password = password

    def drive(
            self,
            delta: datetime.timedelta | None = None) -> bool:
        try:
            try:
                self.connection.run_command("port 1 state set 1")
            except Exception:
                self.connection = connect.SSHConnector(ip=self.m_ip, port=self.m_port, username=self.m_username, password=self.m_password, hot=True).run_command("port 1 state set 1")
            if delta is not None:
                time.sleep(delta.total_seconds())
                self.stop()
        except Exception as r:
            print(f"[Train][drive] encountered error {r}")
            return False
        return True

    def stop(self) -> bool:
        try:
            try:
                self.connection.run_command("port 1 state set 0")
            except Exception:
                self.connection = connect.SSHConnector(ip=self.m_ip, port=self.m_port, username=self.m_username, password=self.m_password, hot=True).run_command("port 1 state set 0")
        except Exception as r:
            print(f"[Train][stop] encountered error {r}")
            return False
        return True