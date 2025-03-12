import cv2
import time
import sys

# The address of UDP stream from RPI
#stream_url = "v4l2src ! video/x-raw, width=640, height=480, framerate=15/1 ! videoconvert ! x264enc tune=zerolatency bitrate=2000 speed-preset=superfast ! rtph264pay ! udpsink host=192.168.1.17 port=5000"

# Gstreamer pipeline to receive video from camera
cap_pipeline = ("v4l2src device=/dev/video0 ! video/x-raw, width=640, height=480, framerate=15/1 ! videoconvert ! appsink")

# Gstreamer pipeline to send processed video via UPD
gst_pipeline = (
    "appsrc is-live=true ! videoconvert ! x264enc tune=zerolatency bitrate=2000 speed-preset=superfast ! "
    "rtph264pay ! udpsink host=192.168.1.17 port=5000"
)

print("Attempting to open stream...")

timeout = time.time() + 10

# Open stream with OpenCV
while time.time() < timeout:
	cap = cv2.VideoCapture(cap_pipeline, cv2.CAP_GSTREAMER)
	if cap.isOpened(): 
		break
else:
	print("Time out...")
	sys.exit()

print("VideoCapture object created")

time.sleep(1)

if not cap.isOpened():
	print("Failed to connect to stream")
	sys.exit()

else:
	print("Connected to stream successfully")

# Open GStreamer pipeline to send video
out =cv2.VideoWriter(gst_pipeline, cv2.CAP_GSTREAMER, 0 , 15, (640, 480),True)

if not out.isOpened():
	print("Failed to open GStreamer pipeline")
	cap.release()
	sys.exit()

print("Streaming video to laptop...")

error_count = 0
while True:
	ret, frame = cap.read()

	if not ret:
		error_count += 1
		print(f"Did not get frame! Attemp {error_count}/10")

		if error_count >= 10:
			print("Too many failed attempts, exiting...");
			break
		continue	
	
	# Process image on RPI (e.x. drawing bounding box)
	cv2.rectangle(frame, (150,100), (500,400), (0,255,0),2)

	# Send processed video via GStreamer
	out.write(frame)

# Free all resources when out of loop
cap.release()
out.release()
print("Stream released")
