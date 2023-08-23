import matplotlib

matplotlib.use('Agg')
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.patches import Circle, Wedge, Rectangle
from matplotlib import cm
from io import BytesIO
import seaborn as sns
import pandas as pd
import plotly.graph_objects as go
import base64
import pickle

# Importing png files scraped from Github with scrape_icons.py
with open('data.pkl', 'rb') as f:
    loaded_data = pickle.load(f)
    png_files = loaded_data


def get_forecast_fig(df):
    fig = go.Figure(data=[
        go.Scatter(x=df['temperature'].index, y=df['temperature'], mode='lines', line=dict(color='blue'),
                   fillcolor="grey", name="Actual", legendrank=1),
        go.Scatter(x=[df['temperature'].index[df['temperature'].idxmax()]],
                   y=[df['temperature'].max()],
                   text="H", textposition='top right',
                   mode='markers', marker=dict(size=12, color='red'), name="Max", legendrank=3),
        go.Scatter(x=[df['temperature'].index[df['temperature'].idxmin()]],
                   y=[df['temperature'].min()],
                   text="L", textposition='top right',
                   mode='markers', marker=dict(size=12, color='blue'), name="Min", legendrank=4),
        go.Scatter(x=df['temperature'].index, y=df['temperatureApparent'], mode='lines',
                   line=dict(dash='dot', color="grey"), name="Feels Like", legendrank=2)
    ])

    for index, row in df.iterrows():
        # Get image data and add to figure
        img_name = row['image_names']
        byte_content = png_files.get(img_name)
        encoded_image = base64.b64encode(byte_content).decode('utf-8')
        data_uri = "data:image/png;base64," + encoded_image

        fig.add_layout_image(
            dict(
                source=data_uri,
                xref="x",
                yref="paper",
                x=index - .5,
                y=1.1,
                sizex=.8,
                sizey=.8,
                opacity=1,
                layer="above"
            )
        )

    fig.update_xaxes(
        ticktext=df['local_time'],  # Convert timestamps to desired string format
        tickvals=df['temperature'].index  # Use integer indices as actual tick values
    )

    fig.update_layout(
        autosize=False,
        width=1000,
        height=600,
        title="24 Hour Weather Forecast",
        xaxis_title="Local Time",
        yaxis_title="Temperature (F°)")

    return fig


def wind_rose_plot(df):
    fig = go.Figure(data=go.Area(
        r=df['windSpeed'],
        theta=df['windDirection'],
        marker=dict(
            color=df['windSpeed'],
            colorscale='Viridis',
            showscale=True
        ),
        hovertemplate='Direction: %{theta}°<br>Speed: %{r} m/s',
        name='Wind Rose'
    ))

    fig.update_layout(
        title='Wind Rose Plot',
        polar=dict(
            radialaxis=dict(
                showgrid=True,
                tickangle=0,
                ticksuffix=' m/s',
                ticks='outside',
                tickfont=dict(size=10),
                range=[0, df['windSpeed'].max()]
            ),
            angularaxis=dict(
                tickmode='array',
                tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                ticktext=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
                direction='clockwise'
            )
        ),
        showlegend=True
    )

    return fig


def arrow_pos(uvIndex):
    if uvIndex <= 2:
        return 1
    elif uvIndex <= 5:
        return 2
    elif uvIndex <= 10:
        return 3
    else:
        return 4


"""
Fauchereau,N (2015) drawing a gauge with matplotlib source code [Source code]. 
http://nicolasfauchereau.github.io/climatecode/posts/drawing-a-gauge-with-matplotlib/
"""

def degree_range(n):
    start = np.linspace(0, 180, n + 1, endpoint=True)[0:-1]
    end = np.linspace(0, 180, n + 1, endpoint=True)[1::]
    mid_points = start + ((end - start) / 2.)
    return np.c_[start, end], mid_points


def rot_text(ang):
    rotation = np.degrees(np.radians(ang) * np.pi / np.pi - np.radians(90))
    return rotation


