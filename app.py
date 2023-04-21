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
        return Response("Invalid Api Key", status=400, mimetype='application/json')
        # return 'Invalid Api Key', 400

    if content_type != 'application/json':
        return Response("Content-Type not supported", status=400, mimetype='application/json')
    
    try:
        data = json.loads(request.data)
    except Exception as e:
        logging.exception('An error occurred: %s', str(e))
        return Response("Error parsing body", status=400, mimetype='application/json')
    missing_fields = [field for field in ['start_date', 'end_date', 'tags', 'budget', 'travel_method', 'trip_pace', 'must_include'] if field not in data]
    if missing_fields:
        return Response("Missing fields", status=400, mimetype='application/json')
    
    if not set(data['travel_method'].split(',')).issubset({'walk','drive'}):
        return Response("Invalid travel method", status=400, mimetype='application/json')
    
    try: 
        res = json.dumps(TripBuilder.generate_trip_mcts(start_date=datetime.fromisoformat(data['start_date']), end_date=datetime.fromisoformat(data['end_date']), tags=data['tags'].split(','), must_include=data['must_include'], budget=int(data['budget']), travel_method=data['travel_method'].split(','), trip_pace=int(data['trip_pace'])))
        return Response(res, status=200, mimetype='application/json')
    except Exception as e:
        logging.exception('An error occurred: %s', str(e))
        return Response("error generating plan", status=500, mimetype='application/json')
    
@app.route('/get_alternative_place', methods=['POST'])
def alternative_route():
    content_type = request.headers.get('Content-Type')
    api_key = request.headers.get('Api-Key')

    if api_key is None or api_key not in secret['valid_api_keys']:
        return Response('Invalid Api Key', status=500, mimetype='application/json')

    if content_type != 'application/json':
        return Response('Content-Type not supported', status=500, mimetype='application/json')
    
    try:
        data = json.loads(request.data)
    except Exception as e:
        logging.exception('An error occurred: %s', str(e))
        return Response('Error parsing body', status=500, mimetype='application/json')
    if not {'trip', 'loc_id', 'day'}.issubset(set(data.keys())):
        return Response('Missing data field/s in body', status=500, mimetype='application/json')
    
    try:
        return json.dumps(TripBuilder.get_alternative_place(data['trip'], str(data['loc_id']), data['day']))
    except Exception as e:
        logging.exception('An error occurred: %s', str(e))
        return Response("error getting alternative place", status=500, mimetype='application/json')

if __name__ == "__main__":
    app.run(host=secret["host"], port=secret["port"],
            debug=(secret['debug'].lower() == "true"))
