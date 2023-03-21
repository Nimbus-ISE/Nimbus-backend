from datetime import datetime
from traveltimepy import Location, Coordinates, PublicTransport, Property, FullRange, TravelTimeSdk
from dotenv import dotenv_values
import os
from .processData import dataProcesser

if os.environ.get("VERCEL"):
    secret = os.environ
else:
	secret = dotenv_values(os.path.dirname(os.path.realpath(__file__)) + '/../.env')


class travelTimeAPI():
    
    
	def __init__(self) -> None:
		self.sdk = TravelTimeSdk(app_id=secret['tt_app_id'], api_key=secret['tt_api_key'])
		self.dat_process = dataProcesser()

	def getDistanceMetrix(self, POI, transport):
		locations, search_ids = self.dat_process.get_places_for_travelTimeAPI()

		# travel time api matrix allow 20 x 10000 (check doc again can't rmb)
		# need to cut search_ids in block of 20
  
		results = []

		# while len(search_ids) > 0:

		results += self.sdk.time_filter(
    									locations=locations,
    									search_ids=search_ids,
    									departure_time=datetime.now(),
    									travel_time=3600,
    									transportation=PublicTransport(type='bus'),
    									properties=[Property.TRAVEL_TIME],
    									full_range=FullRange(enabled=True, max_results=3, width=600))
			# search_ids = search_ids[20:]

		return results