import os
import unittest
from typing import List

from jivago.lang.stream import Stream

import infra
from vision_project.detection.sheet import Sheet
from vision_project.detection.sheet_detector import SheetDetector
from vision_project.vision.drawing import draw_crosshair
from vision_project.vision.image_repository import LabelledImageRepository
from vision_project.vision.util import PixelCoordinate

INTERACTIVE_TESTING = False


class SheetDetectorTest(unittest.TestCase):

    def setUp(self):
        self.sheet_detector = SheetDetector()
        self.image_repository = LabelledImageRepository(
            os.path.join(os.path.dirname(infra.__file__), "training_datasets/test_sheet_detection_corner"),
            os.path.join(os.path.dirname(infra.__file__), "labelled_datasets/test_sheet_detection_corner"))

    def test_corner(self):
        correct = incorrect = 0
        while self.image_repository.more_images():
            image, label, filename = self.image_repository.get_test_data_from_dataset()

            sheets = self.sheet_detector.find_sheets(image)

            if assertASheetMatchesLabelledCorner(sheets, label):
                correct += 1
            else:
                incorrect += 1

            if INTERACTIVE_TESTING:
                Stream(sheets).forEach(lambda sheet: draw_crosshair(image, sheet.origin, [0, 0, 255]))
                Stream(sheets).forEach(lambda sheet: draw_crosshair(image, sheet.oposite_corner, [255, 0, 0]))
                image.show_on_window()

        correct_ratio = correct / (incorrect + correct)
        print(f"correct_ratio : {correct_ratio}")
        self.assertTrue(correct_ratio > 0.85)

    def test_sheet_with_orientation(self):
        self.image_repository = LabelledImageRepository(
            os.path.join(os.path.dirname(infra.__file__), "training_datasets/orientation-feuille"),
            os.path.join(os.path.dirname(infra.__file__), "labelled_datasets/orientation-feuille"))

        correct = incorrect = 0

        while self.image_repository.more_images():
            image, label, filename = self.image_repository.get_test_data_from_dataset()

            sheets = self.sheet_detector.find_sheets(image)
            expected_origin = PixelCoordinate(*label['origin'])
            expected_opposite = PixelCoordinate(*label['opposite'])

            if not sheets[0].origin.isclose(expected_origin, delta=10) or not sheets[0].opposite_corner.isclose(
                    expected_opposite, delta=10):
                incorrect += 1
            else:
                correct += 1

            if INTERACTIVE_TESTING:
                Stream(sheets).forEach(lambda sheet: draw_crosshair(image, sheet.origin, [0, 0, 255]))  # origin = red
                Stream(sheets).forEach(
                    lambda sheet: draw_crosshair(image, sheet.oposite_corner, [255, 0, 0]))  # opposite = blue

                draw_crosshair(image, expected_origin, [255, 0, 255], size=8)  # Expected origin = purple
                draw_crosshair(image, expected_opposite, [255, 255, 0], size=8)  # Expected opposite =teal

                image.show_on_window()
        correct_ratio = correct / (incorrect + correct)
        print(f"correct_ratio : {correct_ratio}")
        self.assertTrue(correct_ratio > 0.85)


def assertASheetMatchesLabelledCorner(sheets: List[Sheet], label: dict):
    for sheet in sheets:
        expected = PixelCoordinate(*label["position"])

        if expected.isclose(sheet.origin, delta=5):
            return True
    return False
