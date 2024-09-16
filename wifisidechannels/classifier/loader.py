from datasets import BFIDataSet
import pathlib, os
import numpy as np

class BFIDataSetFolder(BFIDataSet):
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
                            super(BFIDataSetFolder, self).__init__(
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

        #print(self[0]["data"])
        print("FINAL:", self[[0,1]]["data"])
        return BFIDataSet(sample=self[train_data_pos]), BFIDataSet(sample=self[test_data_pos])