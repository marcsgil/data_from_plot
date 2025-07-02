# Data from Plot

## Usage

1. **Start the App**  
   Run the application with:
   ```
   python main.py
   ```

2. **Load an Image**  
   - Click the **"Load Image"** button in the control panel.
   - Select a PNG file of your plot.

3. **Set Axis Types and Limits**  
   - Choose the X and Y axis types (Linear or Log10) from the dropdown menus.
   - Enter the minimum and maximum values for each axis.  
     You can use scientific notation (e.g., `1e-3` for `0.001`).

4. **Extract Data Points**  
   - Click on the plot image to mark data points.
   - Each click will place a numbered marker and print the corresponding coordinates (converted according to your axis settings).

5. **Export Data**  
   - Use the provided controls (if available) to export the collected data to CSV.

6. **Tips**  
   - Markers and labels scale automatically with the image size for better visibility.
   - If you load a new image, previous markers will be cleared.