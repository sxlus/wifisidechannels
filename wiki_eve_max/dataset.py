

import joblib, pathlib, os
import numpy as np
import typing
import torch


class BFIDataSet(torch.utils.data.Dataset):

    def __init__(
            self,
            targ_label = None,
            targ_domain = None,
            bfi_file = None,
            time_file = None,
            bfi = None,
            time = None,
            transform=None,
            sample = None
        ):

        if (not (bfi or bfi_file) or not (time or time_file)) and not sample:
            print("Need time and bfi")
            return

        self.bfi_file = bfi_file
        self.time_file = time_file
        if sample:
            print(sample)
            self.targ_label = sample["label"] # np.concatenate([sample[i]["label"] for i in range(len(sample))])
            self.targ_domain = sample["domain"] # np.concatenate([sample[i]["domain"] for i in range(len(sample))])
            self.bfi = sample["data"] # np.concatenate([sample[i]["data"] for i in range(len(sample))])
            #self.time = np.concatenate([sample[i]["time"] for i in range(len(sample))])
            print(len(sample["data"]))
        else:
            if targ_label is None or targ_domain is None:
                print("Need Domain and Label")
                return
            self.bfi = np.squeeze(joblib.load(bfi_file) if bfi_file else bfi)
            #self.time = np.squeeze(joblib.load(time_file) if time_file else time)
            self.targ_label = np.repeat(targ_label, len(self.bfi)) if not isinstance(targ_label, typing.Iterable) else targ_label
            self.targ_domain = np.repeat(targ_domain, len(self.bfi)) if not isinstance(targ_domain, typing.Iterable) else targ_domain

        self.transform = transform

    def __len__(self) -> int:
        return len(self.bfi)

    def __getitem__(self, idx: int) -> dict:

        if not isinstance(idx, int):
            print("Need int idx.")
            return None 
        if torch.is_tensor(idx):
            idx = idx.tolist()

        if isinstance(idx, typing.Iterable):
            VAL = self.transform(self.bfi[idx]) if self.transform is not None else np.array(self.bfi[idx])
        else:
            VAL = self.transform([self.bfi[idx]]) if self.transform is not None else np.array([self.bfi[idx]])

        sample = {
            "data": VAL,
            #"time": self.time[idx], # currently broken
            "label": self.targ_label[idx],
            "domain": self.targ_domain[idx]
            }

        #print(sample["data"].shape)
        return sample

    def __str__(self):
        return f"[ BFIDataSet ]: {str(self.bfi_file)}\n\t" \
            f"* SIZE        : {len(self): >10}\n\t" \
            f"* LABEL       : {self.targ_label}\n\t" \
            f"* DOMAIN      : {self.targ_domain}"
    
    def read(
            self,
            targ_label,
            targ_domain,
            bfi_file,
            time_file
    ):

        new_bfi = np.squeeze(joblib.load(bfi_file))
        new_time = np.squeeze(joblib.load(time_file))
        new_label = np.repeat(targ_label, len(new_bfi))
        new_domain = np.repeat(targ_domain, len(new_bfi))

        self.add(
            targ_domain=new_domain,
            targ_label=new_label,
            bfi=new_bfi,
            time=new_time,
            bfi_file=bfi_file,
            time_file=time_file
        )

    def add(
            self,
            targ_label,
            targ_domain,
            bfi,
            time,
            bfi_file,
            time_file
    ):
        if len(targ_label) > 0 and len(targ_domain) > 0 and len(bfi) > 0 and len(time) > 0 :
            if not isinstance(self.bfi_file, typing.Iterable):
                self.bfi_file = [self.bfi_file]
            #if not isinstance(self.time_file, typing.Iterable):
            #    self.time_file = [self.time_file]
            self.bfi_file += [bfi_file]
            #self.time_file += [time_file]
            self.targ_domain = np.concatenate((self.targ_domain, targ_domain))
            self.targ_label = np.concatenate((self.targ_label, targ_label))
            self.bfi = np.concatenate((self.bfi, bfi))
            #self.time = np.concatenate((self.time, time))

