
import time
import board
import busio
import numpy as np
import adafruit_mlx90640
import matplotlib
matplotlib.use('TkAgg')  # Use the TkAgg backend to avoid Wayland issues
import matplotlib.pyplot as plt
import cv2
import requests
import tkinter as tk
from datetime import datetime
import socket

# Configuration defaults
TEMP_THRESHOLD = 60  # Default temperature threshold
VIDEO_DURATION = 90  # Default recording duration in seconds
MONITOR_DURATION = 90  # Default monitoring duration (for auto switch after test)
UPSCALE_WIDTH = 640  # Width for upscaling
UPSCALE_HEIGHT = 480  # Height for upscaling
FRAME_RATE = 2  # Frame rate of the MLX90640 sensor
RETRY_DELAY = 0.5  # Delay in seconds before retrying a failed frame

# Initialize sensor
def initialize_sensor():
    i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
    mlx = adafruit_mlx90640.MLX90640(i2c)
    mlx.refresh_rate = adafruit.mlx90640.RefreshRate.REFRESH_2_HZ
    return mlx

# Check Wi-Fi status using socket connection to an external website
def check_wifi():
    try:
        socket.create_connection(("www.google.com", 80), timeout=5)
        return True
    except OSError:
        return False

# Function to send data to the server (only if Wi-Fi is available)
def send_data_to_server(timestamp, temperature, max_temperature, threshold_exceeded):
    if check_wifi():
        url = 'http://<your_pi_ip>/temperature_receiver.php'
        data = {
            'timestamp': timestamp,
            'temperature': temperature,
            'max_temperature': max_temperature,
            'threshold_exceeded': threshold_exceeded
        }
        try:
            response = requests.post(url, data=data)
            print("Data sent to server:", response.status_code)
        except Exception as e:
            print(f"Error sending data: {e}")
    else:
        print("No network, data not sent")

# Add radio buttons for selecting view modes
def setup_gui(root, mode_var):
    tk.Radiobutton(root, text="Max and Avg", variable=mode_var, value="MaxAvg").pack(side=tk.TOP, anchor=tk.W)
    tk.Radiobutton(root, text="Multi Location", variable=mode_var, value="MultiLocation").pack(side=tk.TOP, anchor=tk.W)

# Function to set up the real-time plot
def setup_plot():
    plt.ion()  # Enable interactive mode
    fig, ax = plt.subplots()
    return fig, ax

# Detect hottest and coldest areas
def find_extreme_areas(frame, num_hot_areas=3):
    flat_frame = frame.flatten()
    indices = np.argsort(flat_frame)
    
    coldest_idx = indices[0]  # Coldest area
    hottest_idxs = indices[-num_hot_areas:]  # Top hot areas
    return coldest_idx, hottest_idxs

# Plot temperature data with selected view mode
def plot_frame(ax, frame, mode, threshold):
    ax.clear()
    if mode == "MaxAvg":
        ax.imshow(frame, cmap="plasma")
        ax.set_title("Max and Avg Temperature View")
    elif mode == "MultiLocation":
        ax.imshow(frame, cmap="plasma")
        ax.set_title("Multi Location View")
        
        # Detect hottest and coldest areas
        coldest_idx, hottest_idxs = find_extreme_areas(frame)
        
        # Convert flat indices back to 2D coordinates
        coldest_coords = np.unravel_index(coldest_idx, frame.shape)
        hottest_coords = [np.unravel_index(idx, frame.shape) for idx in hottest_idxs]

        # Mark coldest area with a blue circle and label
        ax.scatter(coldest_coords[1], coldest_coords[0], color="blue", label=f"Coldest: {frame[coldest_coords[0], coldest_coords[1]]:.0f}C")
        ax.text(coldest_coords[1], coldest_coords[0], f"{frame[coldest_coords[0], coldest_coords[1]]:.0f}C", color="blue", fontsize=12)

        # Mark hottest areas and add arrows for nearby colder areas
        for hot_coords in hottest_coords:
            ax.scatter(hot_coords[1], hot_coords[0], color="red", label=f"Hot: {frame[hot_coords[0], hot_coords[1]]:.0f}C")
            ax.text(hot_coords[1], hot_coords[0], f"{frame[hot_coords[0], hot_coords[1]]:.0f}C", color="red", fontsize=12)
        
        ax.legend()

    plt.draw()

# Main function to run the live stream
def run_live_stream():
    mlx = initialize_sensor()
    fig, ax = setup_plot()

    root = tk.Tk()
    root.title("Thermal Camera Menu")
    mode_var = tk.StringVar(value="MaxAvg")
    
    # Set up the GUI with radio buttons for mode selection
    setup_gui(root, mode_var)
    
    def update_stream():
        frame = np.zeros((24,32))  # Placeholder for actual frame data from MLX90640
        try:
            mlx.getFrame(frame)  # Update frame data from the camera
            
            # Plot the data with the selected view mode
            plot_frame(ax, frame, mode_var.get(), TEMP_THRESHOLD)
        except Exception as e:
            print(f"Error reading from sensor: {e}")
        
        root.after(500, update_stream)  # Refresh every 500 ms
    
    # Start the live stream and GUI loop
    update_stream()
    root.mainloop()

# Call the live stream function
if __name__ == "__main__":
    run_live_stream()
