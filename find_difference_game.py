import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import random
import math

#  CLASS 1: DifferenceGenerator
#  Handles all OpenCV image manipulation

class DifferenceGenerator:
    """
    Responsible for creating and tracking programmatic
    image differences using OpenCV.
    Demonstrates encapsulation of image-processing logic.
    """

    MIN_SIZE = 30
    MAX_SIZE = 70
    NUM_DIFFERENCES = 5

    def __init__(self):
        self.differences = []   # list of (x, y, w, h) bounding boxes
        self.alteration_types = [
            self._colour_shift,
            self._brightness_patch,
            self._blur_patch,
            self._invert_patch,
            self._tint_patch,
        ]