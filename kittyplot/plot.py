import matplotlib.pyplot as plt
from math import ceil, sqrt
from state import State
import array, fcntl, termios # for get_terminal_size

def get_terminal_size():
    buf = array.array('H', [0, 0, 0, 0])
    fcntl.ioctl(1, termios.TIOCGWINSZ, buf)
    return buf[2], buf[3]

def apply_settings_before_plot(cfg):
    # run mpl commands before plotting
    with open(cfg.mpl_settings) as f:
        for line in f:
            line = line.strip().split()
            if line[0] == "style":
                if line[1] == "dark":
                    plt.style.use(["dark_background", "fast"])
                else:
                    plt.style.use(["classic", "fast"])

def apply_settings_to_ax(cfg, ax):
    with open(cfg.mpl_settings) as f:
        for line in f:
            line = line.strip().split()
            if len(line) not in (1, 2, 3):
                continue
            
            if line[0] == "ylog":
                ax.set_yscale('log')
            if line[0] == "xmin":
                ax.set_xlim(max(ax.get_xlim()[0],float(line[1])))
            elif line[0] == "ymin":
                ax.set_ylim(max(ax.get_ylim()[0],float(line[1])))
            elif line[0] == "xmax":
                ax.set_xlim(None, min(ax.get_xlim()[1],float(line[1])))
            elif line[0] == "ymax":
                ax.set_ylim(None, min(ax.get_ylim()[1],float(line[1])))
            elif line[0] == "legend":
                ax.legend(loc=" ".join(line[1:])) 

def plot(ax, metrics: dict, metric: str, label: str):
    if metric not in metrics.keys():
        return
    ax.plot(metrics[metric], label=label, linewidth=4)

    # Skip processing plot statistics if there are none
    if not metric.endswith("_mean"):
        ax.set_title(metric)
        return
    ax.set_title(metric[:-5])
    # plot shaded area between min and max of metric
    min_met = metric[:-5]+"_min"
    max_met = metric[:-5]+"_max"
    std_met = metric[:-5]+"_std"
    ax.fill_between(list(range(len(metrics[metric]))),
                    metrics[min_met],
                    metrics[max_met],alpha=0.2)
    if std_met not in metrics.keys():
        return
    # plot std if exists
    xs = list(range(len(metrics[metric])))
    std_mins = [max(_min, mean-sqrt(std)) for _min, mean, std in 
            zip(metrics[min_met], metrics[metric], metrics[std_met])]
    std_maxes = [min(_max, mean+sqrt(std)) for _max, mean, std in 
            zip(metrics[max_met], metrics[metric], metrics[std_met])]
    ax.fill_between(xs, std_mins, std_maxes, alpha=0.2) 

def compute_num_rows_and_cols(num_metrics: int):
    """Determines the size of the graph grid"""
    if num_metrics % 2 == 0 and num_metrics % 6 != 0:
        num_cols = 2
    else:
        num_cols = min(num_metrics, 3)
    num_rows = ceil(num_metrics / num_cols)
    return num_rows, num_cols

def get_ax(axes, i, num_rows, num_cols):
    """Gets axis i from matrix of axes"""
    r, c = i // num_cols, i % num_cols
    ax = 0
    # matplotlib doesn't make 2d grid a dimension is len 1
    if num_cols==1:
        ax = axes
    elif num_rows==1:
        ax = axes[c]
    else:
        ax = axes[r,c]
    return ax


# Image generation
def make_grid(cfg, s: State, unfiltered_metrics: list):
    if len(unfiltered_metrics) == 0:
        print("no metrics")
        return None
    unfiltered_metrics.sort()
    metrics = [m for m in unfiltered_metrics if not m.endswith("_min") and not m.endswith("_max") and not m.endswith("_std")]
    
    num_rows, num_cols = compute_num_rows_and_cols(len(metrics))
    # users can change visible runs by commenting or deleting lines in runlist
    with open(cfg.runlist) as f:
        runs_to_plot = [r.strip() for r in f.readlines() if not r.startswith("#")]

    apply_settings_before_plot(cfg)

    size = get_terminal_size()
    xsize = (size[0]*cfg.px) - 1
    ysize = (size[1]*cfg.px) - 1 if num_rows <= 2 else ((num_rows * size[1]*cfg.px)/2) - 1
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(xsize, ysize))
    for i, metric in enumerate(metrics):
        ax = get_ax(axes, i, num_rows, num_cols)

        for run in runs_to_plot:
            label = None if len(s.runs) < 2 else run
            plot(ax, s.runs[run], metric, label)
            
        if len(s.runs) > 1:
            ax.legend(loc="upper left")

        apply_settings_to_ax(cfg, ax)
    return 1
