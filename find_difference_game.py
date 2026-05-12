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












# ==================== Part-C: FindDiffGame Constructor + UI Builder + Image Loader + Display Refresh ====================

class FindDiffGame(tk.Tk):

    MAX_MISTAKES = 3

    def __init__(self):
        super().__init__()
        self.title("Find the Difference Game")
        self.resizable(False, False)

        # Initialize game state variables
        
        self.processor = DifferenceGenerator()     # `processor`: manages generated image differences
        self.mistakes = 0       # `mistakes`: count of incorrect clicks by the player
        self.total_remaining = 0     # `total_remaining`: helper counter for differences remaining (kept for clarity)
        self.game_over = False   # `game_over`: when True, input is ignored until a new image is loaded
        self.display_scale = 1.0        # `display_scale`: ratio used to map canvas (display) coordinates back to
                                        # original image coordinates. When images are scaled down
                                        # for display, we divide click coordinates by this value
                                        # to check against the true pixel locations stored in
                                        # `DifferenceRegion` objects.
        self.image_width = 500      # `image_width`/`image_height`: default canvas dimensions used for layout
        self.image_height = 400        

        self.orig_overlay = None        # `orig_overlay`/`mod_overlay`: working copies of the images used for
                                        # drawing markers (so we don't change the processor's stored images directly).
        self.mod_overlay = None         
