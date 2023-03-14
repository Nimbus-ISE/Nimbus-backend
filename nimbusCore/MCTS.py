from .processData import dataProcesser
import pickle

data_file = "place_dat.txt"


class MCTS():


	def __init__(self):
		self.dataProcessor = dataProcesser()
		self.places, self.distance_matrix = self.dataProcessor.get_MCTS_data("mon")

	def update_data(self):
		self.places, self.distance_matrix = self.dataProcessor.get_MCTS_data("mon")

	def save_data(self):
		file = open(data_file, "wb")
		pickle.dump((self.places,self.distance_matrix), file)
		file.close()

	def load_data(self):
		with open(data_file, 'rb') as f:
			(self.places,self.distance_matrix) = pickle.load(f)

	def demo_travel_plan(self):
		with open('demo_itenary.bin', 'rb') as f:
			return pickle.load(f)

	def travel_plan(self,date_range,good_tags,bad_tags,must_add,start=None,end=None):
		return [{}]

	def _generate_score_matrix(self,good_tags,bad_tags):
		scoreMatrix = {}