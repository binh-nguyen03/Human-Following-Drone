# Human-Following-Drone

DESCRIPTION
    - Main algorithm: HOG + SVM, Optical flow, KCF tracker
    - Application: 
        + HOG + SVM: Identify whether there's human in the frame or not.
        + Optical flow: Follow the movement of human in short-term period.
        + KCF tracker: Drawing a bounding box surrounding the human, following smoother in long-term period.

SW DEVELOPMENT ORIENTATION:
    - Break down into two sepearte threads:
        + Thread 1: Image processing based on captured live video from GStreamer pipeline without directly get access to camera.
        + Thread 2: Read processed video for thread 1 and stream to laptop via UDP.
    
