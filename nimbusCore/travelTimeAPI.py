from datetime import datetime
import requests
from traveltimepy import Location, Coordinates, PublicTransport, Property, FullRange, TravelTimeSdk, Driving
from dotenv import dotenv_values
import os
import math
import sys
import json

sys.path.append(os.path.realpath(os.path.dirname(__file__)))

from processData import dataProcesser

secret = dotenv_values(dotenv_path=os.path.join(os.path.realpath(
    os.path.dirname(__file__)),'..','.env'))


class travelTimeAPI():

    def __init__(self) -> None:
        self.sdk = TravelTimeSdk(
            app_id=secret['tt_app_id'], api_key=secret['tt_api_key'])
        self.dp = dataProcesser()

    # POI and transport are
    def getDistanceMetrix(self, POI, transport, time: datetime):
        locations, search_ids = self.dp.get_places_for_travelTimeAPI()

        results = []

        sliced_search_ids = [{k: search_ids[k] for k in list(
            search_ids.keys())[i:i+10]} for i in range(0, len(search_ids), 10)]

        for ten_search_ids in sliced_search_ids:

            results += self.sdk.time_filter(
                locations=locations,
                search_ids=ten_search_ids,
                departure_time=time,
                travel_time=3600,
                transportation=Driving(),
                properties=[Property.TRAVEL_TIME],
                range=FullRange(enabled=True, max_results=3, width=600))

        return results

    def getDistanceMatrixRestful(self):
        payloads = self.dp.get_json_for_ttapi()

        headers = {
            'Host': 'api.traveltimeapp.com',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Application-Id': secret['tt_app_id'],
            'X-Api-Key': secret['tt_api_key']
        }

        response = []
        url = "https://api.traveltimeapp.com/v4/time-filter"
        for payload in payloads:

            response.append(requests.request(
                "POST", url, headers=headers, data=json.dumps(payload)).text)

        # result = {}
        # data = json.loads(response)
        # data = [json.loads(datum) for datum in data]
        # for res in data:
        #     for onexn_mat in res['results']:
        #         result[onexn_mat['search_id'].split('.')[1]] = {}
        #         for location in onexn_mat['locations']:
        #             result[int(onexn_mat['search_id'].split('.')[1])][int(location['id'].split('.')[1])] = location['properties'][0]['travel_time'] / 60
        with open("dis_mat_post.json", "w") as text_file:
            text_file.write(json.dumps(response))


if __name__ == "__main__":
    ttapi = travelTimeAPI()
    ttapi.getDistanceMatrixRestful()
