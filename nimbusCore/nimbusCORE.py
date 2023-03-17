from .MCTS import MCTS


class TripBuilder():
   

    def __init__(self):
        self.mcts = MCTS()

    def generate_trip_mcts(self,date_range="1",good_tags=(),bad_tags=(),must_add=()): # ("12/12/2020","15/12/2020")
        return self.mcts.travel_plan(date_range=date_range,good_tags=good_tags,bad_tags=bad_tags,must_add=must_add)

    def demo_trip(self):
        return self.mcts.demo_travel_plan()

    def refetch_data(self):
        try:
            self.mcts.update()
        except:
            return False
        return True