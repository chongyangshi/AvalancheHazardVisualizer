from GeoData import rasters
from GeoData.raster_reader import RasterReader
from SAISCrawler.script import db_manager, utils

from sys import maxsize
from math import sqrt
from numpy import amax, amin, ndarray
from copy import deepcopy

NAISMITH_CONSTANT = 7.92
PIXEL_RES = 5 # 5 meters each direction per pixel
PIXEL_RES_DIAG = sqrt(PIXEL_RES ^ 2 * 2)

class PathFinder:
    """ Class for pathfinding based on Naismith's distance,
        static risk and dynamic risk. """

    def __init__(self, height_map_reader, static_risk_reader, dynamic_risk_cursor):

        self._height_map_reader = height_map_reader
        self._static_risk_reader = static_risk_reader
        self._dynamic_risk_cursor = dynamic_risk_cursor


    def find_path(self, longitude_initial, latitude_initial, longitude_final, latitude_final, risk_weighing):
        """ Given initial and final coordinates and a risk-to-distance weighing, find a path. """

        # Sanity checks.
        if not all(isinstance(item, float) for item in [longitude_initial, latitude_initial, longitude_final, latitude_final]):
            return False

        valid_ratio = False
        if isinstance(risk_weighing, float):
            if risk_weighing >= 0 and risk_weighing <= 1:
                valid_ratio = True

        if not valid_ratio:
            return False

        # Swap if directions of two points not what we want (top left, bottom right)
        x_side = 0
        y_side = 0
        if longitude_initial > longitude_final:
            temp = longitude_initial
            longitude_initial = longitude_final
            longitude_final = temp
            x_side = 1
        if latitude_initial < latitude_final:
            temp = latitude_initial
            latitude_initial = latitude_final
            latitude_final = temp
            y_side = 1

        height_grid = self._height_map_reader.read_points(longitude_initial, latitude_initial, longitude_final, latitude_final)
        risk_grid = self._static_risk_reader.read_points(longitude_initial, latitude_initial, longitude_final, latitude_final)

        if (not isinstance(height_grid, ndarray)) or (not isinstance(risk_grid, ndarray)):
            return False

        # Build the grid and a list of vertices.
        naismith_max = -1
        naismith_min = maxsize
        risk_grid_max = amax(risk_grid)
        risk_grid_min = amin(risk_grid)

        x_max = len(height_grid[0]) - 1
        y_max = len(height_grid) - 1
        path_grid = {}
        nodes = [] # List of vertices.
        distance_grid = {} # Distance from source for Dijkstra's.
        prev_grid = {} # Previous node for Dijkstra's.

        for y in range(0, y_max + 1):
            for x in range(0, x_max + 1):
                # The grid dictionary is indexed by (displacement indices from top left), and contains a height, a 0-1
                # scaled risk, and the coordinates-indices of its neighbours, arranged in list index as followed:
                # 2 3 4
                # 5 * 6
                # 7 8 9
                # a Naismith distance is attached to each neighbour.
                height = height_grid[y, x]
                scaled_risk = (risk_grid[y, x] - risk_grid_min) / (risk_grid_max - risk_grid_min)
                path_grid[(x, y)] = [height, scaled_risk]

                for j in range(y - 1, y + 2):
                    for i in range(x - 1, x + 2):

                        if ((i, j) == (x, y)):
                            continue
                        elif (0 <= i <= x_max) and (0 <= j <= y_max):
                            if (abs(i - x) + abs(j - y)) <= 1:
                                naismith_distance = PIXEL_RES + NAISMITH_CONSTANT * abs(height_grid[j, i] - height_grid[y, x])
                            else:
                                naismith_distance = PIXEL_RES_DIAG + NAISMITH_CONSTANT * abs(height_grid[j, i] - height_grid[y, x])

                            if naismith_distance > naismith_max:
                                naismith_max = naismith_distance
                            if naismith_distance < naismith_min:
                                naismith_min = naismith_distance
                            path_grid[(x, y)].append((i, j, naismith_distance))
                        else:
                            path_grid[(x, y)].append(None)

                        # Index, distance from source (since normalised, smaller than max read_points size 9999 * 0-1),
                        # previous node in path.
                        nodes.append((x, y))
                        distance_grid[(x, y)] = 9999
                        prev_grid[(x, y)] = None

        # Determine the coordinates of initial and final by the sides recorded.
        initial = (0, 0)
        final = (x_max, y_max)
        if x_side == 1:
            initial[0] = x_max
            final[0] = 0
        if y_side == 1:
            initial[1] = y_max
            final[1] = 0

        # Make copies for reverse lookup.
        nodes_backwards = deepcopy(nodes)
        distance_grid_backwards = deepcopy(distance_grid)
        prev_grid_backwards = deepcopy(prev_grid)
        initial_backwards = deepcopy(final)
        final_backwards = deepcopy(initial)

        # Initialise source.
        distance_grid[initial] = 0
        distance_grid_backwards[initial_backwards] = 0
        meeting_point = None

        while len(nodes) > 0:

            # Find the min distance node in forward.
            min_distance = maxsize
            min_node = None
            for n in nodes:
                if min_distance > distance_grid[n]:
                    min_node = n
                    min_distance = distance_grid[n]

            if min_node is None:
                return False

            min_distance_backwards = maxsize
            min_node_backwards = None
            for n in nodes_backwards:
                if min_distance_backwards > distance_grid_backwards[n]:
                    min_node_backwards = n
                    min_distance_backwards = distance_grid_backwards[n]

            if min_node is None or min_node_backwards is None:
                return False

            # Found target.
            if min_node == min_node_backwards:
                meeting_point = deepcopy(min_node)
                break

            nodes.remove(min_node)
            neighbours = [n for n in path_grid[min_node][2:] if (n is not None) and ((n[0], n[1]) in nodes)]
            for neighbour in neighbours:
                scaled_naismith = (neighbour[2] - naismith_min) / (naismith_max - naismith_min)
                edge_cost = scaled_naismith * (1 - risk_weighing) + risk_grid[(neighbour[1], neighbour[0])] * risk_weighing
                potential_cost = min_distance + edge_cost
                if potential_cost < distance_grid[(neighbour[0], neighbour[1])]:
                    distance_grid[(neighbour[0], neighbour[1])] = potential_cost
                    prev_grid[(neighbour[0], neighbour[1])] = min_node

            nodes_backwards.remove(min_node_backwards)
            neighbours = [n for n in path_grid[min_node_backwards][2:] if (n is not None) and ((n[0], n[1]) in nodes_backwards)]
            for neighbour in neighbours:
                scaled_naismith = (neighbour[2] - naismith_min) / (naismith_max - naismith_min)
                edge_cost = scaled_naismith * (1 - risk_weighing) + risk_grid[(neighbour[1], neighbour[0])] * risk_weighing
                potential_cost = min_distance_backwards + edge_cost
                if potential_cost < distance_grid_backwards[(neighbour[0], neighbour[1])]:
                    distance_grid_backwards[(neighbour[0], neighbour[1])] = potential_cost
                    prev_grid_backwards[(neighbour[0], neighbour[1])] = min_node_backwards

        if meeting_point is None:
            return False

        path = []
        current_node = meeting_point
        while prev_grid[current_node] is not None:
            path = [current_node] + path
            current_node = prev_grid[current_node]
        path = [current_node] + path

        path_backwards = []
        current_node = meeting_point
        while prev_grid_backwards[current_node] is not None:
            path_backwards = path_backwards + [current_node]
            current_node = prev_grid_backwards[current_node]
        path_backwards = path_backwards + [current_node]

        path = path[:-1] + path_backwards
        # Convert indices back into coordinates.
        for p in path:
            p = self._height_map_reader.convert_displacement_to_coordinate(longitude_initial, latitude_initial, p[0], p[1])

        return path



if __name__ == '__main__':
    dbFile = utils.get_project_full_path() + utils.read_config('dbFile')
    risk_cursor = db_manager.CrawlerDB(dbFile)
    finder = PathFinder(RasterReader(rasters.HEIGHT_RASTER), RasterReader(rasters.ASPECT_RASTER), risk_cursor)
    print(finder.find_path(-5.031738281250013, 56.800878312330426, -5.009765624999997, 56.78884524518923, 0.5))