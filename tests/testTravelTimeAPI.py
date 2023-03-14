from context import travelTimeAPI, secret
import unittest


class TestTravelTimeAPI(unittest.TestCase):

	
	def setUp(self):
		self.ttapi = travelTimeAPI.travelTimeAPI()

	def tearDown(self):
		del self.ttapi

	# def test_api(self):
		# print(self.ttapi.getDistanceMetrix(None,None))

if __name__ == "__main__":
	unittest.main()