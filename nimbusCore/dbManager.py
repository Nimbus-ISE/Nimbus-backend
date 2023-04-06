import psycopg2
from dotenv import dotenv_values
import os
import json

if os.environ.get("VERCEL"):
    secret = os.environ
else:
    secret = dotenv_values(dotenv_path=os.path.realpath(os.path.dirname(__file__)) + '\..\.env')


def checkConnection(func):
    def wrapper(self : dbMan, *args, **kwargs):
        if self.test_connection():
            self.start_connection()
        return func(self, *args, **kwargs)
    return wrapper

class dbMan():
    
    
    def __init__(self):
        self.start_connection()

    # def __die__(self):
    #     self.conn.close()
    #     self.cursor.close()
    
    def test_connection(self):
        return self.conn.closed == 0
    
    def start_connection(self):
        self.conn = psycopg2.connect(database=secret["database"],
                                host=secret["dbhost"],
                                user=secret["dbuser"],
                                password=secret["dbpassword"],
                                port=secret["dbport"],
                                sslmode='prefer'
                                )
        self.cursor = self.conn.cursor()
    
    @checkConnection
    def get_loc_columns(self):
        self.cursor.execute('Select * FROM location_data LIMIT 0')
        return [desc[0] for desc in self.cursor.description]

    @checkConnection
    def get_loc_data_by_day(self, day):
        self.cursor.execute("""SELECT loc_data_with_tag.LOC_ID,rating,LOC_NAME,TAG_LIST,LAT,lng,PRICE_LEVEL,est_time_stay,PROVINCE,operating_time.OPEN_DAY,operating_time.OPEN_TIME,operating_time.CLOSE_TIME FROM (SELECT LOCATION_DATA.LOC_ID,
                                	LOC_NAME,
                                	STRING_AGG(TAG_NAME,
                                		', ') AS TAG_LIST,
                                	LAT, lng,
                                	PRICE_LEVEL,
                                	PROVINCE,
                                    RATING,
                                    est_time_stay
                                FROM LOCATION_DATA
                                INNER JOIN BELONG_TO ON LOCATION_DATA.LOC_ID = BELONG_TO.LOC_ID
                                GROUP BY LOCATION_DATA.LOC_ID
                                ORDER BY LOC_ID) as loc_data_with_tag
                                LEFT JOIN OPERATING_TIME ON loc_data_with_tag.LOC_ID = OPERATING_TIME.LOC_ID
                                where open_day = %s and open_time != 'Close'""",
                                vars=(day.upper(),))
        return {'cols' : [desc[0] for desc in self.cursor.description], 'data' : self.cursor.fetchall()}
    
    @checkConnection
    def get_loc_data(self):
        self.cursor.execute("""SELECT loc_data_with_tag.LOC_ID,rating,LOC_NAME,TAG_LIST,LAT,lng,PRICE_LEVEL,est_time_stay,PROVINCE,operating_time.OPEN_DAY,operating_time.OPEN_TIME,operating_time.CLOSE_TIME FROM (SELECT LOCATION_DATA.LOC_ID,
                                	LOC_NAME,
                                	STRING_AGG(TAG_NAME,
                                		', ') AS TAG_LIST,
                                	LAT, lng,
                                	PRICE_LEVEL,
                                	PROVINCE,
                                    RATING,
                                    est_time_stay
                                FROM LOCATION_DATA
                                INNER JOIN BELONG_TO ON LOCATION_DATA.LOC_ID = BELONG_TO.LOC_ID
                                GROUP BY LOCATION_DATA.LOC_ID
                                ORDER BY LOC_ID) as loc_data_with_tag
                                LEFT JOIN OPERATING_TIME ON loc_data_with_tag.LOC_ID = OPERATING_TIME.LOC_ID
                                WHERE open_day is not null and open_time != 'Close'""")
        return {'cols' : [desc[0] for desc in self.cursor.description], 'data' : self.cursor.fetchall()}
    
    @checkConnection
    def get_all_tags(self):
        self.cursor.execute("""
                            SELECT * from tag
                            """)
        return self.cursor.fetchall()

    @checkConnection
    def get_travel_time_matrix(self):
        #TODO
        return {{}}

    @checkConnection
    def update_travel_time_matrix(self,dis_mat):
        #TODO
        pass

    @checkConnection
    def get_places_coordinate(self):
        self.cursor.execute("SELECT LOC_ID, LAT, lng FROM LOCATION_DATA where LAT is not NULL and LNG is not NULL")
        return self.cursor.fetchall()

if __name__ == "__main__":
    db = dbMan()
    print(db.get_loc_data_by_day('mon'))