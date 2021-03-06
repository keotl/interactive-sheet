import logging
from typing import Optional, List

from jivago.lang.annotations import BackgroundWorker, Inject, Override
from jivago.lang.runnable import Runnable
from jivago.lang.stream import Stream

from vision_project.detection.finger import Finger
from vision_project.detection.finger_detector import FingerDetector
from vision_project.detection.sheet import Sheet
from vision_project.detection.sheet_detector import SheetDetector
from vision_project.drawing.drawing import Drawing
from vision_project.vision.image_repository import ImageRepository
from vision_project.vision.util import RelativeWorldCoordinate


@BackgroundWorker
class FingerDrawingWorker(Runnable):
    LOGGER = logging.getLogger("FingerDrawingWorker")

    @Inject
    def __init__(self, image_repository: ImageRepository, sheet_detector: SheetDetector, drawing: Drawing,
                 finger_detector: FingerDetector):
        self.drawing = drawing
        self.image_repository = image_repository
        self.sheet_detector = sheet_detector
        self.finger_detector = finger_detector
        self.no_current_position_found_in_a_row = 0
        self.last_position: RelativeWorldCoordinate = None
        self.should_exit = False

    @Override
    def run(self):
        while not self.should_exit:
            try:
                image = self.image_repository.get_next_image()
                finger = self.finger_detector.find_finger(image)
                if finger:
                    sheets = self.sheet_detector.find_sheets(image)
                    current_position = self._get_relative_world_coordinate_of_finger(finger, sheets)
                    if self._should_draw_line(current_position) and not self.drawing.locked:
                        self.drawing.draw_line(self.last_position, current_position)
                    self._update_last_position(current_position)
                else:
                    self.no_current_position_found_in_a_row += 1

            except Exception as e:
                FingerDrawingWorker.LOGGER.warning(f"Uncaught exception {e}.")
            finally:
                pass
                # time.sleep(0.25)

    def _get_relative_world_coordinate_of_finger(self, finger: Finger, sheets: List[Sheet]) \
            -> Optional[RelativeWorldCoordinate]:
        return Stream(sheets) \
            .map(lambda sheet: sheet.to_relative_coordinate(finger.position)) \
            .firstMatch(lambda coordinate: coordinate is not None)

    def _should_draw_line(self, current_position: Optional[RelativeWorldCoordinate]):
        if self.last_position == current_position or self.last_position is None or current_position is None:
            return False
        return True

    def _update_last_position(self, current_position: RelativeWorldCoordinate):
        if current_position is not None:
            self.last_position = current_position
        elif current_position:
            self.no_current_position_found_in_a_row += 1
        if self.no_current_position_found_in_a_row > 8:
            self.last_position = None
            self.no_current_position_found_in_a_row = 0

    def cleanup(self):
        self.should_exit = True