def gauge(labels=['LOW', 'MEDIUM', 'HIGH', 'VERY HIGH', 'EXTREME'], colors='jet_r', arrow=1, title='', fname=False):
    # begin with sanity checks
    N = len(labels)

    if arrow > N:
        raise Exception("\n\nThe category ({}) is greated than the length\nof the labels ({})".format(arrow, N))

    """
    if colors is a string, we assume it's a matplotlib colormap
    and we discretize in N discrete colors 
    """

    if isinstance(colors, str):
        cmap = cm.get_cmap(colors, N)
        cmap = cmap(np.arange(N))
        colors = cmap[::-1, :].tolist()
    if isinstance(colors, list):
        if len(colors) == N:
            colors = colors[::-1]
        else:
            raise Exception("\n\nnumber of colors {} not equal to number of categories{}\n".format(len(colors), N))

    """
    begins the plotting
    """

    fig, ax = plt.subplots(figsize=(2, 2))

    ang_range, mid_points = degree_range(N)

    labels = labels[::-1]

    """
    plots the sectors and the arcs
    """
    patches = []
    for ang, c in zip(ang_range, colors):
        # sectors
        patches.append(Wedge((0., 0.), .4, *ang, facecolor='w', lw=2))
        # arcs
        patches.append(Wedge((0., 0.), .4, *ang, width=0.10, facecolor=c, lw=2, alpha=0.5))

    [ax.add_patch(p) for p in patches]

    """
    set the labels (e.g. 'LOW','MEDIUM',...)
    """

    for mid, lab in zip(mid_points, labels):
        ax.text(0.35 * np.cos(np.radians(mid)), 0.35 * np.sin(np.radians(mid)), lab, horizontalalignment='center',
                verticalalignment='center', fontsize=3,
                fontweight='bold', rotation=rot_text(mid))

    """
    set the bottom banner and the title
    """
    r = Rectangle((-0.4, -0.1), 0.8, 0.1, facecolor='w', lw=2)
    ax.add_patch(r)

    ax.text(0, -0.05, title, horizontalalignment='center', verticalalignment='center', fontsize=5, fontweight='bold')

    """
    plots the arrow now
    """

    pos = mid_points[abs(arrow - N)]

    ax.arrow(0, 0, 0.225 * np.cos(np.radians(pos)), 0.225 * np.sin(np.radians(pos)), width=0.04, head_width=0.09,
             head_length=0.1, fc='k', ec='k')

    ax.add_patch(Circle((0, 0), radius=0.02, facecolor='k'))
    ax.add_patch(Circle((0, 0), radius=0.01, facecolor='w', zorder=11))

    """
    removes frame and ticks, and makes axis equal and tight
    """

    ax.set_frame_on(False)
    ax.axes.set_xticks([])
    ax.axes.set_yticks([])
    ax.axis('equal')
    plt.tight_layout()

    # Save the figure to a BytesIO object
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Convert the figure to a data URI
    encoded_image = base64.b64encode(buf.getvalue()).decode('utf-8')
    data_uri = 'data:image/png;base64,' + encoded_image

    # Close the figure
    plt.close()

    return data_uri


"""
This code was adapted from wind_rose.ipynb by Paul Hobson
Available at: https://gist.github.com/phobson/41b41bdd157a2bcf6e14
Date accessed: 05 Aug 2023
"""


def speed_labels(bins, units):
    labels = []
    for left, right in zip(bins[:-1], bins[1:]):
        if left == bins[0]:
            labels.append('calm'.format(right))
        elif np.isinf(right):
            labels.append('>{} {}'.format(left, units))
        else:
            labels.append('{} - {} {}'.format(left, right, units))

    return list(labels)


def _convert_dir(directions, N=None):
    if N is None:
        N = directions.shape[0]
    barDir = directions * np.pi / 180. - np.pi / N
    barWidth = 2 * np.pi / N
    return barDir, barWidth


def generate_wind_rose(forecast_df):
    total_count = forecast_df.shape[0]
    calm_count = forecast_df.query("windSpeed == 0").shape[0]

    spd_bins = [-1, 0, 5, 10, 15, 20, 25, 30, np.inf]
    spd_labels = speed_labels(spd_bins, units='knots')

    dir_bins = np.arange(-7.5, 370, 15)
    dir_labels = (dir_bins[:-1] + dir_bins[1:]) / 2

    rose = (
        forecast_df.assign(WindSpd_bins=lambda df:
        pd.cut(df['windSpeed'], bins=spd_bins, labels=spd_labels, right=True)
                           )
        .assign(WindDir_bins=lambda df:
        pd.cut(df["windDirection"], bins=dir_bins, labels=dir_labels, right=False)
                )
        .replace({'WindDir_bins': {360: 0}})
        .groupby(by=['WindSpd_bins', 'WindDir_bins'])
        .size()
        .unstack(level='WindSpd_bins')
        .fillna(0)
        .assign(calm=lambda df: calm_count / df.shape[0])
        .sort_index(axis=1)
        .applymap(lambda x: x / total_count * 100)
    )

    directions = np.arange(0, 360, 15)

    # Generate the wind rose plot
    wind_fig = wind_rose(rose, directions)

    # Save the figure to a BytesIO object and convert it to a data URI
    wind_data_uri = save_figure_to_data_uri(wind_fig)

    return wind_data_uri


def wind_rose(rosedata, wind_dirs, palette=None):
    if palette is None:
        palette = sns.color_palette('inferno', n_colors=rosedata.shape[1])

    bar_dir, bar_width = _convert_dir(wind_dirs)

    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
    ax.set_theta_direction('clockwise')
    ax.set_theta_zero_location('N')

    for n, (c1, c2) in enumerate(zip(rosedata.columns[:-1], rosedata.columns[1:])):
        if n == 0:
            # first column only
            ax.bar(bar_dir, rosedata[c1].values,
                   width=bar_width,
                   color=palette[0],
                   edgecolor='none',
                   label=c1,
                   linewidth=0)

        # all other columns
        ax.bar(bar_dir, rosedata[c2].values,
               width=bar_width,
               bottom=rosedata.cumsum(axis=1)[c1].values,
               color=palette[n + 1],
               edgecolor='none',
               label=c2,
               linewidth=0)

    leg = ax.legend(loc=(0.75, 0.95), ncol=2, fontsize="8")
    ax.set_xticks(np.deg2rad(np.arange(0, 360, 45)))
    ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])

    return fig


def save_figure_to_data_uri(fig):
    # Save the figure to a BytesIO object
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)

    # Convert the figure to a data URI
    data_uri = base64.b64encode(buf.read()).decode('utf-8')

    # Close the BytesIO object
    buf.close()

    # Return the data URI
    return "data:image/png;base64," + data_uri
