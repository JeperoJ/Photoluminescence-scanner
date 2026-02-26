import numpy as np
import cv2
import math
import tifffile

from . import helpers
from  src.utils import ingaas_processing

__all__ = ["continuous"]

# def roughStitchPL(images, K, P, DIM, imagepath, savename="stitched_image.png", disp=False, EL=True): #TODO: Rewrite or delete
#     """
#     Stitch one scan of already calibrated images.
#     load as .TIFF or .RAW
#     """
#     width, height = 640, 512  # Example dimensions, adjust as necessary
#
#     print("Images loaded. number of images: ", len(images))
#     #cv2.imshow("image",ProcessInGaAs.lin_stretch_img(img[0],1,99.99))
#     #cv2.waitKey()
#     #cv2.destroyAllWindows()
#     #Undistort images
#     #print("DEBUG: input image dtype: ",images[0].dtype)
#     imgUndistorted = ProcessInGaAs.undistort(images, K, P, DIM)
#     ####
#     # Camera is oriented wrong in this version of the gantry. Rotate images 90 degrees clockwise.
#     ####
#     print("Camera is oriented wrong. Rotating undistorted images")
#     imgUndistorted = [np.rot90(image, k=3) for image in imgUndistorted]  #rotate images 90 degrees counterclockwise
#     #DEBUG: Show dtypes of images
#     #print("DEBUG:Image dtypes rotated: ",imgUndistorted[0].dtype)
#     #show rotated images?
#     if disp:
#         #DEBUG - show imported, undistorted images
#         for i in range(len(imgUndistorted)):
#             cv2.imshow("image", ingaas_processing.lin_stretch_img(imgUndistorted[i], 1, 99.99))
#             cv2.waitKey(0)
#     DIM = (DIM[1], DIM[0])  #swap dimensions
#     print("Images undistorted")
#     # Easy rough stitch
#     PLimg = np.zeros_like(imgUndistorted[0])  #Placeholder
#     ELimg = np.zeros_like(imgUndistorted[0])  #Placeholder
#     #print("DEBUG:PL image dtype: ",PLimg.dtype)
#     for i in range(len(imgUndistorted)):
#         im = imgUndistorted[i]
#         #print("DEBUG: img to cast dtype: ",im.dtype)
#         #print("Image input to bounding box dtype: ",im.dtype)
#         peakIdx = src.stitching.stitching_helpers.find_peak_intensity(im)  #Find peak intensity for PL detection
#
#         BB_PL1, BB_EL1, LED1 = src.stitching.helpers.create_bounding_box(im, peakIdx, BB_width=6,
#                                                                          disp=False)  #find PL and EL bounding boxes
#         #Append bounding box to the PL image by averaging the pixel values in each column
#         # cv2.imshow("image",ProcessInGaAs.lin_stretch_img(im[:,BB_PL1[0][0]:BB_PL1[1][0]],1,99.99))
#         # cv2.waitKey(1)
#         #print("BB_PL1: ",BB_PL1)
#         for i in range(BB_PL1[0][0], BB_PL1[1][0]):
#             #if no pixels in column, add to PL image
#             if np.sum(PLimg[:, i]) == 0:
#                 PLimg[:, i] = im[:, i]
#                 # print("PL: ",PLimg[300,i])
#                 # print("im",im[300,i])
#
#             else:
#                 #if pixels in column, weakly average the pixel values?
#                 PLimg[:, i] = 0.8 * PLimg[:, i] + 0.2 * im[:, i]
#         # print("PLimg dtype: ",PLimg.dtype)
#         # print("im dtype: ",im.dtype)
#         # cv2.imshow("im_orig",ProcessInGaAs.lin_stretch_img(im[:,BB_PL1[0][0]:BB_PL1[1][0]],1,99.99))
#         # cv2.imshow("PLImg",ProcessInGaAs.lin_stretch_img(PLimg[:,BB_PL1[0][0]:BB_PL1[1][0]],1,99.99))
#         # cv2.waitKey(1)
#         # # cv2.destroyAllWindows()
#
#         #Create EL image
#         if EL:
#             for i in range(BB_EL1[0][0], BB_EL1[1][0]):
#                 #loop over bounding box for PL area
#                 if np.sum(ELimg[:, i]) == 0:
#                     #if no pixels in column, add to EL image
#                     ELimg[:, i] = im[:, i]
#                 else:
#                     #if pixels in column, weakly average the pixel values?
#                     ELimg[:, i] = 0.8 * ELimg[:, i] + 0.2 * im[:, i]
#
#     #Histogram stretching PL image
#     PLimg = ingaas_processing.crop_image(PLimg)
#     PLimg = ingaas_processing.lin_stretch_img(PLimg, 1, 99.99)
#     cv2.imshow("PL image - manual", PLimg)
#     cv2.waitKey()
#     # cv2.imshow("original image",ProcessInGaAs.lin_stretch_img(im,40,99.99) )
#     # cv2.waitKey()
#     if EL:
#         #Histogram stretching EL image
#         ELimg = ingaas_processing.crop_image(ELimg)
#         ELimg = ingaas_processing.lin_stretch_img(ELimg, 40, 99.99)
#         cv2.imshow("EL image - manual", ELimg)
#         cv2.waitKey()
#     cv2.destroyAllWindows()
#     #save image
#     cv2.imwrite(imagepath + "PL" + savename, PLimg)
#     print("partial PL image saved as: ", "PL" + savename)
#     if EL:
#         cv2.imwrite(imagepath + "EL" + savename, ELimg)
#         print("partial EL image saved as: ", "EL" + savename)


