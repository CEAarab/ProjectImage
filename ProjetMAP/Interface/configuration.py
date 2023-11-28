# Fenêtres de configurations pour la matrice R et D

import tkinter as tk
from tkinter import ttk, filedialog

from parameter import Parameter
from Interface.imageViewer import ImageViewer

from PIL import Image, ImageTk

import os
import shutil
import cv2
import numpy as np

PAD = 10


# Fenetre pour la configuration de la matrice R
# Choix du fichier csv ou chargement d'un nouveau fichier (txt ou csv)
class ConfigurationR(tk.Toplevel):

	def __init__(self, master, parameters):
		
		super().__init__(master)

		self.title('Configuration Rélféctance')
		self.resizable(False, False)
		self.master = master
		self.transient(self.master) # Met la fenetre devant

		self.window_width = 400
		self.window_height = 300
		self.x = (self.winfo_screenwidth()/2) - (self.window_width/2)
		self.y = (self.winfo_screenheight()/2) - (self.window_height/2)
		self.geometry("%dx%d+%d+%d" % (self.window_width, self.window_height, self.x, self.y))

		self.parameters = parameters
		self.tmp_R_file = None
		self.initWidget()


	# Liste les fichier csv contenu dans un dossier du logiciel parameters/R
	def getRFiles(self):

		return os.listdir(self.parameters.R_path)


	def initWidget(self):
			
		self.file_listBox = tk.Listbox(self)
		self.updateListFiles()
		self.file_listBox.bind("<<ListboxSelect>>", self.select_file)
		self.error_label = tk.Label(self, text='Format des données incorrect', fg='red')

		self.file_listBox.pack(pady=PAD, padx=PAD, fill='x')

		self.frame_controls = tk.Frame(self)
		self.frame_controls.pack(pady=PAD, padx=2*PAD, fill='x', side='bottom')
		ttk.Button(self.frame_controls, text='OK', width=12, takefocus=False, cursor='hand2', command=self.validateFile).pack(side='right')
		ttk.Button(self.frame_controls, text='Charger', width=12, takefocus=False, cursor='hand2', command=self.loadRFile).pack(side='left')


	# Met à jour la liste de fchier si un nouveau est ajouté
	def updateListFiles(self):

		self.file_listBox.delete(0, tk.END)
		for file in self.getRFiles():
			self.file_listBox.insert(tk.END, file)


	# Récupère le nom du fichier selectionné
	def select_file(self, event):

		self.tmp_R_file = self.file_listBox.get(self.file_listBox.curselection())


	# Charge un nouveau fichier dess valeur de R
	def loadRFile(self):

		file = filedialog.askopenfilename(filetypes=[("Comma Separated Values", "*.csv"), ("Text Files", "*.txt")])

		# Vérifie le format
		if file[-4:].lower() == ".txt":
			self.parameters.txt_to_csv(file)
		elif file[-4:].lower() == ".csv":
			shutil.copy(file, self.parameters.R_path)

		self.updateListFiles()


	# Met à jour la matrice R et son fichier
	def validateFile(self):

		# Vérifie si un fichier est sélectionné
		if self.tmp_R_file != None:
			try:
				self.parameters.loadMatrixR(self.tmp_R_file)
			except: # Si le fichier ne contient pas les bonnes données
				if not self.error_label.winfo_ismapped():
					self.error_label.pack(pady=PAD)
				return
			else: # Mise à jour des paramètres
				self.parameters.R_file = self.tmp_R_file
				self.destroy()

		# Met à jour le nom du fichier R dans le menu Cube MS
		try: # Si le menu est affiché
			self.master.R_entry.delete(0, tk.END)
			self.master.R_entry.insert(0, self.parameters.R_file)
		except AttributeError:
			pass
				

