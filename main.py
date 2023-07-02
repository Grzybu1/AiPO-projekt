import tkinter as tk
from functools import partial
from argparse import ArgumentParser
import cv2 as cv
from pathlib import Path
from pathfinder import Pathfinder

def coordinate_selector(map_file: Path, size: tuple[int, int]) -> list[tuple[int, int]]:
    def callback(event, canvas, coords, root):
        DOT_SIZE = 4
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


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("map_file", type=Path)
    ARGS = parser.parse_args()
    map_img = cv.imread(str(ARGS.map_file))
    start, finish = coordinate_selector(ARGS.map_file, map_img.shape[:2])
    pf = Pathfinder(map_img, start, finish)
    pf.generate_layers()
    pf.reallocate_coords()
    pf.calculate_shortest_path()
    pf.display_shortest_path()
