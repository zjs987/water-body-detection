import numpy as np
from PIL import Image, ImageFilter


class ImageProcessor:
    """Image processing class providing various image processing functions"""

    def __init__(self):
        pass

    def detect_edges(self, image):
        """
        Perform edge detection on an image

        Parameters:
        image: PIL Image object

        Returns:
        Processed PIL Image object
        """
        # Ensure the image is a PIL Image object
        if not isinstance(image, Image.Image):
            image = Image.fromarray(np.uint8(image))

        # Convert to grayscale image
        gray_image = image.convert('L')

        # Use Sobel filter for edge detection
        edge_image = gray_image.filter(ImageFilter.FIND_EDGES)

        return edge_image