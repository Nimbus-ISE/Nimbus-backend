from math import sqrt
import requests
from traveltimepy import Location, Coordinates
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
from collections import defaultdict

import pytz
import json

sys.path.append(os.path.realpath(os.path.dirname(__file__)))

from dbManager import dbMan

class dataProcesser():

    def __init__(self, db=dbMan()):
        self.db = db

    def get_MCTS_data_by_day(self, day):
        loc_data = self.db.get_loc_data_by_day(day)
        places = self._process_places_for_MCTS(loc_data)

        travel_time_matrix = self._process_travel_time_for_MCTS(self.db.get_travel_time_matrix())
        return (places, travel_time_matrix)

    def get_MCTS_data(self):
        loc_datas = self._process_places_for_MCTS(self.db.get_loc_data())
        places = {}
        for value in loc_datas:
            if value["open_day"].lower() not in places.keys():
                places[value["open_day"].lower()] = [value]
            else:
                places[value["open_day"].lower()].append(value)

        travel_time_matrix = self._process_travel_time_for_MCTS(self.db.get_travel_time_matrix())
        return (places, travel_time_matrix)

    def _process_places_for_MCTS(self, loc_data):
        df = pd.DataFrame.from_records(
            loc_data['data'], columns=loc_data['cols'])
        df['tags'] = df['tag_list'].str.split(', ')
        df['coordinate'] = list(zip(df['lat'], df['lng']))
        df['hours'] = list(zip(df['open_time'], df['close_time']))
        #TODO get duration from db or remove this? alrdy have est_time_stay
        df['duration'] = 60
        df['durationH'] = df.duration/60
        df.drop(["lat", "lng", "province", "open_time",
                "close_time", "tag_list"], axis=1, inplace=True)
        df = df[['loc_id', 'loc_name', 'coordinate', 'tags', 'hours', 'price_level', 'est_time_stay',
                 'duration', 'durationH', 'rating', "open_day"]]
        df['rating'] = df['rating'].apply(lambda x: float(x))

        return df.to_dict('records')
    
    def _process_travel_time_for_MCTS(self, travel_time_array):
        result_dict = defaultdict(dict)
        for (loc_id_from, loc_id_to, travel_time) in travel_time_array:
            result_dict[loc_id_from][loc_id_to] = int(travel_time)
        return dict(result_dict)
        

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
        locations = []
        departure_searches = []

        tz = pytz.timezone('Asia/Bangkok')
        dt = datetime.now(tz).replace(
            hour=12, minute=0, second=0, microsecond=0)

        next_monday = dt + timedelta(days=(7 - dt.weekday()))

        for loc_data in locations_data:
            locations.append(
                {"id": 'P.' + str(loc_data[0]), "coords": {"lat": loc_data[1], "lng": loc_data[2]}})

            arrival_location_ids = []
            for loc_data_B in locations_data:
                if loc_data != loc_data_B:
                    arrival_location_ids.append('P.' + str(loc_data_B[0]))

            departure_searches.append({
                "id": 'from.' + str(loc_data[0]),
                'departure_location_id': 'P.' + str(loc_data[0]),
                'arrival_location_ids': arrival_location_ids,
                'departure_time': next_monday.isoformat(),
                'travel_time': 3600,
                "properties": [
                    "travel_time"
                ],
                "transportation": {
                    "type": "driving",
                    # "max_changes": {  # for public transportation
                    #     "enabled": True,
                    #     "limit": 0
                    # }
                },
                # "range": {  # for public transportation
                #     "enabled": False,
                #     "max_results": 0,
                #     "width": 600
                # },
            })

        sliced_departure_searches = [departure_searches[i:i+10]
                                     for i in range(0, len(departure_searches), 10)]

        payloads = [{
            "locations": locations,
            "departure_searches": sliced_departure_search_10
        } for sliced_departure_search_10 in sliced_departure_searches]

        return payloads

    def update_travel_time_matrix(self, travel_time_matrix : dict, transport : str):
        # have {a:{b:1}}
        # want ((a,b,1),(a,c,2))
        data = []
        for loc_id_from, value in travel_time_matrix.items():
            for loc_id_to, travel_time in value.items():
                data.append((loc_id_from,loc_id_to,travel_time,transport))
        self.db.update_travel_time_matrix(data)


if __name__ == "__main__":
    data_processor = dataProcesser()
    # print(data_processor.get_places_for_travelTimeAPI())
    with open("place_data.txt", "w", encoding='utf8') as file:
        file.write(json.dumps(data_processor.get_MCTS_data()
                   [0], ensure_ascii=False))
