""" Simple tool to label images for classification.
    Use the keyboard to label images, moving them into sub-directories ready for training a classifier.

    Usage:
      python label_images.py path_to_images

    Directory structure:
      The setup is simple: have a directory with images to label, and sub-directories in
      that directory which are the labels. Files will be moved to those directories as you
      perform labeling.

    Keyboard shortcuts:
      The keyboard shortcut when labeling is the first letter of the label name (or the first
      unused letter if the first letter is already taken by another label). It's highlighted
      in brackets [] on the UI. You can also click on the UI buttons to label.

    Example directory structure:
      path_to_images=/home/myimages/ (contains img1.jpg, img2.jpg...)
          also contains sub directories which we turn into labels
            e.g. /home/myimages/cat/, /home/myimages/dog/ etc.

    Example usage:
      python label_images.py /home/myimages/

    Dependencies:
      pip install tk

    Originally written by: Marc Stogaitis
    Updated by: Luke Hoggatt
"""

import os
from os import walk
import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk, Image
import sys
import random
from datetime import datetime

img_idx = -1
keyboard_shortcuts_indexed_by_letter = {}
keyboard_shortcuts_indexed_by_idx = {}
undo = []


def load_labels(path):
    """ Loads labels by creating one label per sub-directory name """
    labels = next(os.walk(path))[1]
    labels.sort()
    for i, label in enumerate(labels):
        for letter_idx, letter in enumerate(label):
            # Setup keyboard shortcuts as the first letter of the label or the first available
            # letter if it's already taken by another label.
            if letter not in keyboard_shortcuts_indexed_by_letter:
                keyboard_shortcuts_indexed_by_letter[letter] = i
                keyboard_shortcuts_indexed_by_idx[i] = letter_idx
                break
    return labels


def load_image_filenames(path):
    """ Loads just the image filenames from a directory, ignoring sub-directories """
    f = []
    for (_, _, filenames) in walk(path):
        f.extend(filenames)
        break
    f = [pic for pic in f if pic.endswith(".png") or pic.endswith(".jpg") or pic.endswith(".jpeg")]
    # f.sort()
    random.shuffle(f)
    return f


""" Command line parameter """
if len(sys.argv) != 2:
    print("Missing parameter: path_to_images")
    print("Usage: python label_images.py path_to_images")
    print(
        "The setup is simple: have a directory with images to label, and sub-directories in that directory which are the labels."
    )
    print(
        "Example directory structure: /home/myimages/img1.jpg ... /home/myimages/cat/ ... /home/myimages/dog/"
    )
    print("Example usage: python label_images.py /home/myimages/")
    sys.exit()
path = sys.argv[1]
outfile = os.path.join(path, "image_labels.csv")
labels = load_labels(path)
print("Labels:", labels)
image_filenames = load_image_filenames(path)
print("Image count", len(image_filenames))

# Create the UI
window = tk.Tk()
window.title("Simple Image Labeler")
window.rowconfigure(0, minsize=700, weight=1)
window.columnconfigure(1, minsize=700, weight=1)
panel = tk.Label(window)


def change_img(decrement=False):
    """ Go to the next image """
    global img_idx
    if decrement:
        img_idx -= 1
    else:
        img_idx += 1
    if img_idx >= len(image_filenames):
        print("Finished")
        messagebox.showinfo(
            "Simple Image Labeler",
            "Congrats! You're done.\nYou've successfully labeled " + str(img_idx) + " images.",
            parent=window,
        )
        window.quit()
        return
    img = Image.open(os.path.join(path, image_filenames[img_idx]))
    window.title("Simple Image Labeler - " + image_filenames[img_idx])
    # Resize the image. Use img.thumbnail since it preserves aspect ratio.
    img.thumbnail((500, 500), Image.ANTIALIAS)
    # img = img.resize((round(img.size[0]*3.5), round(img.size[1]*3.5)), Image.ANTIALIAS)
    photo_img = ImageTk.PhotoImage(img)
    panel.configure(image=photo_img)
    panel.image = photo_img


def undo_click():
    global undo
    global img_idx
    print("Trying to undo", undo)
    if len(undo) == 2:
        if os.path.isfile(undo[0]):
            os.rename(undo[0], undo[1])
            change_img(True)
            with open(outfile) as f1:
                lines = f1.readlines()
            with open(outfile, "w") as f2:
                f2.writelines(lines[:-1])
        else:
            messagebox.showwarning("Warning", "Sorry, you can only undo once!", parent=window)
    else:
        messagebox.showwarning("Warning", "Nothing to undo.", parent=window)


def on_btn_click(btn_idx):
    global undo
    """ When a user labels an image """
    label = labels[btn_idx]
    img_filename = image_filenames[img_idx]
    percentage = "(" + str(round(((img_idx + 1) / len(image_filenames))*100, 2)) + "%)"
    print(
        "Img",
        img_idx + 1,
        "of",
        len(image_filenames),
        percentage,
        "Moving",
        img_filename,
        "to label",
        label,
    )

    # append csv
    parts = img_filename.split("_")
    serial = parts[0]
    itr = parts[1].split(".")[0]
    fname = os.path.splitext(img_filename.split(itr)[1])[0]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(outfile, "a") as outcsv:
        outcsv.write(",".join([now, serial, itr, fname, label]) + "\n")

    # move file
    new_img_filename = os.path.join(path, label, image_filenames[img_idx])
    os.rename(os.path.join(path, image_filenames[img_idx]), new_img_filename)
    undo = [new_img_filename, os.path.join(path, image_filenames[img_idx])]
    change_img()


def add_buttons():
    """ Add label buttons to the UI """
    fr_buttons = tk.Frame(window, relief=tk.RAISED, bd=2)
    btn = tk.Button(fr_buttons, text="undo", command=undo_click)
    btn.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    col = 0
    row = 1
    for i, label in enumerate(labels):
        modified_label = ""
        if i in keyboard_shortcuts_indexed_by_idx:
            for letter_idx, letter in enumerate(label):
                if letter_idx == keyboard_shortcuts_indexed_by_idx[i]:
                    modified_label += "[" + letter + "]"
                else:
                    modified_label += letter
        else:
            modified_label = label
        btn = tk.Button(fr_buttons, text=modified_label, command=lambda idx=i: on_btn_click(idx))
        btn.grid(row=row, column=col, sticky="ew", padx=5, pady=5)
        row += 1
        if row >= 10:
            row = 0
            col += 1
    fr_buttons.grid(row=0, column=0, sticky="ns")


def handle_keypress(event):
    """ Handle keyboard shortcuts for labeling """
    if event.char in keyboard_shortcuts_indexed_by_letter:
        on_btn_click(keyboard_shortcuts_indexed_by_letter[event.char])


add_buttons()
window.bind("<Key>", handle_keypress)
change_img()
panel.grid(row=0, column=1, sticky="nsew")
window.mainloop()
