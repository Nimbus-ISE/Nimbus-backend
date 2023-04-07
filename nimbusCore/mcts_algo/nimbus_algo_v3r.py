# # user parameters

import random
import time
import math
import matplotlib.pyplot as plt
import numpy as np
import copy
import json

from .helper import timeStringToFloat

    
def generatePlan(places, tags, distanceMatrix, userSelectedTags, budget):

    # C is bias to explore new route
    # higher C = explore more = run longer
    C = 5
    tagWeight = 2
    timeModifier = 1
    # time spend ** modifier
    # higher = prefer longer distance but better place score
    # lower = prefer shorter distance but less place score

    # convert openHours into correct format
    for i in range(len(places)):
        new_hours = (timeStringToFloat(places[i]['hours'][0]), timeStringToFloat(places[i]['hours'][1]))
        places[i]['hours'] = new_hours

    placesDict = {place['id']: place for place in places}

    # # calculate score

    placesTagsMatrix = np.array([[tag in place['tags']
                                for tag in tags] for place in places])

    tagsMatrix = tagWeight * np.array([(tag in userSelectedTags) for tag in tags]).reshape((len(tags), 1))

    # each location tags score
    tagScores = list(np.matmul(placesTagsMatrix, tagsMatrix).reshape(len(places)))

    # each location rating score
    ratingScores = np.array([place['rating'] for place in places])

    totalScores = tagScores + ratingScores

    placeScores = {}
    for i in range(len(totalScores)):
        placeScores[places[i]['id']] = totalScores[i]

    # scoring criteria: tag + rating + distance
    placeScoresMatrix = {}
    for x in places:
        placeScoresMatrix[x['id']] = {}

        for y in places:
            if 'wait' in x['tags'] or 'wait' in y['tags'] or x['id'] == y['id']:
                placeScoresMatrix[x['id']][y['id']] = 0
            else:
                placeScoresMatrix[x['id']][y['id']] = placeScores[y['id']] / (1 + (distanceMatrix[x['id']][y['id']]))

    # # MCTS ALGORITHM
    
    class Node:
        def __init__(self, place, child=[], parent=None):
            self.id = place['id']
            self.est_time_stay_HR = toHour(place['est_time_stay'])
        
            self.child = child
            self.parent = parent

            self.totalReward = 0
            self.visitCount = 0
            self.nodeReward = None

            if parent is not None:
                self.travelTime = getTravelTimeHR(self.id, parent.id)  # time to get here
                self.leaveTime = parent.leaveTime + self.est_time_stay_HR + getTravelTimeHR(self.id, parent.id)
            else:
                self.travelTime = 0
                self.leaveTime = startHour

    def getTravelTimeHR(x, y):
        if x == y or 'wait' in [x, y]:
            return 0

        return distanceMatrix[x][y] / 60

    def toHour(x):
        return x / 60

    def calcExploitScore(startNode, destNode):
        if startNode.id == 'wait' and destNode != 'wait':
            while startNode.id == 'wait':
                startNode = startNode.parent
                
        return placeScoresMatrix[startNode.id][destNode.id]

    def calcExploreScore(startNode, destNode):
        return C * math.sqrt(math.log(startNode.visitCount + 1) / (destNode.visitCount + 1))

    def selection(startNode):
        index = 0
        output_idx = 0
        max = float('-inf')

        for destNode in startNode.child:
            score = (calcExploitScore(startNode, destNode) +
                    calcExploreScore(startNode, destNode))
            if max < score:
                output_idx = index
                max = score
            index += 1

        return startNode.child[output_idx]

    def backPropagation(leaf):
        # accumulate totalReward for all ancestor
        # add node accumulated visitCount by 1
        node = leaf
        totalReward = placeScoresMatrix[node.parent.id][node.id]
        node.visitCount += 1
        while node.parent.parent is not None:
            node = node.parent
            totalReward += placeScoresMatrix[node.parent.id][node.id]
            node.visitCount += 1

        # update totalReward
        node = leaf
        node.totalReward += totalReward
        while node.parent is not None:
            node = node.parent
            node.totalReward += totalReward

    def printOptimalPath(itTree): # root
        pointer = itTree

        global itArr
        itArr = []
        itArr.append((placesDict[pointer.id], 0)) # starting place
        
        print(placesDict[pointer.id])
        print(f'leave at {pointer.leaveTime} node rewards : {pointer.nodeReward}')

        while len(pointer.child) != 0:
            maxScore = float('-inf')
            index = 0
            for i in range(len(pointer.child)):
                if pointer.child[i].visitCount > 0 and pointer.child[i].totalReward / pointer.child[i].visitCount > maxScore:
                    index = i
                    maxScore = pointer.child[i].totalReward / pointer.child[i].visitCount
            pointer = pointer.child[index]

            print(placesDict[pointer.id])
            print(f'DEPART AT {pointer.leaveTime}')
            temp = copy.deepcopy(placesDict[pointer.id])
            if pointer.id == ['wait']:
                temp['coordinate'] = itArr[-1][0]['coordinate']

            # itinerary result
            itArr.append((temp, pointer.leaveTime))

    # # Main function

    def mcts(cycle, budget=4, tripPace=2):

        def childrenNodeExpansion(placeNode, availablePlace):
            if len(placeNode.child) == 0 and len(availablePlace) != 0:
                placeNode.child = [Node(p, [], placeNode) for p in availablePlace]

        def takeFood(place, pointer, hadFood):
            # find food place after 11.00
            foodHours = 11
            # if already has food then take place that does not have 'food' tag
            if pointer.leaveTime < foodHours or hadFood: # if not food time yet
                return 'Restaurant' not in place['tags']
            # if it's food time!
            return 'Restaurant' in place['tags']
        
        def isLowerThanBudget(place, selectedPlace, budget):
            curCost = [placesDict[loc_id]['price_level'] for loc_id in selectedPlace]
            
            return ((sum(curCost) + place['price_level']) / (len(selectedPlace) + 1)) <= budget
                
        def getAvailablePlace(pointer, hadFood, budget):
            includeLunch=True
            if includeLunch:
                availPlace = [place for place in places if
                        # time budget
                        pointer.leaveTime + getTravelTimeHR(pointer.id, place['id']) + toHour(place['est_time_stay']) < endHour
                        # operating hour
                        and pointer.leaveTime + getTravelTimeHR(pointer.id, place['id']) >= place['hours'][0]
                        # operating hour
                        and pointer.leaveTime + getTravelTimeHR(pointer.id, place['id']) + toHour(place['est_time_stay']) < place['hours'][1]
                        # not chosen
                        and place['id'] not in selectedPlace
                        and takeFood(place, pointer, hadFood)  # food once after noon
                        and isLowerThanBudget(place, selectedPlace, budget)
                        ]
                
                return availPlace

        # TEMP: best score -> first place hehe
        max_key = max(placeScores, key=placeScores.get)
        firstPlace = placesDict[max_key]
        
        # global itTree
        itTree = Node(firstPlace)
        selectedPlace = [firstPlace['id']]
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
                if pointer.id != 'wait':
                    selectedPlace += [pointer.id]
                if 'Restaurant' in placesDict[pointer.id]['tags']:
                    hadFood = True
                # expansion
                if pointer.child == []:
                    availablePlace = getAvailablePlace(pointer, hadFood, budget)
                    childrenNodeExpansion(pointer, availablePlace)

            # back propagation
            backPropagation(pointer)

        curCost = [placesDict[loc_id]['price_level'] for loc_id in selectedPlace]
        print('avg price_level:', sum(curCost) / (len(selectedPlace)))
        print('selected place_id:', selectedPlace)
        printOptimalPath(itTree)

    # # output

    # ### profiling + run + debug

    # user input params
    POINUM = len(places)
    startHour = 8
    endHour = 19
    searchCycle = 10_000
    budget = 4

    startTimer = time.time()
    mcts(searchCycle, budget=budget)
    timeUsed = time.time() - startTimer
    print("-----------------------")
    print(f"finish in {timeUsed} second")
    print(f"with {POINUM} POI and {searchCycle} search cycle")
    print(f"selected tags : {userSelectedTags}")
    print(f"start hours : {startHour}")
    print(f"end hours : {endHour}")


    def printGraph():
        x = [place[0]['coordinate'][0] for place in itArr]
        y = [place[0]['coordinate'][1] for place in itArr]
        placeName = [place[0]['loc_name'] for place in itArr]
        placeTags = [place[0]['tags'] for place in itArr]
        leaveTime = [round(place[1],2) for place in itArr]

        fig, ax = plt.subplots()
        ax.plot(x, y)

        for i, placeTag in enumerate(placeTags):
            ax.annotate(f'{str(i + 1)} {placeName[i]} {itArr[i][0]["hours"]} {str(placeTag)} LT: {str(leaveTime[i])}', (x[i], y[i]))

        plt.show()

    # printGraph()


if __name__ == '__main__':
    random.seed(time.time())

    def randInt(n):
        return math.floor((n+1)*random.random())

    # special location: wait - wait for next location to open
    waitHalfHour = {
        'id': 'wait',
        'loc_id': 'wait',
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
        "Mall",
        "Religion",
        "Nature",
        "Temple",
        "Shopping",
        "Must See Attraction",
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


    # # User params
    # real places
    with open('../locations.txt', 'r', encoding='utf-8') as file:
        data = file.read()
        places = eval(data)
    places = places['mon'] # get monday only for now
    places.append(waitHalfHour)

    # # calculate distance matrix
    # real distances
    with open('../driving.txt', 'r', encoding='utf-8') as file:
        data = file.read()
        distanceMatrix = eval(data)

    # # generate random userSelectedTags params
    userSelectedTags = [tag for tag in tags if randInt(1)]
    budget = 3

    print('Generating plan...')
    generatePlan(places=places, tags=tags, distanceMatrix=distanceMatrix, userSelectedTags=userSelectedTags, budget=budget)