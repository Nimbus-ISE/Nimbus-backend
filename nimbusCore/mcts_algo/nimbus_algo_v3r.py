# # user parameters

from __future__ import annotations
import random
import time
import math
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import datetime
import copy
from typing import Union,TypeVar

# have this before importing helper so no import error
sys.path.append(os.path.realpath(os.path.dirname(__file__)))

from helper import timeStringToTime


def generatePlan(places, tags, distanceMatrix, walkMatrix, 
                 userSelectedTags: list, 
                 budget: int, 
                 travelMethod: list, 
                 tripPace: int, 
                 mustInclude: str, 
                 wantGraph: bool = True):

    # deep copy to avoid overwriting variables
    distanceMatrix = copy.deepcopy(distanceMatrix)
    walkMatrix = copy.deepcopy(walkMatrix)
    
    # ALGO params
    searchCycle = 10000
    tagWeight = 2
    C = 5 # C is bias to explore new route
    # TODO
    timeModifier = 1
    # time spend ** modifier
    # higher = prefer longer distance but better place score
    # lower = prefer shorter distance but less place score
    if tripPace == 0:
        startHour = datetime.datetime(2023, 4, 9, 10, 0) # year month day hour min
        endHour = datetime.datetime(2023, 4, 9, 16, 0)
    if tripPace == 1:
        startHour = datetime.datetime(2023, 4, 9, 9, 0) # year month day hour min
        endHour = datetime.datetime(2023, 4, 9, 18, 0)
    if tripPace == 2:
        startHour = datetime.datetime(2023, 4, 9, 9, 0) # year month day hour min
        endHour = datetime.datetime(2023, 4, 9, 20, 0)


    # TODO wrap in another function file
    # convert openHours, est_time_stay into datetime format
    for i in range(len(places)):
        places[i]['hours'] = (timeStringToTime(places[i]['hours'][0]), timeStringToTime(places[i]['hours'][1]))
        places[i]['est_time_stay'] = datetime.timedelta(minutes=places[i]['est_time_stay'])

    # convert to datetime delta
    for start in distanceMatrix.keys():
        for dest in distanceMatrix[start].keys():
            distanceMatrix[start][dest] = datetime.timedelta(minutes=distanceMatrix[start][dest])
            if dest in walkMatrix[start].keys():
                walkMatrix[start][dest] = datetime.timedelta(minutes=walkMatrix[start][dest])
            else:
                walkMatrix[start][dest] = datetime.timedelta(minutes=600)
    
    startNode = {
        'loc_id': 'start',
        'loc_name': 'start',
        'coordinate': (0, 0),
        'tags': ['start'],
        'hours': ('0:00', '24:00'),
        'rating': 0,
        'est_time_stay': datetime.timedelta(),
        'price_level': 0,
    }
    startNode['hours'] = (timeStringToTime(startNode['hours'][0]), timeStringToTime(startNode['hours'][1]))
        
    # TODO hidden gem weight increase
    # generate place dict
    placesDict = {place['loc_id']: place for place in places}
    placesDict['start'] = startNode

    # # calculate score
    placesTagsMatrix = np.array([[tag in place['tags'] for tag in tags] for place in places])
    tagsMatrix = tagWeight * np.array([(tag in userSelectedTags) for tag in tags]).reshape((len(tags), 1))
    tagsMatrix[0] = (tagsMatrix[0] * randInt(3)) + 2 # hidden gem boost

    # print(tagsMatrix)

    # each location tags score
    tagScores = list(np.matmul(placesTagsMatrix, tagsMatrix).reshape(len(places)))

    # each location rating score
    ratingScores = np.array([place['rating'] for place in places])
    totalScores = tagScores + ratingScores

    placeScores = {}
    for i in range(len(totalScores)):
        placeScores[places[i]['loc_id']] = totalScores[i]
    placeScores['start'] = 0
    if mustInclude != None:
        placeScores[mustInclude] = 99999 # increase the mustInclude placeScores 

    # SCORING FUNCTION: tagMatched + rating / distance
    placeScoresMatrix = {}
    travelMethodMatrix = {}
    for x in places:
        placeScoresMatrix[x['loc_id']] = {}
        travelMethodMatrix[x['loc_id']] = {}

        for y in places:
            if 'wait' in x['tags'] or 'wait' in y['tags'] or x['loc_id'] == y['loc_id']:
                placeScoresMatrix[x['loc_id']][y['loc_id']] = 0
                travelMethodMatrix[x['loc_id']][y['loc_id']] = 'none'
            else:
                walkTime = walkMatrix[x['loc_id']][y['loc_id']].seconds
                driveTime = walkMatrix[x['loc_id']][y['loc_id']].seconds
                driveScore = placeScores[y['loc_id']] / ((1 + driveTime)) # v1.0
                # driveScore = 0.99 * placeScores[y['loc_id']] / ((1 + driveTime) ** 0.5) # v1.1 :(
                placeScoresMatrix[x['loc_id']][y['loc_id']] = driveScore
                
                # travel method
                # 1) walk and drive 
                if 'walk' in travelMethod and 'drive' in travelMethod:
                    if walkTime <= 15 * 60 and 'walk': # walk if less than 15 mins
                        travelMethodMatrix[x['loc_id']][y['loc_id']] = 'walk'
                    else:
                        travelMethodMatrix[x['loc_id']][y['loc_id']] = 'drive'
                # 2) walk only
                elif 'walk' in travelMethod:
                    travelMethodMatrix[x['loc_id']][y['loc_id']] = 'walk'
                # 3) drive only
                elif 'drive' in travelMethod:
                    if walkTime <= 5 * 60 and 'walk': # walk if less than 5 mins
                        travelMethodMatrix[x['loc_id']][y['loc_id']] = 'walk'
                    else:
                        travelMethodMatrix[x['loc_id']][y['loc_id']] = 'drive'

    placeScoresMatrix['start'] = {place['loc_id'] : placeScores[place['loc_id']] for place in places} # start score matrix = 0 to treat every node equally
    travelMethodMatrix['start'] = {place['loc_id'] : 'none' for place in places}

    def getTravelDuration(x, y, travelMethod):
        if x == y or 'wait' in [x, y] or 'start' in [x, y]:
            return datetime.timedelta() # 0

        if travelMethod == 'walk':
            return walkMatrix[x][y]
        
        return distanceMatrix[x][y]

    def getTravelMethod(x, y):
        if x == y or 'wait' in [x, y] or 'start' in [x, y]:
            return 'none'

        return travelMethodMatrix[x][y]
    
    # # MCTS ALGORITHM
    class Node:
        loc_id: Union[int,str]
        est_time_stay: datetime.timedelta
        child: list[Node]
        parent: list[Node]
        totalReward: int
        visitCount: int
        travelMethod: str
        travelDuration: datetime.timedelta
        arrivalTime: datetime.datetime
        leaveTime: datetime.datetime


        def __init__(self, place, child=[], parent:Node=None):
            self.loc_id = place['loc_id']
            self.est_time_stay = place['est_time_stay']

            self.child = child
            self.parent = parent

            self.totalReward = 0
            self.visitCount = 0
            # self.nodeReward = None # unused

            if parent is not None:
                self.travelMethod = getTravelMethod(self.loc_id, parent.loc_id)  # method to get here
                self.travelDuration = getTravelDuration(self.loc_id, parent.loc_id, self.travelMethod)  # time to get here
                self.arrivalTime = parent.leaveTime + self.travelDuration
                self.leaveTime = parent.leaveTime + self.travelDuration + self.est_time_stay
            else: # first place
                self.travelMethod = 'none' # method to get here
                self.travelDuration = 0
                self.arrivalTime = startHour
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
        max_score = float('-inf')

        # get highest child
        for destNode in startNode.child:
            score = (calcExploitScore(startNode, destNode) + calcExploreScore(startNode, destNode))
            if max_score < score:
                output_loc_idx = index
                max_score = score
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
        node.parent.visitCount += 1

        # update totalReward
        node = leaf
        node.totalReward += totalReward
        while node.parent is not None:
            node = node.parent
            node.totalReward += totalReward

    # to get the best path from the Monte Carlo Tree
    def getOptimalPath(treeRoot):
        pointer = treeRoot

        itArr = [] # itinerary list
        # start place
        # itArr.append({'type': 'locations',
        #               'loc_id': pointer.loc_id,
        #               'arrival_time': startHour.time().isoformat(),
        #               'leave_time': pointer.leaveTime.time().isoformat(),
        #               'reward': pointer.totalReward / pointer.visitCount,
        #               'totalReward': pointer.totalReward,
        #               'visitCount': pointer.visitCount,
        #               })

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
                        'travel_dur': pointer.travelDuration.seconds,
                        'travel_type': pointer.travelMethod,
                        })
            # append next location
            itArr.append({'type': 'locations',
                        'loc_id': pointer.loc_id,
                        'arrival_time': pointer.arrivalTime.time().isoformat(),
                        'leave_time': pointer.leaveTime.time().isoformat(),
                        # 'reward': pointer.totalReward / pointer.visitCount,
                        # 'totalReward': pointer.totalReward,
                        # 'visitCount': pointer.visitCount,
                        })

        if wantGraph:
            printGraph(itArr[1:], placesDict)

        return itArr[1:]

    # # Main function
    def mcts(cycle):
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
                            and (pointer.leaveTime + getTravelDuration(pointer.loc_id, place['loc_id'], pointer.travelMethod) + place['est_time_stay']).time() < endHour.time()
                            # after open hour
                            and (pointer.leaveTime + getTravelDuration(pointer.loc_id, place['loc_id'], pointer.travelMethod)).time() >= place['hours'][0]
                            # before close hour
                            and (pointer.leaveTime + getTravelDuration(pointer.loc_id, place['loc_id'], pointer.travelMethod) + place['est_time_stay']).time() <= place['hours'][1]
                            # food or not
                            and takeFood(place, pointer, hadFood)
                            ]

                return availPlace

        treeRoot = Node(placesDict['start'])
        selectedPlace = []
        # generate children nodes for the firstPlace
        availablePlace = getAvailablePlace(treeRoot, False, budget)
        childrenNodeExpansion(treeRoot, availablePlace)

        for _ in range(0, cycle):
            # simulation
            pointer = treeRoot
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

        # curCost = [placesDict[loc_id]['price_level'] for loc_id in selectedPlace]
        # print('avg price_level:', sum(curCost) / (len(selectedPlace)))

        return getOptimalPath(treeRoot), treeRoot

    # print graph for debug
    def printGraph(itArr, placeDict):
        all_places = [placeDict[loc_id] for loc_id in placeDict.keys()]
        x = [place['coordinate'][0] for place in all_places]
        y = [place['coordinate'][1] for place in all_places]

        # in it
        places = [place for place in itArr if place['type'] == 'locations']
        lat = [placeDict[place['loc_id']]['coordinate'][0] for place in places]
        long = [placeDict[place['loc_id']]['coordinate'][1] for place in places]
        placeName = [placeDict[place['loc_id']]['loc_name'] for place in places]
        placeHour = [placeDict[place['loc_id']]['hours'] for place in places]
    
        plt.figure(figsize=(8, 8))
        plt.plot(lat, long)
        # plt.scatter(x, y)

        for i, place in enumerate(places):
            plt.annotate(f'{i + 1} {placeName[i]} {placeHour[i]}', (lat[i], long[i]))

        plt.show()

    return mcts(searchCycle)


