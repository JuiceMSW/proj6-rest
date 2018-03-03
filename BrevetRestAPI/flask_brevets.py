"""
Replacement for RUSA ACP brevet time calculator
(see https://rusa.org/octime_acp.html)

"""

import flask
from flask import request
from pymongo import MongoClient
import arrow  # Replacement for datetime, based on moment.js
import acp_times  # Brevet time calculations
import config
import datetime

import logging

###
# Globals
###
app = flask.Flask(__name__)
CONFIG = config.configuration()
app.secret_key = CONFIG.SECRET_KEY

client = MongoClient(CONFIG.MONGO_URI)
db = client.get_default_database()
brevet_times_col = db['brevet_times']

###
# Pages
###


@app.route("/")
@app.route("/index")
def index():
    app.logger.debug("Main page entry")
    return flask.render_template('calc.html')


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    flask.session['linkback'] = flask.url_for("index")
    return flask.render_template('404.html'), 404


###############
#
# AJAX request handlers
#   These return JSON, rather than rendering pages.
#
###############
@app.route("/_calc_times")
def _calc_times():
    """
    Calculates open/close times from miles, using rules
    described at https://rusa.org/octime_alg.html.
    Expects one URL-encoded argument, the number of miles.
    """
    app.logger.debug("Got a JSON request")
    km = request.args.get('km', 999, type=float)
    brevet = request.args.get('brevet', type=int)
    start_info = request.args.get('start_info', type=str)
    app.logger.debug("km={}".format(km))
    app.logger.debug("request.args: {}".format(request.args))
    open_time = acp_times.open_time(km, brevet, start_info)
    close_time = acp_times.close_time(km, brevet, start_info)
    result = {"open": open_time, "close": close_time}
    return flask.jsonify(result=result)

@app.route("/_submit_times_db")
def _submit_times_db():
    brevet_times_col.delete_many({})

    miles = request.args.get("miles", type=str).split("|")
    km = request.args.get("km", type=str).split("|")
    openTime = request.args.get("open", type=str).split("|")
    closeTime = request.args.get("close", type=str).split("|")

    num_controls = len(miles)

    print(miles)
    print(km)
    print(openTime)
    print(closeTime)

    for control in range(num_controls - 1):
        brevet_times_col.insert({
                                "miles": miles[control],
                                "km": km[control],
                                "openTime": openTime[control],
                                "closeTime": closeTime[control]
                                })
    return ""

@app.route("/_display_times_db")
def _display_times_db():
    controls = brevet_times_col.find({})
    parsedControls = ""
    controlNum = 1
    for entries in controls:
        parsedControls += "[Control {}<br/> miles: {}<br/>km: {}<br/>openTime: {}<br/>closeTime: {}<br/>]<br/>".format(controlNum, entries['miles'], entries['km'], entries['openTime'], entries['closeTime'])
        controlNum += 1
    return flask.jsonify(result=parsedControls)

@app.route("/listAll")
@app.route("/listAll/json")
def json_listAll():
    k = request.args.get("top", default = -1, type=int)
    controls = brevet_times_col.find({})
    containerString = "<html>"
    containerString += '{<br/>&emsp;"results" : [<br/>'
    openTimes = []
    closeTimes = []
    for entries in controls:
        openTimes.append(entries['openTime'])
        closeTimes.append(entries['closeTime'])
    if k != -1:
        # Sorting Code from : https://stackoverflow.com/a/17627575
        openTimes.sort(key=lambda x: datetime.datetime.strptime(x, ' %m/%d %H:%M'))
        closeTimes.sort(key=lambda x: datetime.datetime.strptime(x, ' %m/%d %H:%M'))
    for i in range(len(openTimes)):
        if i == k: #Break when i = k to only display top k results.  If for loop went from 0 to k, if k > len(openTimes) it would error, this prevents that
            break
        containerString += "&emsp;&emsp;{"
        containerString += '<br/>&emsp;&emsp;&emsp;"openTime" : ' + openTimes[i] + ",<br/>&emsp;&emsp;&emsp;" + '"closeTime" : ' + closeTimes[i] + "<br/>"
        containerString += "&emsp;&emsp;},<br/>"
    containerString = containerString[:-6]
    containerString += "<br/>&emsp;]<br/>}"
    containerString += "</html>"
    return containerString

