from context import MCTS, secret
import unittest


class TestMCTS(unittest.TestCase):

	
	def setUp(self):
		self.mcts = MCTS.MCTS()

	def tearDown(self):
		del self.mcts

	def test_demo_travel_plan(self):
		self.assertIsNotNone(self.mcts.demo_travel_plan())


if __name__ == "__main__":
	unittest.main()