""""
This file contains functions that are needed in several routes.py files to
display the webpages, but do not have a decorator binding them to a
particular webpage.
"""
from flask import session, url_for, flash, current_app, request
from werkzeug.routing import RequestRedirect
import pandas as pd
import numpy as np
from scipy.interpolate import PchipInterpolator

from bokeh.models import HoverTool
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.palettes import Spectral6


def eucl(a, b):
    return np.sqrt((a - b) ** 2)


def collect_mongodbobjects(videoid=None):
    """
    Fetch all data that is stored in the MongoDB database.

    NB: This already processes them as a DataFrame using sort_df(),
    which means that the names and variable types of the data must be known
    in advance (they're hardcoded, see sort_df() ).
    :return: Boolean indicating availability of data, DataFrame with all db
    entries
    """
    posts = current_app.d.collect_posts()
    collected = []
    for p in posts:
        if p['_id']:
            del p['_id']
        if videoid == None or p['videoid'] == videoid:
            collected.append(p)

    # If there is data at all
    if collected:
        df = pd.DataFrame(collected)
        df = sort_df(df)
        return True, df
    else:
        return False, None


def sort_df(df):
    """
    Reorder columns in a dataframe, give them suitable data types and sort the
    values.

    :param df: Dataframe to be sorted
    :return: Sorted dataframe
    """
    try:
        standard_data_cols = ['videoid', 'username', 'timestamp', 'date']
        user_data_cols = [c for c in list(df.columns.values) if
                          c not in standard_data_cols]
        ordered_cols = standard_data_cols[:3] + user_data_cols + \
                       standard_data_cols[-1:]
        col_types = ['str', 'str', 'float'] + ['float'] * len(user_data_cols) \
                    + ['int']
        df = df[ordered_cols]
        for t, c in zip(col_types, ordered_cols):
            df[c] = df[c].astype(t)
        df.sort_values(ordered_cols, inplace=True)
    except:
        print("Error! Values are not in right types")
        print(df)
    return df


def check_access_right(forbidden, redirect_url, msg='default'):
    """
    Check if access to a given page is allowed with the current role (the one
    saved in session['role']).
    N.B. Use werkzeug for redirect, the flask redirect function does not work here.
    :param forbidden: The role that is forbidden
    :param redirect_url: The URL to redirect to, e.g. 'control.choose_role'
    :param msg: Message, if there is a message to be flushed. Defaults to
    'default'.
    :return: Redicrects to other page if access not allowed
    """
    if 'role' not in session.keys():
        # If the user has no role yet redirect to choose one.
        raise RequestRedirect(url_for('control.choose_role'))
    if session['role'] != forbidden:
        # Access approved!
        return None
    else:
        # Access denied, redirect.
        if msg:
            if msg == 'default':
                msg = "You can't access that page with your role (current " \
                      "role: " + str(session['role']) + ")."
            flash(msg)
        raise RequestRedirect(url_for(redirect_url))


def get_interpolators(df, currentVariable):

    # Group by username and extract timestamps and values for each user
    grouped_data = df.groupby('username')
    data_by_user = [user for _, user in grouped_data]
    ts = [np.array(t) for t in
          (data_by_user[i]['timestamp'].apply(lambda x: float(x)) for i in
           range(len(data_by_user)))]
    vals = [np.array(val) for val in
            (data_by_user[i][currentVariable].apply(lambda x: float(x)) for i in
             range(len(data_by_user)))]

    # Make sure all data starts and ends at the same time for each user, if the
    # data doesn't suggest otherwise start and end value are 50.
    max_t = max([max(t) for t in ts])
    total = np.sum([np.sum(v) for v in list(np.array(vals))])
    avg = total / np.sum([len(v) for v in vals])
    for i in range(len(ts)):
        if min(ts[i]) != 0:
            ts[i] = np.append([0], ts[i])
            vals[i] = np.append([avg], vals[i])
        if max(ts[i]) != max_t:
            ts[i] = np.append(ts[i], [max_t])
            vals[i] = np.append(vals[i], [avg])
        # Round last timestamp up (for smoother display):
        ts[i] = np.append(ts[i][:-1], int(ts[i][-1]) + 1)

    # Create the interpolation
    interpolators = [PchipInterpolator(t, val) for (t, val) in zip(ts, vals)]
    return interpolators, max_t


def get_videos():
    """
    Find the currently available video names and ids.
    :return: Dictionary of available videos, each stored as id:name, and list
    containing id and name of the video that is the first one in the file.
    """
    with open(current_app.vid_file, 'r') as f:
        videos = f.readlines()
    vid_list = [x.strip() for x in videos if x.strip() if
                (x.strip()[0] is not '#')]
    vid_dict = dict([i.split(':', 1) for i in vid_list])
    first_vid = vid_list[0].split(':', 1)
    return vid_dict, first_vid


def get_video_information(cur_vid_id='', cur_cluster_num=''):
    """
    Parse information on what video and number of clusters should be shown,
    based on available videos and possible input from the website (the input
    parameters to this function)
    :param cur_vid_id: The current video requested by the website
    :param cur_cluster_num: The current cluster number requested by the website
    :return: Current video, id of the current video and dictionary of
    available videos (described more detailly in get_videos() )
    """
    vid_dict, first_vid = get_videos()
    if not cur_vid_id:
        currentVideo = first_vid
    else:
        currentVideo = [cur_vid_id, vid_dict[cur_vid_id]]

    if not cur_cluster_num:
        n_clusters = 3
    else:
        n_clusters = int(cur_cluster_num)
    return currentVideo, vid_dict, n_clusters


def get_input_fields():
    """
    Find what sliders are required to be shown with the video.
    NB: Only a maximum of 2 1d-sliders can be shown, because otherwise they
    will not fit next to the video!
    :return: List containing information on sliders. Each element in the list is
    a list itself, containing [slider type, min_val, max_val, default_val,
    slider name].
    """
    with open(current_app.input_fields, 'r') as f:
        fields = f.readlines()
    field_list = [x.strip() for x in fields if x.strip() if
                  (x.strip()[0] is not '#')]
    field_list = [i.split(':') for i in field_list]

    return field_list


def signal_data_modification(video_id):
    """
    Signal cache that data of specified video id has changed. This causes
    re-calculating plots later.
    """
    current_app.config['CACHE'].set(video_id + 'modified_correlations', True)
    current_app.config['CACHE'].set(video_id + 'modified_chart', True)


def extract_variable(data, request_variable):
    """
   Process data to make it ready for plotting by variable. For example,
   remove rows where the specific variable is nan.

   If the requested variable is not found in the dataframe, it picks another
   variable.
   :param data: Pandas dataframe containing the data
   :param request_variable: The name of the column in the dataframe
   :return: data, currentVariable, list of all possible variables
   """
    columns = data.columns.values
    other_columns = ['date', 'videoid', 'timestamp', 'username']
    variable_list = [x for x in columns if x not in other_columns]

    if request_variable in variable_list:
        currentVariable = request_variable
    else:
        currentVariable = variable_list[0]

    data = data.replace('nan', np.nan)
    data = data[pd.notna(data[currentVariable])]
    return data, currentVariable, variable_list
