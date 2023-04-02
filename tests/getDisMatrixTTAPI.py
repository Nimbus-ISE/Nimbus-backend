from context import *
import json
from datetime import datetime, timedelta
import pytz
from traveltimepy import Location, Coordinates, PublicTransport, Property, FullRange, TravelTimeSdk, Driving
from dotenv import dotenv_values
import os
import math
import asyncio

secret = dotenv_values(dotenv_path=os.path.realpath(
    os.path.dirname(__file__)) + '\..\.env')

dp = processData.dataProcesser()
locations, search_ids = dp.get_places_for_travelTimeAPI()
del dp

async def main():
    sdk = TravelTimeSdk(app_id=secret['tt_app_id'], api_key=secret['tt_api_key'])
    
    async def getDistanceMetrix(POI, transport, time : datetime):
        results = []

        sliced_search_ids = [{k: search_ids[k] for k in list(search_ids.keys())[i:i+10]} for i in range(0, len(search_ids), 10)]

        
        for ten_search_ids in sliced_search_ids:
            results += [await sdk.time_filter_async(
                                        locations=locations,
                                        search_ids=ten_search_ids,
                                        # search_ids=sliced_search_ids[0],
                                        departure_time=time,
                                        travel_time=3600,
                                        transportation=Driving(),
                                        properties=[Property.TRAVEL_TIME],
                                        range=FullRange(enabled=True, max_results=3, width=600))]

        return results
    tz = pytz.timezone('Asia/Bangkok')
    dt = datetime.now(tz).replace(hour=12, minute=0, second=0, microsecond=0)

    next_monday = dt + timedelta(days=(7 - dt.weekday()))

    res = await getDistanceMetrix([],[],next_monday)

    with open('dis_matrix.txt', 'w') as outfile:
        try:
            json.dump(res, outfile)
        except TypeError:
            outfile.write(str(res))

    
# https://stackoverflow.com/questions/45600579/asyncio-event-loop-is-closed-when-getting-loop
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())