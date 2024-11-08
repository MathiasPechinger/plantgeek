from picamera2 import Picamera2
import shutil
import datetime
import threading
import os
import sys

class CameraRecorder:
    def __init__(self, camera_index=0):
        self.camera = Picamera2()
        camera_config = self.camera.create_still_configuration()  # Use default native resolution
        self.camera.configure(camera_config)
        self.camera.start()
        self.targetCounter = 3600
        self.counter = self.targetCounter-60
        self.lock = threading.Lock()

    def record(self, scheduler_camera, mqtt_interface):  # Add mqtt_interface parameter
        scheduler_timer = 1 # time in seconds
        
        with self.lock:
            temp_path = "static/cameraImages/latest/tempFrame.jpg"
            final_path = "static/cameraImages/latest/lastFrame.jpg"
            self.camera.capture_file(temp_path)
            os.replace(temp_path, final_path)
        
        # Check available disk space before saving the image
        disk_usage = shutil.disk_usage("/")  # Get disk usage for root directory
        free_space = disk_usage.free  # Free space in bytes
        required_space = 1024 * 1024 * 500  # Set required space (500 MB)

        if free_space < required_space:
            print("Warning: Not enough disk space. No new image will be stored.")
            return  # Exit the method if there's not enough space

        # Only save images if light is on
        if mqtt_interface.getLightState():
            # Save an image to cameraimages/storage every hour
            self.counter += 1
            if self.counter >= self.targetCounter/scheduler_timer:  # Every hour (60 minutes)
                current_time = datetime.datetime.now()
                storage_path = f"static/cameraImages/storage/{current_time.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
                with self.lock:
                    shutil.copyfile(final_path, storage_path)
                self.counter = 0
        
        scheduler_camera.enter(scheduler_timer, 1, self.record, (scheduler_camera, mqtt_interface,))

    def get_latest_image(self):
        with self.lock:
            with open("static/cameraImages/latest/lastFrame.jpg", "rb") as image_file:
                return image_file.read()
