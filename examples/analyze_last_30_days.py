import os
import shutil

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

from ratpmetro import RATPMetroTweetsAnalyzer

api = {}
api["consumer_key"] = "63OrjYzZFY1nTkJD3pTCVdoIt"
api["consumer_secret"] = "UzCqxKEnbtpLJJzOURfUOdBeY3RUP2SIBWBItm60PIjlA14YZ0"
api["access_key"] = "59343714-QSsu8Uqc7ind3qwPTCAHJinjH0shaIRh4qL2O0bQ5"
api["access_secret"] = "h2ZkZ8PDsG6W5ktAWJrlg6y2UgOYoBXzAE9bsnAXq236G"

outdir = os.path.join(os.path.dirname(__file__), "..", "docs", "_static")
os.makedirs(outdir, exist_ok=True)

# Download and process tweets
lines = np.arange(1, 16, dtype=int)  # line 15 == RER A
ratp_line = {}
force_download = True
folder_tweets = os.path.join(os.path.dirname(__file__), "temp")
for line in lines:
    ratp_line[line] = RATPMetroTweetsAnalyzer(api=api)
    if int(line) != 15:
        ratp_line[line].load(
            line=int(line),
            number_of_tweets=500,
            force_download=force_download,
            folder_tweets=folder_tweets,
        )
    else:
        ratp_line[line].load(
            line="A",
            number_of_tweets=3200,  # they tweet a lot (responding to angry passengers)
            force_download=force_download,
            folder_tweets=folder_tweets,
        )
    ratp_line[line].process()

# Compare 15 lines
incident_prob = np.zeros(len(lines))
today = pd.Timestamp.today(tz="Europe/Paris")
loc = (today - pd.Timedelta(days=30), today)
color = [None] * len(lines)
for i, line in enumerate(lines):
    incident_prob[i] = ratp_line[line].incident_prob(loc=loc)
    color[i] = ratp_line[line].color

idx = np.argsort(incident_prob)[::-1]  # descending order
x = lines[idx]
y = incident_prob[idx]
color = np.array(color)[idx]
plt.bar(lines, y, width=0.6, color=color)

mean = incident_prob.mean()
plt.plot(
    (lines.min(), lines.max()), (mean, mean), "k-", linewidth=3, alpha=0.2, label="mean"
)
x = [str(x_) for x_ in x]
x[x == "15"] = "A"
plt.xticks(lines, x)
plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.1%}"))
plt.xlabel("RATP line #")
plt.ylabel("probability of incidents")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(outdir, "ranking.png"), dpi=150)

# Plot incident probability by hour-weekday for the last 30 days
plt.figure(figsize=(18, 20))
for line in lines:
    plt.subplot(5, 3, line)
    ratp_line[line].plot_incident_prob(by="hour-weekday", loc=loc)
    if line != 15:
        line = str(line)
    else:
        line = "A"
    plt.title(plt.gca().get_title() + f" for line {line}")

plt.tight_layout()
plt.savefig(os.path.join(outdir, "hour-weekday.png"), dpi=150)

shutil.rmtree(folder_tweets)
