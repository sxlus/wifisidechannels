
import wifisidechannels.components.packet_processor as packet_processor
import wifisidechannels.components.plotter as plotter
import wifisidechannels.models.models as models
import wifisidechannels.models.presets as presets

import subprocess, pathlib, os, time
import multiprocessing as mp
import threading as td
import shlex
import typing
import joblib
import datetime 

class WiFi():

    """
    Interface for different aspects of WiFi 802.11x
    """
    PROCESSES   : int                               = 4
    m_name      : str                               = "[ wifi ]"
    m_interface : str                               = ""
    m_channel   : int
    m_freq      : int

    m_processor : list[packet_processor.PacketProcessor]

    m_plotter   : plotter.Plotter                   = plotter.Plotter()


    m_data      : list                              = []
    ## bash script for NIC handling
    m_set_up    : pathlib.Path

    # procs
    m_procs     : list[mp.Process]                  = []

    ## queues for supprocesses
    m_stdout    : mp.Queue                          = mp.Queue()
    ## stdin currently unused, but largely implemented for foreward compability
    m_stdin     : mp.Queue                          = mp.Queue()
    m_stderr    : mp.Queue                          = mp.Queue()

    def __init__(self, **kwargs):
        self.m_name     = self.m_name + str(kwargs.get("name")) if kwargs.get("name") else self.m_name
        self.m_interface= kwargs.get("interface") if isinstance(kwargs.get("interface"), str) else self.m_interface
        self.m_channel  = kwargs.get("channel", 0)
        self.m_freq     = kwargs.get("freq", 0) 
        self.m_processor   = [
            kwargs.get("processor") ] if isinstance(kwargs.get("processor"), packet_processor.PacketProcessor) \
                else kwargs.get("processor") if isinstance(kwargs.get("processor"), list) else []
        self.m_plotter  = kwargs.get("plotter") if kwargs.get("plotter") else self.m_plotter
        # ???? data again
        self.m_data     = kwargs.get("data") if isinstance(kwargs.get("data"), dict) else []

        self.m_set_up   = pathlib.Path(os.path.join("bash/setup_device.sh")) if \
                           not kwargs.get("set_up", "") else kwargs.get("set_up", "")

    def _eavesdrop(
            self,
            processor:  packet_processor.PacketProcessor | \
                    list[packet_processor.PacketProcessor] | None = None,
            timeout: int                                    = 10,
            kwargs: dict                                    = {}
    ) -> list[models.Packet]:

        """
        Utilizes NIC to record Packtets in Monitor Mode.
        @OUT Queue filled with data for other Process possebly to perform calculations on that data.
        The main thread could continue to capture data and manage the nic while this is done.

        @PARAM kwargs shall be use to to further configure the NIC and the capture_procedure.
            kwargs is used to configure and select tasks (processes) to launch. they are mostly directly passed.
            Additional kwargs are:
                filter_fields   : str = pass string that instructs to apply filter and display certain fields on call to _listen
                frequency       : int = freq to set NIC to before listening
                channel         : int = channel to set NIC to before listening
                write_file      : str = path to store to pcapng

        NOTES:
        From here one could further mangle data filtered/selected by tshark display_filters 
        ( capture_filter support in setup_script currently not present ) and handeled by packet processor.
        for TxBf this will be the respective class. 
        """

        print(
            f"[*] {self.m_name} - Capturing on: {self.m_interface}" + \
            (f" @freq:{str(freq)}" if (freq:= kwargs.get("frequency", None)) else "") + \
            (f" @channel:{str(chan)}" if (chan:= kwargs.get("channel", None)) else "") + \
            (f" for {str(sec)} seconds." if (sec:= kwargs.get("timeout", None)) else "")
        )

        if processor is None:
            processor = self.m_processor
        write_file      = kwargs.pop("write_file", "")
        filter_fields   = kwargs.pop("filter_fields", "")
        preset = None

        if write_file:
            print(f"\t[*] Writing to {write_file}.")
    
        if not processor:
            preset = presets.TSHARK_FIELDS_VHT
            if (mac_sa:= kwargs.pop("mac_sa", None)) and isinstance(mac_sa, str):
                preset.add_filter(models.TsharkDisplayFilter.MAC_SA.value, preset.vrfy_mac(mac_sa))
            if (mac_da:= kwargs.pop("mac_da", None))and  isinstance(mac_da, str):
                preset.add_filter(models.TsharkDisplayFilter.MAC_DA.value, preset.vrfy_mac(mac_da))

            print(f"\t[*] Using preset: {str(preset)}.")

            kwargs |= (
                {
                    "add": " -w " + str(write_file)
                } if not filter_fields and write_file else {
                    "add": str(filter_fields) + " "
                } if filter_fields else {
                    "add" : str(preset)
                }
            )
            processor = packet_processor.PacketProcessor(
                name=preset.NAME,
                extractor=preset.extractor()
            )
            self.m_processor.append(processor)
        else:
            # not used
            mac_sa = kwargs.pop("mac_sa")
            mac_da = kwargs.pop("mac_da")

            kwargs |= (
                {
                    "add": " -w " + str(write_file)
                } if not filter_fields and write_file else {
                    "add": str(filter_fields) + " "
                }
            )

        if isinstance(processor, packet_processor.PacketProcessor):
            processor = [ processor ]

        #self.launch_process(function=self._enable_monitor, blocking=True)

        kwargs |= {
            "timeout": timeout
        } if not kwargs.get("timeout") else {}
        
        if (channel:= kwargs.pop("channel", "")):
            pass
        #    kw = kwargs | ({
        #        "add": channel
        #    })
        #    self.launch_process(function=self._set_channel, kwargs=kw, blocking=True)
        if (frequency:= kwargs.pop("frequency", "")):
            pass
        #    kw = kwargs | ({
        #        "add": frequency
        #    })
        #    self.launch_process(function=self._set_frequency, kwargs=kw, blocking=True)

        proc = self.launch_process(function=self._listen, kwargs=kwargs, blocking=True if write_file else False)
        time.sleep(1)
        self.procs_alive(procs=[proc])
        print(f"Procs after listen: {proc} - {self.m_procs}")

        if write_file:
            kwargs |= {
                "add" : write_file + " " + (filter_fields if filter_fields else str(preset))
            }
            proc = self.launch_process(function=self._read, kwargs=kwargs)

        return processor,timeout,kwargs,proc

    def eavesdrop(
            self,
            processor:  packet_processor.PacketProcessor | \
                    list[packet_processor.PacketProcessor] | None = None,
            timeout: int                                    = 10,
            kwargs: dict                                    = {}
    ) -> list[models.Packet]:

        processor,timeout,kwargs,proc = self._eavesdrop(processor=processor,timeout=timeout,kwargs=kwargs)

        # here we can wait until the timeout ends the shell script and _listen teminates 
        # while emptying the queue or read just A few of them and dispatch new tasks that 
        # processes the data further

        data = self.collect_stdout(procs=[proc],    timeout=timeout)
        error  = self.collect_stderr(procs=[proc],  timeout=timeout)

        for err in error:
            print(err)

        packets = []
        for proc in processor:
            packets += proc.handle(raw=data)

        #for pack in packets:
        #    print(str(pack))

        self.m_data = packets

        return packets

    def _process_capture(
            self,
            processor:  packet_processor.PacketProcessor | \
                    list[packet_processor.PacketProcessor] | None = None,
            timeout: int                                    = 10,
            kwargs: dict                                    = {}
    ) -> list[models.Packet]:

        """
        Utilizes precaptured .pcapng to pass it trough set_up script
        @OUT Queue filled with data for other Process possebly to perform calculations on that data.
        The main thread could continue to capture data and manage the nic while this is done.

        @PARAM kwargs shall be use to to further configure the NIC and the capture_procedure.
            kwargs is used to configure and select tasks (processes) to launch. they are mostly directly passed.
            Additional kwargs are:
                filter_fields   : str = string that instructs to apply filter and display certain fields on call to _listen
                read_file       : str = name of file to read from
                mac_sa          : str = MAC filtering source
                mac_da          : str = MAC filtering dest 
        """

        if not kwargs.get("read_file"):
            print(f"[ERROR] process_capture - No file to read in 'read_file' key of kwargs specified.")
        print(f"[*] {self.m_name} - Processing capture: {kwargs.get('read_file', '')}")
        if processor is None:
            processor = self.m_processor

        if not processor:
            preset = presets.TSHARK_FIELDS_VHT
            if (mac_sa:= kwargs.pop("mac_sa", None)) and isinstance(mac_sa, str):
                preset.add_filter(models.TsharkDisplayFilter.MAC_SA.value, preset.vrfy_mac(mac_sa))
            if (mac_da:= kwargs.pop("mac_da", None))and  isinstance(mac_da, str):
                preset.add_filter(models.TsharkDisplayFilter.MAC_DA.value, preset.vrfy_mac(mac_da))
            print(f"\t[*] Using preset: {str(preset)}.")

            processor = packet_processor.PacketProcessor(
                name=preset.NAME,
                extractor=preset.extractor()
            )

            kwargs |= (
                {
                    "add": str(kwargs.pop("read_file", "")) + " " + str(preset)
                } if not (val:= kwargs.pop("filter_fields", "")) else {
                    "add": str(kwargs.pop("read_file", "")) + " " + val
                }
            )

        else:
            kwargs |= (
                {
                    "add": str(kwargs.pop("read_file", "")) + (" " + val if (val:= kwargs.pop("filter_fields", "")) else "") 
                }
            )
        if isinstance(processor, packet_processor.PacketProcessor):
            processor = [ processor ]

        kwargs |= {
            "timeout": timeout
        } if not kwargs.get("timeout") else {}

        proc = self.launch_process(function=self._read, kwargs=kwargs)

        return processor,timeout,kwargs,proc

    def process_capture(
            self,
            processor:  packet_processor.PacketProcessor | \
                    list[packet_processor.PacketProcessor] | None = None,
            timeout: int                                    = 10,
            kwargs: dict                                    = {}
    ) -> list[models.Packet]:

        """
            @PARAM kwargs shall be use to to further configure the NIC and the capture_procedure.
            kwargs is used to configure and select tasks (processes) to launch. they are mostly directly passed.
            Additional kwargs are:
            filter_fields   : str = string that instructs to apply filter and display certain fields on call to _listen
            read_file       : str = name of file to read from
            mac_sa          : str = MAC filtering source
            mac_da          : str = MAC filtering dest
        """
        processor,timeout,kwargs,proc =  self._process_capture(processor=processor,timeout=timeout,kwargs=kwargs)

        #print(f"Procs after read: {proc} - {self.m_procs}")
        self.procs_alive(procs=[proc])

        # here we can wait until the timeout ends the shell script and _listen teminates 
        # while emptying the queue or read just A few of them and dispatch new tasks that 
        # processes the data further

        data = self.collect_stdout(procs=[proc],    timeout=timeout)
        error  = self.collect_stderr(procs=[proc],  timeout=timeout)

        for err in error:
            print(err)

        packets = []
        for proc in processor:
            packets += proc.handle(raw=data)

        #for pack in packets:
        #    print(str(pack))

        self.m_data = packets

        return packets


    def collect_sample(
            self,
            processor:  packet_processor.PacketProcessor | \
                    list[packet_processor.PacketProcessor] | None = None,
            timeout: int                                    = 10,
            kwargs: dict                                    = {}
    ) -> list[models.Packet]:
        """
        Collect a specific number of packets of a specific kind while packets beeing read from disk or sniffed.
        @PARAM:
            num             : Number of packets to sample
        """
        num = x if (x:=kwargs.get("num", None)) is not None else 1
        nkwargs = kwargs.copy()
        nkwargs.pop("num", None)
        processor,timeout,kwargs,proc = self._eavesdrop(processor=processor,timeout=timeout,kwargs=nkwargs)
        #processor,timeout,kwargs,proc = self._process_capture(processor=processor,timeout=timeout,kwargs=kwargs)
        #print("PROCESSOR: ", str(processor[0]))
        packets = self.search_stdout(procs=[proc], timeout=timeout, num = num, found_call=lambda x: [ i for i in processor[0].handle(x) if i.DATA != {} ])
        self.terminate(procs=[proc])
        error  = self.collect_stderr(procs=[proc],  timeout=timeout)
        #print("PROCESSOR: ", str(processor[0]))

        for err in error:
            print(err)

        self.m_data += packets
        self.clear_queue()
        return packets

    # lauches processes for tasks in the form of funtions
    def launch_process(
            self,
            function: typing.Callable,
            blocking: bool | None = False,
            kwargs: dict = {}
    ) -> mp.Process:
        """Shedules tasks to be handled."""
        abort = 10
        i = 0
        while len(self.procs_alive()) == self.PROCESSES:
            print("[DEBUG]: lauch_task - waiting for processes to finish.")
            i+=1
            if i >= abort:
                return None
            time.sleep(1)
        proc = mp.Process(target=function, kwargs=kwargs)
        if not blocking:
            self.m_procs.append(proc)
        proc.start()
        if blocking:
            proc.join()

        return proc

    def _exec(
            self,
            cmd: str,
            stdin = None,
            stdout = None,
            stderr = None,
            timeout: int = None
    ):
        """
        Does the 'heavy' lifting of dealing with Popen and collecting the outs in the desired queues.
        """
        if stdin is None:
            stdin = self.m_stdin
        if stdout is None:
            stdout = self.m_stdout
        if stderr is None:
            stderr = self.m_stderr
        cmd = shlex.split((f"timeout {timeout} " if timeout else "") + str(cmd))

        print(f"Proc {os.getpid()} launching tasks" + (f" with timeout {timeout}" if timeout is not None else "") + f": {str(cmd)}")

        with subprocess.Popen(
            args=cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE) as proc:
            if stdout:
                for line in proc.stdout:
                    #rint(line)
                    stdout.put(line)
            if stderr:
                for line in proc.stderr:
                    #print(line)
                    stderr.put(line)

    # common usecases for _exec
    ## by now for each of the followwing tasks is launched in a seperate process. 
    def _listen(
            self,
            stdin = None,
            stdout = None,
            stderr = None,
            timeout: int    = None,
            dry: bool       = False,
            add: str     = ""
    ) -> None | str:
        cmd = f"\"{self.m_set_up}\" -n {self.m_interface} -l" + ((" " + str(add)) if add else "")
        if not dry:
            self._exec(cmd=cmd,
                    stdin=stdin, 
                    stderr=stderr,
                    stdout=stdout,
                    timeout=timeout)
        else:
            return cmd
        
    def _read(
            self,
            stdin = None,
            stdout = None,
            stderr = None,
            timeout: int = None,
            dry: bool       = False,
            add: str     = ""
    ) -> None | str:
        """
        Use add to supply file to read.
        """
        cmd = f"{self.m_set_up} -r" + (" " + str(add) if add else "")
        if not dry:
            self._exec(cmd=cmd,
                   stdin=stdin, 
                   stderr=stderr,
                   stdout=stdout,
                   timeout=timeout)
        else:
            return cmd

    def _enable_monitor(
            self,
            stdin = None,
            stdout = None,
            stderr = None,
            timeout: int = None,
            dry: bool    = False, # not needed 
            add: str     = ""
    ) -> None | str:

        cmd = f"{self.m_set_up} -n {self.m_interface} -e" + (" "+str(add) if add else "")
        if not dry:
            self._exec(cmd=cmd,
                   stdin=stdin, 
                   stderr=stderr,
                   stdout=stdout,
                   timeout=timeout)
        else:
            return cmd

    def _disable_monitor(
            self,
            stdin = None,
            stdout = None,
            stderr = None,
            timeout: int = None,
            dry: bool       = False,
            add: str     = ""
    ) -> None | str:

        cmd = f"{self.m_set_up} -n {self.m_interface} -d" + (" "+str(add) if add else "")
        if not dry:
            self._exec(cmd=cmd,
                   stdin=stdin, 
                   stderr=stderr,
                   stdout=stdout,
                   timeout=timeout)
        else:
            return cmd

    def _set_frequency(
            self,
            stdin = None,
            stdout = None,
            stderr = None,
            timeout: int = None,
            dry: bool       = False,
            add: str     = ""
    ) -> None | str:

        cmd = f"{self.m_set_up} -n {self.m_interface} -f" + (" "+str(add) if add else "")
        if not dry:
            self._exec(cmd=cmd,
                   stdin=stdin, 
                   stderr=stderr,
                   stdout=stdout,
                   timeout=timeout)
        else:
            return cmd

    def _set_channel(
            self,
            stdin = None,
            stdout = None,
            stderr = None,
            timeout: int = None,
            dry: bool       = False,
            add: str     = ""
    ) -> None | str:

        cmd = f"{self.m_set_up} -n {self.m_interface} -c" + (" "+str(add) if add else "")
        if not dry:
            self._exec(cmd=cmd,
                   stdin=stdin, 
                   stderr=stderr,
                   stdout=stdout,
                   timeout=timeout)
        else:
            return cmd

    # gets data from main queues that might be filled by capturing live or reading from pcapng 
    def _collect_queue(
            self,
            queue: mp.Queue,
            procs: list[mp.Process] | None = None,
            num: int | None = None,
            timeout: int | None = None
    ) -> list:

        if num is None and procs is None:
            print(f"[WARN]: collect_queue - Amount to read an procs to care about not specified usind ALL!")
            procs = self.m_procs
        if not isinstance(procs, list):
            procs = [ procs ]
        data = []
        try:
            if num:
                i = 0
                while i < num and any(self.procs_alive(procs=procs)) and not queue.empty():
                    try:
                        data.append(queue.get(
                            block=False,
                            timeout=timeout))
                        i+=1
                    except Exception as r:
                        print(r, end="\r")
                        time.sleep(1)
            else:
                while any(self.procs_alive(procs=procs)):
                    try:
                        data.append(queue.get(
                            block=False,
                            timeout=timeout))
                    except Exception as r:
                        print(r, end="\r")
                        time.sleep(1)
                while not queue.empty():
                    data.append(queue.get(block=False, timeout=timeout))
        except KeyboardInterrupt:
            self.terminate()
        return data

    def collect_stdout(
            self,
            procs: list[mp.Process] = None,
            num: int = None,
            timeout: int = 5
    ):
        return self._collect_queue(
            queue=self.m_stdout,
            procs=procs,
            num=num,
            timeout=timeout
        )

    def search_stdout(
            self,
            found_call: typing.Callable[..., list],
            procs: list[mp.Process] = None,
            num: int = 1,
            timeout: int = 5):

        new = []
        if num <= 0:
            return []
        print("NUM:", num)
        while (len(new) < num) and self.procs_alive(procs=procs):
            data = found_call(self._collect_queue(
                                        queue=self.m_stdout,
                                        procs=procs,
                                        num=1,
                                        timeout=timeout))
            #for x in data:
            #    print("NEW : ", str(x))
            new += data
            #print("DATA found so far: ", len(new))


        return new[:num]
        

    def collect_stderr(
            self,
            procs: list[mp.Process] = None,
            num: int = None,
            timeout: int = 5
    ):

        return self._collect_queue(
            queue=self.m_stderr,
            procs=procs,
            num=num,
            timeout=timeout
        )
    def clear_queue(self) -> bool:
        try:
            if self.m_stdin is not None:
                self.m_stdin.empty()
            if self.m_stderr is not None:
                self.m_stderr.empty()
            if self.m_stdout is not None:
                self.m_stdout.empty()
        except Exception as r:
            print(f"Clear Queue: {r}")
            return 1
        return 0


    # stuff on procs that might have been spawned
    def procs_alive(
            self,
            procs: list[mp.Process] | None = None
    ) -> list[mp.Process]:

        if procs is None or procs == self.m_procs:
            self.m_procs = [x for x in self.m_procs if x.is_alive()]
            return self.m_procs
        else:
            return [x for x in procs if x.is_alive()]

    def terminate(
            self,
            procs: list[mp.Process] | None = None
    ):
        if procs is None:
            procs = self.m_procs
        for x in [x for x in procs if x.is_alive()]:
            x.terminate()

    # will want to save data in parsed form. Here very basic.
    def store(
            self,
            data: typing.Iterable[models.Packet] | None = None,
            write_file: pathlib.Path | str | None = "test",
            meta_info: dict = {},
    ) -> bool:
        """
        Stores Packages.
        """
        now = datetime.datetime.now()
        now_str = datetime.datetime.strftime(now, "%y_%m_%d-%H_%M_%S")
        reset = False

        if data is None:
            data = self.m_data
            reset = True
    
        if not data:
            print(f"{self.m_name}[ STORE ][ ERROR ]: No data to save!")
            return True

        if isinstance(write_file, str):
            write_file = pathlib.Path(write_file)
        elif write_file is None:
            write_file = pathlib.Path(now_str)

        if not isinstance(write_file, pathlib.Path):
            print(f"{self.m_name}[ STORE ][ ERROR ]: write_file should be path or string, is {type(write_file)} - {str(write_file)}.")
            return False
        
        if not isinstance(meta_info, dict):
            print(f"{self.m_name}[ STORE ][ ERROR ]: meta_info should be dict, is {type(meta_info)} - {str(meta_info)}.")
            return False
        
        
        joblib.dump(data,       pathlib.Path( os.path.join(write_file.parents, str(now_str) + ("_" + write_file.stem if str(write_file) != now_str else "") + "_data") + (".dump" if write_file.suffixes == [] else "".join(write_file.suffixes))))
        joblib.dump(meta_info,  pathlib.Path( os.path.join(write_file.parents, str(now_str) + ("_" + write_file.stem if str(write_file) != now_str else "") + "_meta") + (".dump" if write_file.suffixes == [] else "".join(write_file.suffixes))))
        
        if reset:
            self.m_data = []

        return True