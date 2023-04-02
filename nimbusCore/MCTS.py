from .processData import dataProcesser
import pickle
from datetime import datetime, timedelta

data_file = "place_dat.txt"


class MCTS():

    def __init__(self):
        self.dataProcessor = dataProcesser()
        self.POI_dict_day_of_week, self.distance_matrix = self.dataProcessor.get_MCTS_data()
        self.allTags = self.dataProcessor.db.get_all_tags()

    #for daily / weekly / data update
    def update_data(self):
        # do try except??
        self.POI_dict_day_of_week, self.distance_matrix = self.dataProcessor.get_MCTS_data()
        return "OK"

    def save_data(self):
        file = open(data_file, "wb")
        pickle.dump((self.POI_dict_day_of_week, self.distance_matrix), file)
        file.close()

    def load_data(self):
        with open(data_file, 'rb') as f:
            (self.POI_dict_day_of_week, self.distance_matrix) = pickle.load(f)


    def demo_travel_plan(self):
        with open('demo_plan.json', 'r', encoding='utf8') as f:
            return f.read()

    # TOTEST
    def travel_plan(self, start_date : datetime, end_date : datetime, tags : list, must_add : list = None): #, starting_POI=None, ending_POI=None):
        delta = end_date - start_date
        date_list = [start_date + timedelta(days=i) for i in range(delta.days + 1)]
        dayRange = [date.strftime('%a').lower() for date in date_list]
        POI_dict_day_of_week = self.POI_dict_day_of_week
        travel_plan = []
        for day in dayRange:
            self._remove_duplicate(POI_dict_day_of_week[day],travel_plan)
            travel_plan.append(self._travel_day(POI_dict_day_of_week[day],))
        
        return [{}]
    
    # TOTEST
    def _remove_duplicate(self,places : list,travel_plan : list):
        for travel_day in travel_plan:
            for i in range(len(places)):
                for used_place in travel_day:
                    if places[i]['loc_id'] == used_place['loc_id']:
                        places.pop(i)
            
    
    # TODO
    def _travel_day(self, places, score_matrix : dict, startHour = 8, endHour = 18):
        
        return [{}]
    
    #TODO
    def _generate_scoreMatrix(self, places, good_tags, bad_tags, distance_martix, time_modifier):
        # { loc_id : { loc_id : score, }, }
        
        score_matrix = {}