import random

import cv2
import numpy as np

from augraphy.augmentations.lib import add_noise
from augraphy.augmentations.lib import sobel
from augraphy.base.augmentation import Augmentation


class PencilScribbles(Augmentation):
    """Applies random pencil scribbles to image.

    :param size_range: Pair of floats determining the range for
           the size of the scribble to be created
    :type size_range: tuple, optional
    :param count_range: Pair of floats determining the range for
           the number of scribbles to create.
    :type count_range: tuple, optional
    :param stroke_count_range: Pair of floats determining the range for
           the number of strokes to create in each scribble.
    :type stroke_count_range: tuple, optional
    :param thickness_range: Pair of floats determining the range for
           the size of the scribbles to create.
    :type thickness_range: tuple, optional
    :param brightness_change: Value change for the brightness of
           the strokes. Default 128 creates a graphite-like appearance.
           32 creates a charcoal-like appearance.
    :type brightness_change: int, optional
    :param p: Probability of this Augmentation being applied.
    :type p: float, optional
    """

    def __init__(
        self,
        size_range=(250, 400),
        count_range=(1, 10),
        stroke_count_range=(1, 6),
        thickness_range=(2, 6),
        brightness_change=128,
        p=1,
    ):
        """Constructor method"""
        super().__init__(p=p)
        self.size_range = size_range
        self.count_range = count_range
        self.stroke_count_range = stroke_count_range
        self.thickness_range = thickness_range
        self.brightness_change = brightness_change

    # Constructs a string representation of this Augmentation.
    def __repr__(self):
        return f"PencilScribbles(size_range={self.size_range}, count_range={self.count_range}, stroke_count_range={self.stroke_count_range}, thickness_range={self.thickness_range}, brightness_change={self.brightness_change}, p={self.p})"

    def apply_pencil_stroke(self, stroke_image, image):
        """Apply image with pencil strokes to background image.

        :param stroke_image: Image with pencil strokes.
        :type stroke_image: numpy.array (numpy.uint8)
        :param image: The background image.
        :type image: numpy.array (numpy.uint8)
        """
        stroke_image = cv2.cvtColor(stroke_image, cv2.COLOR_BGR2GRAY)
        noise_mask = add_noise(stroke_image, (0.3, 0.5), (32, 128), 0)
        stroke_image[stroke_image < 64] = noise_mask[stroke_image < 64]
        stroke_image = add_noise(stroke_image, (0.4, 0.7), (32, 128), 1, sobel)

        stroke_image = cv2.cvtColor(stroke_image, cv2.COLOR_GRAY2BGR)
        stroke_image = cv2.GaussianBlur(stroke_image, (3, 3), 0)

        hsv = cv2.cvtColor(stroke_image.astype("uint8"), cv2.COLOR_BGR2HSV)
        hsv = np.array(hsv, dtype=np.float64)
        hsv[:, :, 2] += self.brightness_change
        hsv[:, :, 2][hsv[:, :, 2] > 255] = 255
        hsv = np.array(hsv, dtype=np.uint8)
        stroke_image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        return cv2.multiply(stroke_image, image, scale=1 / 255)

    def create_scribble(self, max_height, max_width):
        """Create scribbles of pencil strokes in an image.

        :param max_height: Maximum height of scribble effect.
        :type max_height: int
        :param max_width: Maximum width of scribble effect.
        :type max_width: int
        """
        size = random.randint(max(self.size_range[0], 30), max(40, self.size_range[1]))
        size = min([size, max_height, max_width])
        width, height = size, size  # picture's size

        strokes_img = np.zeros((height, width, 3), np.uint8) + 255  # make the background white

        for i in range(
            random.randint(self.stroke_count_range[0], self.stroke_count_range[1]),
        ):
            # lets say these are my black pixels in a white image.
            stroke_img = np.zeros((height, width, 3), np.uint8) + 255  # make the background white
            x = np.array(
                [
                    random.randint(5, size - 25),
                    random.randint(5, size - 25),
                    random.randint(5, size - 25),
                    random.randint(5, size - 25),
                    random.randint(5, size - 25),
                ],
            )
            y = np.array(
                [
                    random.randint(5, size - 25),
                    random.randint(5, size - 25),
                    random.randint(5, size - 25),
                    random.randint(5, size - 25),
                    random.randint(5, size - 25),
                ],
            )

            start_stop = [
                random.randint(5, size // 2),
                random.randint(size // 2, size - 5),
            ]

            # Initilaize y axis
            lspace = np.linspace(min(start_stop), max(start_stop))

            # calculate the coefficients.
            z = np.polyfit(x, y, 2)

            # calculate x axis
            line_fitx = z[0] * lspace**2 + z[1] * lspace + z[2]
            verts = np.array(list(zip(line_fitx.astype(int), lspace.astype(int))))
            cv2.polylines(
                stroke_img,
                [verts],
                False,
                (0, 0, 0),
                thickness=random.randint(
                    self.thickness_range[0],
                    self.thickness_range[1],
                ),
            )

            strokes_img = self.apply_pencil_stroke(stroke_img, strokes_img)

        return strokes_img

    def random_paste(self, paste, target):
        """Randomly paste image to another image.

        :param paste: Image for the paste effect.
        :type paste: numpy.array (numpy.uint8)
        :param target: The image to be pasted.
        :type target: numpy.array (numpy.uint8)
        """

        target_shape_length = len(target.shape)

        # scribbles is always in 3 channels, need to check and convert if target is not in 3 channels
        if target_shape_length < 3:
            target = cv2.cvtColor(target, cv2.COLOR_GRAY2RGB)

        target_x = random.randint(0, target.shape[1] - paste.shape[1])
        target_y = random.randint(0, target.shape[0] - paste.shape[0])

        target[
            target_y : target_y + paste.shape[1],
            target_x : target_x + paste.shape[0],
        ] = paste

        # convert target back to original channel
        if target_shape_length < 3:
            target = cv2.cvtColor(target, cv2.COLOR_RGB2GRAY)

        return target

    # Applies the Augmentation to input data.
    def __call__(self, image, layer=None, force=False):
        if force or self.should_run():
            image = image.copy()

            for i in range(random.randint(self.count_range[0], self.count_range[1])):
                scribbles = np.full(image.shape, 255).astype("uint8")
                strokes_img = self.create_scribble(image.shape[1], image.shape[0])
                scribbles = self.random_paste(strokes_img, scribbles)
                image = cv2.multiply(scribbles, image, scale=1 / 255)

            return image