# def roughStitchGeo(images, K, P, DIM, imagepath, speed, nsteps, FPS, savename="stitched_image_geometric.png"): TODO: Rewrite or delete
#     """
#     Geometrically stitch images
#     Here, we use the known speed, number of stops of the gantry to stitch the images
#     """
#     offsetBegin = 500  #offset from the first edge of the gantry to end stops
#     offsetEnd = 100  #offset from the last edge of the gantry to max travel of the axes
#     IRAngle = 30  #Angle of the IR LED bar in degrees
#     IRHeight = 30  #Height of the IR LED bar in cm from PV panel
#     cameraHeight = 1080  #mm
#     #FPS=50 #frames per second
#     f = 6  #focal length (mm)
#     imremove = 100  #DEBUG: remove images from end due to too long scans? (weird scan bug)
#     deltaX = math.tan(
#         math.radians(IRAngle)) * IRHeight  #Distance from the projection of IR bar on PV panel to the camera in cm
#     dist_travel = (
#                               2500 - offsetBegin - offsetEnd) / nsteps  #Distance calculation same as in PLRobot.scan() function. We then know first offset
#     distance = dist_travel - deltaX  #distance in x-axis between camera bar and IR projection
#     dpf = speed / 60 / FPS  #distance per frame (mm)
#     print("Images loaded for geo stitch. number of images: ", len(images))
#     ###########
#     # UNDISTORT
#     ###########
#     imgUndistorted = ingaas_processing.undistort(images, K, P, DIM)
#     imgUndistorted = [np.rot90(image, k=3) for image in imgUndistorted]  #rotate images 90 degrees counterclockwise
#
#     #We know the physical position of the traveled distance, which corresponds to a pixel dist
#     #dist_travel/cameraHeight=d/f
#     d = dist_travel / cameraHeight * f  #distance in mm on image plane
#     dpf_f = dpf / cameraHeight * f  #distance per frame in mm on image plane
#     pxratiox = 15  #um/px in x dir
#     pxratioy = 15  #um/px in y dir -
#     dpx = d / (pxratiox / 1000)  #distance in px on image plane
#     dpfpx = dpf_f / (pxratiox / 1000)  #distance per frame in px on image plane
#     #Find first PL line
#     im = imgUndistorted[0]
#     peakIdx = src.stitching.stitching_helpers.find_peak_intensity(im)  #Find peak intensity for PL detection
#     #given the speed, we know the distance between subsequent images. Interpolating line placement in each image
#     PLimg = np.zeros_like(imgUndistorted[0])  #Placeholder
#     for i in range(len(imgUndistorted[:-imremove])):
#         im = imgUndistorted[i]
#         PLidx = int(peakIdx + i * dpfpx)
#         PLimg[:, PLidx] = im[:, PLidx]
#         # cv2.imshow("PL image - geometric",PLimg)
#         # cv2.waitKey(1)
#
#     #Histogram stretching PL image
#     PLimg = ingaas_processing.crop_image(PLimg)
#     PLimg = ingaas_processing.lin_stretch_img(PLimg, 1, 99.99)
#     cv2.imshow("PL image - geometric", PLimg)
#     cv2.waitKey()
#     cv2.destroyAllWindows()
#     cv2.imwrite(imagepath + "GeoPL" + savename, PLimg)
#     print("partial Geometric PL geometric image saved as: ", "GeoPL" + savename)


