"""
This file contains the routes, i.e. the functions to be executed when a page
(like "/researcher_view") is accessed in the browser.

It has only the webpages belonging to the researcher blueprint,
i.e. those belonging to the researcher interface.
"""

import json
import pandas as pd
from flask import render_template, flash, current_app
import numpy as np

from bokeh.models import HoverTool
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.palettes import Spectral6
from bokeh.layouts import row

from app.researcher import bp
from app.functionalities import collect_mongodbobjects, check_access_right, get_interpolators

# PChipInterpolator finds monotonic interpolations, which we need to make
# sure that our interpolated values don't go below 0 or above 100.
from scipy.interpolate import PchipInterpolator

from tslearn.clustering import TimeSeriesKMeans
from tslearn.datasets import CachedDatasets
from tslearn.preprocessing import TimeSeriesScalerMeanVariance, TimeSeriesResampler


# from scipy.interpolate import spline
# from scipy.interpolate import interp1d

@bp.route('/chart', methods=['GET'])
def chart():
    """
    Display the web page for the researcher view.

    This webpage is only for the role researcher.
    :return: Researcher view webpage
    """
    check_access_right(forbidden='user', redirect_url='control.index')

    # Get the data:
    _, data = collect_mongodbobjects()
    data['timestamp'] = pd.to_numeric(data['timestamp'])
    data['value'] = pd.to_numeric(data['value'])
    data.sort_values(by=['timestamp'], inplace=True)

    # Group by username and extract timestamps and values for each user
    grouped_data = data.groupby('username')
    data_by_user = [user for _, user in grouped_data]
    ts = [np.array(t) for t in
          (data_by_user[i]['timestamp'].apply(lambda x: float(x)) for i in
           range(len(data_by_user)))]
    vals = [np.array(val) for val in
            (data_by_user[i]['value'].apply(lambda x: float(x)) for i in
             range(len(data_by_user)))]

    # Make sure all data starts and ends at the same time for each user, if the
    # data doesn't suggest otherwise start and end value are 50.
    max_t = max([max(t) for t in ts])
    for i in range(len(ts)):
        if min(ts[i]) != 0:
            ts[i] = np.append([0], ts[i])
            vals[i] = np.append([50], vals[i])
        if max(ts[i]) != max_t:
            ts[i] = np.append(ts[i], [max_t])
            vals[i] = np.append(vals[i], [50])
        # Round last timestamp up (for smoother display):
        ts[i] = np.append(ts[i][:-1], int(ts[i][-1])+1)

    # Create the interpolation
    xs = np.arange(0, int(max_t) + 1.5, 1)
    interpolators = [PchipInterpolator(t, val) for (t, val) in zip(ts, vals)]
    user_timeseries = [[xs, interpolator(xs)] for interpolator in interpolators]

    # Create the Bokeh plot
    TOOLS = 'save,pan,box_zoom,reset,wheel_zoom,hover'
    p = figure(title="Valence ratings by timestamp", y_axis_type="linear",
               plot_height=500,
               tools=TOOLS, active_scroll='wheel_zoom', plot_width=900)
    p.xaxis.axis_label = 'Timestamp (seconds)'
    p.yaxis.axis_label = 'Valence rating'

    for i, tseries in enumerate(user_timeseries):
        p.line(tseries[0], tseries[1], line_color=Spectral6[i%6],
               line_width=3, name=data_by_user[i]['username'].iloc[0])
    for i in range(len(ts)):
        for j in range(len(ts[i])):
            p.circle(ts[i][j], vals[i][j], fill_color=Spectral6[i%6],
                     line_color='black', radius=0.7)

    p.select_one(HoverTool).tooltips = [
        ('Time', '@x'),
        ('Valence', '@y'),
        ('User', '$name')

    ]

    script, div = components(p)
    return render_template("researcher/researcher.html", the_div=div,
                           the_script=script)


@bp.route('/correlations', methods=['GET'])
def correlations():
    check_access_right(forbidden='user', redirect_url='control.index')
    _, data = collect_mongodbobjects()
    interpolators, max_t = get_interpolators(data)
    xs = np.arange(0, int(max_t) + 1.5, 1)
    user_timeseries = [[interpolator(xs)] for interpolator in interpolators]

    seed = 0
    np.random.seed(seed)

    n_clusters = 3
    if n_clusters > np.array(user_timeseries).shape[0]:
        n_clusters = np.array(user_timeseries).shape[0]
    # Euclidean k-means
    km = TimeSeriesKMeans(n_clusters=n_clusters, verbose=True, random_state=seed)
    y_pred = km.fit_predict(user_timeseries)

    # add a line renderer
    all_plots = ""
    all_scripts = ""
    plots = []

    for yi in range(n_clusters):
        title = "Cluster " + str(yi + 1)
        p = figure(plot_width=300, plot_height=300, title=title)
        for xx in range(0, len(y_pred)):
            if y_pred[xx] == yi:
                p.line(range(0, len(user_timeseries[xx][0])), user_timeseries[xx][0], line_width=0.3)
        values = km.cluster_centers_[yi].ravel()
        p.line(range(0, len(values)), values, line_width=2)
        plots.append(p)
    script, div = components(row(plots))

    return render_template("researcher/correlations.html", the_div=div, the_script=script)