if __name__ == '__main__':
    random.seed(time.time())

    def randInt(n):
        return math.floor((n + 1) * random.random())

    tags = [
        "Hidden Gem",
        "Restaurant",
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

    # real places
    with open('locations.txt', 'r', encoding='utf-8') as file:
        data = file.read()
        places = eval(data)
    places = places['mon']  # get monday only for now
    # places.append(waitHalfHour)

    # # calculate distance matrix
    # real distances
    with open('driving.txt', 'r', encoding='utf-8') as file:
        data = file.read()
        distanceMatrix = eval(data)

    with open('walking.txt', 'r', encoding='utf-8') as file:
        data = file.read()
        walkMatrix = eval(data)
        
    placesDict = {place['loc_id']: place for place in places}

    travelMethods = [['drive'], ['drive', 'walk'], ['walk']]

    # # testing user params
    # generate random userSelectedTags params
    userSelectedTags = [tag for tag in tags if randInt(1)]
    userSelectedTags = [tag for tag in userSelectedTags if randInt(1)]
    userSelectedTags.append(tags[0])
    budget = randInt(4)
    travelMethod = travelMethods[randInt(2)]
    tripPace = randInt(2)
    mustInclude = 76
    
    # TODO change parameters to dict object
    # TEST RUN
    startTimer = time.time()
    print('Generating plan...')

    plan, treeRoot = generatePlan(
                            places=places, 
                            tags=tags, 
                            distanceMatrix=distanceMatrix,  
                            walkMatrix=walkMatrix,
                            userSelectedTags=userSelectedTags, 
                            budget=budget,
                            travelMethod=travelMethod,
                            tripPace=tripPace,
                            mustInclude=mustInclude,
                            )
    
    print('------------------------------------------------------')
    for place in plan:
        print(place)
        if place['type'] == 'locations':
            print(placesDict[place['loc_id']]['tags'], '\n')
        else:
            print(' ')
    print('------------------------------------------------------')
    print('tags :', userSelectedTags)
    print('budget :', budget)
    print('travelMethod :', travelMethod)
    print('tripPace :', tripPace)
    print('mustInclude :', mustInclude)
    print('------------------------------------------------------')
    print(f'Runtime : {time.time() - startTimer} sec')

