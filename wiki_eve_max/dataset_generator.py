import pathlib
import typing
import joblib
import os
import numpy as np

class BFIPWDatasetGenerator():

    m_folder:   pathlib.Path
    m_meta:     dict[int, dict]  = {}

    def __init__(self, folder: str | pathlib.Path):

        self.m_folder = folder if isinstance(folder, pathlib.Path) else \
                            pathlib.Path(folder) if isinstance(folder, str) else None

        self.m_meta = self.read_meta(folder=folder)

    def read_meta(self, folder: pathlib.Path | None = None, sub: str = "meta"):
        if folder is None:
            folder = self.m_folder
        if not folder:
            return {}
        data = self.read(folder=folder, sub=sub)
        print(data)
        meta = {}
        for x in data:
            meta[x["domain"]] = x 
        self.m_meta = meta
        print(meta)
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
        for file in sorted([os.path.join(x, file ) for x,_,y in os.walk(folder) for file in y if sub in file]):
            print(file)
            data += self.read(file=file)
            data[-1] |= {"meta_file": file}
            #self.write(data = data[-1] | { "data_file": str(file).replace("meta", "data") }, file=file)

        return data

    def write(
            self,
            data: typing.Any,
            file: pathlib.Path | str
    ):

        if isinstance(file, str):
            file = pathlib.Path(file)

        if not os.path.exists(file.parents[0]):
            os.makedirs(file.parents[0], exist_ok=True)
        joblib.dump(data, file)

    def create_embedded_keystroke_samples(self,
            data,
            meta,
            out_dir: pathlib.Path = pathlib.Path("DATASETS"),
            states_per_transient: int | None = None,
            func_on_state: typing.Callable = lambda x: x[np.random.randint(0, len(x))],
            sample_spacing_random: bool = True
    ) -> bool:
        print("YAK")
       # CWD = pathlib.Path(os.getcwd())
       # DSD = pathlib.Path(os.path.join(CWD, out_dir))


        number_of_chunks = meta.get("number_of_chunks", None)

        if number_of_chunks is None:
            print(f"[ BFIPWDatasetGenerator ][ ERROR ] Need to know how many samples per datapoint where recorded.")
            return False

        if states_per_transient is None:
            states_per_transient = meta.get("number_of_chunks", None)

        num_prefix_samples      = meta.get("num_prefix_samples", 0)
        data = data[num_prefix_samples:]


        num_states              = meta.get("max_positions", 10)
        num_samples_per_state   = meta.get("samples_per_state", 1)
        domain                  = meta.get("domain", 0)
        print("HELLO")
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
                    prefix_start    = (prefix*number_of_chunks)# + (1 if prefix > 0 else 0)
                    prefix_end      = prefix_start + 1

                    target_start    = (target*number_of_chunks)# + (1 if target > 0 else 0)
                    target_end      = target_start + 1

                    suffix_start    = (suffix*number_of_chunks)# + (1 if suffix > 0 else 0)
                    suffix_end      = suffix_start + 1

                    if prefix < target:
                        pt_start    = prefix_end
                        pt_end      = target_start
                    elif prefix > target:
                        pt_start    = target_end
                        pt_end      = prefix_start
                    else:
                        pt_start    = target_start
                        pt_end      = target_end

                    if suffix < target:
                        ts_start    = suffix_end
                        ts_end      = target_start
                    elif suffix > target:
                        ts_start    = target_end
                        ts_end      = suffix_start
                    else:
                        ts_start    = target_start
                        ts_end      = target_end

                    prefix_sample  = [ func_on_state(data[prefix_start*num_samples_per_state:prefix_end*num_samples_per_state]) ]
                    target_sample  = [ func_on_state(data[target_start*num_samples_per_state:target_end*num_samples_per_state]) ]
                    suffix_sample  = [ func_on_state(data[suffix_start*num_samples_per_state:suffix_end*num_samples_per_state]) ]

                    print(prefix, prefix_start, prefix_end)
                    print(target, target_start, target_end)
                    print(suffix, suffix_start, suffix_end)

                    if sample_spacing_random:
                        pt_idx = sorted([np.random.randint(pt_start, pt_end) for _ in range(states_per_transient)], reverse=True if target < prefix else False)
                        ts_idx = sorted([np.random.randint(ts_start, ts_end) for _ in range(states_per_transient)], reverse=True if suffix < target else False)
                    else:
                        pt_idx = [ x for x in range(pt_start, pt_end, (pt_end-pt_start)//states_per_transient+1) ]
                        ts_idx = [ x for x in range(ts_start, ts_end, (ts_end-ts_start)//states_per_transient+1) ]
    
                    print(len(pt_idx), pt_idx)
                    print(len(ts_idx), ts_idx)

                    pt_sample = [ func_on_state(data[i*num_samples_per_state:(i+1)*num_samples_per_state]) for i in pt_idx ]
                    ts_sample = [ func_on_state(data[i*num_samples_per_state:(i+1)*num_samples_per_state]) for i in ts_idx ]

                    sample = np.array( prefix_sample + pt_sample + target_sample + ts_sample + suffix_sample )
                    print()
                    #print(sample)

                    self.write(sample, os.path.join(out_dir, pw + ".dump"))