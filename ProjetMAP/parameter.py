# Permet de gérer tous les paramètre :
# - Matrices
# - Fichiers

import numpy as np
import csv
import cv2
import os
from matplotlib import pyplot as plt

import tkinter as tk
from tkinter import filedialog


class Parameter:

	def __init__(self, master):

		self.master = master

		self.R_path = "C:/Users/Dell_Latitude_3510/OneDrive/Bureau/Projet_2A/OneDrive_1_9-26-2023/Projet22-23/parameters/R/"

		self.R_file = "Macbeth_bc_mac.csv"
		self.white_files = []
		self.black_file = ''

		self.R = None 
		self.D = np.zeros((0, 0))
		self.D = np.loadtxt("C:/Users/Dell_Latitude_3510/OneDrive/Bureau/Projet_2A/OneDrive_1_9-26-2023/Projet22-23/parameters/D/mon_tableau.csv", delimiter=",", dtype=str).astype('float64')
		self.Q = None

		self.means_whites = []
		self.black = None

		self.nb_ROIS = 3
		self.size_ROIS = 0

		# R par défaut
		self.loadMatrixR(self.R_file)


	# Converti txt en csv contenant les valeurs de R
	# Le fichier txt doit avoir un format particulier sinon marche pas
	def txt_to_csv(self, filename):
		values = []
		series = []
		header = []

	    # Lecture et récupération des données du fichier txt
		with open(filename, 'r') as f:
			lines = f.readlines()

			for line in lines:
				line = line.strip().replace('"', '')
				if line.find('Patch') != -1:
					header.append(line)
					if values != []:
						series.append(values[10:])
						values = []
				elif line.find('OBJE01200TXT') == -1:
					values.append(line)
			series.append(values[10:])

			# enregistrement du nouveau fichier csv
			filename = filename.split('/')[-1]
			with open(self.R_path + filename.replace('.txt', '.csv'), 'w', newline='') as f:
				writer = csv.writer(f)
				writer.writerow(header)
				np.savetxt(f, np.array(series, dtype='float').T, delimiter=',')


	# Charge la matrice R à partir d'un fichier csv (Label, Data)
	def loadMatrixR(self, filename):

		arr = np.loadtxt(self.R_path + filename, delimiter=",", dtype=str)
		self.R_labels = arr[0]
		self.R = np.delete(arr, 0, 0).astype('float')


	# Cacul de la matrice Q à partir de R et D
	def calcQ(self):

		D_inv = np.linalg.pinv(self.D.T)
		self.Q = self.R.dot(D_inv)
		#np.savetxt('mon_tableau_mac_50.csv', self.Q, delimiter=',')


	# charger images blanches et calcule les 16 moyennes pour chaque blanc
	def whiteFiles(self):

		files = filedialog.askopenfilenames(filetypes=[("Fichiers TIFF", "*.tiff"), ("Tous les fichiers", "*.*")])
		if files == '':
			return

		whites = [cv2.imreadmulti(file, flags=cv2.IMREAD_ANYDEPTH)[1] for file in files]
		self.white_files = [os.path.basename(file) for file in files] # Nom des fichiers sans le path

		for i in range(len(whites[0])):
			group = [w[i] for w in whites]
			group_mean = np.mean(group, axis=0)
			self.means_whites.append(group_mean)

		# Met à jour les noms des fichiers des images blanches dans le menu Cube MS
		try:
			self.master.white_entry.delete(0, tk.END)
			self.master.white_entry.insert(0, self.white_files)
			self.master.white_var.set('Images Blances ' + '(' + str(len(self.white_files)) + ' fichiers)')
		except AttributeError:
			pass


	# Charger l'image noire noire
	def blackFile(self):

		file = filedialog.askopenfilename(filetypes=[("Fichiers TIFF", "*.tiff"), ("Tous les fichiers", "*.*")])
		if file == '':
			return
		self.black = cv2.imreadmulti(file, flags=cv2.IMREAD_ANYDEPTH)[1]
		self.black_file = os.path.basename(file)

		try:
			self.master.black_entry.delete(0, tk.END)
			self.master.black_entry.insert(0, self.black_file)
		except AttributeError:
			pass


if __name__ == "__main__":
	root = tk.Tk()
	
	P = Parameter(root)

	P.txt_to_csv('C:/Users/Dell_Latitude_3510/OneDrive/Bureau/Projet_2A/OneDrive_1_9-26-2023/Projet22-23/parameters/R/Macbeth_bc_mac.csv')