def continuous(images, speed, fps, cam_height=945, f=6, drift=0.02448, show_append=False):
    """
        Stitches a sequence of images together based on geometric alignment and optional drift correction.
        Returns a stitched image either as a .tiff (int16) or a .png (uint8 linearly stretched) and saves it to the specified path.
        Parameters:
        -----------
        images : list of ndarray
            List of images to be stitched, with necessary corrections applied.
        speed : float
            Speed of the scanning process in mm/min.
        fps : int
            Frames per second of the image capture.
            :
            Angle of the IR LED bar in degrees

            :
            Height of the IR LED bar in cm from PV panel
            :
            Height of the camera from PV panel
        drift : [px/img], optional
            Drift is [px/img] to account for different speeds of the axes. Default is None.


        Returns:
        --------
        None
            The function saves the stitched image to the specified path and displays it.
        Notes:
        ------
        - The function assumes that the images are captured in a continuous sequence.
        - The function uses geometric properties and known physical distances to align the images.
        - Drift correction is applied if the `drift` parameter is set to a value.
    """
    # offsetBegin=500 #offset from the first edge of the gantry to end stops
    # offsetEnd=100 #offset from the last edge of the gantry to max travel of the axes
    # imremove=None #DEBUG: remove images from end due to too long scans? (weird scan bug)
    # if imremove is not None:
    #     #handling a none imremove
    #     imremove=-imremove
    #deltaXIRproj= math.tan(math.radians(ir_angle)) * ir_height #Distance from the projection of IR bar on PV panel to the camera in cm
    dpf = (speed / 60) / fps  #distance per frame (mm)
    ###########
    # UNDISTORT. 
    ###########
    #We know the physical position of the traveled distance, which corresponds to a pixel dist
    #dist_travel/cameraHeight=d/f
    #d_offset = 200 / cam_height * f  #distance in mm on image plane
    dpf_f = dpf / cam_height * f  #distance per frame in mm on image plane
    px_ratio_x = 15  #um/px in x dir
    #pxratioy = px_ratio_x  #um/px in y dir -
    #doffsetpx = d_offset / (px_ratio_x / 1000)  #distance in px on image plane
    dpf_px = dpf_f / (px_ratio_x / 1000)  #distance per frame in px on image plane
    #Find first PL line
    im = images[0]
    #peakIdx = helpers.peak_intensity(im, axis=0)  #Find peak intensity for PL detection - just to start the scan off. Could probably be hardcoded for robustness
    #print("peakIdx: ", peakIdx) #DEBUG
    peakIdx = 233  #Hardcoded peak index for robustness
    shape=(np.shape(im)[0],len(images))
    #given the speed, we know the distance between subsequent images. Interpolating line placement in each image
    PLimg = np.zeros(shape, dtype=np.int16)
    #if there is a drift variable, the peak index needs to be adjusted
    dvar = 0
    if drift:
        dvar = drift
    # print("PLimg dtype before: ",PLimg.dtype)
    #Loop through and append
    show_append=False
    for i in range(len(images)):
        im = images[i]
        PLidx = int(i * dpf_px)
        PLimg[:, PLidx] = im[
            :, int(peakIdx + dvar * i)]  #drift factor corrects here. append the index based on the dpf_px value
        #imshow for debugging - show window around appended line
        if show_append:
            linstretched_window = ingaas_processing.lin_stretch_img(im, 1, 99.99)
            imageRGB = cv2.cvtColor(linstretched_window, cv2.COLOR_GRAY2BGR)
            # Draw line at peakIdx + drift correction
            line_x = int(peakIdx + dvar * i)
            line_x = max(0, min(line_x, linstretched_window.shape[1] - 1))
            line_color = (255, 0, 0)
            cv2.line(imageRGB, (line_x, 0), (line_x, shape[0]), line_color, 1)
            cv2.imshow("PL image - continuous (window)", imageRGB)
            cv2.waitKey(1)

    cv2.destroyAllWindows()


    PLimg = ingaas_processing.crop_image(PLimg)
    return PLimg


# def multiStitch(stitched_partiaL_images): TODO: Rewrite or delete
#     """
#     Stitches multiple partial images into a single image by cropping each image to the region with data and concatenating them horizontally.
#     Args:
#         stitched_partiaL_images (list of str): List of file paths to the partial images to be stitched.
#     Returns:
#         None
#     This function performs the following steps:
#     1. Reads the first image from the list and crops it to the region with data.
#     2. Iterates through the remaining images, reads and crops each one, and concatenates it horizontally to the previously processed images.
#     3. Displays the final stitched image.
#     4. Saves the final stitched image as "total_stitched_image.png".
#     """
#
#     #crop to only the region with data
#     print("Cropping image to only the region with data")
#     PLimg = cv2.imread(stitched_partiaL_images[0], cv2.IMREAD_GRAYSCALE)
#     PLimgCropped = ingaas_processing.crop_image(PLimg)
#     for i in range(1, len(stitched_partiaL_images)):
#         PLimg = cv2.imread(stitched_partiaL_images[i], cv2.IMREAD_GRAYSCALE)
#         PLimg2Cropped = ProcessInGaAs.crop_image(PLimg)
#         #stitch images by concatenating them
#         PLimgCropped = np.concatenate((PLimgCropped, PLimg2Cropped), axis=1)
#         cv2.imwrite(f"cropped{i}.png", PLimgCropped)
#     #show stitched image
#     cv2.imshow("PL image - manual", PLimgCropped)
#     cv2.waitKey()
#     cv2.destroyAllWindows()
#     #save image
#     cv2.imwrite("total_stitched_image.png", PLimgCropped)
#     print("stitched image saved as: total_stitched_image.png")
