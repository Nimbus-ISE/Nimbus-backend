from datetime import datetime
from traveltimepy import Location, Coordinates, PublicTransport, Property, FullRange, TravelTimeSdk, Driving
from dotenv import dotenv_values
import os
from .processData import dataProcesser
import math

secret = dotenv_values(dotenv_path=os.path.realpath(os.path.dirname(__file__)) + '\..\.env')

class travelTimeAPI():
    
    
	def __init__(self) -> None:
		self.sdk = TravelTimeSdk(app_id=secret['tt_app_id'], api_key=secret['tt_api_key'])
		self.dp = dataProcesser()

	# POI and transport are 
	def getDistanceMetrix(self, POI, transport, time : datetime):
		locations, search_ids = self.dp.get_places_for_travelTimeAPI()
  
		results = []

		sliced_search_ids = [{k: search_ids[k] for k in list(search_ids.keys())[i:i+10]} for i in range(0, len(search_ids), 10)]

		
		for ten_search_ids in sliced_search_ids:

			results += self.sdk.time_filter(
    									locations=locations,
    									search_ids=ten_search_ids,
    									departure_time=datetime.now(),
    									travel_time=3600,
    									transportation=Driving(),
    									properties=[Property.TRAVEL_TIME],
    									range=FullRange(enabled=True, max_results=3, width=600))

		return results