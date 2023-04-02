from flask import Flask
from nimbusCore import *
import json
import os
from dotenv import dotenv_values

if os.environ.get("VERCEL"):
    secret = os.environ
else:
    secret = dotenv_values(dotenv_path=os.path.realpath(os.path.dirname(__file__)) + '/.env')

TripBuilder = nimbusCORE.TripBuilder()

app = Flask(__name__)

@app.route('/')
def index():
    return secret["host"]

@app.route('/get_sample_trip')
def getSampleTrip():
    return json.dumps(TripBuilder.demo_trip())

@app.route('/get_trip_mcts')
def getTripMCTS():
    return json.dumps(TripBuilder.generate_trip_mcts())

if __name__ == "__main__":
    app.run(host = secret["host"], port = secret["port"], debug = (secret['debug'].lower()=="true"))
