from .MCTS import MCTS


class TripBuilder():

    def __init__(self):
        self.mcts = MCTS()

    def generate_trip_mcts(self, start_date, end_date, tags, must_add, budget):
        return self.mcts.travel_plan(start_date, end_date, tags, must_add, budget)

    def demo_trip(self):
        return self.mcts.demo_travel_plan()

    def refetch_data(self):
        try:
            self.mcts.update_data()
        except:
            return False
        return True
