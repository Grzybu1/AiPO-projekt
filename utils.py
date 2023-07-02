import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt


def segment(map_img, coords):
    return map_img[coords[0][1] : coords[1][1], coords[0][0] : coords[1][0]]


def circle_kernel(r):
    k = np.ones((r * 2 + 1, r * 2 + 1))
    for i in np.arange(-r, r + 1):
        for j in np.arange(-r, r + 1):
            if i**2 + j**2 > r**2:
                k[i + r][j + r] = 0
    return k


def map_show(map_img):
    if len(map_img.shape) == 2:
        plt.imshow(map_img, cmap="gray")
    else:
        plt.imshow(cv.cvtColor(map_img, cv.COLOR_BGR2RGB))
    plt.show()
