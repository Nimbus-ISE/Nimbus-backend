# # user parameters

import random
import time
import math
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import datetime
import copy

# have this before importing helper so no import error
sys.path.append(os.path.realpath(os.path.dirname(__file__)))

from helper import timeStringToTime


def generatePlan(places, tags, distanceMatrix_from_above, userSelectedTags, budget):
    distanceMatrix = copy.deepcopy(distanceMatrix_from_above)
    
    # Algo params
    startHour = datetime.datetime(2023, 4, 9, 9, 0) # year month day hour min
    endHour = datetime.datetime(2023, 4, 9, 16, 0)

    searchCycle = 10_000
    # C is bias to explore new route
    # higher C = explore more = run longer
    C = 5
    tagWeight = 2
    # TODO
    timeModifier = 1
    # time spend ** modifier
    # higher = prefer longer distance but better place score
    # lower = prefer shorter distance but less place score

    # TODO wrap in another function file
    # convert openHours, est_time_stay into datetime format
    for i in range(len(places)):
        places[i]['hours'] = (timeStringToTime(places[i]['hours'][0]), timeStringToTime(places[i]['hours'][1]))
        places[i]['est_time_stay'] = datetime.timedelta(minutes=places[i]['est_time_stay'])

    # convert to datetime delta
    for start in distanceMatrix.keys():
        for dest in distanceMatrix[start].keys():
            distanceMatrix[start][dest] = datetime.timedelta(minutes=distanceMatrix[start][dest])

    # generate place dis
    placesDict = {place['loc_id']: place for place in places}

    # # calculate score
    placesTagsMatrix = np.array([[tag in place['tags'] for tag in tags] for place in places])
    tagsMatrix = tagWeight * np.array([(tag in userSelectedTags) for tag in tags]).reshape((len(tags), 1))

    # each location tags score
    tagScores = list(np.matmul(placesTagsMatrix, tagsMatrix).reshape(len(places)))

    # each location rating score
    ratingScores = np.array([place['rating'] for place in places])
    totalScores = tagScores + ratingScores

    placeScores = {}
    for i in range(len(totalScores)):
        placeScores[places[i]['loc_id']] = totalScores[i]

    # scoring criteria: tag + rating + distance
    placeScoresMatrix = {}
    for x in places:
        placeScoresMatrix[x['loc_id']] = {}

        for y in places:
            if 'wait' in x['tags'] or 'wait' in y['tags'] or x['loc_id'] == y['loc_id']:
                placeScoresMatrix[x['loc_id']][y['loc_id']] = 0
            else:
                placeScoresMatrix[x['loc_id']][y['loc_id']] = placeScores[y['loc_id']] 
                    # / (1 + (distanceMatrix[x['loc_id']][y['loc_id']])) # TODO remove distance cal for now

    def getTravelDuration(x, y):
        if x == y or 'wait' in [x, y]:
            return datetime.timedelta() # 0

        return distanceMatrix[x][y]
    
    # # MCTS ALGORITHM
    class Node:
        def __init__(self, place, child=[], parent=None):
            self.loc_id = place['loc_id']
            self.est_time_stay = place['est_time_stay']

            self.child = child
            self.parent = parent

            self.totalReward = 0
            self.visitCount = 0
            # self.nodeReward = None # unused

            if parent is not None:
                self.travelDuration = getTravelDuration(self.loc_id, parent.loc_id)  # time to get here
                self.arrivalTime = parent.leaveTime + self.travelDuration
                self.leaveTime = parent.leaveTime + self.travelDuration + self.est_time_stay
            else: # first place
                self.travelDuration = 0
                self.leaveTime = startHour + self.est_time_stay

    def calcExploitScore(startNode, destNode):
        if startNode.loc_id == 'wait' and destNode != 'wait':
            while startNode.loc_id == 'wait':
                startNode = startNode.parent

        return placeScoresMatrix[startNode.loc_id][destNode.loc_id]

    def calcExploreScore(startNode, destNode):
        return C * math.sqrt(math.log(startNode.visitCount + 1) / (destNode.visitCount + 1))

    def selection(startNode):
        index = 0
        output_loc_idx = 0
        max = float('-inf')

        # get highest child
        for destNode in startNode.child:
            score = (calcExploitScore(startNode, destNode) + calcExploreScore(startNode, destNode))
            if max < score:
                output_loc_idx = index
                max = score
            index += 1

        return startNode.child[output_loc_idx]

    def backPropagation(leaf):
        node = leaf
        totalReward = placeScoresMatrix[node.parent.loc_id][node.loc_id]
        node.visitCount += 1
        while node.parent.parent is not None:
            node = node.parent
            totalReward += placeScoresMatrix[node.parent.loc_id][node.loc_id]
            node.visitCount += 1

        # update totalReward
        node = leaf
        node.totalReward += totalReward
        while node.parent is not None:
            node = node.parent
            node.totalReward += totalReward

    # to get the best path from the Monte Carlo Tree
    def getOptimalPath(itTree):
        pointer = itTree

        itArr = [] # itinerary list
        # starting place
        itArr.append({'type': 'locations',
                      'loc_id': pointer.loc_id,
                      'arrival_time': startHour.time().isoformat(),
                      'leave_time': pointer.leaveTime.time().isoformat(),
                      })

        while len(pointer.child) != 0:
            # find max child of all children
            maxScore = float('-inf')
            index = 0
            for i in range(len(pointer.child)):
                if pointer.child[i].visitCount > 0 and pointer.child[i].totalReward / pointer.child[i].visitCount > maxScore:
                    index = i
                    maxScore = pointer.child[i].totalReward / pointer.child[i].visitCount
            pointer = pointer.child[index] # get max child node

            # append max child place to itinerary
            # append travel duration
            itArr.append({'type': 'travel_dur',
                        'travel_dur': pointer.travelDuration.seconds
                        })
            # append next location
            itArr.append({'type': 'locations',
                        'loc_id': pointer.loc_id,
                        'arrival_time': pointer.arrivalTime.time().isoformat(),
                        'leave_time': pointer.leaveTime.time().isoformat(),
                        })

        return itArr

    # # Main function
    def mcts(cycle, budget=4, tripPace=2):
        def childrenNodeExpansion(placeNode, availablePlace):
            if len(placeNode.child) == 0 and len(availablePlace) != 0:
                placeNode.child = [Node(p, [], placeNode) for p in availablePlace]

        def takeFood(place, pointer, hadFood):
            # find food place after 11.00
            foodHours = datetime.time(11)

            if pointer.leaveTime.time() < foodHours or hadFood:  # if not food time yet or already had food
                return 'Restaurant' not in place['tags']
            
            return 'Restaurant' in place['tags']

        def isLowerThanBudget(place, selectedPlace, budget):
            curCost = [placesDict[loc_loc_id]['price_level'] for loc_loc_id in selectedPlace]

            return ((sum(curCost) + place['price_level']) / (len(selectedPlace) + 1)) <= budget

        def getAvailablePlace(pointer, hadFood, budget):
            includeLunch = True
            if includeLunch:
                availPlace = [place for place in places if
                            # not chosen
                            place['loc_id'] not in selectedPlace
                            # money budget
                            and isLowerThanBudget(place, selectedPlace, budget)
                            # time budget
                            and pointer.leaveTime + getTravelDuration(pointer.loc_id, place['loc_id']) + place['est_time_stay'] < endHour
                            # after open hour
                            and (pointer.leaveTime + getTravelDuration(pointer.loc_id, place['loc_id'])).time() >= place['hours'][0]
                            # before close hour
                            and (pointer.leaveTime + getTravelDuration(pointer.loc_id, place['loc_id']) + place['est_time_stay']).time() <= place['hours'][1]
                            # food or not
                            and takeFood(place, pointer, hadFood)
                            ]

                return availPlace

        # TODO : rn best score -> first place hehe
        max_key = max(placeScores, key=placeScores.get)
        firstPlace = placesDict[max_key]

        itTree = Node(firstPlace)
        selectedPlace = [firstPlace['loc_id']]
        # generate children nodes for the firstPlace
        availablePlace = getAvailablePlace(itTree, False, budget)
        childrenNodeExpansion(itTree, availablePlace)

        for _ in range(0, cycle):
            # simulation
            pointer = itTree
            selectedPlace = []
            hadFood = False

            while pointer.child != []:
                # selection
                pointer = selection(pointer)
                if pointer.loc_id != 'wait':
                    selectedPlace += [pointer.loc_id]
                if 'Restaurant' in placesDict[pointer.loc_id]['tags']:
                    hadFood = True
                # expansion
                if pointer.child == []:
                    availablePlace = getAvailablePlace(pointer, hadFood, budget)
                    childrenNodeExpansion(pointer, availablePlace)

            # back propagation
            backPropagation(pointer)

        curCost = [placesDict[loc_id]['price_level'] for loc_id in selectedPlace]
        print('avg price_level:', sum(curCost) / (len(selectedPlace)))

        return getOptimalPath(itTree)

    # print graph for debug
    # def printGraph():
    #     # print(itArr)
    #     x = [place[0]['coordinate'][0] for place in itArr]
    #     y = [place[0]['coordinate'][1] for place in itArr]
    #     placeName = [place[0]['loc_name'] for place in itArr]
    #     placeTags = [place[0]['tags'] for place in itArr]
    #     leaveTime = [round(place[1], 2) for place in itArr]

    #     fig, ax = plt.subplots()
    #     ax.plot(x, y)

    #     for i, placeTag in enumerate(placeTags):
    #         ax.annotate(
    #             f'{str(i + 1)} {placeName[i]} {itArr[i][0]["hours"]} {str(placeTag)} LT: {str(leaveTime[i])}', (x[i], y[i]))

    #     plt.show()

    # printGraph()

    return mcts(searchCycle, budget=budget)


