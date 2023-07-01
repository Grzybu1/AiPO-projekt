import tkinter as tk
from functools import partial
from argparse import ArgumentParser
from PIL import Image
from pathlib import Path

DOT_SIZE = 4
WINDOW_SIZE = (600, 600)


def coordinate_selector(map_file: Image) -> list[tuple[int, int]]:
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
    canvas = tk.Canvas(root, width=WINDOW_SIZE[0], height=WINDOW_SIZE[1], bg="white")
    canvas.pack(anchor=tk.CENTER, expand=True)
    map_pi = tk.PhotoImage(file=map_file)
    canvas.create_image([x // 2 for x in WINDOW_SIZE], image=map_pi)
    canvas.bind(
        "<Button-1>", partial(callback, canvas=canvas, coords=coords, root=root)
    )

    root.mainloop()

    return coords

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('map_file', type=Path)
    ARGS = parser.parse_args()
    print(coordinate_selector(ARGS.map_file))