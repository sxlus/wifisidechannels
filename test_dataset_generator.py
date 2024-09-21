import numpy as np
from wifisidechannels.models.export_models import Packet
from wiki_eve_max.dataset_generator import BFIPWDatasetGenerator
import os 
import pathlib

def random_sample(x):
    idx = np.random.randint(0, len(x))
    return x[idx]

def mean_sample_packet(x):
    data = [ y.DATA["V"] for y in x ]
    return Packet(DATA={"V":np.mean(data, axis=0)})

def mean_sample_np(x):
    data = [ y.DATA["V"] for y in x ]
    return np.mean(data, axis=0)

CWD = os.getcwd()
DSD = pathlib.Path(os.path.join(CWD, "EXPERIMENT"))

X = BFIPWDatasetGenerator(
    folder_in=DSD,
    folder_out="DATASET_TEST"
)

N_SAMPLES       = 32
RANDOM_SPACING  = False
RANDOM_S        = False
PACKET          = False

SPACING = "random_spacing" if RANDOM_SPACING else "even_spacing"
SELECT  = "random_select" if RANDOM_S else "mean"
FUNC    = random_sample if RANDOM_S else mean_sample_packet if PACKET else mean_sample_np
FORMAT  = "PACKET" if PACKET else "NP"

X.create_dataset(
    out_dir=pathlib.Path(os.path.join("DATASETS_TEST", FORMAT, SPACING, SELECT, str(N_SAMPLES))),
    func_on_state=FUNC,
    states_per_transient=N_SAMPLES,
    sample_spacing_random=RANDOM_SPACING,
    v=False,
    vv=False
)