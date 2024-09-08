from typing import Any
import time, datetime
from pySerialTransfer import pySerialTransfer as txfer

class Sensor:

    m_serial: str = ""
    m_link = None
    m_no_save: int = 5
    m_state: list[list] = []
    m_timeout: datetime.timedelta = None
    CHAR_SIZE: int = 1
    m_last_known_pos: int = 0

    def __init__(
            self,
            serial: str = "",
            no_save: int = 5,
            timeout: datetime.timedelta = datetime.timedelta(seconds=5),
            char_size: int = 1
    ):
        self.m_serial = serial
        self.m_no_save = no_save
        self.m_timeout = timeout
        self.CHAR_SIZE = char_size
        self.m_link = txfer.SerialTransfer(self.m_serial)
        try:
            self.m_link.open()
        except Exception as r:
            self.error_handle(msg="Init " + str(r))

    def __len__(self):
        return 0 if len(self.m_state) == 0 else len(self.m_state[0]) 

    def __str__(self):
        return "\n".join([f"State of sens No.{i} : " + str(x) for i,x in enumerate(self.m_state)])

    def error_handle(
            self,
            msg: str = "thing"):
        print(f"[SENSOR][Error] with: {msg}")

        import traceback
        traceback.print_exc()
        try:
            self.m_link.close()
        except:
            pass

    def wait_answer(
            self,
            timeout: datetime.timedelta | None = None
    ):
        ###################################################################
        # Wait for a response and report any errors while receiving packets
        ###################################################################
        if timeout is None:
            timeout = self.m_timeout
        start = datetime.datetime.now()

        try:
            while not self.m_link.available():
                if datetime.datetime.now() > (start + timeout):
                    print("Timeout!")
                    break
                # A negative value for status indicates an error
                if self.m_link.status < 0:
                    if self.m_link.status == txfer.Status.CRC_ERROR:
                        print('ERROR: CRC_ERROR')
                    elif self.m_link.status == txfer.Status.PAYLOAD_ERROR:
                        print('ERROR: PAYLOAD_ERROR')
                    elif self.m_link.status == txfer.Status.STOP_BYTE_ERROR:
                        print('ERROR: STOP_BYTE_ERROR')
                    else:
                        print('ERROR: {}'.format(self.m_link.status))

        except Exception as r:
            self.error_handle(msg="wait_answer " + str(r))
            return -1

    def poll(self) -> Any:

        try:
            # Send Some
            self.m_link.tx_obj(1)
            self.m_link.send(1)
            self.wait_answer()
            num_rec = self.m_link.rx_obj(
                            obj_type=str,
                            obj_byte_size=self.CHAR_SIZE
            )
            num_rec = int.from_bytes(
                        num_rec.encode("utf-8")
                    )
            if num_rec is not None:
                rec = []
                for i in range(num_rec):
                    new = self.m_link.rx_obj(
                                obj_type=str,
                                obj_byte_size=self.CHAR_SIZE,
                                start_pos=(i+1)*self.CHAR_SIZE
                    )
                    rec.append(
                        int.from_bytes(
                            new.encode("utf-8")
                        )
                    )
                    #print(rec)
            else:
                print("EXIT")

        except Exception as r:
            self.error_handle(msg="poll " + str(r))
            return

        if any([True if x>0 else False for x in rec]):
            self.m_last_known_pos = rec.index(max(rec))
            if len(self.m_state) == self.m_no_save:
                self.m_state.pop(0)
            self.m_state += [rec]

        print(self.m_last_known_pos, self.m_state)
        return self.m_last_known_pos