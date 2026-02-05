import numpy as np
from PIL import Image
from tkinter import filedialog
import matplotlib.pyplot as plt

def plot_intensity_line(image_paths, column_n):
    """
    Load multiple TIFF images, display them with a horizontal line at column n,
    and plot the light intensity along that line for all images on the same graph.
    
    Args:
        image_paths: List of paths to TIFF image files
        column_n: Column index for the horizontal line
    """
    num_cols = max(3, (len(image_paths) + 2) // 3)
    fig, axes = plt.subplots(3, num_cols, figsize=(14, 5 * 3))
    
    if len(image_paths) == 1:
        axes = axes.reshape(1, -1)
    
    for idx, image_path in enumerate(image_paths):
        # Load the image
        image = Image.open(image_path)
        image_array = np.array(image)
        
        # Handle both grayscale and color images
        if len(image_array.shape) == 3:
            intensity = np.mean(image_array, axis=2)
        else:
            intensity = image_array
        
        # Extract intensity values along the horizontal line at column n
        line_intensity = intensity[:, column_n]
        
        # Display the image with the line marked
        axes[idx % 3, idx // 3].imshow(intensity, cmap='gray')
        axes[idx % 3, idx // 3].axvline(x=column_n, color='red', linewidth=2, label=f'Column {column_n}')
        axes[idx % 3, idx // 3].set_title(f'Image {idx + 1} with Line at Column {column_n}')
        axes[idx % 3, idx // 3].legend()
    
    # Plot all intensities on the same graph
    for idx, image_path in enumerate(image_paths):
        image = Image.open(image_path)
        image_array = np.array(image)
        
        if len(image_array.shape) == 3:
            intensity = np.mean(image_array, axis=2)
        else:
            intensity = image_array
        
        line_intensity = intensity[:, column_n]
        axes[1, 2].plot(line_intensity, label=f'Image {idx + 1}')
    
    axes[1, 2].set_title(f'Light Intensity Along Column {column_n}')
    axes[1, 2].set_xlabel('Row')
    axes[1, 2].set_ylabel('Intensity')
    axes[1, 2].grid(True, alpha=0.3)
    axes[1, 2].legend()
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    image_paths = []
    for i in range(6):
        path = filedialog.askopenfilename(title=f"Select TIFF Image {i + 1}", filetypes=[("TIFF files", "*.tif;*.tiff")])
        if path:
            image_paths.append(path)
    
    if len(image_paths) > 0:
        column_n = 200
        plot_intensity_line(image_paths, column_n)