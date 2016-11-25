
import logging
import json
import os

import flask
from flask import request, Response

import warner
import archiver
import announcer
import flagger

isDebugMode = os.getenv("DESTALINATOR_ACTIVATED") not in ['true', 'True']

# Create and configure the Flask app
application = flask.Flask(__name__)
application.debug = isDebugMode

print('Destalinator application began running')

@application.route('/warner', methods=['POST'])
def warner_route():

    print('warner started')

    response = None
    try:
        if "SB_TOKEN" not in os.environ or "API_TOKEN" not in os.environ or "SLACK_NAME" not in os.environ:
            raise ValueError('ERR: Missing at least one Slack environment variable.')
        else:
            scheduled_warner = warner.Warner(debug=isDebugMode, verbose=isDebugMode)
            print("warning")
            scheduled_warner.warn()

        response = Response("", status=200)
        
    except ValueError as err:
        logging.exception('Error processing message: %s' % request.json)
        logging.exception('Exception: ' + err.args)
        response = Response(err.args, status=500)

    print("warned")
        
    return response

@application.route('/archiver', methods=['POST'])
def archiver_route():

    print('archiver started')

    response = None
    try:
        if "SB_TOKEN" not in os.environ or "API_TOKEN" not in os.environ or "SLACK_NAME" not in os.environ:
            raise ValueError('ERR: Missing at least one Slack environment variable.')
        else:
            scheduled_archiver = archiver.Archiver(debug=isDebugMode, verbose=isDebugMode)
            print("archiving")
            scheduled_archiver.archive()

        response = Response("", status=200)
        
    except ValueError as err:
        logging.exception('Error processing message: %s' % request.json)
        logging.exception('Exception: ' + err.args)
        response = Response(err.args, status=500)

    print("archived")
        
    return response

@application.route('/announcer', methods=['POST'])
def announcer_route():

    print('announcer started')

    response = None
    try:
        if "SB_TOKEN" not in os.environ or "API_TOKEN" not in os.environ or "SLACK_NAME" not in os.environ:
            raise ValueError('ERR: Missing at least one Slack environment variable.')
        else:
            scheduled_announcer = announcer.Announcer(debug=isDebugMode, verbose=isDebugMode)
            print("announcing")
            scheduled_announcer.announce()

        response = Response("", status=200)
        
    except ValueError as err:
        logging.exception('Error processing message: %s' % request.json)
        logging.exception('Exception: ' + err.args)
        response = Response(err.args, status=500)

    print("announced")
        
    return response

@application.route('/flagger', methods=['POST'])
def flagger_route():

    print('flagger started')

    response = None
    try:
        if "SB_TOKEN" not in os.environ or "API_TOKEN" not in os.environ or "SLACK_NAME" not in os.environ:
            raise ValueError('ERR: Missing at least one Slack environment variable.')
        else:
            scheduled_flagger = flagger.Flagger(debug=isDebugMode, verbose=isDebugMode)
            print("flagging")
            scheduled_flagger.flag()

        response = Response("", status=200)
        
    except ValueError as err:
        logging.exception('Error processing message: %s' % request.json)
        logging.exception('Exception: ' + err.args)
        response = Response(err.args, status=500)

    print("flagged")
        
    return response

if __name__ == '__main__':
    application.run(host='0.0.0.0')
