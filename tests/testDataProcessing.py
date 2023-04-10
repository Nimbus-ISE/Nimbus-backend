from context import processData, secret
import unittest


class TestProcessData(unittest.TestCase):

    def setUp(self):
        self.dataProcessor = processData.dataProcesser()

    def tearDown(self):
        del self.dataProcessor

    def test_get_MCTS_data(self):
        print(self.dataProcessor.get_MCTS_data_by_day('mon', transport='driving'))


if __name__ == "__main__":
    unittest.main()
