from .MCTS import MCTS


class TripBuilder():

    def __init__(self):
        self.mcts = MCTS()

    def generate_trip_mcts(self, start_date, end_date, tags, must_include, budget, travel_method: list, trip_pace: int):
        return self.mcts.travel_plan(start_date, end_date, tags, budget, travel_method, trip_pace, must_include)

    def demo_trip(self):
        return self.mcts.demo_travel_plan()
    
    def get_alternative_place(self, trip,  place, day):
        return self.mcts.alternative_place(trip, place, day)

    def refetch_data(self):
        try:
            self.mcts.update_data()
        except:
            return False
        return True
