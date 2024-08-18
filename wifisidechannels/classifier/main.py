import argparse
import torch
import torchvision
import gradient_reversal
# Get cpu, gpu or mps device for training.
device = (
    "cuda"
    if torch.cuda.is_available()
    else "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)
if __name__ == '__main__':
    