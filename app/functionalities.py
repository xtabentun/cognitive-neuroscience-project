""""
This file contains functions that are needed in several routes.py files to
display the webpages, but do not have a decorator binding them to a
particular webpage.
"""
from flask import session, url_for, flash, current_app
from werkzeug.routing import RequestRedirect
import pandas as pd
import numpy as np
from scipy.interpolate import PchipInterpolator


def collect_mongodbobjects():
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
    ordered_cols = ['videoid', 'username', 'timestamp', 'value', 'date']
    col_types = ['str', 'str', 'float', 'int', 'str']
    df = df[ordered_cols]
    for t, c in zip(col_types, ordered_cols):
        df[c] = df[c].astype(t)
    df.sort_values(ordered_cols, inplace=True)
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


def get_interpolators(df):
    df['timestamp'] = pd.to_numeric(df['timestamp'])
    df['value'] = pd.to_numeric(df['value'])
    df.sort_values(by=['timestamp'], inplace=True)

    # Group by username and extract timestamps and values for each user
    grouped_data = df.groupby('username')
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
        ts[i] = np.append(ts[i][:-1], int(ts[i][-1]) + 1)

    # Create the interpolation
    interpolators = [PchipInterpolator(t, val) for (t, val) in zip(ts, vals)]
    return interpolators, max_t
