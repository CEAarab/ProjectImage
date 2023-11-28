import numpy as np
from itertools import combinations
import math
from PIL import Image

MAT = np.array([[0.412453, 0.357580, 0.180423],
				[0.212671, 0.715160, 0.072169],
				[0.019334, 0.119193, 0.950227]])

# rgb -> XYZ -> Lab
def rgb2lab(valuesRVB):

	def func(t):
		if t > 0.008856:
			return np.power(t, 1/3.0)
		else:
			return 7.787 * t +16 / 116.0

	for i in range(valuesRVB.shape[0]):
		if valuesRVB[i] < 0.04045 :
			valuesRVB[i] = valuesRVB[i] / 12.92
		else:
			valuesRVB[i] = np.power(((valuesRVB[i] + 0.055)/1.055), 2.4)


	XYZ = np.dot(MAT, valuesRVB)

	XYZ[0] = XYZ[0] / 0.950456
	XYZ[2] = XYZ[2] / 1.088754

	L = 116 * np.power(XYZ[1], 1/3.0) - 16 if XYZ[1] > 0.008856 else 903.3 * XYZ[1]
	a = 500 * (func(XYZ[0]) - func(XYZ[1]))
	b = 200 * (func(XYZ[1]) - func(XYZ[2]))

	return (L, a, b)


# Quand 3 ROIS
# Ratio area/standard deviation
def calcRapport(coordLab):

	S = []
	for i in combinations(coordLab[0:3], 2):
		S.append(math.sqrt(pow(i[0][0] - i[1][0], 2) + pow(i[0][1] - i[1][1], 2) + pow(i[0][2] - i[1][2], 2)))

	# Formule de Héron
	s = (S[0] + S[1] + S[2])/2 # demi périmètre
	return (math.sqrt(s*(s - S[0])*(s - S[1])*(s - S[2]))/np.std(S), coordLab[3].astype('uint8'))


def calcBestRapport(lab):

	rapport = [calcRapport(i) for i in lab]
	rapport.sort()
	return rapport[-10:]


# Quand 2 ROIS
def calcDistance(coordLab):

	S = []
	for i in combinations(coordLab[0:2], 2):
		S.append(math.sqrt(pow(i[0][0] - i[1][0], 2) + pow(i[0][1] - i[1][1], 2) + pow(i[0][2] - i[1][2], 2)))

	return S, coordLab[2].astype('uint8')


def bestDistance(lab):

	distances = [calcDistance(i) for i in lab]
	distances.sort()
	return distances[-10:]


# Moyenne des pixels du ROIS à partir des coordonnées
def moyenne_voisons(pixel_coords, size, image):

	row, col = pixel_coords

	if size > 0:
		# sélectionner les pixels voisins
		voisins = image[row - size:row + size + 1, col - size:col + size + 1]

		# calculer la moyenne des pixels voisins
		average = np.mean(voisins)
		return average
	else:
		return image[row, col]