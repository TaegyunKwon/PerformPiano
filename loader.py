from __future__ import division
from torch.utils.data import Dataset
from torchvision import datasets
from torchvision import transforms


def denorm(x):
    out = (x + 1) / 2
    return out.clamp(0, 1)

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))])

'''
def dataset(set_name):
    if set_name == 'mnist':
        set = datasets.
    else:
        raise Exception(set_name +': unknown dataset. choose between mnist / f-mnist')

    return set
'''