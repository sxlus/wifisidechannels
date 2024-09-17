import pathlib
import typing
import joblib
import os
import numpy as np

class BFIPWDatasetGenerator():

    m_folder:   pathlib.Path
    m_meta:     list[dict]  = []

    def __init__(self, folder: str | pathlib.Path):

        self.m_folder = folder if isinstance(folder, pathlib.Path) else \
                            pathlib.Path(folder) if isinstance(folder, str) else None

        self.m_meta = self.read_meta(folder=folder)

    def read_meta(self, folder: pathlib.Path | None = None, sub: str = "meta"):
        if folder is None:
            folder = self.m_folder
        if not folder:
            return []
        meta = self.read(folder=folder, sub=sub)
        self.m_meta = sorted(meta)
        return meta

    def read(
            self,
            file: pathlib.Path | None = None,
            folder: pathlib.Path | None = None,
            sub: str = "",
            num: int | None = None
    ) -> typing.Iterable[typing.Any]:

        if file is None and folder is None:
            print("YAK")
            return []
        
        if file is not None:
            return [joblib.load(file)]

        data = []
        for file in [os.path.join(x, file ) for x,_,y in os.walk(folder) for file in y if sub in file]:
            print(file)
            #data += self.read(file=file)

        return data

    def create_embedded_keystroke_samples(
            data: list,
            meta: dict,
            out_dir: pathlib.Path = pathlib.Path("DATASETS"),
            states_per_transient: int | None = None,
            func_on_state: typing.Callable = lambda x: x[np.random.randint(0, len(x))]
    ) -> bool:

        CWD = pathlib.Path(os.getcwd())
        DSD = pathlib.Path(os.path.join(CWD, out_dir))

        if states_per_transient is None:
            states_per_transient = meta.get("states_per_transient", None)
        if states_per_transient is None:
            print(f"[ BFIPWDatasetGenerator ][ ERROR ] Need to know how many samples per datapoint where recorded.")
            return False
        
        num_prefix_samples      = meta.get("states_per_transient", 0)

        data = data[num_prefix_samples:]

        num_states              = meta.get("max_positions", 10)
        num_samples_per_state   = meta.get("num_samples_per_state", 1)
        domain                  = meta.get("domain", 0)

        index = { i: {
            "start" : 0,
            "end"   : num_samples_per_state
        } for i in range(num_states)}
        for target in range(num_states):
            for prefix in range(num_states):
                for suffix in range(num_states):
                    pw = f"{str(prefix)}{str(target)}{str(suffix)}"
                    new_meta = {
                        "target": target,
                        "domain": domain,
                        "pw"    : pw,
                        "num_states": 1+states_per_transient*2,
                    }
                    prefix_samples = func_on_state(data[prefix*num_samples_per_state])