class BFIDomainAdaptDataset(BFIDataSet):

    def __init__(
            self,
            folder = None,
            access: dict = {0: "domain", 1: "label"},
            datasets = None,
            transform = None
    ):

        #assert all([ True if x in ["domain", "label"] else False for x in access.items() ]) 
        if not datasets:
            if not folder:
                print("Need folder!")
                return None
            datasets = []
            kk = 0
            for y, f in enumerate([ pathlib.Path(os.path.join(folder, x)) for x in os.listdir(folder) ]):
                for y0, f0 in enumerate([ pathlib.Path(os.path.join(f, x)) for x in os.listdir(f) ]):
                    data = {}
                    for file, sfile in [ (pathlib.Path(os.path.join(f0, x)), x) for x in os.listdir(f0) if "data" in x]:
                        sfile = sfile.split("data")
                        if sfile[0] not in data.keys():
                            data[sfile[0]] = {}
                        data[sfile[0]]["V" if "V" in sfile[1] else "T"] = file

                    for i, x in enumerate(data.keys()):
                        if i == 0 and kk == 0:
                            super(BFIDomainAdaptDataset, self).__init__(
                                bfi_file=data[x]["V"],
                                time_file=data[x]["T"],
                                targ_label=y if access[0] == "label" else y0,
                                targ_domain=y if access[0] == "domain" else y0,
                                transform=transform
                        )
                        else:
                            self.read(
                                bfi_file=data[x]["V"],
                                time_file=data[x]["T"],
                                targ_label=y if access[0] == "label" else y0,
                                targ_domain=y if access[0] == "domain" else y0
                            )
                    kk += 1

    def split(
            self,
            train_p: float = None,
            test_p: float = None,
            train_domain : int | list[int] = None,
            train_n: int = None,
            test_n: int = None
    ):

        if not isinstance(train_domain, list):
            train_domain = [ train_domain ]

        train_data_pos = np.arange(len(self.bfi))
        test_data_pos  = np.arange(len(self.bfi))

        if train_domain is not None:
            train_data_pos = train_data_pos[[True if self.targ_domain[i] in train_domain else False for i in range(len(self.targ_domain))]]
            test_data_pos  = test_data_pos[[True if self.targ_domain[i] not in train_domain else False for i in range(len(self.targ_domain))]]

        if train_p is not None:
            np.random.shuffle(train_data_pos)
            np.random.shuffle(test_data_pos)
            if len(train_data_pos) == len(test_data_pos) and all([train_data_pos[i] == test_data_pos[i] for i in range(min(len(train_data_pos), len(test_data_pos)))]):
                train_data_pos = train_data_pos[:int(len(self.bfi)*train_p)]
                test_data_pos  = train_data_pos[int(len(self.bfi)*train_p):]
            else:
                if test_p is None:
                    test_p = 1
                train_data_pos = train_data_pos[:int(len(train_data_pos)*train_p)]
                test_data_pos  = test_data_pos[int(len(test_data_pos)*test_p):]

        if train_n is not None and test_n is not None:
            if len(train_data_pos) == len(test_data_pos) and all([train_data_pos[i] == test_data_pos[i] for i in range(min(len(train_data_pos), len(test_data_pos)))]):
                np.random.shuffle(train_data_pos)
                np.random.shuffle(test_data_pos)
                train_data_pos = train_data_pos[:train_n]
                test_data_pos = train_data_pos[train_n:train_n+test_n]
            else:
                train_data_pos = train_data_pos[:train_n]
                test_data_pos = test_data_pos[:test_n]

        print(self[0]["data"])
        #print("FINAL:", self[[0,1]]["data"])
        return BFIDataSet(sample=self[train_data_pos]), BFIDataSet(sample=self[test_data_pos])
    

