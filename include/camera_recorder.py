import cv2
import datetime

class CameraRecorder:
    def __init__(self, camera_index=0):
        self.camera = cv2.VideoCapture(camera_index)

    def record(self, scheduler_camera):
        ret, frame = self.camera.read()
        frame = cv2.resize(frame, (320, 240)) # change to 320p stream
        if not ret:
            print("Failed to capture frame")
            scheduler_camera.enter(1, 1, self.record, (scheduler_camera,))

        cv2.imwrite(f"static/cameraImages/latest/lastFrame.jpg", frame)
        
        # Save an image to cameraimages/storage every hour
        current_time = datetime.datetime.now()
        if current_time.minute == 0:  # Every hour
            storage_path = f"static/cameraImages/storage/{current_time.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
            cv2.imwrite(storage_path, frame)
        
        scheduler_camera.enter(1, 1, self.record, (scheduler_camera,))