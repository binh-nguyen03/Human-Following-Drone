import cv2
import time
import sys
import threading
import queue
import numpy as np

# Gstreamer pipeline to receive video from camera
cap_pipeline = ("v4l2src device=/dev/video0 ! video/x-raw, width=640, height=480, framerate=15/1 ! videoconvert ! appsink")

# Gstreamer pipeline to send processed video via UDP
gst_pipeline = (
	"appsrc is-live=true ! videoconvert ! x264enc tune=zerolatency bitrate=2000 speed-preset=superfast ! "
	"rtph264pay ! udpsink host=192.168.1.101 port=5000"
)

frame_queue: queue = queue.Queue(maxsize=1)
"""
Used to store the latest frame with the maximum of only one frame (maxsize = 1)
"""

frame: np.ndarray | None = None
"""
Used to store frame shared among threads
"""

running: threading.Event = threading.Event()
"""
Used to control the loop of both threads
"""
running.set() # Start the loops

def image_processing() -> None:
	'''
	Thread 1:
	- Read video from camera
	- Implement image-processing algorithms
	- Command to control drone
	'''

	global frame, running

	try:
		cap = cv2.VideoCapture(cap_pipeline, cv2.CAP_GSTREAMER)
		if not cap.isOpened():
			print("Failed to connect to stream")
			return 
		print("Connected to stream successfully")

		error_count: int = 0  # Limit the number of errors
	
		while running.is_set():
			ret, temp_frame = cap.read()
			
			if not ret:
				error_count += 1
				print(f"Did not get frame! Attempt {error_count}/10")
				
				if error_count >= 10:
					print("Too many failed attempts, stopping image processing thread.")
					break
				continue

			if error_count != 0:
				error_count = 0
			
			# Process image (e.g., drawing bounding box)
			cv2.rectangle(temp_frame, (150, 100), (640, 480), (0, 255, 0), 2)
			
			# Insert new frame into queue (eliminate old one if queue's full)
			if not frame_queue.full():
				frame_queue.put(temp_frame)
			else:
				frame_queue.get()  # Delete old frame
				frame_queue.put(temp_frame)

			# cv2.waitKey(1) # To optimize OpenCV, make image processing more stable

	except Exception as e:
		print(f"Unexpected error in image processing: {e}")

	finally: # Make sure resource is always freed	
		cap.release()
		print("Image processing thread stopped")

def stream_video() -> None:
	'''
	Thread 2:
	- Receive processed frame from thread 1
	- Send it on to laptop via UDP
	'''

	global frame, running
	out = None

	try:
		out = cv2.VideoWriter(gst_pipeline, cv2.CAP_GSTREAMER, 0, 15, (640, 480), True)
		if not out.isOpened():
			print("Failed to open GStreamer pipeline")
			return
		print("Streaming video to laptop...")

		error_count = 0
		while running.is_set():
			try:
				frame = frame_queue.get_nowait() # Get the latest frame from queue
				if frame is not None and isinstance(frame, np.ndarray): 
					out.write(frame)

			except queue.Empty:
				continue
				# Not print log, avoid spamming console

			except cv2.error as e:
				error_count += 1
				print(f"GStreamer error: {e}")
				if error_count >= 10:
					print("Too many GStreamer errors, stopping stream_video thread.")
					break

			time.sleep(0.1) # reduce CPU load

	except Exception as e:
		print(f"Unexpected error in stream video: {e}")

	finally: # Make sure resource is always freed
		out.release() 
		print("Streaming thread stopped")

if __name__ == '__main__':
	# Create threads
	image_thread = threading.Thread(target=image_processing,daemon=True)
	stream_thread = threading.Thread(target=stream_video,daemon=True)

	# Start threads
	image_thread.start()
	stream_thread.start()

	try:
		while True:
			time.sleep(1) # To reduce CPU load, prevent loop from running too fast and avoid unnecessary resource consumption
	except KeyboardInterrupt:
		print("Stopping threads...")
		running.clear() # End the loops safely
		time.sleep(0.5) # To make sure that threads actually stop
		image_thread.join()
		stream_thread.join()
		print("Threads stopped, exiting program...")
