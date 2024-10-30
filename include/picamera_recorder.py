from picamera2 import Picamera2
import shutil
import datetime

class CameraRecorder:
    def __init__(self, camera_index=0):
        self.camera = Picamera2()
        camera_config = self.camera.create_still_configuration()  # Use default native resolution
        self.camera.configure(camera_config)
        self.camera.start()
        self.counter = 0

    def record(self, scheduler_camera, mqtt_interface):  # Add mqtt_interface parameter
        # Only save images if light is on
        scheduler_timer = 2
        
        self.camera.capture_file("static/cameraImages/latest/lastFrame.jpg")
        
        if mqtt_interface.getLightState():
            
            # Save an image to cameraimages/storage every hour
            self.counter += 1
            if self.counter >= 3600/scheduler_timer:  # Every hour (60 minutes)
                current_time = datetime.datetime.now()
                storage_path = f"static/cameraImages/storage/{current_time.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
                shutil.copyfile("static/cameraImages/latest/lastFrame.jpg", storage_path)
                self.counter = 0
        
        scheduler_camera.enter(scheduler_timer, 1, self.record, (scheduler_camera, mqtt_interface,))
