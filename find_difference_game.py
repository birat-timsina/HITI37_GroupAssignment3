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

        self.canvas_mod.bind("<Button-1>", self._on_canvas_click)

        self._original_photo = None
        self._modified_photo = None
        self._source_image = None
        self._display_image_size = (self.image_width, self.image_height)

        self._refresh_status("Load an image to start.")

    def _refresh_status(self, message=None):
        remaining_text = self.total_remaining if self.total_remaining else "–"
        self.lbl_remaining.config(text=f"Remaining: {remaining_text}")
        self.lbl_mistakes.config(text=f"Mistakes: {self.mistakes} / {self.MAX_MISTAKES}")
        if message is not None:
            self.lbl_msg.config(text=message)

    def _show_on_canvas(self, canvas, pil_image, attr_name):
        canvas_width = int(canvas.cget("width"))
        canvas_height = int(canvas.cget("height"))
        display_image = pil_image.copy()
        display_image.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)

        photo = ImageTk.PhotoImage(display_image)
        canvas.delete("all")
        canvas.create_image(canvas_width // 2, canvas_height // 2, image=photo, anchor="center")
        setattr(self, attr_name, photo)
        self._display_image_size = display_image.size

    def _load_image(self):
        image_path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("All files", "*.*"),
            ],
        )
        if not image_path:
            return

        try:
            source = Image.open(image_path).convert("RGB")
        except Exception as exc:
            messagebox.showerror("Load Image", f"Could not open image:\n{exc}")
            return

        self._source_image = source
        self.processor = DifferenceGenerator()
        self.mistakes = 0
        self.total_remaining = 0
        self.game_over = False

        self._show_on_canvas(self.canvas_orig, source, "_original_photo")
        self._show_on_canvas(self.canvas_mod, source, "_modified_photo")
        self._refresh_status("Image loaded. UI is ready.")

    def _reveal_all(self):
        if self._source_image is None:
            self._refresh_status("Load an image first.")
            return

        self.game_over = True
        self._refresh_status("Reveal mode is available after difference generation.")

    def _on_canvas_click(self, event):
        if self._source_image is None:
            self._refresh_status("Load an image before clicking.")
            return

        self._refresh_status(f"Clicked at ({event.x}, {event.y}). UI preview only.")


if __name__ == "__main__":
    app = FindDiffGame()
    app.mainloop()





