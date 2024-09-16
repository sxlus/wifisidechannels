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
        return torch.Tensor([ np.abs(sample[i][j]) for i in range(len(sample)) for j in range(len(sample[i])) ])