from context import MCTS, secret
import unittest
import datetime


class TestMCTS(unittest.TestCase):

    def setUp(self):
        self.mcts = MCTS.MCTS()

    def tearDown(self):
        del self.mcts

    def test_demo_travel_plan(self):
        self.assertIsNotNone(self.mcts.demo_travel_plan())

    def test_import_data(self):
        self.assertEqual(self.mcts.update_data(), "OK")
        
    def test_travel_plan(self):
        startDate = datetime.datetime(2023,5,20).date()
        endDate = datetime.datetime(2020,5,22).date()
        goodTags = []
        badTags = []
        mustAdd = []
        start = None
        end = None
        self.assertIsNotNone(self.mcts.travel_plan(startDate,endDate,goodTags,badTags,mustAdd,start,end))

if __name__ == "__main__":
    unittest.main()