# Fenetre pour la configuration de la matrice D
class ConfigurationD(tk.Toplevel):

	def __init__(self, master, parameters):
		
		super().__init__(master)
		self.title('Configuration Patches')
		self.resizable(False, False)

		self.master = master
		self.transient(self.master)
		self.parameters = parameters
		self.patches_file = None
		self.patche_num = 0

		self.rect_start = None
		self.rect_end = None
		self.rect_coords = []

		self.window_width = 0.9 * self.winfo_screenwidth()
		self.window_height = 0.85 * self.winfo_screenheight()
		self.x = (self.winfo_screenwidth()/2) - (self.window_width/2)
		self.geometry("%dx%d+%d+%d" % (self.window_width, self.window_height, self.x, 20))

		self.initWidget()


	def initWidget(self):

		self.frame_image = tk.Frame(self)
		self.frame_controls = tk.Frame(self)
		self.image_viewer = ImageViewer(self.frame_image)

		ttk.Button(self.frame_controls, text='Charger', width=12, takefocus=False, cursor='hand2', command=self.loadPatches).pack(side='left')
		ttk.Button(self.frame_controls, text='OK', width=12, takefocus=False, cursor='hand2', command=self.validatePatches).pack(side='right')
		ttk.Button(self.frame_controls, text='Aide', width=12, takefocus=False, cursor='hand2', command=self.displayHelp).pack(side='right', padx=PAD)
		ttk.Button(self.frame_controls, text='Annuler', width=12, takefocus=False, cursor='hand2', command=self.destroy).pack(side='right')
		self.label = tk.Label(self, text='Chargez les images des patches')
		self.label.place(rely=.5, relx=.5, anchor='center')

		self.image_viewer.bind("<Button-1>", self.onClick)
		self.image_viewer.bind("<B1-Motion>", self.onDrag)
		self.image_viewer.bind("<ButtonRelease-1>", self.onRelease)

		self.frame_controls.pack(pady=PAD, padx=2*PAD, side='bottom', fill='x')
		self.frame_image.pack(side='left', fill='both', expand=True)
		self.image_viewer.pack(padx=PAD)
		


	# Charge un fichier TIFF, doit être l'image des patches
	def loadPatches(self):

		self.file_dialog = filedialog.Open(self, filetypes=[('Fichiers TIFF', '*.tif *.tiff'), ('Tous les fichiers', '*.*')])
		self.patches_file = self.file_dialog.show()
		self.grab_release()
		self.focus_set()

		if self.patches_file == None:
			return

		# Met à jour l'affichage
		self.label.place_forget()
		self.img = cv2.imreadmulti(filename=self.patches_file, flags=cv2.IMREAD_UNCHANGED)[1]
		self.D = np.zeros((24, len(self.img)), dtype='uint16')
		self.image_viewer.updateImages(self.img)
		self.image_viewer.displayImage()
		self.displayTableau()


	def displayTableau(self):

		self.frame_info = tk.Frame(self)
		self.frame_info.pack(side='right',padx=PAD)

		self.tableau = ttk.Treeview(self.frame_info, columns=list(range(1, 17)), show="headings", height=25)
		hsb = ttk.Scrollbar(self.frame_info, orient="horizontal", command=self.tableau.xview)
		self.tableau.configure(xscrollcommand=hsb.set)
		self.tableau.bind('<Delete>', self.deleteLigne)
		self.tableau.pack(fill="none", expand=True)
		hsb.pack(fill="x", expand=True)

		for i in range(16):
			self.tableau.heading(i, text=str(i))
			self.tableau.column(str(i), width=50)


	# Met à jour la matrice D et calcule la matrice Q
	def validatePatches(self):
		
		self.parameters.D = self.D
		#np.savetxt('mon_tableau_mac_50.csv', self.D, delimiter=',')
		self.parameters.calcQ()
		self.destroy()

		try:
			self.master.D_entry.delete(0, tk.END)
			self.master.D_entry.insert(0, self.D)
		except AttributeError:
			pass


	def deleteLigne(self, event):

		sel = self.tableau.selection()
		self.patche_num -= 1
		for item in sel:
			self.tableau.delete(item)


	# Fenêtre d'aide pour l'utilisateur
	def displayHelp(self):

		self.aide = tk.Toplevel(self)
		self.aide.title('Aide')

		self.img_aide = Image.open("icons/image_aide.jpg")
		self.img_aide = ImageTk.PhotoImage(self.img_aide)
		tk.Label(self.aide, image=self.img_aide).grid(column=0, row=0)
		tk.Label(self.aide, 
				 text="1. Charger l'image des patches.\n2. Sélectionner les patches dans l'ordre.\n3. Les rectangles de sélection ne doivent pas être trop près des bords du patches.",
				 justify="left").grid(column=1, row=0, sticky='n', pady=PAD)


	# Fonctions pour dessiner les rectangles de sélection des patches


	def onClick(self, event):

		self.rect_start = (event.x, event.y)


	def onDrag(self, event):

		self.rect_end = (event.x, event.y)
		self.drawRect()


	def onRelease(self, event):

		self.rect_end = (event.x, event.y)
		self.drawRect()
		self.rect_coords = self.image_viewer.coords('rect')

		# Prend en compte le redimensionnement de l'image pour les coordonnées du rectangle
		for i in range(len(self.rect_coords)):
			if i%2 == 0:
				self.rect_coords[i] = int(self.rect_coords[i] / self.image_viewer.x_scale)
			else:
				self.rect_coords[i] = int(self.rect_coords[i] / self.image_viewer.y_scale)

		if self.patche_num < 24:
			self.moy(self.rect_coords[0:2], self.rect_coords[-2:])

		self.rect_start = None
		self.rect_end = None


	def drawRect(self):
		
		self.image_viewer.delete('rect')
		if self.rect_start and self.rect_end:
			x0, y0 = self.rect_start
			x1, y1 = self.rect_end
			self.image_viewer.create_rectangle(x0, y0, x1, y1, outline="red", tag="rect")


	# Moyenne de la valeur des pixel dans le carré sélectionné
	def moy(self, start, end):

		for i in range(len(self.img)):
			square = self.img[i][start[1]:end[1], start[0]:end[0]]
			if 0 in square.shape: # Si rectangle vide
				return
			self.D[self.patche_num, i] = np.mean(square)

		self.tableau.insert('', str(self.patche_num), 'Image'+ str(self.patche_num), values=tuple(self.D[self.patche_num]))
		self.patche_num += 1
	

if __name__ == '__main__':

	C = ConfigurationR(Parameter())
	C.mainloop()