if __name__ == '__main__':
    random.seed(time.time())

    def randInt(n):
        return math.floor((n+1)*random.random())

    # special location: wait - wait for next location to open
    waitHalfHour = {
        'loc_id': 'wait',
        'loc_name': 'wait',
        'coordinate': (0, 0),
        'tags': ['wait'],
        'hours': ('0:00', '24:00'),
        'rating': 0,
        'est_time_stay': 30,
        'price_level': 0,
    }

    tags = [
        "Restaurant",
        "Hidden Gem",
        "Must See Attraction",
        "Mall",
        "Religion",
        "Nature",
        "Temple",
        "Shopping",
        "Beach",
        "Local Culture",
        "Luxury",
        "Historical Place",
        "Outdoor",
        "Wellness & Spa",
        "Zoo",
        "Market",
        "Sports",
        "Arts",
        "Theater",
        "Museum",
        "Nightlife",
        "Adventure",
        "Amusement Park",
        "Family",
        "Modern",
        "Park",
        "Photography",
        "Snack",
        "Buffet",
    ]

    # real places
    with open('locations.txt', 'r', encoding='utf-8') as file:
        data = file.read()
        places = eval(data)
    places = places['mon']  # get monday only for now
    places.append(waitHalfHour)

    # # calculate distance matrix
    # real distances
    with open('driving.txt', 'r', encoding='utf-8') as file:
        data = file.read()
        distanceMatrix = eval(data)
        
    # # User params
    # generate random userSelectedTags params
    userSelectedTags = [tag for tag in tags if randInt(1)]
    budget = 3
    
    # TODO change parameters to dict object
    # TEST RUN
    startTimer = time.time()
    print('Generating plan...')
    print(generatePlan(places=places, 
                       tags=tags, 
                       distanceMatrix=distanceMatrix,  
                       userSelectedTags=userSelectedTags, 
                       budget=budget))
    timeUsed = time.time() - startTimer
    print(f'Runtime : {timeUsed} sec')

