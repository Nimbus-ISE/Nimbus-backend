from context import travelTimeAPI, secret, dbManager

ttapi = travelTimeAPI.travelTimeAPI()
print(ttapi.getDistanceMetrix(None,None))