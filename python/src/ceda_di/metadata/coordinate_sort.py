#!/bin/python

'''                         
    Sort coordinates to counterclockwise order, and make sure the polygon is closed
    Assumes coordinates are supplied as a list of  lat, lon (y,x) pairs.
'''

from math import pi, atan2, sqrt

def find_midpoint(coordinates):
    '''Remove duplicates and calculate average lon,lat'''

    x = set([float(x[0]) for x in coordinates]) #lon
    y = set([float(y[1]) for y in coordinates]) #lat

    midx = sum(x)/len(x)
    midy = sum(y)/len(y)

    return [midx,midy]


def reference_vectors(coordinates, midpoint):
    '''Get the atan2 result for the reference vector. This is the first point from the coordinate list'''

    first_point = coordinates[0]
    u = first_point[0] - midpoint[0] #lon
    v = first_point[1] - midpoint[1] #lat

    reference = atan2(v,u) #lat, lon
    return reference


def magnitude(u,v):
    '''Returns the vector magnitude'''
    return sqrt(u**2 + v**2)


def winding_angle(reference_vector, lon, lat):
    '''
    Calculates the winding angle from the coordinates
    :param reference_vector: the atan2 result calculated using the first point
    :param lon: lon coordinate
    :param lat: lat coodinate
    :return: winding angle
    '''

    u = lon
    v = lat
    angle = reference_vector - atan2(v, u)  # lat, lon

    return angle


def calculate_sorting_index(coordinates):
    '''
    :param coordinates: list of [Lon, lat] coordinate pairs
    :return: Sorting index to be applied to ensure that the list is a closed loop of counter-clockwise definition.
    '''
    midpoint = find_midpoint(coordinates)
    reference = reference_vectors(coordinates, midpoint)

    index = []
    for i,point in enumerate(coordinates):

        u = point[0] - midpoint[0] #lon
        v = point[1] - midpoint[1] #lat

        angle = winding_angle(reference,u,v)

        # constrain to be counter-clockwise
        if angle > 0:
            angle -= 2 * pi

        distance = magnitude(u,v)

        index.append({'angle': angle,'distance':distance,'coordindex':i})

    # Sort on ascending angle and decending distance
    index = sorted(index, key=lambda x: (-x['angle'], -x['distance']))

    # Check to see if the polygon coords close and order appropriately.
    closed = False
    start = index[0]
    if index[1]['angle'] == 0:
        if index[1]['distance'] == start['distance']:
            closed = True
            index.append(index.pop(1))

    if not closed:
        index.append(index[0])

    return [d['coordindex'] for d in index]


def sort_coords(coordinates):
    '''
    Takes the sorting index calculated by calculate_sorting_index() and returns the coordinates sorted as a closed polygon.
    
    :param coordinates: list of [lon, lat] coordinate pairs.
    :return: a sorted list of [lon, lat] coordinate pairs
    '''

    sorting_index = calculate_sorting_index(coordinates)

    sorted_coordinates = []
    for i in sorting_index:
        sorted_coordinates.append(coordinates[i])

    return sorted_coordinates


def ccw(coordinates):
    '''
    Accepts a [lon, lat] list and determines the orientation of the coordinates.
    Returns true if the shape is counter-clockwise and false if the polygon is defined clockwise.
    '''

    signedArea = 0
    end = len(coordinates)
    for i,point in enumerate(coordinates):
        x1 = point[0]
        y1 = point[1]
        if i == end-1:
            x2 = coordinates[0][0]
            y2 = coordinates[0][1]
        else:
            x2 = coordinates[i+1][0]
            y2 = coordinates[i+1][1]

        signedArea += (x1 * y2 - x2 * y1)

    if signedArea > 0:
        return True # counter-clockwise
    else:
        return False # clockwise


def close_polygon(coordinates):
    '''
    Closes the polygon by duplicating the first coordinate pair and adding to the end.
    
    :param coordinates: 
    :return: A closed polygon 
    '''
    first = coordinates[0]

    return coordinates + [first]


def filterDupes(coordinates):
    '''
    Removes consecutive duplicates from a list of coordinates.

    :param coordinates:  A list of [lon, lat] coordinate pairs.
    :return: same list with consecutive duplicates removed.
    '''

    for i, pair in enumerate(coordinates):
        if i > 0:
            if pair == coordinates[i - 1]:
                coordinates.pop(i)

    return coordinates


def conditionPolygon(coordinates):
    '''
    Wrapper:

     1. Checks if polygon is ccw, if not it sorts it.
     2. Removes and duplicate coordinates that are not starting or closing the polygon.
     3. Checks if polygon is closed, if not closes it.

    :param coordinates: list of [lon, lat] coordinate pairs
    :return: sanitised coordinates, making sure it is a closed polygon and defined counter-clockwise
    '''

    if not ccw(coordinates):
        coordinates = sort_coords(coordinates)

    coordinates = filterDupes(coordinates)

    if not coordinates[0] == coordinates[-1]:
        coordinates = close_polygon(coordinates)

    return coordinates
