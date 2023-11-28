import cv2
import numpy as np
from PIL import Image, ImageTk
from tkinter import filedialog 

import time
import queue


def registration(tiffImage, queue1, queue2, num_ref):

  img_ref = tiffImage[num_ref]
  height, width = img_ref.shape

  for i in range(16):
    
    if i == num_ref:
      queue1.put(img_ref)
      queue2.put((0,0))
    else:

      img = tiffImage[i]
    
      # Create ORB detector with 5000 features.
      orb_detector = cv2.SIFT_create(10000)
     
      # Find keypoints and descriptors.
      # The first arg is the image, second arg is the mask
      #  (which is not required in this case).
      kp1, d1 = orb_detector.detectAndCompute(img, None)
      kp2, d2 = orb_detector.detectAndCompute(img_ref, None)
       
      # Match features between the two images.
      # We create a Brute Force matcher with
      # Hamming distance as measurement mode.
      matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck = True)
       
      # Match the two sets of descriptors.
      matches = matcher.match(d1, d2)
       
      # Sort matches on the basis of their distance.
      list(matches).sort(key = lambda x: x.distance)
       
      # Take the top 90 % matches forward.
      matches = matches[:int(len(matches)*0.9)]
      no_of_matches = len(matches)
      
      # Define empty matrices of shape no_of_matches * 2.
      p1 = np.zeros((no_of_matches, 2))
      p2 = np.zeros((no_of_matches, 2))
       
      for i in range(len(matches)):
        p1[i, :] = kp1[matches[i].queryIdx].pt
        p2[i, :] = kp2[matches[i].trainIdx].pt
       
      # Find the homography matrix.
      homography, mask = cv2.findHomography(p1, p2, cv2.RANSAC)
       
      # Use this matrix to transform the
      # colored image wrt the reference image.
      transformed_img = cv2.warpPerspective(img,
                          homography, (width, height))
     
      queue1.put(transformed_img)
      queue2.put(caclOffsetRegistration(transformed_img))


# Calcul des décalage en x et y de l'image après le recalage
# Utile pour les fausses coueleurs
def caclOffsetRegistration(image):

  direction_column = 1
  direction_rows = 1

  # nb of pixel!=0 per rows, columns
  non_zero_rows = np.count_nonzero(image, axis=1)
  non_zero_columns = np.count_nonzero(image, axis=0)

  # indexs of black lines and columns 
  black_row_indices = np.where(non_zero_rows == 0)[0]
  black_column_indices = np.where(non_zero_columns == 0)[0]

  # offset direction
  try:
    if black_column_indices[-1] == image.shape[1] - 1:
      direction_column = -1
  except IndexError:
    pass
  try:
    if black_row_indices[-1] == image.shape[0] - 1:
      direction_rows = -1
  except IndexError:
    pass

  # Number of black lines and columns
  num_black_rows = len(black_row_indices)
  num_black_columns = len(black_column_indices)

  return  num_black_columns * direction_column, num_black_rows * direction_rows