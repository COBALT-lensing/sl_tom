from astropy.stats import sigma_clip
from astropy.time import Time
from matplotlib import pyplot

import seaborn

DEFAULT_SIGMA_CLIP = 4


def generate_image(
    timeseries,
    figsize=(15, 10),
    highlights=None,
    sigma=DEFAULT_SIGMA_CLIP,
    errorbars=True,
):
    df = timeseries.to_pandas()
    df["time_jd"] = timeseries["time"].jd

    if sigma is not None and sigma is not False:
        df["flux"] = sigma_clip(df["flux"], sigma=sigma)

    fig, ax = pyplot.subplots(figsize=figsize)

    if highlights is not None:
        for xmin, xpeak, xmax in highlights:
            if type(xmin) is float:
                xmin = Time(xmin, format="jd")
            if type(xpeak) is float:
                xpeak = Time(xpeak, format="jd")
            if type(xmax) is float:
                xmax = Time(xmax, format="jd")
            pyplot.axvspan(xmin.jd, xmax.jd, color="green", alpha=0.2)
            pyplot.axvline(xpeak.jd, color="orange", alpha=0.2)
    # Remove the original index before plotting to avoid ValueError from Pandas due to duplicate index
    seaborn.scatterplot(
        data=df.reset_index(),
        x="time_jd",
        y="flux",
        ax=ax,
        s=4,
        alpha=0.5,
    )

    if errorbars:
        ax.errorbar(
            df["time_jd"],
            df["flux"],
            yerr=df["flux_err"],
            ecolor="red",
            ls="none",
            alpha=0.2,
            elinewidth=0.5,
        )

    return fig
