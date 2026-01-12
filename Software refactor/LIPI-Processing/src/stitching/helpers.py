import cv2
import numpy as np
from matplotlib import pyplot as plt
from src.utils import ingaas_processing


def __find_peak_intensity(image):
    """Find the average intensity along one axis. Then, find the index of the peak value."""
    im_sum=np.sum(image,axis=0)/np.shape(image)[0] #averaged sum
    idx=im_sum.argmax() #index of peak

    return idx

def peak_intensity(img, axis=1):
    "Finds the line of peak intensity along specified axis for either single image or array of images. Expects grayscale."
    img_sum = np.sum(img, axis=axis)
    peak = img_sum.argmax(axis=len(img.shape)-2)
    return peak

def plot_intensity(img, axis=0, peak=True):
    im_sum = np.sum(img, axis=axis)

    xax = np.arange(0, len(im_sum), 1)
    plt.plot(xax, im_sum, "r-")
    if peak:
        idx = peak_intensity(img, axis=axis)
        plt.axvline(x=idx)  # plot the peak line!
    plt.axis((0, len(im_sum), 0, max(im_sum)))
    plt.xlabel("Column Index [px]")
    plt.ylabel("Average Intensity[arb. u]")
    plt.ylim(0, 255 * img.shape[axis])
    plt.title("Average emmision intensity along x-axis")
    plt.show()
    #plt.imshow(img)
    #plt.show()
    return None


def create_bounding_box(image, idx,BB_width=15,ELoffset=30,LEDoffset=40,disp=True):
    """
    Create a vertical bounding box in the image based on an index.

    Parameters:
    image (numpy.ndarray): The input image in which the bounding box will be created.
    idx (int): The index around which the bounding box will be centered.
    BB_width (int, optional): The width of the bounding box. Default is 15.
    disp (bool, optional): If True, the image with the bounding box will be displayed. Default is True.

    Returns:
    tuple: A tuple containing two lists:
        - BB_PL (list): The primary bounding box coordinates as [(minx, miny), (maxx, maxy)].
        - BB_EL (list): The EL bounding box coordinates as [(minx, miny), (maxx, maxy)].
        - BB_LED (list): The LED bounding box coordinates as [(minx, miny), (maxx, maxy)].
    """

    # _, binary = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)
    rectColor=(255, 0, 0)
    rectColorEL=(255, 0, 255)
    thickness=1
    BB_PL=[((idx-round(BB_width/2)),0),((idx+round(BB_width/2)),np.shape(image)[0])] #kernel bounding box [(minx,miny)(maxx)(maxy)] (that is, [upper left, lower right])
    BB_EL=[((idx-round(BB_width/2))+ELoffset,0),((idx+round(BB_width/2))+ELoffset,np.shape(image)[0])] #For EL.
    BB_LED=[((idx-round(BB_width/3))-LEDoffset,0),((idx+round(BB_width/3))-LEDoffset,np.shape(image)[0])] #For LEDS.
    #Either this, or threshold, segment, find contours and subtract PL box?
    if disp:
        imageRGB= ingaas_processing.lin_stretch_img(image, 1, 99.99)
        imageRGB = cv2.cvtColor(imageRGB, cv2.COLOR_GRAY2BGR)
        cv2.rectangle(imageRGB,BB_PL[0],BB_PL[1],rectColor,thickness)
        cv2.rectangle(imageRGB,BB_EL[0],BB_EL[1],rectColorEL,thickness)
        cv2.imshow("LoadedImageEnhanced1_kernel",imageRGB)
        cv2.waitKey(1)
    return BB_PL,BB_EL,BB_LED


def display_and_save_video(image, bounding_box, output_file):
    """Display and save video in .mp4 format of linear stretching and bounding box."""
    height, width = image.shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_file, fourcc, 20.0, (width, height))

    for _ in range(100):  # Display the same frame 100 times for demonstration
        frame = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        if bounding_box:
            x, y, w, h = bounding_box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        out.write(frame)
        cv2.imshow('Frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    out.release()
    cv2.destroyAllWindows()