@app.route("/listOpenOnly")
@app.route("/listOpenOnly/json")
def json_listOpenOnly():
    k = request.args.get("top", default = -1, type=int)
    controls = brevet_times_col.find({})
    containerString = "<html>"
    containerString += '{<br/>&emsp;"results" : [<br/>'
    openTimes = []
    for entries in controls:
        openTimes.append(entries['openTime'])
    if k != -1:
        # Sorting Code from : https://stackoverflow.com/a/17627575
        openTimes.sort(key=lambda x: datetime.datetime.strptime(x, ' %m/%d %H:%M'))
    for i in range(len(openTimes)):
        if i == k: #Break when i = k to only display top k results.  If for loop went from 0 to k, if k > len(openTimes) it would error, this prevents that
            break
        containerString += "&emsp;&emsp;{"
        containerString += '<br/>&emsp;&emsp;&emsp;"openTime" : ' + openTimes[i] + "<br/>"
        containerString += "&emsp;&emsp;},<br/>"
    containerString = containerString[:-6]
    containerString += "<br/>&emsp;]<br/>}"
    containerString += "</html>"
    return containerString

@app.route("/listCloseOnly")
@app.route("/listCloseOnly/json")
def json_listCloseOnly():
    k = request.args.get("top", default = -1, type=int)
    controls = brevet_times_col.find({})
    containerString = "<html>"
    containerString += '{<br/>&emsp;"results" : [<br/>'
    openTimes = []
    closeTimes = []
    for entries in controls:
        closeTimes.append(entries['closeTime'])
    if k != -1:
        # Sorting Code from : https://stackoverflow.com/a/17627575
        closeTimes.sort(key=lambda x: datetime.datetime.strptime(x, ' %m/%d %H:%M'))
    for i in range(len(closeTimes)):
        if i == k: #Break when i = k to only display top k results.  If for loop went from 0 to k, if k > len(openTimes) it would error, this prevents that
            break
        containerString += "&emsp;&emsp;{"
        containerString += '<br/>&emsp;&emsp;&emsp;"closeTime" : ' + closeTimes[i] + "<br/>"
        containerString += "&emsp;&emsp;},<br/>"
    containerString = containerString[:-6]
    containerString += "<br/>&emsp;]<br/>}"
    containerString += "</html>"
    return containerString

@app.route("/listAll/csv")
def csv_listAll():
    k = request.args.get("top", default = -1, type=int)
    controls = brevet_times_col.find({})
    containerString = "<html>Open, Close<br/>"
    openTimes = []
    closeTimes = []
    for entries in controls:
        openTimes.append(entries['openTime'])
        closeTimes.append(entries['closeTime'])
    if k != -1:
        # Sorting Code from : https://stackoverflow.com/a/17627575
        openTimes.sort(key=lambda x: datetime.datetime.strptime(x, ' %m/%d %H:%M'))
        closeTimes.sort(key=lambda x: datetime.datetime.strptime(x, ' %m/%d %H:%M'))
    for i in range(len(openTimes)):
        if i == k: #Break when i = k to only display top k results.  If for loop went from 0 to k, if k > len(openTimes) it would error, this prevents that
            break
        containerString += openTimes[i] + ", " + closeTimes[i] + "<br/>"
    containerString += "</html>"
    return containerString

@app.route("/listOpenOnly/csv")
def csv_listOpenOnly():
    k = request.args.get("top", default = -1, type=int)
    controls = brevet_times_col.find({})
    containerString = "<html>Open<br/>"
    openTimes = []
    for entries in controls:
        openTimes.append(entries['openTime'])
    if k != -1:
        # Sorting Code from : https://stackoverflow.com/a/17627575
        openTimes.sort(key=lambda x: datetime.datetime.strptime(x, ' %m/%d %H:%M'))
    for i in range(len(openTimes)):
        if i == k: #Break when i = k to only display top k results.  If for loop went from 0 to k, if k > len(openTimes) it would error, this prevents that
            break
        containerString += openTimes[i] + "<br/>"
    containerString += "</html>"
    return containerString

@app.route("/listCloseOnly/csv")
def csv_listCloseOnly():
    k = request.args.get("top", default = -1, type=int)
    controls = brevet_times_col.find({})
    containerString = "<html>Close<br/>"
    closeTimes = []
    for entries in controls:
        closeTimes.append(entries['closeTime'])
    if k != -1:
        # Sorting Code from : https://stackoverflow.com/a/17627575
        closeTimes.sort(key=lambda x: datetime.datetime.strptime(x, ' %m/%d %H:%M'))
    for i in range(len(closeTimes)):
        if i == k: #Break when i = k to only display top k results.  If for loop went from 0 to k, if k > len(openTimes) it would error, this prevents that
            break
        containerString += closeTimes[i] + "<br/>"
    containerString += "</html>"
    return containerString

#############

app.debug = CONFIG.DEBUG
if app.debug:
    app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    print("Opening for global access on port {}".format(CONFIG.PORT))
    app.run(port=CONFIG.PORT, host="0.0.0.0")
