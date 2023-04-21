from flask import Flask, request, Response
from nimbusCore import *
import json
import os
from dotenv import dotenv_values
from datetime import datetime

import logging

logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

# create a file handler and set the level to ERROR
fh = logging.FileHandler('error.log')
fh.setLevel(logging.ERROR)

# create a console handler and set the level to ERROR
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

# create a formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


secret = dotenv_values(dotenv_path=os.path.join(os.path.realpath(
    os.path.dirname(__file__)),'.env'))

valid_api_keys = secret['valid_api_keys'].split(',')

TripBuilder = nimbusCORE.TripBuilder()

app = Flask(__name__)


@app.route('/')
def index():
    return secret["host"]


@app.route('/get_sample_trip')
def getSampleTrip():
    return json.dumps(TripBuilder.demo_trip())


# date in string iso format
# tags as comma separated string or json
# budget as int/string 0 - 3
# must add not done
@app.route('/get_trip_mcts', methods=['POST'])
def getTripMCTS():
    content_type = request.headers.get('Content-Type')
    api_key = request.headers.get('Api-Key')

    if api_key is None or api_key not in secret['valid_api_keys']:
        return 'Invalid Api Key', 400

    if content_type != 'application/json':
        return 'Content-Type not supported', 400
    
    try:
        data = json.loads(request.data)
    except Exception as e:
        logging.exception('An error occurred: %s', str(e))
        return 'Error parsing body', 400
    missing_fields = [field for field in ['start_date', 'end_date', 'tags', 'budget', 'travel_method', 'trip_pace'] if field not in data]
    if missing_fields:
        return f"Missing fields: {', '.join(missing_fields)}", 400
    
    if not set(data['travel_method'].split(',')).issubset({'walk','drive'}):
        return 'Invalid travel method', 400
    
    try:
        return json.dumps(TripBuilder.generate_trip_mcts(start_date=datetime.fromisoformat(data['start_date']), end_date=datetime.fromisoformat(data['end_date']), tags=data['tags'].split(','), must_add=None, budget=int(data['budget']), travel_method=data['travel_method'].split(','), trip_pace=int(data['trip_pace']))), 200
    except Exception as e:
        logging.exception('An error occurred: %s', str(e))
        return 'error generating plan', 400
    
@app.route('/get_alternative_place', methods=['POST'])
def alternative_route():
    content_type = request.headers.get('Content-Type')
    api_key = request.headers.get('Api-Key')

    if api_key is None or api_key not in secret['valid_api_keys']:
        return 'Invalid Api Key'

    if content_type != 'application/json':
        return 'Content-Type not supported'
    
    try:
        data = json.loads(request.data)
    except Exception as e:
        logging.exception('An error occurred: %s', str(e))
        return 'Error parsing body'
    if not {'trip', 'loc_id', 'day'}.issubset(set(data.keys())):
        return 'Missing data field/s in body'
    
    try:
        return json.dumps(TripBuilder.get_alternative_place(data['trip'], str(data['loc_id']), data['day']))
    except Exception as e:
        logging.exception('An error occurred: %s', str(e))
        return 'error getting alternative place'

if __name__ == "__main__":
    app.run(host=secret["host"], port=secret["port"],
            debug=(secret['debug'].lower() == "true"))
