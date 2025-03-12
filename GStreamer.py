import cv2
import time
import sys
import threading
import numpy as np

# Gstreamer pipeline to receive video from camera
cap_pipeline = ("v4l2src device=/dev/video0 ! video/x-raw, width=640, height=480, framerate=15/1 ! videoconvert ! appsink")

# Gstreamer pipeline to send processed video via UDP
gst_pipeline = (
    "appsrc is-live=true ! videoconvert ! x264enc tune=zerolatency bitrate=2000 speed-preset=superfast ! "
    "rtph264pay ! udpsink host=192.168.1.17 port=5000"
)

frame_lock: threading.Lock = threading.Lock()
"""
Lock used to avoid data conflict when both threads access the 'frame' variable.
"""

frame: np.ndarray | None = None
"""
Used to store frame shared among threads
"""

running: bool = True
"""
Used to control the loop of both threads
"""

def image_processing() -> None:
    '''
    Thread 1:
    - Read video from camera
    - Implement image-processing algorithms
    - Command to control drone
    '''

    global frame, running
    cap = cv2.VideoCapture(cap_pipeline, cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        print("Failed to connect to stream")
        sys.exit()
    print("Connected to stream successfully")
    
    while running:
        ret, temp_frame = cap.read()
        if not ret:
            print("Did not get frame!")
            continue
        
        # Process image (e.g., drawing bounding box)
        cv2.rectangle(temp_frame, (150, 100), (500, 400), (0, 255, 0), 2)
        
        # Store processed frame safely
        with frame_lock:
            frame = temp_frame.copy()
    
    cap.release()
    print("Image processing thread stopped")

def stream_video() -> None:
    '''
    Thread 2:
    - Receive processed frame from thread 1
    - Send it on to laptop via UDP
    '''

    global frame, running
    out = cv2.VideoWriter(gst_pipeline, cv2.CAP_GSTREAMER, 0, 15, (640, 480), True)
    if not out.isOpened():
        print("Failed to open GStreamer pipeline")
        sys.exit()
    print("Streaming video to laptop...")
    
    while running:
        with frame_lock:
            if frame is not None:
                out.write(frame)
    
    out.release()
    print("Streaming thread stopped")

if __name__ == '__main__':
	# Create threads
	image_thread = threading.Thread(target=image_processing)
	stream_thread = threading.Thread(target=stream_video)

	# Start threads
	image_thread.start()
	stream_thread.start()

	try:
		while True:
			time.sleep(1) # To reduce CPU load, prevent loop from running too fast and avoid unnecessary resource consumption
	except KeyboardInterrupt:
		print("Stopping threads...")
		running = False
		image_thread.join()
		stream_thread.join()
		print("Threads stopped, exiting program")
