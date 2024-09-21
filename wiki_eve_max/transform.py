import torch
import numpy as np

class MeanSubtract(object):
    def __init__(self):
        pass
    def __call__(self, sample):
        pass

class BFIRatio(object):
    def __init__(self):
        pass
    def __call__(self, sample):
        pass

class Absolute(object):
    def __init__(self):
        pass
    def __call__(self, sample):
        #print("ABSOLUTE: ", sample.shape if not isinstance(sample, list) else len(sample))
        return torch.Tensor(np.array([[ np.abs(s[i]) for i in range(len(s))] for s in sample]))
        #return torch.Tensor(np.array([[np.abs(s[i][j])for i in range(len(s)) for j in range(len(s[i])) ] for s in sample ] )) 