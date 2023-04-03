from math import sqrt
import requests
from traveltimepy import Location, Coordinates
import pandas as pd
from dbManager import dbMan
from datetime import datetime, timedelta
import sys
import os

import pytz
import json

sys.path.append(os.path.realpath(os.path.dirname(__file__)))


class dataProcesser():

    def __init__(self, db=dbMan()):
        self.db = db

    # TODO remove open_day from this one
    def get_MCTS_data_by_day(self, day):
        loc_data = self.db.get_loc_data_by_day(day)
        places = self._process_places_for_MCTS(loc_data)

        # use travel time api / db
        # TODO
        travel_time_matrix = {}
        # TEMP
        for placeA in places:
            travel_time_matrix[placeA['id']] = {}
            for placeB in places:
                if placeB['tags'] == ['wait'] or placeA['tags'] == ['wait']:
                    travel_time_matrix[placeA['id']][placeB['id']] = 0
                else:
                    travel_time_matrix[placeA['id']][placeB['id']] = sqrt(
                        (placeA['coordinate'][0] - placeB['coordinate'][0]) ** 2 + (placeA['coordinate'][1] - placeB['coordinate'][1]) ** 2)

        # buffer places and travel_time_matrix ?? maybe update every hours/days
        return (places, travel_time_matrix)

    def get_MCTS_data(self):
        loc_datas = self._process_places_for_MCTS(self.db.get_loc_data())
        places = {}
        for value in loc_datas:
            if value["open_day"].lower() not in places.keys():
                places[value["open_day"].lower()] = [value]
            else:
                places[value["open_day"].lower()].append(value)

        # use travel time api / db
        # TODO
        travel_time_matrix = {}
        # TEMP
        for placeA in places["mon"]:
            travel_time_matrix[placeA['id']] = {}
            for placeB in places["mon"]:
                if placeB['id'] == 'wait' or placeA['id'] == 'wait':
                    travel_time_matrix[placeA['id']][placeB['id']] = 0
                else:
                    travel_time_matrix[placeA['id']][placeB['id']] = sqrt(
                        (placeA['coordinate'][0] - placeB['coordinate'][0]) ** 2 + (placeA['coordinate'][1] - placeB['coordinate'][1]) ** 2)

        # buffer places and travel_time_matrix ?? maybe update every hours/days
        return (places, travel_time_matrix)

    def _process_places_for_MCTS(self, loc_data):
        df = pd.DataFrame.from_records(
            loc_data['data'], columns=loc_data['cols'])
        df['tags'] = df['tag_list'].str.split(', ')
        df['coordinate'] = list(zip(df['lat'], df['lng']))
        df['hours'] = list(zip(df['open_time'], df['close_time']))
        df['duration'] = 60  # temp
        df['durationH'] = df.duration/60  # temp
        df.drop(['price_level', "lat", "lng", "province", "open_time",
                "close_time", "tag_list"], axis=1, inplace=True)
        df.rename(columns={'loc_id': 'id'}, inplace=True)
        df = df[['id', 'loc_name', 'coordinate', 'tags', 'hours',
                 'duration', 'durationH', 'rating', "open_day"]]
        df['rating'] = df['rating'].apply(lambda x: float(x))
        # TODO add wait node

        return df.to_dict('records')

    def get_places_for_travelTimeAPI(self):
        locations_data = self.db.get_places_coordinate()
        locations = []
        search_ids = {}
        # dimension :
        # locations = [ Location(id="Samyan Mitrtown", coords=Coordinates(lat=13.7344606, lng=100.52829290867629)), ]
        # search_ids = {'Samyan Mitrtown' : ['Chamchuri Square','Siam Square','Wat Pathum Wanaram', ], }

        for loc_data in locations_data:
            locations += [Location(id=loc_data[0],
                                   coords=Coordinates(lat=loc_data[1], lng=loc_data[2]))]
            search_ids[loc_data[0]] = []
            for loc_data_B in locations_data:
                if loc_data != loc_data_B:
                    search_ids[loc_data[0]] += [loc_data_B[0]]

        return locations, search_ids

    def get_json_for_ttapi(self):
        locations_data = self.db.get_places_coordinate()
        payload = {}
        locations = []
        departure_search = []
        arrival_searches = []
        url = "https://api.traveltimeapp.com/v4/time-filter"

        tz = pytz.timezone('Asia/Bangkok')
        dt = datetime.now(tz).replace(
            hour=12, minute=0, second=0, microsecond=0)

        next_monday = dt + timedelta(days=(7 - dt.weekday()))

        for loc_data in locations_data:
            locations.append(
                [{'id': loc_data[0], 'coords':{'lat': loc_data[1], 'lng':loc_data[2]}}])

            arrival_location_ids = []
            for loc_data_B in locations_data:
                if loc_data != loc_data_B:
                    arrival_location_ids.append(loc_data_B[0])

            departure_search.append({
                "id": loc_data[0],
                'departure_location_id': loc_data[0],
                'arrival_location_ids': arrival_location_ids,
                'departure_time': next_monday.isoformat(),
                'travel_time': 3600,
                "properties": [
                    "travel_time"
                ],
                "transportation": {  # for public transportation
                    "type": "driving",
                    "max_changes": {
                        "enabled": True,
                        "limit": 0
                    }
                },
                "range": {  # for public transportation
                    "enabled": False,
                    "max_results": 0,
                    "width": 600
                },
            })

        
        
        sliced_departure_search = [departure_search[i:i+10] for i in range(0, len(departure_search), 10)]
        
        payloads = [{
            "locations": locations,
            "departure_search": sliced_departure_search_10
        } for sliced_departure_search_10 in sliced_departure_search]
        
        
        
        return payloads


if __name__ == "__main__":
    data_processor = dataProcesser()
    # print(data_processor.get_places_for_travelTimeAPI())
    print(data_processor.get_json_for_ttapi())