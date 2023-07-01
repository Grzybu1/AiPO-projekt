import tkinter as tk
from functools import partial
from argparse import ArgumentParser
import cv2 as cv
from pathlib import Path
from matplotlib import pyplot as plt
import numpy as np
from copy import deepcopy

DOT_SIZE = 4


def _segment(map_img, coords):
    return map_img[coords[0][1] : coords[1][1], coords[0][0] : coords[1][0]]


def _circle_kernel(r):
    k = np.ones((r * 2 + 1, r * 2 + 1))
    for i in np.arange(-r, r + 1):
        for j in np.arange(-r, r + 1):
            if i**2 + j**2 > r**2:
                k[i + r][j + r] = 0
    return k


def map_show(map_im):
    plt.imshow(map_im, cmap="gray")
    plt.show()


def coordinate_selector(map_file: Path, size: tuple[int, int]) -> list[tuple[int, int]]:
    def callback(event, canvas, coords, root):
        canvas.create_oval(
            (
                (event.x - DOT_SIZE, event.y - DOT_SIZE),
                (event.x + DOT_SIZE, event.y + DOT_SIZE),
            ),
            fill="red",
        )
        coords.append((event.x, event.y))
        if len(coords) == 2:
            root.destroy()

    coords = []

    root = tk.Tk()
    root.title("Select coordinates")
    canvas = tk.Canvas(root, width=size[0], height=size[1], bg="white")
    canvas.pack(anchor=tk.CENTER, expand=True)
    map_pi = tk.PhotoImage(file=map_file)
    canvas.create_image([x // 2 for x in size], image=map_pi)
    canvas.bind(
        "<Button-1>", partial(callback, canvas=canvas, coords=coords, root=root)
    )

    root.mainloop()

    return coords


def binarize_map(map_file: Path) -> cv.Mat:
    map_img = cv.imread(str(map_file))
    map_img = cv.cvtColor(map_img, cv.COLOR_BGR2GRAY)
    ret, map_img = cv.threshold(map_img, 120, 255, cv.ADAPTIVE_THRESH_MEAN_C)
    return map_img


def remove_matching_pattern_from_img(input_image: cv.Mat, kernel: np.array) -> cv.Mat:
    input_image_comp = cv.bitwise_not(input_image)

    reversed_kernel = np.logical_not(kernel).astype(np.uint8)

    hitormiss1 = cv.morphologyEx(input_image, cv.MORPH_ERODE, kernel)
    hitormiss2 = cv.morphologyEx(input_image_comp, cv.MORPH_ERODE, reversed_kernel)
    hitormiss = cv.bitwise_and(hitormiss1, hitormiss2)
    hitormiss_comp = cv.bitwise_not(hitormiss)
    output_img = cv.bitwise_and(input_image, input_image, mask=hitormiss_comp)
    return output_img


def prune_artifacts(input_image: cv.Mat, iterations: int) -> cv.Mat:
    for _ in range(iterations):
        kernel = np.array([
            [0, 0, 0], 
            [0, 1, 1], 
            [0, 0, 0]
        ], np.uint8)
        input_image = remove_matching_pattern_from_img(input_image, kernel)

        kernel = np.array([
            [0, 0, 0], 
            [0, 1, 0], 
            [0, 1, 0]
        ], np.uint8)
        input_image = remove_matching_pattern_from_img(input_image, kernel)

        kernel = np.array([
            [0, 0, 0], 
            [0, 1, 0], 
            [0, 0, 1]
        ], np.uint8)
        input_image = remove_matching_pattern_from_img(input_image, kernel)

    kernel = np.array([
        [0, 0, 0], 
        [0, 1, 0], 
        [0, 0, 0]
    ], np.uint8)
    input_image = remove_matching_pattern_from_img(input_image, kernel)
    return input_image

def get_point_neighborhood_points_coordinates(point: tuple, image: cv.Mat) -> cv.Mat:
    x,y = point
    neighborhood = image[y-1:y+2, x-1:x+2]
    if neighborhood.shape != (3,3):
        return []
    result=[]
    for i in range(3):
        for j in range(3):
            if i == 1 and j == 1:
                continue
            if neighborhood[i,j]:
                result.append((x+j-1, y+i-1))
    return result

def pull_point_to_road(point: tuple, image: cv.Mat) -> tuple:
    x,y = point
    radius=0
    neighborhood=image[x,y]
    if neighborhood:
        return x,y
    
    while not neighborhood.any():
        radius += 1
        neighborhood=image[y-radius : y+1+radius, x-radius : x+1+radius]
    
    for i in range(radius*2+1):
        for j in range(radius*2+1):
            if neighborhood[i,j]:
                return (x+j-radius, y+i-radius)
    
def width_map(map_thin, map_bin):
    width_maps = []
    r = 1
    while True:
        wm = cv.morphologyEx(map_bin, cv.MORPH_HITMISS, _circle_kernel(r))
        if not np.any(wm):
            break
        width_maps.append(cv.bitwise_and(map_thin, wm) // 255)
        r += 1
    return sum(width_maps)

def flood(width_map, start, end):
    wm = deepcopy(width_map).astype(np.int64)
    wm = np.abs(wm - np.max(wm) - 1)
    wm = wm % np.max(wm)
    wm_bckp = deepcopy(wm)
    current_paths = [[start]]
    interval = 2000
    it=0
    while not any([path[-1] == end for path in current_paths]):
        current_paths_cpy = deepcopy(current_paths)
        for i, path in enumerate(current_paths_cpy):
            current_coord = path[-1]
            if wm[current_coord[1],current_coord[0]]:
                wm[current_coord[1],current_coord[0]]-=1
            else:
                current_paths[i] = []
                for point in get_point_neighborhood_points_coordinates(current_coord, wm):
                    new_path = path + [point]
                    if point == end:
                        return new_path
                    if not any([path[-1] == point for path in current_paths if path]): # Is any agent on this spot?
                        current_paths.append(new_path)
        current_paths = [path for path in current_paths if path]
        if not current_paths:
            map_show(wm)
            map_show(wm_bckp-wm)
            raise Exception("No path to destination.")
        print(it, len(current_paths))
        if not it%interval:
            map_show(wm)
            map_show(wm_bckp-wm)
        it+=1
    

                


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("map_file", type=Path)
    ARGS = parser.parse_args()
    map_img = cv.imread(str(ARGS.map_file))
    start, finish = coordinate_selector(ARGS.map_file, map_img.shape[:2])
    binarized_map = binarize_map(ARGS.map_file)
    map_show(binarized_map)
    tc1_map = cv.morphologyEx(binarized_map, cv.MORPH_DILATE, np.ones((5,5)))
    thinned_map = cv.ximgproc.thinning(tc1_map)
    # tc_map = cv.morphologyEx(thinned_map, cv.MORPH_CLOSE, np.ones((3,3)))
    # tct_map = cv.ximgproc.thinning(tc_map)
    cleaned_thinned_map = prune_artifacts(thinned_map, 1)
    # map_show(cleaned_thinned_map)
    start, finish = pull_point_to_road(start, cleaned_thinned_map), pull_point_to_road(finish, cleaned_thinned_map)
    # print(get_point_neighborhood_points_coordinates(start, cleaned_thinned_map))
    # print(get_point_neighborhood_points_coordinates(finish, cleaned_thinned_map))
    w_map = width_map(cleaned_thinned_map, binarized_map)
    # map_show(w_map)
    path = flood(w_map, start, finish)
    for point in path:
        cv.circle(map_img, point, 1, (0,255,0), 2)
    map_show(map_img)


