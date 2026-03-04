# image_discretizer.py
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import os


class ImageDiscretizer:
    def __init__(self, spatial_resolution=1.0):
        """
        Initialize the grayscale discretization processor

        Parameters:
        spatial_resolution: Spatial resolution of the image in meters/pixel
        """
        self.spatial_resolution = spatial_resolution

    def process_image(self, image, levels=8, visualize=False, save_path=None, save_matrix=False, water_threshold=1):
        """
        Process image and perform grayscale discretization

        Parameters:
        image: PIL Image object or path to image file
        levels: Number of discrete grayscale levels
        visualize: Whether to visualize the results
        save_path: Path to save visualization results
        save_matrix: Whether to save the discretized matrix
        water_threshold: Grayscale threshold for water bodies; pixels with values less than or equal to this are considered water

        Returns:
        discrete_matrix: Discretized matrix
        stats: Tuple (pixel counts, percentages, areas) - all as Python native types
        water_land_stats: Dictionary of water/land statistics
        """
        # If input is a path, load the image
        if isinstance(image, str):
            image = Image.open(image).convert('L')
        elif isinstance(image, np.ndarray):
            # If it's a color image, convert to grayscale
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = Image.fromarray(image).convert('L')
                image = np.array(image)
            # If already grayscale, use directly
        elif isinstance(image, Image.Image):
            # Ensure image is in grayscale mode
            image = image.convert('L')
        else:
            raise TypeError("Unsupported image type")

        # Ensure image is a numpy array
        if isinstance(image, Image.Image):
            image_array = np.array(image)
        else:
            image_array = image

        # Calculate interval for each level
        min_val = np.min(image_array)
        max_val = np.max(image_array)
        interval = (max_val - min_val) / levels

        # Create discretized matrix
        discrete_matrix = np.zeros_like(image_array, dtype=int)

        # Discretize each pixel
        for level in range(levels):
            if level == levels - 1:
                # Last level includes the maximum value
                mask = (image_array >= min_val + level * interval) & (image_array <= max_val)
            else:
                mask = (image_array >= min_val + level * interval) & (image_array < min_val + (level + 1) * interval)
            discrete_matrix[mask] = level

        # Calculate pixel count for each level
        pixel_counts = np.zeros(levels, dtype=int)
        for level in range(levels):
            pixel_counts[level] = np.sum(discrete_matrix == level)

        # Calculate percentages
        total_pixels = discrete_matrix.size
        percentages = (pixel_counts / total_pixels) * 100

        # Calculate areas (assuming spatial resolution information is available)
        areas = pixel_counts * self.spatial_resolution * self.spatial_resolution

        # Add water/land classification statistics
        water_mask = discrete_matrix <= water_threshold
        land_mask = discrete_matrix > water_threshold

        water_pixels = int(np.sum(water_mask))
        land_pixels = int(np.sum(land_mask))
        total_pixels = water_pixels + land_pixels

        water_percentage = float((water_pixels / total_pixels) * 100)
        land_percentage = float((land_pixels / total_pixels) * 100)

        water_area = float(water_pixels * self.spatial_resolution * self.spatial_resolution)
        land_area = float(land_pixels * self.spatial_resolution * self.spatial_resolution)
        total_area = water_area + land_area

        water_land_stats = {
            'water_pixels': water_pixels,
            'land_pixels': land_pixels,
            'total_pixels': total_pixels,
            'water_percentage': water_percentage,
            'land_percentage': land_percentage,
            'water_area': water_area,
            'land_area': land_area,
            'total_area': total_area,
            'spatial_resolution': self.spatial_resolution
        }

        # Visualization
        if visualize:
            plt.figure(figsize=(10, 8))

            # Add support for fonts
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False

            plt.imshow(discrete_matrix, cmap='viridis')
            plt.colorbar(label='Grayscale Level')
            plt.title('Grayscale Discretization Analysis')
            plt.xlabel('X Coordinate')
            plt.ylabel('Y Coordinate')

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
            else:
                plt.show()

        # Save discretized matrix to file
        if save_matrix and save_path:
            matrix_path = save_path.replace('.png', '.npy')
            np.save(matrix_path, discrete_matrix)

        # Convert NumPy arrays to Python native types to ensure JSON serialization
        pixel_counts = [int(count) for count in pixel_counts]
        percentages = [float(p) for p in percentages]
        areas = [float(a) for a in areas]

        return discrete_matrix, (pixel_counts, percentages, areas), water_land_stats

    def visualize_water_land(self, discrete_matrix, water_threshold=1, save_path=None):
        """
        Create water/land classification visualization

        Parameters:
        discrete_matrix: Discretized matrix
        water_threshold: Grayscale threshold for water bodies; pixels with values less than or equal to this are considered water
        save_path: Path to save visualization results
        """
        # Create water/land mask
        water_mask = discrete_matrix <= water_threshold

        # Create color image
        rgb_image = np.zeros((*discrete_matrix.shape, 3), dtype=np.uint8)

        # Set colors: water as blue, land as green
        rgb_image[water_mask] = [0, 0, 255]  # Blue
        rgb_image[~water_mask] = [0, 255, 0]  # Green

        # Visualization
        plt.figure(figsize=(10, 8))

        # Add support for fonts
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False

        plt.imshow(rgb_image)
        plt.title('Water/Land Classification Map')
        plt.xlabel('X Coordinate')
        plt.ylabel('Y Coordinate')

        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='blue', edgecolor='blue', label='Water'),
            Patch(facecolor='green', edgecolor='green', label='Land')
        ]
        plt.legend(handles=legend_elements, loc='lower right')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.show()