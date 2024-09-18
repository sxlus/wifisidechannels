import pathlib
import typing
import joblib
import os
import numpy as np

class BFIPWDatasetGenerator():

    m_folder_in:    pathlib.Path
    m_folder_out:   pathlib.Path
    m_meta:         dict[int, dict]  = {}

    def __init__(self, folder_in: str | pathlib.Path, folder_out: str | pathlib.Path = "DATASETS"):

        self.m_folder_in = folder_in if (( folder_in := pathlib.Path(folder_in) ) and folder_in.is_absolute()) else \
                            pathlib.Path(os.getcwd(), folder_in) 
        self.m_folder_out = folder_out if ( folder_out := pathlib.Path(folder_out) ) and folder_out.is_absolute() else \
                            pathlib.Path(os.getcwd(), folder_out) 

        self.m_meta = self.read_meta(folder=self.m_folder_in)

    def read_meta(
            self,
            folder: pathlib.Path | None = None,
            sub: str = "meta"
    ) -> dict[int, dict]:

        if folder is None:
            folder = self.m_folder_in
        if not folder:
            return {}
        data = self.read(folder=folder, sub=sub)
        meta = {}
        for x in data:
            meta[x["domain"]] = x 
        self.m_meta = meta
        return meta

    def read_data(
            self,
            meta: dict
    ) -> typing.Iterable[typing.Any]:
        
        data_file = meta.get("data_file", None)

        data = self.read(
            file=data_file
        )[0]
        if not data:
            print(f"[ BFIPWDatasetGenerator ][ WARN ] Datafile {data_file} could not be found. Searching for it where Metafile {meta_file} was.")
            meta_file = meta.get("meta_file", None)
            if meta_file is None:
                print(f"[ BFIPWDatasetGenerator ][ ERROR ] Cant find Datafile for Metafile {meta_file}.")
                return []
            data = self.read(
                file=str(meta_file).replace("meta", "data")
            )[0]

        return data

    def read(
            self,
            file: pathlib.Path | None = None,
            folder: pathlib.Path | None = None,
            sub: str = "",
            num: int | None = None
    ) -> typing.Iterable[typing.Any]:

        if file is None and folder is None:
            return []
        
        if file is not None:
            if os.path.exists(file):
                return [ joblib.load(file) ]
            else:
                return []

        data = []
        for file in sorted([os.path.join(x, file ) for x,_,y in os.walk(folder) for file in y if sub in file]):
            print(file)
            data += self.read(file=file)
            data[-1] |= {"meta_file": file}

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

    def create_embedded_keystroke_samples(
            self,
            data,
            meta,
            out_dir:                pathlib.Path | str | None = None,
            states_per_transient:   int | None = None,
            func_on_state:          typing.Callable = lambda x: x[np.random.randint(0, len(x))],
            sample_spacing_random:  bool = True,
            v:                      bool = False
    ) -> dict[int, dict]:

        dataset_meta = {}

        print("META: ", meta.get("meta_file", "NONE"))
        if out_dir is None:
            out_dir = self.m_folder_out

        if isinstance(out_dir, str):
            out_dir = pathlib.Path(out_dir)

        if out_dir.is_absolute() and out_dir.is_relative_to(pathlib.Path(os.getcwd())):
            out_dir = out_dir.relative_to(pathlib.Path(os.getcwd()))

        number_of_chunks = meta.get("number_of_chunks", None)

        if number_of_chunks is None:
            print(f"[ BFIPWDatasetGenerator ][ ERROR ] Need to know how many samples per datapoint where recorded.")
            return dataset_meta

        if states_per_transient is None:
            states_per_transient = meta.get("number_of_chunks", None)

        num_prefix_samples      = meta.get("num_prefix_samples", 0)
        data = data[num_prefix_samples:]


        num_states              = meta.get("max_positions", 10)
        num_samples_per_state   = meta.get("samples_per_state", 1)
        domain                  = meta.get("domain", 0)

        out_dir = pathlib.Path(os.path.join(out_dir, f"ROOM_{str(meta.get("phy_domain", 0))}", str(domain)))


        for target in range(num_states):
            for prefix in range(num_states):
                for suffix in range(num_states):

                    holistic_domain = f"{str(domain)}{str(prefix)}{str(suffix)}"
                    if holistic_domain not in dataset_meta.keys():
                        dataset_meta[holistic_domain] = {}

                    pw = f"{str(prefix)}{str(target)}{str(suffix)}"

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

                    if v: print(prefix, prefix_start, prefix_end)
                    if v: print(target, target_start, target_end)
                    if v: print(suffix, suffix_start, suffix_end)

                    if sample_spacing_random:
                        pt_idx = sorted([np.random.randint(pt_start, pt_end) for _ in range(states_per_transient)], reverse=True if target < prefix else False)
                        ts_idx = sorted([np.random.randint(ts_start, ts_end) for _ in range(states_per_transient)], reverse=True if suffix < target else False)
                    else:
                        pt_idx = [ x for x in range(pt_start, pt_end, (pt_end-pt_start)//states_per_transient+1) ]
                        ts_idx = [ x for x in range(ts_start, ts_end, (ts_end-ts_start)//states_per_transient+1) ]
    
                    if v: print(len(pt_idx), pt_idx)
                    if v: print(len(ts_idx), ts_idx)

                    pt_sample = [ func_on_state(data[i*num_samples_per_state:(i+1)*num_samples_per_state]) for i in pt_idx ]
                    ts_sample = [ func_on_state(data[i*num_samples_per_state:(i+1)*num_samples_per_state]) for i in ts_idx ]

                    sample = np.array( prefix_sample + pt_sample + target_sample + ts_sample + suffix_sample )
                    file_out = os.path.join(out_dir, pw + ".dump")

                    new_meta = {
                                "data_file" : str(file_out),
                                "pw"        : pw,
                                "target"    : target
                            }

                    self.write(sample, file_out)

                    if target not in dataset_meta[holistic_domain].keys():
                        dataset_meta[holistic_domain][target] = [
                            new_meta
                        ]
                    else:
                        dataset_meta[holistic_domain][target].append(new_meta)

        return dataset_meta

    def create_dataset(
            self,
            meta:                   dict[ int, dict ] | None = None,
            out_dir:                pathlib.Path | None = None,
            dataset_meta_file:      str = "meta.dump",
            states_per_transient:   int | None = None,
            func_on_state:          typing.Callable = lambda x: x[np.random.randint(0, len(x))],
            sample_spacing_random:  bool = True,
            v:                      bool = False
    ) -> dict[int, dict]:
        
        if meta is None:
            meta = self.m_meta
        
        if not meta:
            print(f"[ BFIPWDatasetGenerator ][ ERROR ] No meta_info provided.")
            return {}
        if out_dir is None:
            out_dir = self.m_folder_out

        dataset_meta = {
            "meta":{
                "path":                     str(out_dir),
                "sample_spacing_random":    sample_spacing_random,
                "states_per_transient":     states_per_transient,
            }
        }

        for phy_domain in meta.keys():
            data = self.read_data(
                meta=meta[phy_domain]
            )
            print(meta[phy_domain])
            if not data:
                continue
            dataset_meta |= self.create_embedded_keystroke_samples(
                data=data,
                meta=meta[phy_domain],
                out_dir=out_dir,
                states_per_transient=states_per_transient,
                func_on_state=func_on_state,
                sample_spacing_random=sample_spacing_random,
                v=v,
            )
            break
        joblib.dump(dataset_meta, os.path.join(out_dir, dataset_meta_file))