import cv2
import datetime

class CameraRecorder:
    def __init__(self, camera_index=0):
        self.camera = cv2.VideoCapture(camera_index)
        self.counter = 0

    def record(self, scheduler_camera, mqtt_interface):  # Add mqtt_interface parameter
        ret, frame = self.camera.read()
        # frame = cv2.resize(frame, (640, 480)) # change to 640p stream
        # frame = cv2.resize(frame, (320, 240)) # change to 320p stream
        if not ret:
            print("Failed to capture frame")
            scheduler_camera.enter(1, 1, self.record, (scheduler_camera, mqtt_interface,))
            return

        # Only save images if light is on
        if mqtt_interface.getLightState():
            cv2.imwrite(f"static/cameraImages/latest/lastFrame.jpg", frame)
            
            # Save an image to cameraimages/storage every hour
            self.counter += 1
            if self.counter >= 3600:  # Every hour (60 minutes)
                current_time = datetime.datetime.now()
                storage_path = f"static/cameraImages/storage/{current_time.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
                cv2.imwrite(storage_path, frame)
                self.counter = 0
        
        scheduler_camera.enter(1, 1, self.record, (scheduler_camera, mqtt_interface,))
