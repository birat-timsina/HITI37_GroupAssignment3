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







#part A

class DifferenceRegion:

    # Minimum Size allowed for a difference region
    MIN_SIZE = 30

    # Maximum size allowed for a difference region
    MAX_SIZE = 70

    #  Initialize construtor in a difference region
    def __init__(self, x, y, w, h, diff_type):
        self.x = x                  # X-coordinate of region
        self.y = y                  # Y-coordinate of region
        self.w = w                  # Width of region
        self.h = h                  # Height of region
        self.diff_type = diff_type  # Type of alteration applied
        self.found = False          # Tracks whether player found this difference

    # Check whether adifference region's mouse falls inside or not
    def contains(self, px, py, tolerance=20):
        return (self.x - tolerance <= px <= self.x + self.w + tolerance and
                self.y - tolerance <= py <= self.y + self.h + tolerance)

    # Return the centre point of the region
    def centre(self):
        return (self.x + self.w // 2, self.y + self.h // 2)

    # Return drawing highlight circles for a suitable radius
    def radius(self):
        return max(self.w, self.h) // 2 + 15


class ImageProcessor:

    # Total number of differences to generate
    NUM_DIFFERENCES = 5

    # Constructor prepare modified version and also to load image
    def __init__(self, image_path):

        # By Using OpenCV load the orginal image
        self.original = cv2.imread(image_path, cv2.IMREAD_COLOR)

        # If image cannot be loaded then raise a error
        if self.original is None:
            raise ValueError(f"Could not open image: {image_path}")

        # Store Image dimensions 
        self.height, self.width = self.original.shape[:2]

        # Create modifications for a copy of orginal image
        self.modified = self.original.copy()

        # List all generated differences to be store
        self.differences = []

        # Generate differences on image automatically
        self._generate_differences()

    # Flip image patch horizontally
    def _apply_flip(self, patch):
        return cv2.flip(patch, 1)

    # Convert from greyscale to image patch
    def _apply_greyscale(self, patch):

        # Convert BGR image into from grayscale to BGR image    
        grey = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)

        # Convert from BGR format for consistency to grayscale back
        return cv2.cvtColor(grey, cv2.COLOR_GRAY2BGR)



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

#Part - D
    #func to update labels for remaining differences and mistakes
    def _update_labels(self):
        #stops func if there is no image processor
        if self.processor is None:
            return  
        
        #count no. of differences that are not found
        remaining = sum(1 for d in self.processor.differences if not d.found)
        #update remaining differences and mistakes label
        self.lbl_remaining.config(text=f"Remaining: {remaining}")
        self.lbl_mistakes.config(text=f"Mistakes: {self.mistakes} / {self.MAX_MISTAKES}")


    #function to interact when user clicks on modified image
    def _on_click(self, event):
        #stops func if there is no image processor or game is already over
        if self.processor is None or self.game_over:
            return

        #convert displayed image coordinates back to original image coordinates by dividing by display scale
        orig_x = int(event.x / self.display_scale)
        orig_y = int(event.y / self.display_scale)

        #variable to store found differences
        hit = None
        
        for diff in self.processor.differences:
            #check if the difference is not already found and if the click within difference region
            if not diff.found and diff.contains(orig_x, orig_y):
                hit = diff
                break
        
        #if hit found, mark it as found and update display
        if hit:
            self._mark_found(hit)
        else:
            #otherwise, register a mistake and update labels
            self._register_mistake()

    #function to register mistakes when user clicks incorrectly
    def _mark_found(self, diff):
        #set difference as found
        diff.found = True
        #get center of coordinates of difference region
        cx, cy = diff.centre()
        r = diff.radius() #get radius

        #draws red circle on both original and modified images to mark found difference
        cv2.circle(self.orig_overlay, (cx, cy), r, (0, 0, 255), 3)
        cv2.circle(self.mod_overlay,  (cx, cy), r, (0, 0, 255), 3)

        #update remaining, differences and mistakes labels
        self._refresh_display()
        self._update_labels()
        #show message for difference found with its type
        self.lbl_msg.config(text=f"✔ Found! ({diff.diff_type})")

        #checks if all differences are found
        if all(d.found for d in self.processor.differences):
            #game end
            self.game_over = True
            #display congratulation popup message
            messagebox.showinfo("Well done!",
                                "You found all 5 differences! 🎉\nLoad a new image to play again.")


