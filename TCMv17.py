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

# Function to set up the real-time plot
def setup_plot():
    plt.ion()  # Enable interactive mode
    fig, ax = plt.subplots(figsize=(7, 5))
    therm1 = ax.imshow(np.zeros((24, 32)), vmin=0, vmax=60, cmap='coolwarm', interpolation='bilinear')
    cbar = fig.colorbar(therm1)
    cbar.set_label('Temperature [°C]', fontsize=14)
    plt.title('Thermal Image')

    # Add text labels for time, max temp, avg temp, and recording status
    time_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, color='white', fontsize=12)
    max_temp_text = ax.text(0.02, 0.90, '', transform=ax.transAxes, color='white', fontsize=12)
    avg_temp_text = ax.text(0.02, 0.85, '', transform=ax.transAxes, color='white', fontsize=12)
    recording_status = ax.text(0.02, 0.80, '', transform=ax.transAxes, color='red', fontsize=12)

    return fig, ax, therm1, time_text, max_temp_text, avg_temp_text, recording_status

# Close the previous figure window
def close_previous_plot(fig):
    plt.close(fig)

# Update real-time display with the new color scheme and logic
def update_display(fig, ax, therm1, data_array, time_text, max_temp_text, avg_temp_text, recording_status, recording):
    therm1.set_data(np.fliplr(data_array))
    therm1.set_clim(vmin=np.min(data_array), vmax=np.max(data_array))
    
    # New color scheme: black to blue, white, red, yellow
    therm1.set_cmap('coolwarm')

    # Current time, max temp, avg temp
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    max_temp = np.max(data_array)
    avg_temp = np.mean(data_array)

    # Update text
    time_text.set_text(f"Time: {current_time}")
    max_temp_text.set_text(f"Max Temp: {max_temp:.2f}°C")
    avg_temp_text.set_text(f"Avg Temp: {avg_temp:.2f}°C")
    
    if recording:
        recording_status.set_text('Recording...')
    else:
        recording_status.set_text('')

    # Redraw the plot
    fig.canvas.draw_idle()
    plt.pause(0.001)

    # Send data to server
    send_data_to_server(current_time, avg_temp, max_temp, max_temp > TEMP_THRESHOLD)

