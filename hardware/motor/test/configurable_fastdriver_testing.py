from raex.util.pathmanager import PathManager

from omegaconf import DictConfig, OmegaConf
from glom import glom, assign
from fastdriver import FastdriverController
from binascii import hexlify

from datetime import datetime
import time


def configurable_fastdriver_test(cfg: DictConfig):
    try:
        cfg = OmegaConf.to_container(cfg)
    except ValueError:
        pass
    device_cfg = glom(cfg, 'device', default={})

    # create all devices (challenge, radio, env)
    devices = instantiate_devices(device_cfg)

    fastdriver : FastdriverController = devices['challenge']['fastdriver']
    num_motors = 20

    # a = fastdriver.send_command('RETURN_LONG', 11223344)
    # # status = fastdriver.get_status(1)
    # # status = fastdriver.send_command('RESET_POS', 0)
    # status = fastdriver.send_command('GET_STATUS', 0)
    # print(hex(status[0]&(1<<7)))
    # fastdriver.self_test()
    # config = fastdriver.send_command('GET_CONFIG', 0)
    # print(hex(config[0]))
    # # fastdriver.reinit()
    # fastdriver.set_challenge_blocking([45, 45], fs_only=True)
    # fastdriver.set_challenge_blocking([60, 60], fs_only=True)
    # fastdriver.set_default_switch_mode(1)
    # fastdriver.set_default_switch_mode(0)
    #
    # fastdriver.move(0, 500, 'fwd')
    #
    # for cnt in range(20):
    #     fastdriver.move(0xff, 50, 'fwd')
    #     fastdriver.all_block_busy()
    #     time.sleep(0.2)
    #
    # fastdriver.home(0xff)
    # fastdriver.home(0)
    start = time.time()
    count = 15
    for cnt in range(count):
        fastdriver.set_challenge_blocking([100]*num_motors, fs_only=True)
        # fastdriver.set_challenge_blocking([150]*num_motors, fs_only=True)
        fastdriver.set_challenge_blocking([0]*num_motors, fs_only=True)
    print(f'{(time.time() - start) / (count*2)}')
    print()


    motors = list(range(15,20))
    motors = [17]
    start = time.time()
    count = 15
    position = [0]*num_motors
    for motor in motors:
        for cnt in range(count):
            position[motor] = 100
            fastdriver.set_challenge_blocking(position, fs_only=True)
            position[motor] = 0
            fastdriver.set_challenge_blocking(position, fs_only=True)
            # fastdriver.set_challenge_blocking([150]*num_motors, fs_only=True)
    print(f'{(time.time() - start) / (count*2)}')
    print()

    # fastdriver.send_command('RESET_POS', fastdriver.ALL_BOARDS)
    # time.sleep(0.1)
    # print(f'POS RESET: {fastdriver.send_command("GET_POS", 0)} {fastdriver.send_command("GET_POS", 1)}')
    # fastdriver.set_challenge([100, 100])
    # time.sleep(0.1)
    # print(f'POS AFTER SET CHALLENGE: {fastdriver.send_command("GET_POS", 0)} {fastdriver.send_command("GET_POS", 1)}')
    # fastdriver.send_command('MOVE', 0, 200, 1)
    # fastdriver.send_command('MOVE', 1, 200, 1)
    # time.sleep(2)
    # print(f'POS AFTER MOVE: {fastdriver.send_command("GET_POS", 0)} {fastdriver.send_command("GET_POS", 1)}')
    # fastdriver.send_command('GO_TO', 0, 100)
    # time.sleep(1)
    # print(f'POS AFTER GO TO: {fastdriver.send_command("GET_POS", 0)} {fastdriver.send_command("GET_POS", 1)}')
    # fastdriver.set_challenge([100, 100])
    # time.sleep(2)
    # print(f'POS AFTER SECOND CHALLENGE: {fastdriver.send_command("GET_POS", 0)} {fastdriver.send_command("GET_POS", 1)}')




    # status = fastdriver.send_command('MOVE', 0, 100, 0)

    # start = time.time()
    # count = 4
    # for _ in range(count):
    #     a = fastdriver.send_command('HELLO')
    #     # print(hexlify(bytearray(a)))
    #     # autodriver.set_challenge(autodriver.create_random_challenges(1)[0], )
    # print(f'{(time.time()-start)/count}')

    # import time
    # for i in range(5):
    #     block = 1
    #     time.sleep(2)
    #     for cnt in range(5*block, 5*block+5):
    #         autodriver.autodriver_controller.motor_move(cnt, 100, 'fwd')
    #         time.sleep(0.5)
    #         print(cnt)
    #
    # for cnt in range(20):
    #     autodriver.autodriver_controller.motor_move(cnt, 50, 'fwd')
    #     time.sleep(0.5)
    #     print(cnt)



    # a = fastdriver.send_hello()

    print()




