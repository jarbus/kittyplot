import matplotlib.pyplot as plt
class Config:
    def __init__(self):
        self.mpl_settings = "/tmp/kp-mpl.txt"
        self.plot_name="/tmp/kp-name.txt"
        self.runlist = "/tmp/runlist.txt"
        self.plot_file = "/tmp/kp.png"
        with open(self.mpl_settings, "w") as f:
            f.write("")
        self.px = 1/plt.rcParams['figure.dpi']  # pixel in inches