class BFIKEYSTROKE(torch.utils.data.Dataset):

    m_log_file:     pathlib.Path | None
    m_log:          dict = {}

    m_access:      dict = {
        "domain"    : "domain",
        "class"     : "class",
        "data_file" : "data_file"
    }

    m_transform:    typing.Callable | None

    """
        LOG SHOULD HAVE THE FOLLOWING STRUCTURE:
        {
            "DATA":{
                "DOMAIN": {
                    "SAMPLE": [
                        {
                            "META_FILE": "XXX",
                            "DATA_FILE": "YYY"
                        }
                    ]
                }
            }
        }
    """

    def __init__(
            self,
            log_file :      str | pathlib.Path | None = None,
            log:            dict = None,
            folders:        str | pathlib.Path  | typing.Iterable[str | pathlib.Path] | None = None,
            meta_sub:       str = "meta",
            transform:      typing.Callable | None = None,
            access:         dict | None = None,
            SAVE_LOG:       str = "LOG_EXPERIMENT.dump"
    ):
        if log_file is None and log is None and folders is None:
            print(f"[ BFIKEYSTROKE ][ ERROR ] Nedd either folders or log or log_file.")
            return None

        self.m_transform = transform

        if isinstance(log, dict):
            self.m_log = log
            return
        
        if isinstance(log_file, str) or isinstance(log_file, pathlib.Path):
            new = joblib.load(log_file)
            if isinstance(new, dict):
                self.m_log = new
            else:
                print(f"[ BFIKEYSTROKE ][ ERROR ]Logfile content is no dict.")
            return
         
        if folders is not None:
            if not isinstance(folders, typing.Iterable):
                folders = [ folders ]
            for folder in folders:
                self.m_log  = self.build_log(
                    folder  = folder,
                    log     = self.m_log,
                    sub     = meta_sub,
                    access  = access if isinstance(access, dict) else self.m_access 
                )
                
            joblib.dump(self.m_log, SAVE_LOG)
        

    def __len__(self) -> int:
        return len(self.bfi)

    def __getitem__(self, idx: int) -> dict:

        #if not isinstance(idx, int):
        #    print("Need int idx.")
        #    return None 
        #if torch.is_tensor(idx):
        #    idx = idx.tolist()
#
        #if isinstance(idx, typing.Iterable):
        #    VAL = self.transform(self.bfi[idx]) if self.transform is not None else np.array(self.bfi[idx])
        #else:
        #    VAL = self.transform([self.bfi[idx]]) if self.transform is not None else np.array([self.bfi[idx]])
#
        #sample = {
        #    "data": VAL,
        #    #"time": self.time[idx], # currently broken
        #    "label": self.targ_label[idx],
        #    "domain": self.targ_domain[idx]
        #    }
#
        #print(sample["data"].shape)
        return# sample

    def __str__(self):
        return f"[ BFIDataSet ]: {str(self.bfi_file)}\n\t" \
            f"* SIZE        : {len(self): >10}\n\t" \
            f"* LABEL       : {self.targ_label}\n\t" \
            f"* DOMAIN      : {self.targ_domain}"

    def build_log(
            self,
            folder = pathlib.Path | str,
            log: dict | None = None,
            sub: str = "meta",
            access: dict | None = None
            ):

        if access is None:
            access = self.m_access
        if log is None:
            log = { }
        if log.get("DATA", None) is None:
            log["DATA"] = {}
        for meta_file in sorted([ os.path.join(folder, x) for x in os.listdir(folder) if sub in x] if sub is not None else os.listdir(folder)):
            #print(meta_file)
            meta = self.read(file=meta_file)[0]
            #print(meta)
            if (domain:= meta.get(access["domain"], None)) is None:
                continue

            if (target:= meta.get(access["class"], None)) is None:
                continue
            target = int(str(target[1]), 10)
            if (data_file:= meta.get(access["data_file"], None)) is None:
                continue
    
            if log["DATA"].get(domain, None) is None:
                log["DATA"][domain] = {}
            
            if log["DATA"][domain].get(target, None) is None:
                log["DATA"][domain][target] = []

            log["DATA"][domain][target].append({
                "meta_file": str(meta_file),
                "data_file": str(data_file)
            })
        return log

    def read(
            self,
            file: pathlib.Path | None = None,
            folder: pathlib.Path | None = None,
            sub: str | None = None,
            num: int | None = None
    ) -> dict[int, typing.Any]:

        if file is None and folder is None:
            return None
        
        if file is not None:
            return { 0: joblib.load(file) }


        data = {}
        for i, file in enumerate(sorted([ x for x in os.listdir(folder) if sub in str(x)] if sub is not None else os.listdir(folder))):
            if i == num:
                break
            data[i] = joblib.load(file)

        return data