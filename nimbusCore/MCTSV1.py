def generate_plan(places : list, travel_time_matrix :dict, tags : list, food : bool):
    wait_half_hour = {
        'loc_id': 0,
        'loc_name': 'wait_half_hour',
        'coordinate': (0,0),
        'tags': ['wait'],
        'hours': (0,24),
        'price_level':0,
        'est_time_stay':30,
        'rating':0,
        'open_day':'all',
    }
    
    places.append(wait_half_hour)
    
    def get_travel_time(start,end):
        pass
    
    class node():
        def __init__(self):
            pass
        
    
    pass