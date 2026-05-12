import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import random
import math

#  CLASS 1: DifferenceGenerator
#  Handles all OpenCV image manipulation

class ImageLoader:
    """
    Handles loading images from file paths, validation, and conversion
    to PhotoImage format for display in Tkinter.
    Part C: Image Loader Module
    """

    def __init__(self, file_path):
        """
        Load an image from file_path and prepare original and modified copies.
        
        Args:
            file_path (str): Path to the image file (jpg, png, bmp, etc.)
        
        Raises:
            ValueError: If file cannot be loaded or is invalid
        """
        if not file_path or not isinstance(file_path, str):
            raise ValueError("Invalid file path provided")
        
        try:
            # Load image using OpenCV (BGR format)
            self.original = cv2.imread(file_path)
            if self.original is None:
                raise ValueError(f"Could not load image from {file_path}")
            
            # Validate image dimensions
            h, w = self.original.shape[:2]
            if h < 100 or w < 100:
                raise ValueError(f"Image too small ({w}x{h}). Minimum 100x100 pixels required.")
            if h > 4000 or w > 4000:
                raise ValueError(f"Image too large ({w}x{h}). Maximum 4000x4000 pixels.")
            
            # Create a copy for modifications
            self.modified = self.original.copy()
            self.differences = []
            self.file_path = file_path
            
        except Exception as e:
            raise ValueError(f"Error loading image: {str(e)}")
    
    @staticmethod
    def cv2_to_photoimage(cv_image, max_width=500, max_height=400):
        """
        Convert OpenCV BGR image to Tkinter PhotoImage, scaling to fit bounds.
        
        Args:
            cv_image (np.ndarray): OpenCV image in BGR format
            max_width (int): Maximum display width
            max_height (int): Maximum display height
        
        Returns:
            tuple: (PhotoImage object, scale_factor)
        """
        try:
            # Get original dimensions
            h, w = cv_image.shape[:2]
            
            # Calculate scale to fit within max bounds while preserving aspect ratio
            scale = min(max_width / w, max_height / h, 1.0)
            
            # Resize if needed
            if scale < 1.0:
                new_w = int(w * scale)
                new_h = int(h * scale)
                scaled = cv2.resize(cv_image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            else:
                scaled = cv_image
                scale = 1.0
            
            # Convert BGR to RGB
            rgb = cv2.cvtColor(scaled, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image then Tkinter PhotoImage
            pil_image = Image.fromarray(rgb)
            photo = ImageTk.PhotoImage(pil_image)
            
            return photo, scale
            
        except Exception as e:
            raise ValueError(f"Error converting image to PhotoImage: {str(e)}")


# Alias for backwards compatibility
ImageProcessor = ImageLoader


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

        # Build the UI (buttons, labels, canvases)
        self._build_ui()

    def _build_ui(self):
        # Top control bar: load image and reveal buttons
        ctrl = tk.Frame(self, bg="#2c2c2c", pady=8)
        ctrl.pack(fill=tk.X)

        tk.Button(ctrl, text="📂  Load Image", command=self._load_image,
                  bg="#4a90d9", fg="white", font=("Arial", 11, "bold"),
                  relief=tk.FLAT, padx=12, pady=4).pack(side=tk.LEFT, padx=10)

        tk.Button(ctrl, text="👁  Reveal All", command=self._reveal_all,
                  bg="#e07b39", fg="white", font=("Arial", 11, "bold"),
                  relief=tk.FLAT, padx=12, pady=4).pack(side=tk.LEFT, padx=4)

        # Status bar: remaining differences, mistakes and message area
        status = tk.Frame(self, bg="#1e1e1e", pady=6)
        status.pack(fill=tk.X)

        self.lbl_remaining = tk.Label(status, text="Remaining: –",
                                      fg="#90ee90", bg="#1e1e1e",
                                      font=("Arial", 12, "bold"))
        self.lbl_remaining.pack(side=tk.LEFT, padx=20)

        self.lbl_mistakes = tk.Label(status, text="Mistakes: 0 / 3",
                                     fg="#ff9999", bg="#1e1e1e",
                                     font=("Arial", 12, "bold"))
        self.lbl_mistakes.pack(side=tk.LEFT, padx=20)

        self.lbl_msg = tk.Label(status, text="Load an image to start!",
                                fg="#ffff99", bg="#1e1e1e",
                                font=("Arial", 11))
        self.lbl_msg.pack(side=tk.RIGHT, padx=20)

        # Image area: two canvases side-by-side for original and modified images
        # Each canvas displays a scaled version of the loaded image. The
        # modified canvas is interactive (accepts clicks) while the original is
        # read-only and used as a reference.
        img_frame = tk.Frame(self, bg="#1e1e1e")
        img_frame.pack(padx=10, pady=10)

        tk.Label(img_frame, text="Original", bg="#1e1e1e", fg="#cccccc",
                 font=("Arial", 10)).grid(row=0, column=0, pady=(0, 4))
        tk.Label(img_frame, text="Modified  (click here!)", bg="#1e1e1e",
                 fg="#cccccc", font=("Arial", 10)).grid(row=0, column=1, pady=(0, 4))

        # Canvas for the original image (left)
        self.canvas_orig = tk.Canvas(img_frame, width=500, height=400,
                         bg="#333", highlightthickness=1,
                         highlightbackground="#555")
        self.canvas_orig.grid(row=1, column=0, padx=5)

        # Canvas for the modified image (right) — the player clicks here to
        # guess differences. Use `cursor="crosshair"` to make it obvious.
        self.canvas_mod = tk.Canvas(img_frame, width=500, height=400,
                        bg="#333", highlightthickness=1,
                        highlightbackground="#555",
                        cursor="crosshair")
        self.canvas_mod.grid(row=1, column=1, padx=5)

        # Bind clicks on the modified image canvas to handle guesses. Note:
        # clicks arrive in canvas/display coordinates; they are converted to
        # original image coordinates in `_on_click` by dividing by
        # `self.display_scale` so the hit-testing uses the true pixel values.
        self.canvas_mod.bind("<Button-1>", self._on_click)

    def _load_image(self):
        path = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        )
        if not path:
            return

        # Load the image and create ImageProcessor which generates differences.
        # `ImageProcessor` reads the image and creates a `modified` version with
        # synthetic alterations. The `differences` list is populated with
        # `DifferenceRegion` objects describing altered patches.
        try:
            self.processor = ImageProcessor(path)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        # Reset game state for the new image
        self.mistakes = 0
        self.game_over = False

        # Create drawing overlays so we can mark found/revealed differences.
        # We copy the images so marking (drawing circles) does not mutate the
        # original images stored by the processor; overlays are used purely for
        # display and are reset each time a new image is loaded.
        h, w = self.processor.original.shape[:2]
        self.orig_overlay = self.processor.original.copy()
        self.mod_overlay  = self.processor.modified.copy()

        # Update the UI to show the loaded image and reset labels. This will
        # convert the overlays into Tk PhotoImage objects scaled to fit the
        # canvas, and store `self.display_scale` so clicks map correctly.
        self._refresh_display()
        self._update_labels()
        self.lbl_msg.config(text="Click on the right image to find differences!")

    def _refresh_display(self):
        max_w = 500
        max_h = 400

        # Convert OpenCV images to PhotoImage with scaling to fit the UI. The
        # helper returns a `PhotoImage` and the numeric `scale` applied. We
        # store that scale to later map canvas click coordinates back to the
        # original image pixel coordinates.
        photo_orig, scale = ImageProcessor.cv2_to_photoimage(
            self.orig_overlay, max_w, max_h)
        self.display_scale = scale

        # Note: `shape` returns (height, width). We compute the scaled display
        # dimensions by multiplying by the `scale` factor returned above.
        disp_h, disp_w = self.orig_overlay.shape[:2]
        disp_w_scaled = int(disp_w * scale)
        disp_h_scaled = int(disp_h * scale)

        # Configure the canvas to the new size and draw the image. It's
        # important to store a reference to the `PhotoImage` on the canvas
        # object (e.g., `self.canvas_orig.image`) to prevent Python's garbage
        # collector from reclaiming it; Tk will otherwise display a blank box.
        self.canvas_orig.config(width=disp_w_scaled, height=disp_h_scaled)
        self.canvas_orig.delete("all")
        self.canvas_orig.create_image(0, 0, anchor=tk.NW, image=photo_orig)
        self.canvas_orig.image = photo_orig

        # Modified image uses the same scale; create and retain its PhotoImage
        # reference for the same GC reason.
        photo_mod, _ = ImageProcessor.cv2_to_photoimage(
            self.mod_overlay, max_w, max_h)
        self.canvas_mod.config(width=disp_w_scaled, height=disp_h_scaled)
        self.canvas_mod.delete("all")
        self.canvas_mod.create_image(0, 0, anchor=tk.NW, image=photo_mod)
        self.canvas_mod.image = photo_mod

# ==================== End of Part-C ====================