# Add overlay (date, time, temps) to the video
def add_overlay(frame, max_temp, avg_temp):
    font = cv2.FONT_HERSHEY_SIMPLEX
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    threshold_info = f"Threshold Temp: {TEMP_THRESHOLD}C"
    cv2.putText(frame, f'Time: {current_time}', (10, 30), font, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, f'Max Temp: {max_temp:.2f}C', (10, 60), font, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, f'Avg Temp: {avg_temp:.2f}C', (10, 90), font, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, threshold_info, (10, 120), font, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    return frame

# Record video for a given duration
def record_video(mlx, duration, fig, ax, therm1, time_text, max_temp_text, avg_temp_text, recording_status):
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    video_file = f"thermal_video_{timestamp}.avi"
    out = cv2.VideoWriter(video_file, fourcc, FRAME_RATE, (UPSCALE_WIDTH, UPSCALE_HEIGHT))

    frame = np.zeros((24 * 32,))
    total_frames = FRAME_RATE * duration

    for _ in range(int(total_frames)):
        try:
            mlx.getFrame(frame)
            data_array = np.reshape(frame, (24, 32))
            max_temp = np.max(data_array)
            avg_temp = np.mean(data_array)

            # Update display during recording
            update_display(fig, ax, therm1, data_array, time_text, max_temp_text, avg_temp_text, recording_status, True)

            # Prepare and write video frame
            color_frame = upscale_frame(data_array)
            color_frame = add_overlay(color_frame, max_temp, avg_temp)  # Add overlay info to frame
            out.write(color_frame)

        except ValueError:
            time.sleep(RETRY_DELAY)

    out.release()
    print(f"Recorded video saved: {video_file}")
    update_display(fig, ax, therm1, data_array, time_text, max_temp_text, avg_temp_text, recording_status, False)

# Upscale the thermal frame for video
def upscale_frame(frame):
    normalized_frame = cv2.normalize(np.fliplr(frame), None, 0, 255, cv2.NORM_MINMAX)
    upscaled_frame = cv2.resize(np.uint8(normalized_frame), (UPSCALE_WIDTH, UPSCALE_HEIGHT), interpolation=cv2.INTER_LINEAR)
    return cv2.applyColorMap(upscaled_frame, cv2.COLORMAP_COOL)

# Monitoring loop for continuous monitoring
def monitor_continuously(mlx, fig, ax, therm1, time_text, max_temp_text, avg_temp_text, recording_status):
    frame = np.zeros((24 * 32,))

    while True:
        try:
            mlx.getFrame(frame)
            data_array = np.reshape(frame, (24, 32))

            # Check if max temperature exceeds threshold
            max_temp = np.max(data_array)
            avg_temp = np.mean(data_array)

            # Update display without recording
            update_display(fig, ax, therm1, data_array, time_text, max_temp_text, avg_temp_text, recording_status, False)

            # If temperature exceeds the threshold, record a video
            if max_temp > TEMP_THRESHOLD:
                print(f"Temperature exceeded {TEMP_THRESHOLD}°C, recording video.")
                record_video(mlx, VIDEO_DURATION, fig, ax, therm1, time_text, max_temp_text, avg_temp_text, recording_status)
            else:
                time.sleep(1)  # Delay to avoid excessive CPU usage
        except ValueError:
            time.sleep(RETRY_DELAY)

# Menu for selecting mode (Test Mode or Monitoring Mode) and adjusting test duration
def mode_menu():
    global VIDEO_DURATION

    root = tk.Tk()
    root.title("Main Menu")

    def select_test_mode():
        root.quit()
        root.destroy()  # Ensure the menu closes properly
        run_test_mode()

    def select_monitoring_mode():
        root.quit()
        root.destroy()  # Ensure the menu closes properly
        run_monitoring_mode()

    # Test Duration Adjustment
    duration_label = tk.Label(root, text=f"Test Duration: {VIDEO_DURATION}s", font=("Helvetica", 16))
    duration_label.pack(pady=10)

    def increase_duration():
        global VIDEO_DURATION
        VIDEO_DURATION += 5
        duration_label.config(text=f"Test Duration: {VIDEO_DURATION}s")

    def decrease_duration():
        global VIDEO_DURATION
        VIDEO_DURATION = max(5, VIDEO_DURATION - 5)
        duration_label.config(text=f"Test Duration: {VIDEO_DURATION}s")

    tk.Button(root, text="+", command=increase_duration, font=("Helvetica", 14), width=5).pack(pady=5)
    tk.Button(root, text="-", command=decrease_duration, font=("Helvetica", 14), width=5).pack(pady=5)

    tk.Button(root, text="Test Mode", command=select_test_mode, font=("Helvetica", 14), width=20).pack(pady=20)
    tk.Button(root, text="Monitoring Mode", command=select_monitoring_mode, font=("Helvetica", 14), width=20).pack(pady=20)


    def select_blue_red_mode():
        root.quit()
        root.destroy()  # Close the menu window
        run_blue_red_mode()

    def select_multiple_temp_mode():
        root.quit()
        root.destroy()  # Close the menu window
        run_multiple_temp_mode()

    def select_heatmap_mask_mode():
        root.quit()
        root.destroy()  # Close the menu window
        run_heatmap_mask_mode()

    tk.Button(root, text="BlueRed Mode", command=select_blue_red_mode, font=("Helvetica", 14), width=20).pack(pady=20)
    tk.Button(root, text="Multiple Temp Mode", command=select_multiple_temp_mode, font=("Helvetica", 14), width=20).pack(pady=20)
    tk.Button(root, text="HeatMap Mask Mode", command=select_heatmap_mask_mode, font=("Helvetica", 14), width=20).pack(pady=20)



    root.mainloop()

# Test mode: Record for a defined time and automatically switch to monitoring mode with default values
def run_test_mode():
    mlx = initialize_sensor()
    fig, ax, therm1, time_text, max_temp_text, avg_temp_text, recording_status = setup_plot()
    record_video(mlx, VIDEO_DURATION, fig, ax, therm1, time_text, max_temp_text, avg_temp_text, recording_status)
    
    # Close the current plot window
    close_previous_plot(fig)

    # Automatically switch to continuous monitoring after test mode
    run_monitoring_auto()

# Monitoring mode that runs automatically after the test using default values
def run_monitoring_auto():
    global TEMP_THRESHOLD

    mlx = initialize_sensor()
    fig, ax, therm1, time_text, max_temp_text, avg_temp_text, recording_status = setup_plot()
    
    # Reset "Recording..." status for monitoring mode
    recording_status.set_text('')

    # Start continuous monitoring
    monitor_continuously(mlx, fig, ax, therm1, time_text, max_temp_text, avg_temp_text, recording_status)

# Monitoring mode: Adjust time and temperature threshold
def run_monitoring_mode():
    global TEMP_THRESHOLD, VIDEO_DURATION

    root = tk.Tk()
    root.title("Monitoring Mode")

    # Temp threshold label and buttons
    temp_label = tk.Label(root, text=f"Threshold Temp: {TEMP_THRESHOLD}°C", font=("Helvetica", 16))
    temp_label.pack(pady=10)

    def increase_temp():
        global TEMP_THRESHOLD
        TEMP_THRESHOLD += 1
        temp_label.config(text=f"Threshold Temp: {TEMP_THRESHOLD}°C")

    def decrease_temp():
        global TEMP_THRESHOLD
        TEMP_THRESHOLD -= 1
        temp_label.config(text=f"Threshold Temp: {TEMP_THRESHOLD}°C")

    tk.Button(root, text="+", command=increase_temp, font=("Helvetica", 14), width=5).pack(pady=5)
    tk.Button(root, text="-", command=decrease_temp, font=("Helvetica", 14), width=5).pack(pady=5)

    # Recording duration label and buttons
    duration_label = tk.Label(root, text=f"Recording Duration: {VIDEO_DURATION}s", font=("Helvetica", 16))
    duration_label.pack(pady=10)

    def increase_duration():
        global VIDEO_DURATION
        VIDEO_DURATION += 5
        duration_label.config(text=f"Recording Duration: {VIDEO_DURATION}s")

    def decrease_duration():
        global VIDEO_DURATION
        VIDEO_DURATION = max(5, VIDEO_DURATION - 5)
        duration_label.config(text=f"Recording Duration: {VIDEO_DURATION}s")

    tk.Button(root, text="+", command=increase_duration, font=("Helvetica", 14), width=5).pack(pady=5)
    tk.Button(root, text="-", command=decrease_duration, font=("Helvetica", 14), width=5).pack(pady=5)

    def start_monitoring():
        root.quit()
        root.destroy()  # Ensure the menu closes properly
        mlx = initialize_sensor()
        fig, ax, therm1, time_text, max_temp_text, avg_temp_text, recording_status = setup_plot()

        # Start continuous monitoring
        monitor_continuously(mlx, fig, ax, therm1, time_text, max_temp_text, avg_temp_text, recording_status)

    tk.Button(root, text="Start Monitoring", command=start_monitoring, font=("Helvetica", 14), width=20).pack(pady=20)
    root.mainloop()

def run_multiple_temp_mode():
    mlx = initialize_sensor()
    fig, ax, therm1, time_text, max_temp_text, avg_temp_text, recording_status = setup_plot()

    while True:
        try:
            frame = np.zeros((24 * 32,))
            mlx.getFrame(frame)
            data_array = np.reshape(frame, (24, 32))

            # Display the image
            therm1.set_data(np.fliplr(data_array))
            therm1.set_clim(vmin=np.min(data_array), vmax=np.max(data_array))
            fig.canvas.draw_idle()
            plt.pause(0.001)

            # Show temperature values for specific regions
            regions = [(6, 8), (16, 20), (12, 16)]  # Example: pick center points of grids
            for (i, j) in regions:
                temp = data_array[i, j]
                ax.text(j, i, f'{temp:.1f}°C', color='white', fontsize=10, ha='center')

            plt.pause(0.01)

        except ValueError:
            time.sleep(RETRY_DELAY)
def run_heatmap_mask_mode():
    mlx = initialize_sensor()
    fig, ax, therm1, time_text, max_temp_text, avg_temp_text, recording_status = setup_plot()

    while True:
        try:
            frame = np.zeros((24 * 32,))
            mlx.getFrame(frame)
            data_array = np.reshape(frame, (24, 32))

            # Apply mask for temperatures above the threshold
            mask = np.zeros_like(data_array)
            mask[data_array > TEMP_THRESHOLD] = 255  # Mask hot regions

            # Create a transparent overlay for the mask
            masked_frame = cv2.addWeighted(np.fliplr(data_array), 0.5, mask, 0.5, 0)

            therm1.set_data(masked_frame)
            therm1.set_clim(vmin=np.min(data_array), vmax=np.max(data_array))
            fig.canvas.draw_idle()
            plt.pause(0.001)

        except ValueError:
            time.sleep(RETRY_DELAY)

# Main loop to start the menu
def main():
    mode_menu()

if __name__ == '__main__':
    main()
