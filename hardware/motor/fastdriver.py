
from enum import Enum
import time
from binascii import hexlify
import numpy as np


class Order(Enum):
    """
    Pre-defined orders
    """

    HELLO = 200


class Command:

    def __init__(self, order, send_list, receive_list):
        self.order = order
        self.send_list = send_list
        self.receive_list = receive_list

class RcvTimeoutException(Exception):
    pass

class FastdriverController:

    def __init__(self, **kwargs):
        from pySerialTransfer import pySerialTransfer as txfer

        if (dry:= kwargs.pop("dry", None)) is None:
            self.link = txfer.SerialTransfer(kwargs['com_port'], baud=kwargs['baud_rate'])
            self.link.open()
            time.sleep(0.75)  # allow some time for the Arduino to completely reset

        self.challenge_minimum_position = kwargs.get('challenge_minimum_position', 0)
        self.challenge_maximum_position = kwargs.get('challenge_maximum_position', 0)
        self.response_timeout_counter = kwargs.get('response_timeout_counter', 200000)

        self.enable_switch_test = kwargs.get('enable_switch_test', False)

        self.num_motors = kwargs.get('num_motors', 1)
        self.max_command_length = 40 + 1  # self.num_motors * 2 + 1
        self.arduino_answer_payload_length = 4

        self.ALL_BOARDS = 0xFF

        self.all_commands = {'HELLO': Command(0x01, [], ['long']),
                             'RETURN_LONG': Command(0x02, ['long'], ['long']),
                             'SET_STEP_MODE': Command(0x10, ['byte', 'byte'], []),
                             'ACC_KVAL': Command(0x11, ['byte', 'byte'], []),
                             'DEC_KVAL': Command(0x12, ['byte', 'byte'], []),
                             'RUN_KVAL': Command(0x13, ['byte', 'byte'], []),
                             'HOLD_KVAL': Command(0x14, ['byte', 'byte'], []),
                             'MAX_SPEED': Command(0x15, ['byte', 'long'], []),
                             'FULL_SPEED': Command(0x16, ['byte', 'long'], []),
                             'ACC': Command(0x17, ['byte', 'long'], []),
                             'DEC': Command(0x18, ['byte', 'long'], []),
                             'SWITCH_MODE': Command(0x19, ['byte', 'long'], []),
                             'MIN_SPEED': Command(0x20, ['byte', 'long'], []),

                             'GET_POS': Command(0x40, ['byte'], ['long']),
                             'GET_MARK': Command(0x41, ['byte'], ['long']),
                             'RUN': Command(0x42, ['byte', 'long', 'byte'], []),
                             'STEP_CLOCK': Command(0x43, ['byte', 'long'], []),
                             'MOVE': Command(0x44, ['byte', 'long', 'byte'], []),
                             'GO_TO': Command(0x45, ['byte', 'long'], []),
                             'GO_TO_DIR': Command(0x46, ['byte', 'long'], []),
                             'GO_UNTIL': Command(0x47, ['byte', 'long', 'byte', 'byte'], []),
                             'RELEASE_SW': Command(0x48, ['byte', 'byte', 'byte'], []),
                             'GO_HOME': Command(0x49, ['byte', ], []),
                             'GO_MARK': Command(0x50, ['byte', ], []),
                             'SET_MARK': Command(0x51, ['byte', 'long'], []),
                             'SET_POS': Command(0x52, ['byte', 'long'], []),
                             'RESET_POS': Command(0x53, ['byte'], []),
                             'RESET_DEV': Command(0x54, ['byte'], []),
                             'SOFT_STOP': Command(0x55, ['byte'], []),
                             'HARD_STOP': Command(0x56, ['byte'], []),
                             'SOFT_HI_Z': Command(0x57, ['byte'], []),
                             'HARD_HI_Z': Command(0x58, ['byte'], []),
                             'GET_POS_2': Command(0x59, ['byte'], ['long']),
                             'GET_STATUS': Command(0x61, ['byte'], ['long']),
                             'GET_BUSY_CHECK': Command(0x62, ['byte', 'long'], ['long']),
                             'SET_ALL_POSITIONS': Command(0x63, ['uint16'] * self.num_motors, []),
                             'SET_ALL_POSITIONS_BLOCKING': Command(0x64, ['uint16'] * self.num_motors, ['long']),
                             'SET_ALL_POSITIONS_BLOCKING_FS_ONLY': Command(0x65, ['uint16'] * self.num_motors,
                                                                           ['long']),
                             'MOVE_FS_ONLY': Command(0x66, ['byte', 'long', 'byte'], []),
                             'ALL_BLOCKING_BUSY': Command(0x67, [], []),
                             'GET_CONFIG': Command(0x68, ['byte'], ['long']),
                             'GO_TO_FS_ONLY': Command(0x69, ['byte'], ['long']),
                             }

        self.homing_speed = 300
        self.homing_move_constant = 20
        self.switch_open_position = 175
        self.switch_closed_position = 195

        self.step_mode = {'FS': 0, 'FS_2': 1, 'FS_4': 2, 'FS_8': 3, 'FS_16': 4, 'FS_32': 5, 'FS_64': 6, 'FS_128': 7}

        self.go_until_mode = {'reset_abspos': 0x00, 'copy_abspos': 0x08}
        self.direction = {'fwd': 0, 'bwd': 1}

        # INITIALIZE BOARDS
        self.motor_settings = kwargs['motor_settings']
        if dry is None:
            self.set_board_parameter(**self.motor_settings)
        #self.home(self.ALL_BOARDS)

    def set_board_parameter(self, **kwargs):
        self.stop_motors_hard()
        self.set_default_switch_mode(1)
        parameters_to_set = ['ACC_KVAL', 'DEC_KVAL', 'RUN_KVAL', 'HOLD_KVAL', 'MAX_SPEED', 'FULL_SPEED', 'ACC', 'DEC']
        for param in parameters_to_set:
            self.send_command(param, self.ALL_BOARDS, kwargs[param])

        self.set_step_mode(self.ALL_BOARDS, kwargs['step_mode'])

    def send_command(self, command, *payload):
        import logging

        current_command = self.all_commands[command]

        if type(payload) is tuple:
            payload = list(payload)

        payload_bytes = []
        for idx, item in enumerate(current_command.send_list):
            if item == 'byte':
                payload_bytes.append(payload[idx])
            elif item == 'long':
                payload_bytes += [payload[idx] & 0xFF, (payload[idx] >> 8) & 0xFF, (payload[idx] >> 16) & 0xFF,
                                  (payload[idx] >> 24) & 0xFF]
            elif item == 'uint16':
                payload_bytes += [payload[idx] & 0xFF, (payload[idx] >> 8) & 0xFF]
            else:
                raise ValueError()

        try:
            received_payload = self.send_command_internal(current_command.order, payload_bytes)
        except RcvTimeoutException:
            logging.error('fastdriver send_command: rcv timeout')
            received_payload = self.send_command_internal(current_command.order, payload_bytes)

        rcv_index = 0
        return_values = []
        for idx, item in enumerate(current_command.receive_list):
            if item == 'byte':
                return_values.append(received_payload[rcv_index])
                rcv_index += 1
            elif item == 'long':
                return_values.append(received_payload[rcv_index] | (received_payload[rcv_index + 1] << 8) | (
                            received_payload[rcv_index + 2] << 16) | (received_payload[rcv_index + 3] << 24))
                rcv_index += 4
            elif item == 'uint16':
                return_values.append(received_payload[rcv_index] | (received_payload[rcv_index + 1] << 8))
                rcv_index += 2
            else:
                raise ValueError()

        return return_values

    def send_command_internal(self, order, payload=[]):
        from pySerialTransfer import pySerialTransfer as txfer

        fill_length = self.max_command_length - 1 - len(payload)
        payload += [0] * fill_length

        send_size = 0
        send_size = self.link.tx_obj(order, val_type_override='B', start_pos=send_size)
        # print(payload)
        for byte in payload:
            send_size = self.link.tx_obj(byte, val_type_override='B', start_pos=send_size)
        send_successful = self.link.send(send_size)

        timeout_counter = 0
        available = self.link.available()
        while not available:
            if self.link.status < 0:
                if self.link.status == txfer.CRC_ERROR:
                    raise Exception('ERROR: CRC_ERROR')
                elif self.link.status == txfer.PAYLOAD_ERROR:
                    raise Exception('ERROR: PAYLOAD_ERROR')
                elif self.link.status == txfer.STOP_BYTE_ERROR:
                    raise Exception('ERROR: STOP_BYTE_ERROR')
                else:
                    raise Exception('ERROR: {}'.format(self.link.status))
            available = self.link.available()
            if timeout_counter >= self.response_timeout_counter:
                raise RcvTimeoutException()
            timeout_counter += 1

        received_payload = self.link.rx_obj(obj_type=type(payload),
                                            obj_byte_size=5,
                                            list_format='B')
        # print(hexlify(bytearray(received_payload)))
        mirrored_order = received_payload[0]
        if mirrored_order != order:
            raise Exception(f'Arduino answered with wrong order. Expected {order}. Received {mirrored_order}')

        received_payload = received_payload[1:]

        return received_payload

    # def send_hello(self):
    #     return self.send_command(Order.HELLO)

    def set_challenge_internal(self, challenge):
        """
        Set the next challenge. Block until challenge is completely set.

        :param challenge: list of ints
        :return:
        """
        self.send_command('SET_ALL_POSITIONS', *challenge)

    def go_to_position_blocking(self, board, position):
        """
        Set the next challenge. Block until challenge is completely set.

        :param challenge: list of ints
        :return:
        """
        raise Exception('DOES NOT WORK;DEBUG')
        self.send_command('GO_TO_FS_ONLY', board, position)
        self.all_block_busy()

    def run(self, board, direction, speed):
        """


        :param challenge: list of ints
        :return:
        """
        self.send_command('RUN', board, speed,  self.direction[direction])

    def set_challenge_blocking(self, challenge, fs_only=False):
        """
        Set the next challenge. Block until challenge is completely set.

        :param challenge: list of ints
        :return:
        """
        if fs_only:
            self.send_command('SET_ALL_POSITIONS_BLOCKING_FS_ONLY', *challenge)
        else:
            self.send_command('SET_ALL_POSITIONS_BLOCKING', *challenge)

    def create_random_challenges(self, number_of_challenges, rng=None, **kwargs):
        if rng is None:
            rng = np.random.default_rng()
        return rng.integers(self.challenge_minimum_position, self.challenge_maximum_position + 1,
                            size=(number_of_challenges, self.num_motors),
                            dtype='uint16').tolist()

    def set_step_mode(self, board, step_mode):
        self.send_command('SET_STEP_MODE', board, self.step_mode[step_mode])

    def get_status(self, board):
        return self.send_command('GET_STATUS', board)

    def go_until(self, board, speed, action, direction):
        self.send_command('GO_UNTIL', board, speed, self.go_until_mode[action], self.direction[direction])
        while not self.is_switch_pressed(board):
            time.sleep(0.1)

    def move(self, board, steps, direction, fs_only=True):
        if fs_only:
            self.send_command('MOVE_FS_ONLY', board, steps, self.direction[direction])
        else:
            self.send_command('MOVE', board, steps, self.direction[direction])

    def home(self, board):
        self.go_until(board, self.homing_speed, 'reset_abspos', 'fwd')
        self.all_block_busy()
        self.move(board, self.homing_move_constant, 'bwd')
        self.all_block_busy()
        self.go_until(board, self.homing_speed, 'reset_abspos', 'fwd')
        self.all_block_busy()

    def reset_device(self, board):
        self.send_command('RESET_DEV', board)

    def all_block_busy(self):
        self.send_command('ALL_BLOCKING_BUSY')

    def is_switch_pressed(self, selected_motor):
        status = self.get_status(selected_motor)
        #print(status)
        return (status[0] in [32274, 32278, 32282, 32336])  # True means switch is open

    def __del__(self):
        self.stop_motors_hard()
    # self.serial_handler.close()

    def close(self):
        self.stop_motors_hard()
        self.link.close()
        # self.serial_handler.close()

    def set_challenge(self, challenge, block_while_moving=True, no_switch_test=False):
        if self.enable_switch_test and not no_switch_test:
            self.perform_switch_test()
        if isinstance(challenge, np.ndarray):
            challenge = challenge.tolist()
        self.set_challenge_blocking(challenge, fs_only=True)

    def self_test(self):
        # message = 'REHOMING NOW'
        message = ''
        error = False
        self.home(self.ALL_BOARDS)
        # self.set_challenge([self.switch_closed_position] * self.num_motors, no_switch_test=True)
        #
        # switch_closed_status = []
        # for cnt in range(self.num_motors):
        #     switch_closed_status.append(self.is_switch_pressed(cnt))
        # switch_closed_status = np.array(switch_closed_status)
        #
        # if not np.any(switch_closed_status == True):
        #     # print('All switches closed as expected')
        #     pass
        # else:
        #     indices = np.where(switch_closed_status)
        #     message = f'Some switches unexpectedly open: {indices}'
        #     error = True
        #
        # self.set_challenge([self.switch_open_position] * self.num_motors, no_switch_test=True)
        # switch_closed_status = []
        # for cnt in range(self.num_motors):
        #     switch_closed_status.append(self.is_switch_pressed(cnt))
        # switch_closed_status = np.array(switch_closed_status)
        # if not np.any(switch_closed_status == False):
        #     # print('All switches open as expected')
        #     pass
        # else:
        #     indices = np.where(~switch_closed_status)
        #     message += f'Some switches unexpectedly closed: {indices}'
        #     error = True
        # # if error:
        # #     from datetime import datetime
        # #     print(f'A switch error occurred {datetime.now()}')
        # # raise Exception('Switch check, something went wrong')
        # if error:
        #     self.reinit()

        return not error, message

    def reinit(self):
        self.reset_device(self.ALL_BOARDS)
        self.set_board_parameter(**self.motor_settings)

    def stop_motors_hard(self):
        self.send_command('HARD_HI_Z', self.ALL_BOARDS)

    def set_default_switch_mode(self, mode=0):
        self.send_command('SWITCH_MODE', self.ALL_BOARDS, mode)

    def test(self):
        self.go_until(self.ALL_BOARDS, self.homing_speed, 'reset_abspos', 'fwd')

    def start_rotate(self, board, direction, speed):
        self.send_command('RUN', board, speed,  self.direction[direction])

    def stop_rotate(self,board=99):
        #self.send_command('HARD_HI_Z', self.ALL_BOARDS)
        if(board == 99):
            self.send_command('HARD_HI_Z', self.ALL_BOARDS)
        else:
            self.send_command('HARD_HI_Z', board)
