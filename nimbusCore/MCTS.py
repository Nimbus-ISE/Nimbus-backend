from .processData import dataProcesser
import pickle
from datetime import datetime, timedelta
from copy import deepcopy
from mcts_algo import generatePlan
from alternative_algo import alternative_place
import uuid
import threading
import time

data_file = "place_dat.txt"


class MCTS():

    def __init__(self):
        self.dataProcessor = dataProcesser()
        self.POI_dict_day_of_week, self.driving_time_matrix, self.walking_time_matrix = self.dataProcessor.get_MCTS_data()
        self.allTags = [tag[0] for tag in self.dataProcessor.db.get_all_tags()]

    def update_data(self):
        #TODO trigger update for ttapi if tt not include all place
        self.POI_dict_day_of_week, self.driving_time_matrix, self.walking_time_matrix = self.dataProcessor.get_MCTS_data()
        return "OK"

    # deprecated?
    def save_data(self):
        file = open(data_file, "wb")
        pickle.dump((self.POI_dict_day_of_week, self.driving_time_matrix), file)
        file.close()

    # deprecated?
    def load_data(self):
        with open(data_file, 'rb') as f:
            (self.POI_dict_day_of_week, self.driving_time_matrix) = pickle.load(f)

    def demo_travel_plan(self):
        with open('demo_plan.json', 'r', encoding='utf8') as f:
            return f.read()

    def travel_plan(self, start_date: datetime, end_date: datetime, tags: list,  budget: int, travel_method: list, trip_pace: int, must_include: int):
        delta = end_date - start_date
        date_list = [start_date + timedelta(days=i)
                     for i in range(delta.days + 1)]
        dayRange = [date.strftime('%a').lower() for date in date_list]
        POI_dict_day_of_week = deepcopy(self.POI_dict_day_of_week)
        travel_plan = []
        for day in dayRange:
            POI_dict_day_of_week[day] = self._remove_duplicate(POI_dict_day_of_week[day], travel_plan)
            travel_day, tree_root = self._travel_day(POI_dict_day_of_week[day],tags,budget, travel_method, must_include, trip_pace)
            travel_plan.append(travel_day)
            # travel_trees.append(tree_root)
            del tree_root
        
        trip_id = uuid.uuid4().hex

        return {'travel_plan' : travel_plan,'trip_id' : trip_id}
    
    def alternative_place(self, trip , place, day):

        found = False
        the_rest = []
        trip_day_before = []
        for travel_day in trip:
            for i, feature in enumerate(travel_day):
                
                if found and feature['type'] == 'locations':
                    the_rest.append(feature['loc_id'])
            
                if feature['type'] == 'locations' and str(feature['loc_id']) == str(place):
                    if i == 0:
                        start = 'start'
                        start_time = feature['arrival_time']
                    else:
                        start = travel_day[i-2]['loc_id']
                        start_time = travel_day[i-2]['arrival_time']
                    middle = travel_day[i]['loc_id']
                    if i + 2 < len(travel_day):
                        end = travel_day[i+2]['loc_id']
                    else:
                        end = 'end'
                    found = True
                if not found:
                    trip_day_before.append(feature)
                
                    
            if found:
                break
            else:
                trip_day_before = []
        if not found:
            raise Exception('loc id not found in trip')
        
        if len(trip_day_before) > 0:
            trip_day_before.pop(-1)

        day = datetime.fromisoformat(day).strftime('%a').lower()
                        
        POI_dict_day_of_week = deepcopy(self.POI_dict_day_of_week)
        filtered_place = self._remove_duplicate(POI_dict_day_of_week[day],trip)
        filtered_place_id = [place['loc_id'] for place in filtered_place]
        est_time_stay_dict = {place['loc_id'] : place['est_time_stay'] for place in POI_dict_day_of_week[day]}

        print(trip)
        print(filtered_place_id)

        return alternative_place(start, middle, end, self.walking_time_matrix, the_rest, est_time_stay_dict, datetime.strptime(start_time, "%H:%M:%S"),filtered_place_id, trip_day_before)
    
    @staticmethod
    def _remove_duplicate(places: list, travel_plan: list):
        used_place = []
        for travel_day in travel_plan:
            for feature in travel_day:
                if feature['type'] == 'locations':
                    used_place += [int(feature['loc_id'])]
        return [d for d in places if d["loc_id"] not in used_place]

    def _travel_day(self,filtered_POI, tags, budget, travel_method: list, trip_pace: int, must_include: str):
        return generatePlan(filtered_POI, self.allTags,self.driving_time_matrix,self.walking_time_matrix, tags, budget, travel_method, must_include, trip_pace, False)