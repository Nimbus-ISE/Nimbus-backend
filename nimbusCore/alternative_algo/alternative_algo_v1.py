from datetime import timedelta

def alternative_place(start, middle, end, tt_mat, the_rest, est_time_stay_dict, start_time, filtered_loc_id):
    plan_segment = []
    new_middle = sorted({key:value for key, value in tt_mat[middle].items() if key in filtered_loc_id}, key=lambda k: tt_mat[middle][k])[:3]
    for poi in new_middle:
        tmp = []
        time_now = start_time
        if not start == 'start':
            tmp.append([{
                "type": "travel_dur",
                "travel_time": tt_mat[int(start)][int(poi)]
            }])
            time_now += timedelta(seconds=tt_mat[int(start)][int(poi)])
        tmp.append([{
                "type": "locations",
                "loc_id": str(poi),
                "arrival_time": time_now.strftime("%H:%M:%S"),
                "leave_time": (time_now + timedelta(minutes=est_time_stay_dict[poi])).strftime("%H:%M:%S")
            }])
        time_now += timedelta(seconds=est_time_stay_dict[poi])

        
        place_b4 = end
        for place in the_rest:
            tmp.append({
                "type": "travel_dur",
                "travel_time": tt_mat[int(place_b4)][int(place)]
            })
            tmp.append({
                "type": "locations",
                "loc_id": place,
                "arrival_time": (time_now + timedelta(seconds=tt_mat[int(place_b4)][int(place)])).strftime("%H:%M:%S"),
                "leave_time": (time_now + timedelta(seconds=tt_mat[int(place_b4)][int(place)])) + timedelta(minutes=est_time_stay_dict[place]).strftime("%H:%M:%S")
            })
            time_now += timedelta(seconds=tt_mat[int(place_b4)][int(place)] + est_time_stay_dict[place])
            place_b4 = place
        if len(the_rest) > 0:
            tmp.pop(-1)
        
        plan_segment.append(tmp)
    return plan_segment