
import time
import board
import busio
import numpy as np
import adafruit_mlx90640
import matplotlib
matplotlib.use('TkAgg')
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
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
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
            requests.post(url, data=data)
        except Exception as e:
            print(f"Failed to send data: {e}")

# Function to detect the hottest spot and display temperatures around it in real-time
def multiple_point_detection(mlx, temp_threshold):
    plt.ion()  # Turn on interactive mode for live updating
    fig, ax = plt.subplots()

    while True:
        # Capture a thermal frame
        thermal_data = [0] * 768  # Placeholder for 24x32 thermal data
        try:
            mlx.getFrame(thermal_data)
        except Exception as e:
            print(f"Error capturing data: {e}")
            time.sleep(RETRY_DELAY)
            continue

        # Reshape the thermal data to a 24x32 matrix (sensor resolution)
        thermal_array = np.array(thermal_data).reshape((24, 32))

        # Find the hottest point (maximum temperature)
        max_temp = np.max(thermal_array)
        max_temp_coords = np.unravel_index(np.argmax(thermal_array), thermal_array.shape)

        # Define a region around the max point (3x3 region)
        region_size = 1  # radius around the max point
        x, y = max_temp_coords

        # Collect temperatures around the region
        region_temps = []
        for i in range(max(0, x-region_size), min(24, x+region_size+1)):
            for j in range(max(0, y-region_size), min(32, y+region_size+1)):
                region_temps.append((i, j, thermal_array[i, j]))

        # Clear the previous plot and plot the updated thermal data
        ax.clear()
        ax.imshow(thermal_array, cmap='jet', interpolation='nearest')

        # Color code the region
        for i, j, temp in region_temps:
            if temp < temp_threshold - 5:
                color = 'white'
            elif temp_threshold - 5 <= temp <= temp_threshold:
                color = 'yellow'
            else:
                color = 'red'
            ax.text(j, i, f"{temp:.1f}", color=color, ha='center', va='center', fontsize=8, fontweight='bold')

        # Highlight the hottest point
        ax.scatter([y], [x], color='black', marker='x')

        # Add a title and display the colorbar
        ax.set_title("Multiple Point Detection")
        plt.colorbar(ax.imshow(thermal_array, cmap='jet', interpolation='nearest'), ax=ax)

        # Pause to allow the plot to update
        plt.pause(0.1)

# Example function to switch between modes and process data
def capture_and_process_data(mlx, mode="Blue2Red"):
    if mode == "MultiplePointDetection":
        # New multiple point detection mode with real-time updates
        multiple_point_detection(mlx, TEMP_THRESHOLD)
    else:
        # Fallback to a static Blue2Red Mode (existing)
        thermal_data = [0] * 768  # Placeholder for 24x32 thermal data
        try:
            mlx.getFrame(thermal_data)
        except Exception as e:
            print(f"Error capturing data: {e}")
            return

        plt.imshow(np.array(thermal_data).reshape((24, 32)), cmap='RdBu', interpolation='nearest')
        plt.colorbar(label='Temperature (°C)')
        plt.title("Blue2Red Mode")
        plt.show()

# Main entry point
if __name__ == "__main__":
    mlx = initialize_sensor()
    # Capture and process data in the selected mode
    capture_and_process_data(mlx, mode="MultiplePointDetection")
