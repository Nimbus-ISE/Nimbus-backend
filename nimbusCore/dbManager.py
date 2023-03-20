import psycopg2
from dotenv import dotenv_values
import os
import json


if os.environ.get("VERCEL"):
    secret = os.environ
else:
    secret = dotenv_values(os.path.dirname(os.path.realpath(__file__)) + '/../.env')


class dbMan():
    
    
    def __init__(self):
        self.conn = psycopg2.connect(database=secret["database"],
                                host=secret["dbhost"],
                                user=secret["dbuser"],
                                password=secret["dbpassword"],
                                port=secret["dbport"],
                                sslmode='prefer',
                                options=secret["dbhost"].split(".")[0]
                                )
        self.cursor = self.conn.cursor()

    def __die__(self):
        self.conn.close()
        self.cursor.close()
    
    # def get_place_for_MCTS(self):
    #     self.cursor.execute('select loc_id,loc_name,lat,long from location_data')
    #     return self.cursor.fetchall()
    
    def test_connection(self):
        return self.conn.closed == 0
    
    def get_loc_columns(self):
        self.cursor.execute('Select * FROM location_data LIMIT 0')
        return [desc[0] for desc in self.cursor.description]

    def get_loc_data_by_day(self, day):
        self.cursor.execute("""SELECT loc_data_with_tag.LOC_ID,rating,LOC_NAME,TAG_LIST,LAT,long,EST_LOC_PRICE,PROVINCE,operating_time.OPEN_DAY,operating_time.OPEN_TIME,operating_time.CLOSE_TIME FROM (SELECT LOCATION_DATA.LOC_ID,
                                	LOC_NAME,
                                	STRING_AGG(TAG_NAME,
                                		', ') AS TAG_LIST,
                                	LAT, long,
                                	EST_LOC_PRICE,
                                	PROVINCE,
                                    rating
                                FROM LOCATION_DATA
                                INNER JOIN BELONG_TO ON LOCATION_DATA.LOC_ID = BELONG_TO.LOC_ID
                                GROUP BY LOCATION_DATA.LOC_ID
                                ORDER BY LOC_ID) as loc_data_with_tag
                                LEFT JOIN OPERATING_TIME ON loc_data_with_tag.LOC_ID = OPERATING_TIME.LOC_ID
                                where open_day = %s""",
                                vars=(day.upper(),))
        return {'cols' : [desc[0] for desc in self.cursor.description], 'data' : self.cursor.fetchall()}

    def get_travel_time_matrix(self):
        return {{}}

    def update_travel_time_matrix(self):
        return

    def get_places_coordinate(self):
        self.cursor.execute("SELECT LOC_NAME, LAT, long FROM LOCATION_DATA where LAT is not NULL and LONG is not NULL")
        return self.cursor.fetchall()

if __name__ == "__main__":
    db = dbMan()
    print(db.get_loc_data_by_day('mon'))