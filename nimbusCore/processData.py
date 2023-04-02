import sys
import os

sys.path.append(os.path.realpath(os.path.dirname(__file__)))

from dbManager import dbMan
import pandas as pd
from traveltimepy import Location, Coordinates
from math import sqrt


class dataProcesser():
    
    
    def __init__(self,db = dbMan()):
        self.db = db
    
    #TODO remove open_day from this one
    def get_MCTS_data_by_day(self,day):
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
                    travel_time_matrix[placeA['id']][placeB['id']] = sqrt(( placeA['coordinate'][0] - placeB['coordinate'][0]) ** 2 + (placeA['coordinate'][1] - placeB['coordinate'][1]) ** 2 )
        
        #buffer places and travel_time_matrix ?? maybe update every hours/days
        return (places,travel_time_matrix)
    
    
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
                    travel_time_matrix[placeA['id']][placeB['id']] = sqrt(( placeA['coordinate'][0] - placeB['coordinate'][0]) ** 2 + (placeA['coordinate'][1] - placeB['coordinate'][1]) ** 2 )
        
        #buffer places and travel_time_matrix ?? maybe update every hours/days
        return (places,travel_time_matrix)
    
    def _process_places_for_MCTS(self, loc_data):
        df = pd.DataFrame.from_records(loc_data['data'], columns=loc_data['cols'])
        df['tags'] = df['tag_list'].str.split(', ')
        df['coordinate'] = list(zip(df['lat'],df['lng']))
        df['hours'] = list(zip(df['open_time'],df['close_time']))
        df['duration'] = 60 #temp
        df['durationH'] = df.duration/60 #temp
        df.drop(['price_level',"lat","lng","province","open_time","close_time","tag_list"],axis=1,inplace=True)
        df.rename(columns={'loc_id':'id'},inplace=True)
        df = df[['id','loc_name','coordinate','tags','hours','duration','durationH','rating',"open_day"]]
        df['rating'] = df['rating'].apply(lambda x : float(x))
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
            locations += [Location(id=loc_data[0],coords=Coordinates(lat=loc_data[1],lng=loc_data[2]))]
            
            search_ids[loc_data[0]] = []
            for loc_data_B in locations_data:
                if loc_data != loc_data_B:
                    search_ids[loc_data[0]] += [loc_data_B[0]]
        
        return locations, search_ids
    
if __name__ == "__main__":
    data_processor = dataProcesser()
    print(data_processor.get_MCTS_data())