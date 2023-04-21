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
        self.allTags = self.dataProcessor.db.get_all_tags()
        self.travel_plan_dict = {}

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

    def travel_plan(self, start_date: datetime, end_date: datetime, tags: list,  budget: int, travel_method: list, trip_pace: int, must_add: list = []):
        delta = end_date - start_date
        date_list = [start_date + timedelta(days=i)
                     for i in range(delta.days + 1)]
        dayRange = [date.strftime('%a').lower() for date in date_list]
        POI_dict_day_of_week = deepcopy(self.POI_dict_day_of_week)
        travel_plan = []
        # travel_trees = []
        for day in dayRange:
            POI_dict_day_of_week[day] = self._remove_duplicate(POI_dict_day_of_week[day], travel_plan)
            travel_day, tree_root = self._travel_day(POI_dict_day_of_week[day],tags,budget, travel_method, trip_pace)
            travel_plan.append(travel_day)
            # travel_trees.append(tree_root)
        
        trip_id = uuid.uuid4().hex
        def del_this():
            del self.travel_plan_dict[trip_id]
        self.travel_plan_dict[trip_id] = {
        #     'root': tree_root,
            'travel_plan': travel_plan,
            'threading' : threading.Timer(1800, del_this),
            'del_method' : del_this(),
        }

        return travel_plan, trip_id
    
    def alternative_place(self, uuid , place, date : datetime):
        
        if uuid not in self.travel_plan_dict:
            return 'plan deleted',400
        
        self.travel_plan_dict[uuid]['threading'].cancel()
        self.travel_plan_dict[uuid]['threading'] = threading.Timer(1800, self.travel_plan_dict[uuid]['del_method'])

        for travel_day in self.travel_plan_dict[uuid]['travel_plan']:
            for i, feature in enumerate(travel_day):
                if feature['type'] == 'locations' and feature['loc_id'] == place:
                    if i == 0:
                        start = 'start'
                    else:
                        start = travel_day[i-2]['loc_id']
                    middle = travel_day[i]['loc_id']
                    if i < len(travel_day):
                        end = travel_day[i+2]['loc_id']
                    else:
                        end = 'end'
                        
        day = date.day
                        
        POI_dict_day_of_week = deepcopy(self.POI_dict_day_of_week)
        return alternative_place(start, middle, end, self.walking_time_matrix, self._remove_duplicate(POI_dict_day_of_week[day], self.travel_plan_dict[uuid]['travel_plan']))
    
    @staticmethod
    def _remove_duplicate(places: list, travel_plan: list):
        used_place = []
        for travel_day in travel_plan:
            for feature in travel_day:
                if feature['type'] == 'locations':
                    used_place += [int(feature['loc_id'])]
        return [d for d in places if d["loc_id"] not in used_place]

    def _travel_day(self,filtered_POI, tags, budget, travel_method: list, trip_pace: int):
        return generatePlan(filtered_POI, self.allTags,self.driving_time_matrix,self.walking_time_matrix, tags, budget, travel_method, trip_pace, False)