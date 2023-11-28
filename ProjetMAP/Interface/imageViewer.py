# Affichage des images
# Contient toutes les fonctions :
#								- Adapter taille image à la fenêtre
#								- Mettre à jour la liste d'image
#								- Afficher une image sur la fenetre principale
# Mettre seul dans une fenetre
# Ne pas mettre de padding pour ImageViewer


import tkinter as tk
from tkinter import ttk

from PIL import ImageTk, Image

from Algo.spectro import spectro

import numpy as np
import time

PAD = 10

class ImageViewer(tk.Canvas):

	def __init__(self, master, parameters=None, root=None):

		super().__init__(master)
		
		self.master = master
		self.root = root
		self.parameters = parameters
		self.img_display = [] # List image Tk
		self.list_img_tab = []
		self.current_image = None
		self.index_img = 0
		self.list_points = np.zeros((3, 2))
		self.nb_frame = 0

		self.config(highlightthickness=0)
		self.image_container = self.create_image(0, 0, anchor='nw')
		self.canvas_points = [tk.Canvas(self, width=1, height=1, highlightthickness=1, highlightbackground='blue') for i in range(3)]
		self.canva = tk.Canvas(self, width=1, height=1, highlightthickness=1, highlightbackground='blue')


	# Met à jour la liste d'image
	# k indique le nombre d'images à afficher sur toutes les images fourie à intervalles régulières
	# k utile pour le cube multispectral
	def updateImages(self, new_img, k=1):

		self.list_img_tab = list(new_img) # Copie des images de bases

		if k > 1: self.img_ratio = int(len(new_img)/k)
		else: self.img_ratio = 1
		
		new_img = new_img[::self.img_ratio]
		self.nb_frame = len(new_img)
		self.img_display = self.converImage(new_img)
		self.index_img = 0
		
		if self.root: self.root.updateLabelFrameInfo()


	# Converti liste de tableaux en images PIL
	def converImage(self, img_list):

		converted_img = []
		for i in range(self.nb_frame):
			img = self.convertImage8bits(img_list[i])
			converted_img.append(Image.fromarray(img))

		return converted_img


	# Affiche la bonne image avec la bonne taille
	def displayImage(self):

		self.master.update() # Pour avoir les dimensions de la fenetre à jour
		if self.master.winfo_height() > 1:
			self.current_image = self.resizeImage(self.img_display[self.index_img])
			self.current_image = ImageTk.PhotoImage(self.current_image)
			self.itemconfig(self.image_container, image=self.current_image)


	# Adapte la taille de l'image en fonction de la taille de la fenetre
	# Pour des images PIL
	def resizeImage(self, img):

		img_max_height, img_max_width = self.list_img_tab[0].shape[0:2]
		image_scale = img_max_height / img_max_width
		height = self.master.winfo_height() - 2 * PAD

		if height >= img_max_height:
			self.config(width=img_max_width, height=img_max_height)
			img = img.resize((img_max_width, img_max_height))
		else:
			self.config(width=int(height/image_scale), height=height)
			img = img.resize((int(height/image_scale), height))

		self.x_scale = img.size[0] / img_max_width
		self.y_scale = img.size[1] / img_max_height

		return img


	# Selection points à utiliser pour les fausses couleurs
	def clickOnImageFC(self, event):

		x, y = int(event.x / self.x_scale), int(event.y / self.y_scale)
		index_dispo = np.where((self.list_points[:self.parameters.nb_ROIS] == [0, 0]).all(axis=1))[0]
			
		if len(index_dispo) == 0: return

		index_coord = index_dispo[0]
		self.list_points[index_coord] = (x, y)
		self.root.text_labelx[index_coord].set('x : ' + str(x))
		self.root.text_labely[index_coord].set('y : ' + str(y))
		self.canvas_points[index_coord].place(x=event.x, y=event.y, anchor='center')


	def clickOnImageMS(self, event):

		if self.canva.winfo_ismapped(): self.canva.place_forget()

		x, y = int(event.x), int(event.y)
		self.canva.place(x=x, y=y, anchor='center')
		spectro(self.list_img_tab, int(y / self.y_scale), int(x / self.x_scale))


	# Enleve les fonctionalité liées aux fausses couleurs
	def unbindFCFonctions(self):

		self.unbind("<Button-1>")
		self.list_points.fill(0)
		for canva in self.canvas_points:
			canva.place_forget()


	def unbindMSFonctions(self):

		self.unbind("<Button-1>")
		self.canva.place_forget()


	# Enleve une coordonnées d'un ROIS
	def deleteCoord(self, num_point):

		self.canvas_points[num_point].place_forget()
		self.list_points[num_point] = (0, 0)


	# Retourne les images de bases affichées pour la sauvegarde
	def imagesToSave(self):

		return self.list_img_tab[::self.img_ratio]


	# Converti l'image en 8 bits si besoin (obligatoire pour l'affichage)
	def convertImage8bits(self, img):

		if img.dtype != 'uint8':
			return (img / 255).astype(np.uint8)
		return img