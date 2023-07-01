import tkinter as tk
from functools import partial
from argparse import ArgumentParser
import cv2 as cv
from pathlib import Path
from matplotlib import pyplot as plt
import numpy as np

DOT_SIZE = 4

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
    ret, map_img = cv.threshold(map_img, 170, 255, cv.ADAPTIVE_THRESH_MEAN_C)
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
        kernel = np.array([[0, 0, 0],
                            [0, 1, 1],
                            [0, 0, 0]], np.uint8)
        input_image = remove_matching_pattern_from_img(input_image, kernel)

        kernel = np.array([[0, 0, 0],
                            [0, 1, 0],
                            [0, 1, 0]], np.uint8)
        input_image = remove_matching_pattern_from_img(input_image, kernel)

        kernel = np.array([[0, 0, 0],
                            [0, 1, 0],
                            [0, 0, 1]], np.uint8)
        input_image = remove_matching_pattern_from_img(input_image, kernel)

    kernel = np.array([[0, 0, 0],
                        [0, 1, 0],
                        [0, 0, 0]], np.uint8)
    input_image = remove_matching_pattern_from_img(input_image, kernel)
    return input_image

def get_point_neighborhood_without_center(point: tuple, image: cv.Mat) -> cv.Mat:
    x,y = point
    neighborhood = image[y-1:y+2, x-1:x+2]
    neighborhood[1,1] = 0
    return neighborhood

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
    


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('map_file', type=Path)
    ARGS = parser.parse_args()
    map_img = cv.imread(str(ARGS.map_file))
    point1, point2 = coordinate_selector(ARGS.map_file, map_img.shape[:2])
    binarized_map = binarize_map(ARGS.map_file)
    thinned_map=cv.ximgproc.thinning(binarized_map)
    cleaned_thinned_map = prune_artifacts(thinned_map, 1)
    point1 = pull_point_to_road(point1, cleaned_thinned_map)
    point2 = pull_point_to_road(point2, cleaned_thinned_map)
    print(get_point_neighborhood_without_center(point1, cleaned_thinned_map))
    print(get_point_neighborhood_without_center(point2, cleaned_thinned_map))
    
    plt.imshow(cleaned_thinned_map)
    plt.show()