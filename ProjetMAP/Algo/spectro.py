import numpy as np
import cv2
import time
import matplotlib.pyplot as plt


# Fonction pour la construction du cube multispectral
def cubeMS(images, Q):

	n = len(images)
	width, height = images[0].shape

	# Créer une matrice où chaque ligne contient tous les pixels d'une image
	img_matrix = np.zeros((n, width * height), dtype=np.uint16)

	for i in range(n):
		img_matrix[i, :] = images[i].flatten()

	Ra = Q.dot(img_matrix) # Réflectance des images

	# Construction du cube 
	return [np.reshape(i, (width, height)) for i in Ra]


# Construit le spectre aux coordonnées x, y de l'image
# R et num_R permettent de tracer la réflectance d'un patch pour vérification
def spectro(cube_MS, x, y, R=None, num_R=None):

	values = [img[x, y] for img in cube_MS] # Toutes les valeurs entre 0 et 100

	plt.plot(values)
	if num_R != None: plt.plot(R[:, num_R], label=f'Patche réf {num_R}')
	#plt.title(f'Réflectance pixel ({y}, {x})')
	plt.xlabel("Longueur d'onde")
	plt.ylabel('Réflectance')
	plt.ylim(-5, 105)
	#plt.legend()
	plt.show()