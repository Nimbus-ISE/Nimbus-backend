from .dbManager import dbMan
import pandas as pd
from traveltimepy import Location, Coordinates


class dataProcesser():
    
    
    def __init__(self,db = dbMan()):
        self.db = db
        
    def get_MCTS_data(self,day):
        loc_data = self.db.get_loc_data_by_day(day)
        df = pd.DataFrame.from_records(loc_data['data'], columns=loc_data['cols'])
        df['tags'] = df['tag_list'].str.split(', ')
        df['coordinate'] = list(zip(df['lat'],df['long']))
        df['hours'] = list(zip(df['open_time'],df['close_time']))
        df['type'] = ["tourist spot"] * len(df)
        df['duration'] = 60 #temp
        df['durationH'] = df.duration/60 #temp
        df.drop(['est_loc_price',"loc_name","lat","long","province","open_day","open_time","close_time","tag_list"],axis=1,inplace=True)
        df.rename(columns={'loc_id':'name'},inplace=True)
        df = df[['name','coordinate','tags','type','hours','duration','durationH','rating']]
        
        places = df.to_dict('records')
        
        #use travel time api / db
        travel_time_matrix = {}
        
        
        #buffer places and travel_time_matrix ?? maybe update every hours/days
        return (places,travel_time_matrix)
    
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