import os
import json
import pandas as pd
from pandas import DataFrame
from pprint import pprint
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure, show, output_file
from bokeh.embed import components
from bson.json_util import dumps
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

from DatabaseClient import DatabaseClient

app = Flask(__name__) # create the application instance :)
app.config.from_object(__name__) # load config from this file , flaskr.py

app.config.from_envvar('FLASKR_SETTINGS', silent=True)
d = DatabaseClient()

@app.route('/')
def index():
    return render_template('frontend/index.html')

@app.route('/save', methods=['POST'])
def save():
    d.insert_post({"timestamp":request.form.get('timestamp'), "value": request.form.get('value'), "videoname": request.form.get('videoname')})
    return "Saving completed"

@app.route('/researcher_view', methods=['GET'])
def chart():
    # mock data:
    data2 = {"objects": [{"timestamp": "1", "value": "-0.5", "videoname": "dog video"},
                    {"timestamp": "3.5", "value": "1", "videoname": "cat video"},
                    {"timestamp": "5", "value": "-1", "videoname": "rat video"},
                    {"timestamp": "6.5", "value": "0.7", "videoname": "capybara video"},
                    {"timestamp": "10.2", "value": "0.25", "videoname": "parrot video"},
                    {"timestamp": "20.5", "value": "0.57", "videoname": "lizard video"},
                    {"timestamp": "22.8", "value": "0.91", "videoname": "another cat video"}]}
    """
    # commented original calling-json-function:
    data2 = d.collect_posts()
    collected = []
    for p in data2:
        if p['_id']:
            del p['_id']
        collected.append(p)
    return json.dumps({"objects": collected})


    #for document in data2:
    #    pprint(document)
    # d.collect_posts() returns a cursor object which is not serializable"""
    jsonData2 = json.loads(json.dumps(data2))#
    print(jsonData2)
    df = pd.DataFrame(jsonData2)
    data_valence = df.objects.apply(lambda x: pd.Series(x))
    #data_valence = df.apply(lambda x: pd.Series(x))

    TOOLS = 'save,pan,box_zoom,reset,wheel_zoom,hover'
    p = figure(title="Valence ratings by timestamp", y_axis_type="linear", x_range=(0, 23), y_range=(-1, 1), plot_height = 400,
           tools = TOOLS, plot_width = 900)
    p.xaxis.axis_label = 'Timestamp (seconds)'
    p.yaxis.axis_label = 'Valence rating'
    p.line(data_valence.timestamp, data_valence.value,line_color="purple", line_width = 3)

    source = ColumnDataSource(data={
    'timestamp': data_valence.timestamp,
    'value': data_valence.value,
    'videoname': data_valence.videoname})

    p.select_one(HoverTool).tooltips = [
    ('timestamp', '@x'),
    ('Rating of valence', '@y')
    ]

    script, div = components(p)
    return render_template("frontend/index2.html", the_div=div, the_script=script)



@app.route('/collect_data')
def collect_data():
    posts = d.collect_posts()
    collected = []
    for p in posts:
        if p['_id']:
            del p['_id']
        collected.append(p)
    return json.dumps({"objects": collected})

@app.route('/delete_all')
def delete_data():
    d.delete_many({})
    return "All items deleted :)"


@app.route('/<path:path>')
def static_file(path):
    return app.send_static_file(path)
