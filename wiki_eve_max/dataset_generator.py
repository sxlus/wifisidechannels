import pathlib
import typing
import joblib
import os
import numpy as np

class BFIPWDatasetGenerator():

    m_folder_in:    pathlib.Path
    m_folder_out:   pathlib.Path
    m_meta:         dict[int, dict]  = {}

    def __init__(self, folder_in: str | pathlib.Path | typing.Iterable, folder_out: str | pathlib.Path = "DATASETS", foldersub: str = "", metasub: str = "meta"):

        self.m_folder_in = folder_in if (( folder_in := pathlib.Path(folder_in) ) and folder_in.is_absolute()) else \
                            pathlib.Path(os.getcwd(), folder_in) 
        self.m_folder_out = folder_out if ( folder_out := pathlib.Path(folder_out) ) and folder_out.is_absolute() else \
                            pathlib.Path(os.getcwd(), folder_out) 

        self.m_meta = self.read_meta(folder=self.m_folder_in, sub=metasub, fub=foldersub)

    def read_meta(
            self,
            folder: pathlib.Path | None = None,
            sub: str = "meta",
            fub: str = "",
    ) -> dict[int, dict]:

        if folder is None:
            folder = self.m_folder_in
        if not folder:
            return {}
        data = self.read(folder=folder, sub=sub, fub=fub)
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
        )
        if not data:
            print(f"[ BFIPWDatasetGenerator ][ WARN ] Datafile {data_file} could not be found. Searching for it where Metafile was.")
            meta_file = meta.get("meta_file", None)
            if meta_file is None:
                print(f"[ BFIPWDatasetGenerator ][ ERROR ] Cant find Datafile for Metafile {meta_file}.")
                return []
            data = self.read(
                file=str(meta_file).replace("meta", "data")
            )

        if data:
            return data[0]
        else:
            return []

    def read(
            self,
            file: pathlib.Path | None = None,
            folder: pathlib.Path | None = None,
            sub: str = "",
            fub: str = "",
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
        for file in sorted([os.path.join(x, file) for x,_,y in os.walk(folder) if fub in str(x) for file in y if sub in file]):
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
            meta,
            data=None,
            out_dir:                pathlib.Path | str | None = None,
            states_per_transient:   int | None = None,
            func_on_state:          typing.Callable = lambda x: x[np.random.randint(0, len(x))],
            sample_spacing_random:  bool = True,
            v:                      bool = False,
            vv:                     bool = False
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


        num_states              = meta.get("max_positions", 10)
        num_samples_per_state   = meta.get("samples_per_state", 1)
        train_domain            = meta.get("train_domain", 0)
        room_domain             = meta.get("phy_domain", 0)
        out_dir = pathlib.Path(os.path.join(out_dir, f"ROOM_{room_domain}", str(room_domain)+str(train_domain)))
        phy_domain              = str(room_domain)+str(train_domain)

        for target in range(num_states):
            for prefix in range(num_states):
                for suffix in range(num_states):

                    holistic_domain = f"{str(phy_domain)}{str(prefix)}{str(suffix)}"
                    if holistic_domain not in dataset_meta.keys():
                        dataset_meta[holistic_domain] = {}

                    pw = f"{str(prefix)}{str(target)}{str(suffix)}"
                    file_out = os.path.join(out_dir, pw + ".dump")
                    new_meta = {
                                "data_file" : str(file_out),
                                "pw"        : pw,
                                "target"    : target
                            }

                    if target not in dataset_meta[holistic_domain].keys():
                        dataset_meta[holistic_domain][target] = [
                            new_meta
                        ]
                    else:
                        dataset_meta[holistic_domain][target].append(new_meta)

                    if os.path.exists(file_out):
                        continue

                    if data is None:
                        if meta is None:
                            print(f"Need either data or data_file.")
                            return {}
                        data = self.read_data(
                            meta=meta
                        )
                        if not data:
                            return {}
                        data = data[num_prefix_samples:]


                    prefix_start    = (prefix*number_of_chunks)
                    prefix_end      = prefix_start

                    target_start    = (target*number_of_chunks)
                    target_end      = target_start

                    suffix_start    = (suffix*number_of_chunks)
                    suffix_end      = suffix_start

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

                    prefix_sample  = [ func_on_state(data[prefix_start*num_samples_per_state:(prefix_end + 1)*num_samples_per_state]) ]
                    target_sample  = [ func_on_state(data[target_start*num_samples_per_state:(target_end + 1)*num_samples_per_state]) ]
                    suffix_sample  = [ func_on_state(data[suffix_start*num_samples_per_state:(suffix_end + 1)*num_samples_per_state]) ]

                    if vv: print(pw)
                    if v: print("prefix", prefix, prefix_start, prefix_end)
                    if v: print("target", target, target_start, target_end)
                    if v: print("suffix", suffix, suffix_start, suffix_end)

                    if sample_spacing_random:
                        pt_idx = sorted([np.random.randint(pt_start, pt_end+1) for _ in range(states_per_transient)], reverse=True if target < prefix else False)
                        ts_idx = sorted([np.random.randint(ts_start, ts_end+1) for _ in range(states_per_transient)], reverse=True if suffix < target else False)
                    else:
                        pt_idx = []
                        pt_delta = (pt_end - pt_start)
                        d = pt_delta / states_per_transient
                        sum_d = d
                        for _ in range(states_per_transient):
                            pt_idx.append(pt_start + round(sum_d))
                            sum_d += d
                        if prefix > target:
                            pt_idx = sorted(pt_idx, reverse=True)
                        ts_idx = []
                        ts_delta = (ts_end - ts_start)
                        d = ts_delta / states_per_transient
                        sum_d = d
                        for _ in range(states_per_transient):
                            ts_idx.append(ts_start + round(sum_d))
                            sum_d += d
                        if target > suffix:
                            ts_idx = sorted(ts_idx, reverse=True)

                    if vv: print(len(pt_idx), pt_idx)
                    if vv: print(len(ts_idx), ts_idx)

                    pt_sample = [ func_on_state(data[i*num_samples_per_state:(i+1)*num_samples_per_state]) for i in pt_idx ]
                    ts_sample = [ func_on_state(data[i*num_samples_per_state:(i+1)*num_samples_per_state]) for i in ts_idx ]

                    if vv: print(len(pt_sample), pt_sample)
                    if vv: print(len(ts_sample), ts_sample)

                    sample = np.array( prefix_sample + pt_sample + target_sample + ts_sample + suffix_sample )


                    self.write(sample, file_out)


        return dataset_meta

    def create_dataset(
            self,
            meta:                   dict[ int, dict ] | None = None,
            out_dir:                pathlib.Path | None = None,
            dataset_meta_file:      str = "meta.dump",
            states_per_transient:   int | None = None,
            func_on_state:          typing.Callable = lambda x: x[np.random.randint(0, len(x))],
            sample_spacing_random:  bool = True,
            v:                      bool = False,
            vv:                     bool = False
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
            print(meta[phy_domain])

            dataset_meta |= self.create_embedded_keystroke_samples(
                meta=meta[phy_domain],
                out_dir=out_dir,
                states_per_transient=states_per_transient,
                func_on_state=func_on_state,
                sample_spacing_random=sample_spacing_random,
                v=v,
                vv=vv
            )
        joblib.dump(dataset_meta, os.path.join(out_dir, ("meta" if not "meta" in str(dataset_meta_file) else "") + str(dataset_meta_file)))