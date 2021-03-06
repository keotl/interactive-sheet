import os
import subprocess
import time

import cv2
from jivago.config.properties.application_properties import ApplicationProperties
from jivago.lang.annotations import BackgroundWorker, Inject
from jivago.lang.runnable import Runnable

from vision_project.vision import config
from vision_project.vision.image import Image
from vision_project.vision.image_repository import ImageRepository, SimpleImageRepository

capture = None


@BackgroundWorker
class ImageCapturer(Runnable):

    @Inject
    def __init__(self, image_repository: ImageRepository, application_properties: ApplicationProperties):
        self.image_repository: SimpleImageRepository = image_repository
        self.video_capture_file = application_properties['camera_file']
        self.debug: bool = application_properties['debug']

    def run(self):
        global capture
        while True:
            if capture is None:
                capture = cv2.VideoCapture(self.video_capture_file)
                capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 800)
                capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)

                load_camera_settings(self.video_capture_file)

            is_frame_returned, frame = capture.read()
            if is_frame_returned:
                self.image_repository.set_image(Image(frame))

            else:
                capture = cv2.VideoCapture(self.video_capture_file)
                capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 800)
                capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)

                load_camera_settings(self.video_capture_file)
            if self.debug:
                time.sleep(0.1)

    def cleanup(self):
        capture.release()
        cv2.destroyAllWindows()


def load_camera_settings(camera_file: str):
    settings_file = os.path.join(os.path.dirname(config.__file__), "cameraSettings.txt")
    try:
        subprocess.call(["uvcdynctrl", "-L", settings_file, "-d", camera_file])
    except Exception as e:
        pass
