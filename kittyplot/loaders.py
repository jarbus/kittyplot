import re
import sys
import asyncio
import numpy as np
import pandas as pd
import os.path as osp
import logging as log
from collections import defaultdict
from abc import ABC, abstractmethod
from .state import *

class AbstractLoader(ABC):
    @abstractmethod
    def getfile(self, filename):
        pass
    
    @abstractmethod
    def read(self, file):
        pass
    
    @abstractmethod
    def load(self, data):
        pass

class CSVLoader(AbstractLoader):
    def getfile(self, filename):
        metrics_file = osp.join(osp.join("", filename),"metrics.csv")
        results_file = osp.join(osp.join("", filename),"results.txt")
        if osp.exists(metrics_file):
            return metrics_file
        elif osp.exists(results_file): 
            return results_file
        else:
            return False

    async def read(self, file):
        return pd.read_csv(file, dtype=np.float16)

    def load(self, filename: str, futures, labels, runlist: str):
        try:
            label = osp.basename(osp.dirname(filename))
            futures.append(self.read(filename))
            labels.append(label)

            # bug: all runs will appear after reload
            with open(runlist, "a") as f:
                f.write(f"{label}\n")
        except:
            raise OSError(f"Could not read {filename}")


class LogLoader(AbstractLoader):
    """Loads log files into a dict of metrics, matches fp values indicated by |val| and by |min, mean ± std, max|"""
    float_re = r"([-+]?[0-9]*\.?[0-9]+)"
    mmms_re = re.compile(f".* (.+): \|{float_re}, {float_re} ± {float_re}, {float_re}\|")
    single_re = re.compile(f".* (.+): \|{float_re}\|")
    STATS = "_min _mean _std _max".split()

    def match(self, regex, line):
        m = re.match(regex, line)
        if m and all(m.groups()):
            return m
        return False

    def add_metric(self, metrics: defaultdict, line):
        """collects all metrics in line and adds them
        to metrics dict"""
        if m := self.match(self.mmms_re, line):
            met, *vals = m.groups()
            assert len(vals) == len(self.STATS)
            for s, v  in zip(self.STATS, vals):
                metrics[met+s].append(float(v))
        elif m := self.match(self.single_re, line):
            met, vals = m.groups()
            metrics[met].append(float(vals))

    async def read(self, file: str):
        """Reads log data into metrics"""
        metrics = defaultdict(list)
        with open(file) as f:
            for line in f:
                self.add_metric(metrics, line)
        return metrics

    def load(self, filename, futures, labels, runlist):
        """creates an async req to read log data
        and adds the log name to the list of labels"""
        label = osp.basename(filename)
        if label.endswith(".log"):
            label = label[:-4]
        futures.append(self.read(filename))
        labels.append(label)

        with open(runlist, "a") as f:
            f.write(f"{label}\n")

    def getfile(self, filename: str):
        """returns filename if a valid logfile, else False"""
        if not filename.endswith(".log"):
            return False
        metrics_file = filename
        if osp.exists(metrics_file):
            return metrics_file


async def load(runlist: str):
    log.debug("loading data")
    global runs, keys, matches
    with open(runlist, "w") as f:
        f.write("")
    runs = {}
    keys = None
    labels, futures = [], []
    read_file = False
    loaders = [CSVLoader(), LogLoader()]
    for arg in sys.argv[1:]:
        for loader in loaders:
            if filename := loader.getfile(arg):
                read_file = True
                loader.load(filename, futures, labels, runlist)
    if not read_file:
        print(f"ERROR: could not read {sys.argv[1:]}")
    run_data = await asyncio.gather(*futures)
    assert len(labels) == len(run_data)
    runs = dict(zip(labels, run_data))
    keys = list(set().union(*[v.keys() for v in runs.values()]))
    state = State(runs, keys)
    return state
