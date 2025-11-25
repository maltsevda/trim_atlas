#!/usr/bin/env python

# Trimming of images in the Defold atlas.
# Dependencies:
#   > pip install --upgrade Pillow
#   > pip install --upgrade deftree
# Author: Denis Maltsev (https://github.com/maltsevda)

import os, sys
import shutil
import argparse
import deftree
from PIL import Image

# ------------------------------------------------------------------------------
# Global settings and constants
# ------------------------------------------------------------------------------

PROJECT_NAME = 'game.project'
ELEMENT_IMAGES = 'images'
ATTR_IMAGE = 'image'
ATTR_PIVOT_X = 'pivot_x'
ATTR_PIVOT_Y = 'pivot_y'
ATTR_BORDERS = 'inner_padding'
EXT_BAK = '.bak'

# ------------------------------------------------------------------------------
# Auxiliary functions
# ------------------------------------------------------------------------------

# Finds the root folder of the Defold project (based on the script location)
def get_project_dir(filename: str) -> str:
    absname = os.path.abspath(filename)
    dir = os.path.dirname(absname)
    while True:
        project_path = os.path.join(dir, PROJECT_NAME)
        if os.path.exists(project_path):
            return dir
        if os.path.ismount(dir):
            return None
        dir = os.path.dirname(dir)

# Trimming the sprite image ant returning its dimensions
def crop_image(filename: str) -> tuple[int, int] | tuple[int, int, int, int]:
    with Image.open(filename) as img:
        size = img.size
        bbox = img.getbbox()
        img = img.crop(bbox)
        img.save(filename)
        return size, bbox
    return None, None

# ------------------------------------------------------------------------------
# Sprite pivot point calculations
# ------------------------------------------------------------------------------

# Returning the original pivot point of the sprite or its center
def get_source_pivot(element: deftree.Element) -> tuple[float, float]:
    attr_pivot_x = element.get_attribute(ATTR_PIVOT_X)
    attr_pivot_y = element.get_attribute(ATTR_PIVOT_Y)
    pivot_x = attr_pivot_x.value if attr_pivot_x != None else 0.5
    pivot_y = attr_pivot_y.value if attr_pivot_y != None else 0.5
    return (pivot_x, pivot_y)

# Modifying the original pivot point of the sprite with its new dimensions
def calc_pivot(source_size: tuple[int, int], source_pivot: tuple[float, float],
               sprite_bbox:  tuple[int, int, int, int], border: int) -> tuple[float, float]:
    if sprite_bbox is None:
        return (source_pivot[0], source_pivot[1])
    source_w, source_h = source_size[0], source_size[1]
    sprite_x, sprite_y = sprite_bbox[0], sprite_bbox[1]
    sprite_w, sprite_h = sprite_bbox[2] - sprite_bbox[0], sprite_bbox[3] - sprite_bbox[1]
    spivot_dx = (source_pivot[0] - 0.5) * (source_w + border * 2)
    spivot_dy = (source_pivot[1] - 0.5) * (source_h + border * 2)
    pivot_x = (source_w / 2 - sprite_x + spivot_dx + border) / (sprite_w + border * 2)
    pivot_y = (source_h / 2 - sprite_y + spivot_dy + border) / (sprite_h + border * 2)
    return (pivot_x, pivot_y)

# ------------------------------------------------------------------------------
# Functions for modifying atlas Elements
# ------------------------------------------------------------------------------

def set_attribute(element: deftree.Element, name: str, value: float):
    attr = element.get_attribute(name)
    if attr == None:
        element.add_attribute(name, value)
    else:
        attr.value = value

# Modifying image Element: cropping the sprite and calculating new pivot point
def modify_image(element: deftree.Element, project_dir: str, border: int, backup: bool):
    image_path = element.get_attribute(ATTR_IMAGE).value
    image_path = os.path.normpath(project_dir + image_path)
    if os.path.isfile(image_path):
        if backup:
            shutil.copy(image_path, image_path + EXT_BAK)
        source_size, sprite_bbox = crop_image(image_path)
        source_pivot = get_source_pivot(element)
        pivot = calc_pivot(source_size, source_pivot, sprite_bbox, border)
        set_attribute(element, ATTR_PIVOT_X, pivot[0])
        set_attribute(element, ATTR_PIVOT_Y, pivot[1])

# ------------------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------------------

def main(ns: argparse.Namespace):
    # Detecting of all necessary files and paths
    atlas_path = os.path.abspath(ns.filename)
    if not os.path.isfile(atlas_path):
        return False, 'Atlas file not found!'
    project_dir = get_project_dir(atlas_path)
    if not project_dir:
        return False, f'{PROJECT_NAME} not found!'
    # Backuping the atlas file
    if ns.backup:
        shutil.copy(ns.filename, ns.filename + EXT_BAK)
    # Parsing the atlas file
    tree = deftree.parse(ns.filename)
    root = tree.get_root()
    attr_border = root.get_attribute(ATTR_BORDERS)
    border = attr_border.value if attr_border != None else 0
    # Trimming all images Elements in the atlas file
    for child in root.iter_elements(ELEMENT_IMAGES):
        modify_image(child, project_dir, border, ns.backup)
    tree.write()
    return True, 'Ok'

if __name__ == '__main__':
    # Parsing command arguments
    parser = argparse.ArgumentParser(description='Trimming of images in the Defold atlas.')
    parser.add_argument('filename', type=str, help='The name of the atlas file. (.atlas)')
    parser.add_argument('-b', '--backup', action='store_true', help='Creation of a backup (.bak) of all modified files.')
    namespace = parser.parse_args()
    # Running the main program and printing errors if exist
    err, msg = main(namespace)
    if not err:
        print('Error: ' + msg)
