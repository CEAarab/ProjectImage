# Algorithme des fausses couleurs
# Une fonction pour 2 ROIS et une fonction pour 3 ROIS
# Calcul et conversions dans fonctionFaussesCouleurs.py

import numpy as np
import math

from PIL import Image
from PIL.TiffTags import TAGS
from itertools import permutations

from Algo.functionFausseCouleur import *

import time
import queue


def fausseCouleur(tiffImage, queue, listPoints, offsets, size_ROIS, img_registred=None):

	nFrame = len(tiffImage)
	
	listROISBrigthLevel = np.zeros((nFrame, 4))

	for i in range(nFrame):
		# Coordonnées des ROIS en prenant en compte les décalage après la registration
		coord1 = listPoints[0] + offsets[i]
		coord2 = listPoints[1] + offsets[i]
		coord3 = listPoints[2] + offsets[i]

		# Valeurs des ROIS : moyenne puis conversion entre 0 et 1 (obligatoire pour conversion Lab)
		listROISBrigthLevel[i] = (moyenne_voisons((int(coord1[1]), int(coord1[0])), size_ROIS, tiffImage[i])/ 65535.0,
								  moyenne_voisons((int(coord2[1]), int(coord2[0])), size_ROIS, tiffImage[i])/ 65535.0,
								  moyenne_voisons((int(coord3[1]), int(coord3[0])), size_ROIS, tiffImage[i])/ 65535.0,
						  		  i)

	# Calcul de toutes les permutations
	listPermutations = np.array(list(permutations(listROISBrigthLevel, 3)))
	lab = np.zeros((listPermutations.shape[0], 4, 3))

	# rgb -> lab pour toutes les permutations
	for i in range(listPermutations.shape[0]):
		lab[i] = (rgb2lab(listPermutations[i, :, 0]),
				 rgb2lab(listPermutations[i, :, 1]), 
				 rgb2lab(listPermutations[i, :, 2]), 
				 listPermutations[i, :, 3])

	bestRapport = calcBestRapport(lab)
	
	# Construction des images fausses couleurs	
	if img_registred == None:
		for i in range(10):
			perm = bestRapport[i][1]
			result = np.dstack((tiffImage[perm[0]], tiffImage[perm[1]], tiffImage[perm[2]]))
			queue.put((result, perm))
	else:
		for i in range(10):
			perm = bestRapport[i][1]
			result = np.dstack((img_registred[perm[0]], img_registred[perm[1]], img_registred[perm[2]]))
			queue.put((result, perm))


def fausseCouleur2Points(tiffImage, queue, listPoints, offsets, size_ROIS, img_registred=None):

	nFrame = len(tiffImage)
	
	listROISBrigthLevel = np.zeros((nFrame, 3))

	# get the pixels value
	for i in range(nFrame):
		coord1 = listPoints[0] + offsets[i]
		coord2 = listPoints[1] + offsets[i]

		listROISBrigthLevel[i] = (moyenne_voisons((int(coord1[1]), int(coord1[0])), size_ROIS, tiffImage[i])/ 65535.0,
								  moyenne_voisons((int(coord2[1]), int(coord2[0])), size_ROIS, tiffImage[i])/ 65535.0,
						  		  i)

	listPermutations = np.array(list(permutations(listROISBrigthLevel, 3)))
	lab = np.zeros((listPermutations.shape[0], 3, 3))

	for i in range(listPermutations.shape[0]):
		lab[i] = (rgb2lab(listPermutations[i, :, 0]),
				 rgb2lab(listPermutations[i, :, 1]), 
				 listPermutations[i, :, 2])

	best_disatnce = bestDistance(lab)

	if img_registred == None:
		for i in range(10):
			perm = best_disatnce[i][1]
			result = np.dstack((tiffImage[perm[0]], tiffImage[perm[1]], tiffImage[perm[2]]))
			queue.put((result, perm))
	else:
		for i in range(10):
			perm = best_disatnce[i][1]
			result = np.dstack((img_registred[perm[0]], img_registred[perm[1]], img_registred[perm[2]]))
			queue.put((result, perm))