def alternative_place(start, middle, end, tt_mat, the_rest, place_dict, start_time):
    plan_segment = []
    
    new_middle = sorted(tt_mat[middle], key=lambda k: tt_mat[middle][k])[:3]
    
    for poi in new_middle:
        tmp = []
        time_now = start
        if not start == 'start':
            tmp.append([{
                "type": "travel_dur",
                "travel_time": tt_mat[start][poi]
            }])
            time_now += tt_mat[start][poi]
        tmp.append([{
                "type": "locations",
                "loc_id": str(poi),
                "arrival_time": time_now,
                "leave_time": time_now + place_dict[poi]['est_time_stay']
            }])
        time_now += place_dict[poi]['est_time_stay']
        
        if not start == 'end':
            tmp.append([{
                "type": "travel_dur",
                "travel_time": tt_mat[poi][end]
            }])
            time_now += tt_mat[poi][end]
        place_b4 = end
        for place in the_rest:
            tmp.append({
                "type": "travel_dur",
                "travel_time": tt_mat[place_b4][place]
            })
            tmp.append({
                "type": "locations",
                "loc_id": place,
                "arrival_time": time_now + tt_mat[place_b4][place],
                "leave_time": time_now + tt_mat[place_b4][place] + place_dict[place]['est_time_stay']
            })
            place_b4 = place
        if len(the_rest) > 0:
            tmp.pop(-1)
        
        plan_segment.append(tmp)
    return plan_segment