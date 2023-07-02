from copy import deepcopy
from itertools import count

import cv2 as cv
import numpy as np

from utils import map_show, circle_kernel


class Pathfinder:
    def __init__(
        self, map_img: cv.Mat, start_coord: tuple[int, int], end_coord: tuple[int, int]
    ):
        self.default_map = map_img
        self.start = start_coord
        self.end = end_coord

    def grayscale(self):
        self.grey_map = cv.cvtColor(self.default_map, cv.COLOR_BGR2GRAY)

    def binarize(self):
        if self.grey_map is None:
            raise Exception("No grayscale map. Run grayscale() first.")
        _, self.bin_map = cv.threshold(
            self.grey_map, 120, 255, cv.ADAPTIVE_THRESH_MEAN_C
        )

    def thin(self):
        if self.bin_map is None:
            raise Exception("No binary map. Run binarize() first.")
        self.thin_map = cv.morphologyEx(self.bin_map, cv.MORPH_DILATE, np.ones((5, 5)))
        self.thin_map = cv.ximgproc.thinning(self.thin_map)
        # self.thin_map = cv.morphologyEx(self.thin_map, cv.MORPH_CLOSE, np.ones((3,3)))
        # self.thin_map = cv.ximgproc.thinning(self.thin_map)
        self.thin_map = Pathfinder._prune_artifacts(self.thin_map, 1)

    def weight(self):
        if self.bin_map is None:
            raise Exception("No binary map. Run binarize() first.")
        if self.thin_map is None:
            raise Exception("No thin map. Run thin() first.")
        width_maps = [self.thin_map//255]
        r = 1
        for r in count(1):
            wm = cv.morphologyEx(self.bin_map, cv.MORPH_HITMISS, circle_kernel(r))
            if not np.any(wm):
                break
            width_maps.append(cv.bitwise_and(self.thin_map, wm) // 255)
        self.width_map = sum(width_maps)

    def generate_layers(self):
        self.grayscale()
        self.binarize()
        self.thin()
        self.weight()

    def reallocate_coords(self):
        def pull_point_to_road(point: tuple, image: cv.Mat) -> tuple:
            x, y = point
            radius = 0
            neighborhood = image[x, y]
            if neighborhood:
                return x, y
            while not neighborhood.any():
                radius += 1
                neighborhood = image[
                    y - radius : y + 1 + radius, x - radius : x + 1 + radius
                ]
            for i in range(radius * 2 + 1):
                for j in range(radius * 2 + 1):
                    if neighborhood[i, j]:
                        return (x + j - radius, y + i - radius)

        self.start, self.end = pull_point_to_road(
            self.start, self.thin_map
        ), pull_point_to_road(self.end, self.thin_map)

    def calculate_shortest_path(self, interval: int = 1000) -> list[tuple[int, int]]:
        def get_point_neighborhood_points_coordinates(
            point: tuple, image: cv.Mat
        ) -> cv.Mat:
            x, y = point
            neighborhood = image[y - 1 : y + 2, x - 1 : x + 2]
            if neighborhood.shape != (3, 3):
                return []
            result = []
            for i in range(3):
                for j in range(3):
                    if i == 1 and j == 1:
                        continue
                    if neighborhood[i, j]:
                        result.append((x + j - 1, y + i - 1))
            return result

        def reverse_width_values(weight_map):
            weight_map = weight_map.astype(np.int64)
            wm = np.abs(weight_map - np.max(weight_map) - 1)
            return (wm % np.max(wm)).astype(np.uint8)

        def display_traversed(non_traversed_map, full_map):
            map_show(non_traversed_map)
            map_show(full_map - non_traversed_map)

        widht_map = deepcopy(self.width_map)
        widht_map = reverse_width_values(widht_map)
        widht_map_bckp = deepcopy(widht_map)
        current_paths = [[self.start]]
        for it in count(0):
            for i, path in enumerate(deepcopy(current_paths)):
                current_coord = path[-1]
                if widht_map[current_coord[1], current_coord[0]]:
                    widht_map[current_coord[1], current_coord[0]] -= 1
                else:
                    current_paths[i] = None
                    for point in get_point_neighborhood_points_coordinates(
                        current_coord, widht_map
                    ):
                        new_path = path + [point]
                        if point == self.end:
                            self.shortest_path = new_path
                            return new_path
                        if not any(
                            [path[-1] == point for path in current_paths if path]
                        ):  # Is any agent on this spot?
                            current_paths.append(new_path)
            current_paths = [path for path in current_paths if path]
            if not current_paths:
                display_traversed(widht_map, widht_map_bckp)
                raise Exception("No path to destination.")
            print(it, len(current_paths))
            if not it % interval:
                display_traversed(widht_map, widht_map_bckp)

    def display_shortest_path(self):
        map_img = deepcopy(self.default_map)
        for point in self.shortest_path:
            cv.circle(map_img, point, 1, (0, 0, 255), 2)
        map_show(map_img)

    @staticmethod
    def _prune_artifacts(input_image: cv.Mat, iterations: int) -> cv.Mat:
        def remove_matching_pattern_from_img(
            input_image: cv.Mat, kernel: np.array
        ) -> cv.Mat:
            input_image_comp = cv.bitwise_not(input_image)

            reversed_kernel = np.logical_not(kernel).astype(np.uint8)

            hitormiss1 = cv.morphologyEx(input_image, cv.MORPH_ERODE, kernel)
            hitormiss2 = cv.morphologyEx(
                input_image_comp, cv.MORPH_ERODE, reversed_kernel
            )
            hitormiss = cv.bitwise_and(hitormiss1, hitormiss2)
            hitormiss_comp = cv.bitwise_not(hitormiss)
            output_img = cv.bitwise_and(input_image, input_image, mask=hitormiss_comp)
            return output_img

        for _ in range(iterations):
            kernel = np.array([[0, 0, 0], [0, 1, 1], [0, 0, 0]], np.uint8)
            input_image = remove_matching_pattern_from_img(input_image, kernel)

            kernel = np.array([[0, 0, 0], [0, 1, 0], [0, 1, 0]], np.uint8)
            input_image = remove_matching_pattern_from_img(input_image, kernel)

            kernel = np.array([[0, 0, 0], [0, 1, 0], [0, 0, 1]], np.uint8)
            input_image = remove_matching_pattern_from_img(input_image, kernel)

        kernel = np.array([[0, 0, 0], [0, 1, 0], [0, 0, 0]], np.uint8)
        input_image = remove_matching_pattern_from_img(input_image, kernel)
        return input_image
