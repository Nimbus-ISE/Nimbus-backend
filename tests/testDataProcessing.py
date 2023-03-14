from context import processData, secret
import unittest


class TestProcessData(unittest.TestCase):

	
	def setUp(self):
		self.dataProcessor = processData.dataProcesser()

	def tearDown(self):
		del self.dataProcessor

if __name__ == "__main__":
    unittest.main()