Thermal Camera Monitoring System
================================

This project is a continuous thermal monitoring system built using a Raspberry Pi, an MLX90640 thermal camera, and a variety of sensors. The system monitors real-time temperature data, records videos when a temperature threshold is exceeded, and provides continuous monitoring, making it perfect for applications where constant supervision is needed, such as in engine testing or temperature-critical environments.

Features
--------

-   Real-time thermal image display
-   Automatic video recording when a temperature threshold is exceeded
-   Continuous monitoring mode
-   Data overlays on video, including:
    -   Current time
    -   Maximum temperature
    -   Average temperature
    -   Temperature threshold
-   Touchscreen-friendly interface
-   Configurable temperature thresholds and recording durations

Hardware Requirements
---------------------

To set up this project, you will need the following hardware:

-   **Raspberry Pi 4** (or similar model with Python support)
-   **MLX90640 Thermal Camera** (32x24 resolution)
-   **7-inch Touchscreen Monitor** (for real-time display and interface control)
-   **High-speed microSD card** (for data storage and Raspberry Pi OS)
-   **Cooling fan** (if used in temperature-critical environments)

Optional:

-   **ESP32 for additional monitoring** (integration possible but not covered in this project)

Software Requirements
---------------------

### Raspberry Pi Setup

-   **Raspberry Pi OS**: Ensure your Raspberry Pi is set up with the latest version of Raspberry Pi OS.
-   **Python 3.x**: This project requires Python 3.x.
-   **Matplotlib**: For real-time plotting and visual display of temperature data.



    `sudo apt install python3-matplotlib`

-   **OpenCV**: For video handling and overlaying data on video frames.


    `sudo apt install python3-opencv`

-   **Adafruit MLX90640 library**: For communicating with the MLX90640 thermal camera.


    `pip3 install adafruit-circuitpython-mlx90640`

-   **Requests**: For sending data to a server (if needed).

    `pip3 install requests`

### Other Required Python Libraries

-   `numpy`: For matrix manipulation and temperature data processing.


    `pip3 install numpy`

-   `tkinter`: For creating the graphical user interface (GUI).

    `sudo apt install python3-tk`

### Optional Setup

-   **LAMP Stack** (Linux, Apache, MySQL, PHP): If you plan to store data on a server.

Usage Instructions
------------------

### Running the Project

1.  **Clone the repository** and navigate to the project folder:


    `git clone <repo_url>
    cd thermal-camera-monitoring`

2.  **Connect the MLX90640 camera and touchscreen** to your Raspberry Pi.

3.  **Launch the program** using Python:

    `python3 main.py`

### Menu Options

-   **Test Mode**: Records video for a specific duration and switches to continuous monitoring automatically.
-   **Monitoring Mode**: Continuously monitors temperatures and records videos whenever the temperature exceeds the threshold.

### Customization

-   The default **temperature threshold** and **recording duration** can be adjusted through the GUI or by modifying the code in `main.py`.
-   The system supports touchscreen controls for a user-friendly experience, allowing you to adjust settings without a keyboard.

How It Works
------------

-   **Real-Time Display**: The system continuously displays thermal data in real time using Matplotlib.
-   **Automatic Recording**: When the maximum temperature exceeds the set threshold, a video is recorded for the specified duration. The video includes overlays showing the current time, max temperature, average temperature, and threshold.
-   **Continuous Monitoring**: After recording, the system returns to monitoring mode and continues to check the temperature indefinitely.

Video Overlay Details
---------------------

The following data is displayed on the recorded video:

-   **Current Time**: Shows the time the frame was captured.
-   **Max Temperature**: Displays the highest temperature in the frame.
-   **Average Temperature**: Shows the average temperature across the frame.
-   **Threshold Temperature**: Indicates the threshold value set for triggering the recording.

Contributing
------------

Contributions are welcome! If you have improvements or suggestions, feel free to fork the repository and submit a pull request.
