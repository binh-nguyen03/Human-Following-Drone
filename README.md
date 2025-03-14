# GStreamer

Description: (for testing before make it together with image processing) Integrate video transmission platform (aka GStreamer) into python script which is interpretted

WHY USE GSTREAMER PLATFORM?
    - Convenient: more synchronous when using the same platform
    - (Key point) Because GStream have directly accessed to camera to get frame, so if use cv2 to capture video by also accessing to camera, this leads to conflict 
    