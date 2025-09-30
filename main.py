import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from math import log10
import csv


def transform_value(value, type):
    if type == "Log10":
        return 10**value
    else:
        return value


def transform_axis(axis_value, axis_type):
    if axis_type == "Log10":
        return log10(axis_value)  # Use log10 for logarithmic axis
    else:
        return axis_value


def format(val):
    if val == 0:
        return "0"
    if abs(val) >= 1e5 or abs(val) < 1e-3:
        return f"{val:.3e}"
    else:
        return f"{val:.4f}".rstrip("0").rstrip(".")


def pixel2coordinate(
    x,
    y,
    x_min,
    x_max,
    y_min,
    y_max,
    image_width,
    image_height,
    x_axis_type,
    y_axis_type,
):
    """Convert pixel coordinates to linear coordinates based on axis limits."""
    x_min = transform_axis(x_min, x_axis_type)
    x_max = transform_axis(x_max, x_axis_type)
    y_min = transform_axis(y_min, y_axis_type)
    y_max = transform_axis(y_max, y_axis_type)

    # Calculate linear coordinates based on pixel position
    x_linear = x_min + (x / image_width) * (x_max - x_min)
    y_linear = y_min + (1 - (y / image_height)) * (y_max - y_min)

    # Apply transformation based on axis type
    x = transform_value(x_linear, x_axis_type)
    y = transform_value(y_linear, y_axis_type)

    return x, y


class DataFromPlotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Data From Plot App")

        # Create main frame to hold both image and controls
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create frame for the image
        self.image_frame = tk.Frame(self.main_frame)
        self.image_frame.pack(side=tk.LEFT, padx=10, pady=10)

        # Create frame for controls
        self.control_frame = tk.Frame(self.main_frame, bg="lightgray", width=200)
        self.control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        self.control_frame.pack_propagate(False)  # Maintain fixed width

        # Create a label to display an image in the image frame
        self.label = tk.Label(self.image_frame, text="Image will be displayed here")
        self.label.pack()

        # Create a canvas for drawing markers on top of the image
        self.canvas = tk.Canvas(self.image_frame, highlightthickness=0)
        self.canvas.pack()

        self.Xs = []
        self.Ys = []
        self.xs = []
        self.ys = []
        self.markers = []  # Store marker IDs for potential removal

        # Create controls in the control frame
        self.create_controls()

        # Load and display the image
        self.load_image()

        # Initialize plot area selection variables
        self.plot_area = None
        self.selecting_plot_area = False
        self.selection_rect = None
        self.plot_area_rect = None

    def load_image(self, file_path=None):
        try:
            # Use provided file_path or default to example.png
            if file_path is None:
                file_path = "example.png"
            original_image = tk.PhotoImage(file=file_path)

            # Get original dimensions
            orig_width = original_image.width()
            orig_height = original_image.height()

            # Define maximum dimensions (accounting for screen space and controls)
            max_width = 1400  # Maximum width for image
            max_height = 900  # Maximum height for image

            # Calculate scaling factor to fit within max dimensions
            scale_x = max_width / orig_width if orig_width > max_width else 1
            scale_y = max_height / orig_height if orig_height > max_height else 1
            scale = min(scale_x, scale_y)

            # Store the scale factor for coordinate conversion
            self.scale_factor = scale

            # Resize if necessary
            if scale < 1:
                # Calculate subsample factor (must be integer)
                subsample_factor = int(1/scale) + 1
                actual_scale = 1 / subsample_factor
                new_width = int(orig_width * actual_scale)
                new_height = int(orig_height * actual_scale)
                print(subsample_factor)
                image = original_image.subsample(subsample_factor, subsample_factor)
                # Update scale factor with actual value
                self.scale_factor = actual_scale
                # Store both original and displayed dimensions
                self.original_width = orig_width
                self.original_height = orig_height
                self.display_width = new_width
                self.display_height = new_height
            else:
                image = original_image
                self.original_width = orig_width
                self.original_height = orig_height
                self.display_width = orig_width
                self.display_height = orig_height

            self.image = image  # Keep a reference to avoid garbage collection

            # Configure canvas size to match displayed image
            self.canvas.config(width=self.display_width, height=self.display_height)

            # Display image on canvas
            self.image_id = self.canvas.create_image(0, 0, anchor="nw", image=image)

            # Hide the label since we're using canvas now
            self.label.pack_forget()

            # Resize window to match displayed image size plus control panel
            window_width = self.display_width + 200 + 40
            window_height = max(
                self.display_height + 40, 660
            )  # Ensure minimum height for controls
            self.root.geometry(f"{window_width}x{window_height}")

            # Remove previous plot area rectangle if it exists
            if hasattr(self, "plot_area_rect") and self.plot_area_rect:
                self.canvas.delete(self.plot_area_rect)
                self.plot_area_rect = None

            # Reset plot area selection
            self.plot_area = None
            self.selecting_plot_area = False
            self.selection_rect = None
            self.plot_area_rect = None
            self.canvas.bind("<Button-1>", self.start_plot_area_selection)
            self.canvas.bind("<B1-Motion>", self.update_plot_area_selection)
            self.canvas.bind("<ButtonRelease-1>", self.finish_plot_area_selection)
            messagebox.showinfo(
                "Select Plot Area", "Please drag to select the plot area (inside axes)."
            )
            self.clear_points()  # Clear points when loading a new image
        except Exception as e:
            print(f"Error loading image: {e}")
            self.label.config(text="Failed to load image")
            # Show label again if image loading fails
            self.label.pack()

    def create_controls(self):
        """Create control panel with buttons and dropdown menus"""
        # Title for the control panel
        title_label = tk.Label(
            self.control_frame,
            text="Controls",
            font=("Arial", 12, "bold"),
            bg="lightgray",
        )
        title_label.pack(pady=(10, 20))

        # Dropdown menu for X-axis type
        x_axis_label = tk.Label(self.control_frame, text="X-Axis Type:", bg="lightgray")
        x_axis_label.pack(anchor="w", padx=10, pady=(0, 5))

        self.x_axis_var = tk.StringVar(value="Linear")
        x_axis_dropdown = ttk.Combobox(
            self.control_frame,
            textvariable=self.x_axis_var,
            values=["Linear", "Log10"],
        )
        x_axis_dropdown.pack(fill="x", padx=10, pady=(0, 10))

        # Dropdown menu for Y-axis type
        y_axis_label = tk.Label(self.control_frame, text="Y-Axis Type:", bg="lightgray")
        y_axis_label.pack(anchor="w", padx=10, pady=(0, 5))

        self.y_axis_var = tk.StringVar(value="Linear")
        y_axis_dropdown = ttk.Combobox(
            self.control_frame,
            textvariable=self.y_axis_var,
            values=["Linear", "Log10"],
        )
        y_axis_dropdown.pack(fill="x", padx=10, pady=(0, 15))

        # Axis limits section
        limits_label = tk.Label(
            self.control_frame,
            text="Axis Limits:",
            font=("Arial", 10, "bold"),
            bg="lightgray",
        )
        limits_label.pack(anchor="w", padx=10, pady=(10, 5))

        # Create frame for axis limits inputs
        limits_frame = tk.Frame(self.control_frame, bg="lightgray")
        limits_frame.pack(fill="x", padx=10, pady=5)

        # X min
        xmin_frame = tk.Frame(limits_frame, bg="lightgray")
        xmin_frame.pack(fill="x", pady=2)
        tk.Label(xmin_frame, text="X min:", bg="lightgray", width=8).pack(side="left")
        self.xmin_var = tk.StringVar(value="0.15")
        self.xmin_entry = tk.Entry(xmin_frame, textvariable=self.xmin_var, width=12)
        self.xmin_entry.pack(side="right", fill="x", expand=True)

        # X max
        xmax_frame = tk.Frame(limits_frame, bg="lightgray")
        xmax_frame.pack(fill="x", pady=2)
        tk.Label(xmax_frame, text="X max:", bg="lightgray", width=8).pack(side="left")
        self.xmax_var = tk.StringVar(value="0.55")
        self.xmax_entry = tk.Entry(xmax_frame, textvariable=self.xmax_var, width=12)
        self.xmax_entry.pack(side="right", fill="x", expand=True)

        # Y min
        ymin_frame = tk.Frame(limits_frame, bg="lightgray")
        ymin_frame.pack(fill="x", pady=2)
        tk.Label(ymin_frame, text="Y min:", bg="lightgray", width=8).pack(side="left")
        self.ymin_var = tk.StringVar(value="-5")
        self.ymin_entry = tk.Entry(ymin_frame, textvariable=self.ymin_var, width=12)
        self.ymin_entry.pack(side="right", fill="x", expand=True)

        # Y max
        ymax_frame = tk.Frame(limits_frame, bg="lightgray")
        ymax_frame.pack(fill="x", pady=2)
        tk.Label(ymax_frame, text="Y max:", bg="lightgray", width=8).pack(side="left")
        self.ymax_var = tk.StringVar(value="4")
        self.ymax_entry = tk.Entry(ymax_frame, textvariable=self.ymax_var, width=12)
        self.ymax_entry.pack(side="right", fill="x", expand=True)

        # CSV Headers section
        headers_label = tk.Label(
            self.control_frame,
            text="CSV Headers:",
            font=("Arial", 10, "bold"),
            bg="lightgray",
        )
        headers_label.pack(anchor="w", padx=10, pady=(15, 5))

        # Create frame for CSV header inputs
        headers_frame = tk.Frame(self.control_frame, bg="lightgray")
        headers_frame.pack(fill="x", padx=10, pady=5)

        # X header
        x_header_frame = tk.Frame(headers_frame, bg="lightgray")
        x_header_frame.pack(fill="x", pady=2)
        tk.Label(x_header_frame, text="X header:", bg="lightgray", width=8).pack(
            side="left"
        )
        self.x_header_var = tk.StringVar(value="x")
        self.x_header_entry = tk.Entry(
            x_header_frame, textvariable=self.x_header_var, width=12
        )
        self.x_header_entry.pack(side="right", fill="x", expand=True)

        # Y header
        y_header_frame = tk.Frame(headers_frame, bg="lightgray")
        y_header_frame.pack(fill="x", pady=2)
        tk.Label(y_header_frame, text="Y header:", bg="lightgray", width=8).pack(
            side="left"
        )
        self.y_header_var = tk.StringVar(value="y")
        self.y_header_entry = tk.Entry(
            y_header_frame, textvariable=self.y_header_var, width=12
        )
        self.y_header_entry.pack(side="right", fill="x", expand=True)

        # Buttons section
        buttons_label = tk.Label(
            self.control_frame,
            text="Actions:",
            font=("Arial", 10, "bold"),
            bg="lightgray",
        )
        buttons_label.pack(anchor="w", padx=10, pady=(20, 5))

        # Clear points button
        clear_btn = tk.Button(
            self.control_frame,
            text="Clear Points",
            command=self.clear_points,
            bg="white",
        )
        clear_btn.pack(fill="x", padx=10, pady=2)

        # Export data button
        export_btn = tk.Button(
            self.control_frame, text="Export Data", command=self.export_data, bg="white"
        )
        export_btn.pack(fill="x", padx=10, pady=2)

        # Load image button
        load_btn = tk.Button(
            self.control_frame,
            text="Load New Image",
            command=self.load_new_image,
            bg="white",
        )
        load_btn.pack(fill="x", padx=10, pady=2)

        # Add button to clear plot area selection
        clear_area_btn = tk.Button(
            self.control_frame,
            text="Clear Plot Area",
            command=self.clear_plot_area,
            bg="white",
        )
        clear_area_btn.pack(fill="x", padx=10, pady=(5, 10))

    def clear_points(self):
        """Clear all collected points"""
        self.Xs.clear()
        self.Ys.clear()
        self.xs.clear()
        self.ys.clear()

        # Remove all markers from canvas
        for marker_id in self.markers:
            self.canvas.delete(marker_id)
        self.markers.clear()

        print("Points cleared")

    def export_data(self):
        """Export collected data points to a CSV file"""
        if not self.xs or not self.ys:
            print("No data points to export")
            messagebox.showwarning(
                "No Data",
                "No data points to export. Please click on the image to collect points first.",
            )
            return

        # Open file dialog to choose save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save data points as CSV",
        )

        if not file_path:  # User cancelled the dialog
            print("Export cancelled")
            return

        try:
            # Write data to CSV file
            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)

                # Write header using user-defined column names
                x_header = self.x_header_var.get().strip() or "x"
                y_header = self.y_header_var.get().strip() or "y"
                writer.writerow([x_header, y_header])

                # Write data points
                for x, y in zip(self.xs, self.ys):
                    writer.writerow([x, y])

            print(f"Successfully exported {len(self.xs)} data points to: {file_path}")
            messagebox.showinfo(
                "Export Successful",
                f"Successfully exported {len(self.xs)} data points to:\n{file_path}",
            )

        except Exception as e:
            print(f"Error saving file: {e}")
            messagebox.showerror("Export Error", f"Error saving file:\n{e}")

    def load_new_image(self):
        filetypes = [
            ("PNG files", "*.png"),
        ]
        file_path = filedialog.askopenfilename(
            title="Select Image File", filetypes=filetypes
        )
        if file_path:
            self.load_image(file_path)

    def on_click(self, event):
        # Only allow marking points if plot area is set and click is inside it
        if not hasattr(self, "plot_area") or self.plot_area is None:
            messagebox.showwarning(
                "Plot Area Not Set", "Please select the plot area first."
            )
            return
        X, Y = event.x, event.y
        try:
            # Use plot area for coordinate mapping
            plot_x_min, plot_y_min, plot_x_max, plot_y_max = self.plot_area
            image_width = plot_x_max - plot_x_min
            image_height = plot_y_max - plot_y_min
            # Adjust click coordinates relative to plot area
            rel_x = X - plot_x_min
            rel_y = Y - plot_y_min
            x_min = float(self.xmin_var.get())
            x_max = float(self.xmax_var.get())
            y_min = float(self.ymin_var.get())
            y_max = float(self.ymax_var.get())
            x, y = pixel2coordinate(
                rel_x,
                rel_y,
                x_min,
                x_max,
                y_min,
                y_max,
                image_width,
                image_height,
                self.x_axis_var.get(),
                self.y_axis_var.get(),
            )

            # Store both pixel and converted coordinates
            self.Xs.append(X)
            self.Ys.append(Y)
            self.xs.append(x)
            self.ys.append(y)

            print(f"Coordinate: (x={format(x)}, y={format(y)})")

            # Draw a marker at the clicked point
            self.draw_marker(X, Y)

        except ValueError as e:
            print(f"Error parsing axis limits: {e}")
            print("Please check your axis limit values for valid expressions")
        except Exception as e:
            print(f"Error converting coordinates: {e}")
            print("Make sure the image is loaded and axis limits are valid")
            import traceback

            traceback.print_exc()

    def draw_marker(self, x, y):
        """Draw a marker at the specified pixel coordinates, scaling with image size"""
        # Scale marker size with image size (e.g., 2% of min dimension, min 6px, max 24px)
        if hasattr(self, "image"):
            image_width = self.image.width()
            image_height = self.image.height()
            min_dim = min(image_width, image_height)
            radius = max(6, min(24, int(min_dim * 0.01)))
        else:
            radius = 8  # fallback
        marker_id = self.canvas.create_oval(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            fill="red",
            outline="black",
            width=2,
        )
        self.markers.append(marker_id)

        # Also draw point number, offset scaled with radius
        point_num = len(self.xs)
        text_id = self.canvas.create_text(
            x + radius * 2,
            y - radius * 2,
            text=str(point_num),
            fill="red",
            font=("Arial", max(10, radius), "bold"),
        )
        self.markers.append(text_id)

    def start_plot_area_selection(self, event):
        self.selecting_plot_area = True
        self.plot_area_start = (event.x, event.y)
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
        self.selection_rect = self.canvas.create_rectangle(
            event.x,
            event.y,
            event.x,
            event.y,
            outline="blue",
            width=2,
            dash=(2, 2),
        )

    def update_plot_area_selection(self, event):
        if self.selecting_plot_area and self.selection_rect:
            self.canvas.coords(
                self.selection_rect,
                self.plot_area_start[0],
                self.plot_area_start[1],
                event.x,
                event.y,
            )

    def finish_plot_area_selection(self, event):
        if not self.selecting_plot_area:
            return
        self.selecting_plot_area = False
        x0, y0 = self.plot_area_start
        x1, y1 = event.x, event.y
        self.plot_area = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        # Remove the temporary selection rectangle
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None
        # Remove previous permanent plot area rectangle if it exists
        if hasattr(self, "plot_area_rect") and self.plot_area_rect:
            self.canvas.delete(self.plot_area_rect)
        # Draw a permanent shaded rectangle for the selected plot area
        x0, y0, x1, y1 = self.plot_area
        self.plot_area_rect = self.canvas.create_rectangle(
            x0,
            y0,
            x1,
            y1,
            outline="blue",
            width=2,
            dash=(2, 2),
        )
        # Place the plot area rectangle just above the image
        if hasattr(self, "image_id"):
            self.canvas.tag_raise(self.plot_area_rect, self.image_id)
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.bind("<Button-1>", self.on_click)
        messagebox.showinfo(
            "Plot Area Selected",
            "Plot area selected!\n\nNow set the axis limits and types in the control panel, then click inside the selected area to mark data points.",
        )

    def clear_plot_area(self):
        """Clear the selected plot area and its rectangle, and require reselection."""
        self.clear_points()
        self.plot_area = None
        if hasattr(self, "plot_area_rect") and self.plot_area_rect:
            self.canvas.delete(self.plot_area_rect)
            self.plot_area_rect = None
        # Re-enable plot area selection
        self.selecting_plot_area = False
        self.selection_rect = None
        self.canvas.bind("<Button-1>", self.start_plot_area_selection)
        self.canvas.bind("<B1-Motion>", self.update_plot_area_selection)
        self.canvas.bind("<ButtonRelease-1>", self.finish_plot_area_selection)
        messagebox.showinfo(
            "Plot Area Cleared", "Please drag to select a new plot area (inside axes)."
        )


parent = tk.Tk()
app = DataFromPlotApp(parent)
parent.mainloop()
