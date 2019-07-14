import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from pandas.plotting import register_matplotlib_converters

register_matplotlib_converters()

params = {
    "axes.titlesize": 14,
    "axes.labelsize": 14,
    "font.size": 14,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "legend.fontsize": 14,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.01,
}
plt.rcParams.update(params)


class RATPMetroTweetsAnalyzer:
    """
    Class for analyzing Paris RATP metro line incidents, using their
    official Twitter accounts

    To be able to download tweets you need to obtain your Twitter developer API keys (`consumer_key`, `consumer_secret`, `access_key` and `access_secret`). Be aware that it may be not possible to download all 14 lines on a row: there is some usage limitation of the Twitter API.

    Args:
        api (dict): Dictionary containing Twitter developer API keys: ``consumer_key``, ``consumer_secret``, ``access_key``, ``access_secret``
    """

    def __init__(self, api=None):
        self.df = None
        self.df_processed = None
        self._define_incidents()

        if api is not None:
            assert type(api) == dict
            keys = ["consumer_key", "consumer_secret", "access_key", "access_secret"]
            for key in keys:
                assert key in api
                assert type(api[key]) == str
            self.api = api

    def load(
        self, line, number_of_tweets=3200, folder_tweets="tweets", force_download=False
    ):
        """
        Download the tweets from the official RATP Twitter account.

        Some code is adapted from https://github.com/gitlaura/get_tweets

        Args:
            line (int or str): RATP metro line number (1 to 14), or ``"A"``, ``"B"`` for RER lines
            number_of_tweets (int): Number of tweets to download, must be smaller than 3200 due to some limitation of the Twitter API
            folder_tweets (str): Folder to store the downloaded tweets as a ``.csv`` file
            force_download (bool): If ``False``, it will directly load the already downloaded file without re-downloading it. You can force downloading by using ``force_download = True``
        """
        import os

        username = self._twitter_account(line)
        outfile = os.path.join(folder_tweets, username + ".csv")
        if not os.path.isfile(outfile) or force_download:
            os.makedirs(os.path.dirname(outfile), exist_ok=True)
            import csv
            import tweepy

            auth = tweepy.OAuthHandler(self.api["consumer_key"], self.api["consumer_secret"])
            auth.set_access_token(self.api["access_key"], self.api["access_secret"])
            api = tweepy.API(auth, wait_on_rate_limit=True)

            tweets_for_csv = [["time", "tweet"]]
            print(f"Downloading tweets for {username}")
            for tweet in tweepy.Cursor(api.user_timeline, screen_name=username).items(
                number_of_tweets
            ):
                tweets_for_csv.append([tweet.created_at, tweet.text])

            with open(outfile, "w", newline="") as f:
                writer = csv.writer(f, delimiter=",")
                writer.writerows(tweets_for_csv)

        self.df = pd.read_csv(outfile)
        self.line = line
        self.color = self._color_line(line)

    def process(self):
        """
        Process the downloaded raw data frame (using Paris time zone, identifying incidents, resampling...)
        """
        assert self.df is not None

        # Convert to Paris time
        self.df["time"] = pd.DatetimeIndex(pd.to_datetime(self.df["time"]))
        self.df = self.df.set_index("time")
        self.df = self.df.tz_localize("UTC")
        self.df = self.df.tz_convert("Europe/Paris")
        self.df = self.df.sort_index()

        # Detect incidents from tweets
        self.df[["is_incident", "incident_cause"]] = self.df["tweet"].apply(
            self._detect_incident
        )

        # Uniformly resample timestamps every hour and extract time information
        self.df_processed = self.df.drop(["tweet"], axis=1)
        self.df_processed = self.df_processed.resample("30min").agg(
            {"is_incident": np.any, "incident_cause": self._agg_incident_cause}
        )
        for x in ["year", "month", "day", "weekday", "hour"]:
            self.df_processed[x] = eval(f"self.df_processed.index.{x}")

    def incident_prob(self, year=None, loc=None):
        """
        Return the mean probability of incidents

        Args:
            year (int): If ``year`` is given then only tweets within this specific year are used, else then all downloaded tweets are used
            loc (list of str): Time period from ``loc[0]`` to ``loc[1]``
        """
        df = self._df_processed_loc(year=year, loc=loc)
        return df["is_incident"].mean()

    def plot_incident_cause(self, year=None, loc=None):
        """
        Plot frequencies of the main cause of incidents

        Args:
            year (int): If ``year`` is given then only tweets within this specific year are used, else then all downloaded tweets are used
            loc (list of str): Time period from ``loc[0]`` to ``loc[1]``
        """
        df = self._df_processed_loc(year=year, loc=loc)
        incident_cause = df["incident_cause"].value_counts().drop(["N/A"])
        incident_cause.plot(kind="pie", autopct="%.0f%%")
        plt.ylabel("")
        return incident_cause.index, incident_cause.values

    def plot_incident_prob(self, by="hour", year=None, loc=None, **kwargs):
        """
        Plot (marginal) probability of operational incidents

        Args:
            by (str): Can be "year", "month", "day", "weekday", "hour", or any two of them connected by a "-", like "hour-weekday"
            year (int): If ``year`` is given then only tweets within this specific year are used, else then all downloaded tweets are used
            loc (list of str): Time period from ``loc[0]`` to ``loc[1]``
        """
        if "year" in by:
            year = None
        df = self._df_processed_loc(year=year, loc=loc)

        # Extract "by" for 2d plots
        if "-" in by:
            by_x, by_y = by.split("-")
            assert by_x in df
            assert by_y in df
        else:
            assert by in df

        weekday_label = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        # 2d plot
        if "-" in by:
            df = df.groupby([by_x, by_y]).mean()["is_incident"]
            x, y = df.index.levels  # already sorted
            x1 = list(x) + [2 * x[-1] - x[-2]]
            y1 = list(y) + [2 * y[-1] - y[-2]]
            xx, yy = np.meshgrid(x1, y1, indexing="ij")
            c = np.zeros((len(x), len(y)))
            for i in range(len(x)):
                for j in range(len(y)):
                    index = xx[i, j], yy[i, j]
                    if index in df:
                        c[i, j] = df[index]
                    else:  # data not available
                        c[i, j] = np.nan
            plt.pcolormesh(xx, yy, c, cmap="Reds", **kwargs)

            # Center year, month, day, weekday to the ticks center
            for by, label, set_ticks in zip(
                [by_x, by_y], [x, y], [plt.xticks, plt.yticks]
            ):
                ticks = np.linspace(label[0] + 0.5, label[-1] + 0.5, len(label))
                if by == "year":
                    pass
                elif by == "month":
                    ticks = ticks[::2]
                    label = label[::2]
                elif by == "day":
                    ticks = ticks[::5]
                    label = label[::5]
                elif by == "weekday":
                    label = weekday_label
                else:  # "hour":
                    continue
                set_ticks(ticks, label)

            plt.xlabel(by_x)
            plt.ylabel(by_y)
            plt.colorbar(format=FuncFormatter(lambda y, _: "{:.1%}".format(y)))
            plt.title("probability of incidents")
            return xx, yy, c

        # 1d plot
        else:
            df = df.groupby(by).mean()["is_incident"]
            y = df.values
            if by == "weekday":
                x = weekday_label
            else:
                x = df.index

            plt.plot(x, y, "-o", color=self.color, **kwargs)
            plt.gca().yaxis.set_major_formatter(
                FuncFormatter(lambda x, _: "{:.1%}".format(x))
            )
            plt.xlabel(by)
            plt.ylabel("probability of incidents")
            plt.grid()
            return x, y

    def _twitter_account(self, line):
        """
        Return the official RATP twitter account
        """
        # Metro
        try:
            line_int = int(line)
            assert 1 <= line_int <= 14
            return f"Ligne{line_int:d}_RATP"
        except ValueError:
            # RER A or B
            if line == "A":
                return "RER_A"
            elif line == "B":
                return "RER_B"
            else:
                print('line must be a number between 1 and 14, "A", or "B".')
                return None

    def _classify_incident_cause(self, tweet):
        """
        Classify the cause of operational incident
        """
        tweet = tweet.lower().strip()
        for main_cause, keywords in self.incident_causes.items():
            for keyword in keywords:
                if keyword in tweet:
                    return main_cause
        else:
            return self.incident_cause_other

    def _agg_incident_cause(self, cause):
        """
        Given a list of causes found by self._classify_incident_cause,
        return the most common cause (useful when resampling)
        """
        cause = list(filter(("N/A").__ne__, cause))  # remove N/A
        if len(cause) > 0:
            return max(set(cause), key=cause.count)
        else:
            return "N/A"

    def _df_processed_loc(self, year=None, loc=None):
        """
        Return self.df_processed within the given year or time period
        """
        assert self.df is not None
        if self.df_processed is None:
            self.process()

        # Focus on a specific year or time period
        if year is not None:
            df = self.df_processed.loc[f"{year}-01-01":f"{year}-12-31"]
        elif loc is not None:
            df = self.df_processed.loc[loc[0]:loc[1]]
        else:
            df = self.df_processed
        return df

    def _detect_incident(self, tweet):
        """
        Read a tweet message from the RATP official accounts and detect if it announces
        some operational incidents

        Returns:
            bool: Whether the tweet corresponds to an incident
            str: Cause of the incident if applicable, otherwise returns ``N/A``
        """
        if tweet.startswith("RT"):
            return pd.Series(
                [False, "N/A"]
            )  # no incident identified, cause not available
        tweet = tweet.lower()

        for word in self.incident_words:
            negative_word = "n'est pas " +  word
            if word in tweet and negative_word not in tweet:
                cause = self._classify_incident_cause(tweet)
                return pd.Series([True, cause])
        else:
            return pd.Series([False, "N/A"])

    def _define_incidents(self):
        """
        Define some keywords for identifying incidents from RATP tweets
        """
        # Keywords for operational incidents
        self.incident_words = ["perturbé", "interrompu", "ralenti"]

        # Incident causes and their keywords
        # Question: incident voie  -> autre ?
        #           diver incident -> autre ?
        # Some tweets are incomplete (thank you Twitter), like this one
        # > 07:56, le trafic est interrompu entre Chaussee d'Antin (La Fayette)
        # > et Trocadero. Reprise estimée à 09:00. (Personn… https://t.co/ZPsJrIlZBG
        # since the cause is not complete (even though it should be "voyageur",
        # it can only be classified as "autre"
        self.incident_causes = {
            "colis": ["colis", "bagage"],
            "technique": [
                "technique",
                "panne",
                "exploitation",
                "fumée",
                "rail",
                "aiguillage",
                "matériel",
            ],
            "voyageur": [
                "voyageur",
                "personne",
                "malveillance",
                "signal d'alarme",
                "affluence",
            ],
            # "chantier": ["chantier"],  # "fin tartive de chantier", in general not so much so -> autre
            "manifestation": [
                "mesure de sécurité"
            ],  # better name for this (in case of terrorist attacks also)?
        }
        self.incident_cause_other = "autre"

    def _color_line(self, line):
        """
        Return the color to be used for the metro line when plotting

        Source: https://data.ratp.fr/explore/dataset/pictogrammes-des-lignes-de-metro-rer-tramway-bus-et-noctilien/information
        """
        color_line = {}
        color_line[1] = "#FFBE00"
        color_line[2] = "#0055C8"
        color_line[3] = "#6E6E00"
        color_line[4] = "#A0006E"
        color_line[5] = "#FF5A00"
        color_line[6] = "#82DC73"
        color_line[7] = "#FF82B4"
        color_line[8] = "#D282BE"
        color_line[9] = "#D2D200"
        color_line[10] = "#DC9600"
        color_line[11] = "#6E491E"
        color_line[12] = "#00643C"
        color_line[13] = "#82C8E6"
        color_line[14] = "#640082"
        color_line["A"] = "#FF1400"
        color_line["B"] = "#3C91DC"
        assert line in color_line
        return color_line[line]
