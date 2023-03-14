from context import dbManager, secret
import unittest


class TestdbManager(unittest.TestCase):

	
	def setUp(self):
		self.db = dbManager.dbMan()

	def tearDown(self):
		del self.db

	def test_connection(self):
		self.assertEqual(self.db.test_connection(),True)
 
if __name__ == "__main__":
    unittest.main()