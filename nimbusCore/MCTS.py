from .processData import dataProcesser
import pickle
from datetime import datetime, timedelta
from copy import deepcopy
from mcts_algo import generatePlan

data_file = "place_dat.txt"


class MCTS():

    def __init__(self):
        self.dataProcessor = dataProcesser()
        self.POI_dict_day_of_week, self.distance_matrix = self.dataProcessor.get_MCTS_data()
        self.allTags = self.dataProcessor.db.get_all_tags()

    def update_data(self):
        #TODO trigger update for ttapi if tt not include all place
        self.POI_dict_day_of_week, self.distance_matrix = self.dataProcessor.get_MCTS_data()
        return "OK"

    # deprecated?
    def save_data(self):
        file = open(data_file, "wb")
        pickle.dump((self.POI_dict_day_of_week, self.distance_matrix), file)
        file.close()

    # deprecated?
    def load_data(self):
        with open(data_file, 'rb') as f:
            (self.POI_dict_day_of_week, self.distance_matrix) = pickle.load(f)

    def demo_travel_plan(self):
        with open('demo_plan.json', 'r', encoding='utf8') as f:
            return f.read()

    # def travel_plan_v1(self, start_date: datetime, end_date: datetime, tags: list, must_add: list = None):
    #     delta = end_date - start_date
    #     date_list = [start_date + timedelta(days=i)
    #                  for i in range(delta.days + 1)]
    #     dayRange = [date.strftime('%a').lower() for date in date_list]
    #     POI_dict_day_of_week = deepcopy(self.POI_dict_day_of_week)
    #     travel_plan = []
    #     for day in dayRange:
    #         self._remove_duplicate(POI_dict_day_of_week[day], travel_plan)
    #         travel_plan.append(self._travel_day(POI_dict_day_of_week[day],))

    #     return travel_plan

    # def _remove_duplicate(places: list, travel_plan: list):
    #     for travel_day in travel_plan:
    #         for used_place in travel_day:
    #             i = 0
    #             while i < len(places):
    #                 if int(places[i]['loc_id']) == int(used_place['loc_id']):
    #                     places.pop(i)
    #                 i += 1

    # def _travel_day(self, places, score_matrix: dict, startHour=8, endHour=18):
    #     pass

    def travel_plan(self, start_date: datetime, end_date: datetime, tags: list, must_add: list = None, budget: int = None, food: bool = False):
        return generatePlan(self.POI_dict_day_of_week['mon'], self.allTags, self.distance_matrix, tags, budget)
