# Fenêtres de configurations pour la matrice R et D

import tkinter as tk
from tkinter import ttk, filedialog

import tk_tools


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
		self.arePatchesLoaded = False
		self.patche_num = 0
		self.tableau = None

		self.rect_start = None
		self.rect_end = None
		self.rect_coords = []
		#?self.waitConfirm = False

		##self.filterGrid_cornerIndex = 0
		self.polygon = []
		self.drawLock = False
		self.selectionGrid = None
		self.nRows = 4
		self.nCols = 6

		self.rowsScale = 0.6 #linked to width parameter in app
		self.scale1 = None
		self.rowsSizes = None

		self.colsScale = 0.6 #linked to heigth parameter in app
		self.scale2 = None
		self.colsSizes = None

		self.manual_selection = False  # Set to True for manual selection, False for automatic selection




		self.window_width = 0.9 * self.winfo_screenwidth()
		self.window_height = 0.85 * self.winfo_screenheight()
		self.x = (self.winfo_screenwidth()/2) - (self.window_width/2)
		self.geometry("%dx%d+%d+%d" % (self.window_width, self.window_height, self.x, 20))

		self.sel_button = None
		self.initWidget()


	def initWidget(self):

		self.frame_image = tk.Frame(self)
		self.frame_controls = tk.Frame(self)
		self.image_viewer = ImageViewer(self.frame_image)

		ttk.Button(self.frame_controls, text='Charger', width=12, takefocus=False, cursor='hand2', command=self.loadPatches).pack(side='left')
		self.sel_button = ttk.Button(self.frame_controls, text='Sélection manuelle', width=25, takefocus=False, cursor='hand2', command=self.switchMode)
		self.sel_button.pack(side='left')
		ttk.Button(self.frame_controls, text='OK', width=12, takefocus=False, cursor='hand2', command=self.validatePatches).pack(side='right')
		ttk.Button(self.frame_controls, text='Aide', width=12, takefocus=False, cursor='hand2', command=self.displayHelp).pack(side='right', padx=PAD)
		ttk.Button(self.frame_controls, text='Annuler', width=12, takefocus=False, cursor='hand2', command=self.destroy).pack(side='right')
		self.label = tk.Label(self, text='Chargez les images des patches')
		self.label.place(rely=.5, relx=.5, anchor='center')

		self.frame_controls.pack(pady=PAD, padx=2*PAD, side='bottom', fill='x')
		self.frame_image.pack(side='left', fill='both', expand=True)
		self.image_viewer.pack(padx=PAD)

		# Configuration des events pour créer la grille des patchs
		self.image_viewer.bind("<Button-1>", self.onClick_autom)
		self.image_viewer.bind("<Motion>", self.whenDrawing)
		self.image_viewer.bind("<B1-Motion>", self.whenDrawing)
		self.image_viewer.bind("<ButtonRelease-1>", self.onRelease_autom)

		self.frame_info = tk.Frame(self)
		self.frame_info.pack(side='right',padx=PAD)
		

	#Passer entre les modes manuel et automatique de sélection des patchs
	def switchMode(self) :
		self.manual_selection = not(self.manual_selection) #Passage dans l'autre mode manuel/automatique
		if self.tableau != None :
			#Supprime tous les patchs précédents
			self.D = np.zeros_like(self.D)
			self.tableau.delete(*self.tableau.get_children()) 
		if self.manual_selection :
			# Configuration des events pour dessiner les contours de patchs
			self.image_viewer.bind("<Button-1>", self.onClick_manual)
			self.image_viewer.bind("<Motion>", None)
			self.image_viewer.bind("<B1-Motion>", self.onDrag_manual)
			self.image_viewer.bind("<ButtonRelease-1>", self.onRelease_manual)
			self.sel_button["text"] = 'Sélection automatique'
		else :
			# Configuration des events pour créer la grille des patchs
			self.image_viewer.bind("<Button-1>", self.onClick_autom)
			self.image_viewer.bind("<Motion>", self.whenDrawing)
			self.image_viewer.bind("<B1-Motion>", self.whenDrawing)
			self.image_viewer.bind("<ButtonRelease-1>", self.onRelease_autom)
			self.sel_button["text"] = 'Sélection manuelle'


		if self.arePatchesLoaded :
			self.display_changes()

	

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
		self.display_changes()
		self.arePatchesLoaded = True


	def display_changes(self):
		
		# Afficher ou non tous les paramètres liés à la sélection automatique
			
		if self.manual_selection :
			# Suppression des curseurs
			if self.scale2 != None :
				self.scale1.destroy()
				self.scale2.destroy()
			self.image_viewer.delete('polygon')
			self.image_viewer.delete('selectionGrid')
		
		else :
			# Curseurs pour modifier les paramètres du tracé
			# Créer un curseur (Scale) allant de 0 à 1
			self.scale1 = tk.Scale(self.frame_info, from_=0, to=100, label="hauteur des cases", resolution=1, orient="horizontal", command=self.update_colsScale)
			self.scale1.set(100*self.rowsScale)
			self.scale1.pack(side = 'bottom')
			self.scale2 = tk.Scale(self.frame_info, from_=0, to=100, label="largeur des cases", resolution=1, orient="horizontal", command=self.update_rowsScale)
			self.scale2.set(100*self.colsScale)
			self.scale2.pack(side = 'bottom')

			self.image_viewer.delete('rect')
			self.polygon = []




	def displayTableau(self):
		
		self.tableau = ttk.Treeview(self.frame_info, columns=list(range(1, 17)), show="headings", height=25)
		hsb = ttk.Scrollbar(self.frame_info, orient="horizontal", command=self.tableau.xview)
		self.tableau.configure(xscrollcommand=hsb.set)
		self.tableau.bind('<Delete>', self.deleteLigne)
		self.tableau.pack(fill="none", expand=True)
		hsb.pack(fill="x", expand=True)

		for i in range(16):
			self.tableau.heading(i, text=str(i))
			self.tableau.column(str(i), width=50)
		



	def update_colsScale(self, value) :
		self.colsScale = 0.15 + float(value)/120
		if self.selectionGrid != None :
			self.drawGrid()
	

	def update_rowsScale(self, value) :
		self.rowsScale = 0.15 + float(value)/120
		if self.selectionGrid != None :
			self.drawGrid()

	

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
			self.displayTableau()


	# Fenêtre d'aide pour l'utilisateur
	def displayHelp(self):
		self.aide = tk.Toplevel(self)
		self.aide.title('Aide')
		
		if self.manual_selection :
			self.img_aide = Image.open("icons/image_aide.jpg")
			self.img_aide = ImageTk.PhotoImage(self.img_aide)
			tk.Label(self.aide, image=self.img_aide).grid(column=0, row=0)
			tk.Label(self.aide, 
					text="1. Charger l'image des patches.\n\n2. Sélectionner les patches dans l'ordre.\n\n3. Les rectangles de sélection ne doivent pas être trop près des bords du patches.\n\n\nNote : Vous pouvez sélectionner rapidement vos patchs en utilisant la 'Sélection automatique'.",
					justify="left").grid(column=1, row=0, sticky='n', pady=PAD)
			#mettre à jour ce guide ?
			
		else :
			#guide pour la sélection automatique
			self.img_aide = None
			tk.Label(self.aide, 
					text="1. Charger l'image des patches.\n\n2. Positionner 4 points pour encadrer l'ensemble des patchs.\n'échap' permet d'interrompre le tracé.\n\n3. Assurez-vous que la grille générée s'inscrit correctement dans les patchs.\nVous pouvez ajuster la largeur et la hauteur des cases en déplaçant les curseurs correspondants,\nlaissez cependant quelques millimètres de distance avec les bords.\nPlacer un nouveau point permet de recommencer et créer une nouvelle figure.\n\n4. Appuyer sur 'OK' pour confirmer les valeurs de vos patchs.\n\nNote : si cette sélection automatique ne convient pas,\n appuyez sur 'Sélection manuelle' pour enregistrer manuellement vos patchs.",
					justify="left").grid(column=1, row=0, sticky='n', pady=PAD)
			pass




	# Fonctions pour dessiner les cadres de sélection des patchs
		
	## Méthode manuelle conservée comme alternative pour dépanner

	def onClick_manual(self, event):

		self.rect_start = (event.x, event.y)


	def onDrag_manual(self, event):
		self.rect_end = (event.x, event.y)
		self.drawRect()


	def onRelease_manual(self, event):

		self.rect_end = (event.x, event.y)
		self.drawRect()
		self.rect_coords = self.image_viewer.coords('rect')

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


	## méthode à favoriser : positionner un point aux quatre coins de la grille et obtenir immédiatement la grille adaptée

	def onClick_autom(self, event):
			#inutile dans la configuration actuelle

	
		'''
		if len(self.polygon)==0 :
			self.drawLock=False
			#? self.waitConfirm = False
		'''
		if len(self.polygon)==4 : # start to make a new polygon
			self.image_viewer.delete('polygon')
			self.polygon = []
			self.image_viewer.delete('selectionGrid')
			self.drawLock = False


	def whenDrawing(self, event) :
		self.drawLock = False #débloquer le dessin après un mouvement de souris
		if (len(self.polygon) > 0) and (len(self.polygon) < 4):
			self.polygon.append((event.x, event.y))
			self.drawPolygon()
			self.polygon.pop()
		

	def onRelease_autom(self, event):


		if self.drawLock == False : #un point ne sera pas validé que si la souris a bougé
			self.polygon.append((event.x, event.y))
			self.drawLock = True  # Bloquage de la fonction de dessin jusqu'au prochain mouvement de souris
		
		
		if len(self.polygon) == 4: #?   not(self.waitConfirm) and 

			self.sortCorners()
			self.drawPolygon()
			# Adapte la grille au quadrilatère tracé, selon les paramètres donnés
			self.selectionGrid = self.createGrid()
			
			self.drawGrid()
			#? self.waitConfirm = True

			'''
			
			
			
			
			
			
			self.polygon = []





			'''



	# Met les points du quadrilatère dans le bon ordre pour simplifier le traitement
	# En sortie, la liste parcourt dans le sens horaire en partant d'en haut à gauche
	def sortCorners(self):

		self.polygon = sorted(self.polygon, key = lambda point : point[0]) #tri les points du plus à gauche au plus droite

		if self.polygon[1][1] < self.polygon[0][1] :
			c = self.polygon[1]
			self.polygon[1] = self.polygon[0]
			self.polygon[0] = c
		
		if self.polygon[3][1] > self.polygon[2][1] :
			c = self.polygon[3]
			self.polygon[3] = self.polygon[2]
			self.polygon[2] = c

		c = self.polygon[1]
		self.polygon[1] = self.polygon[3]
		self.polygon[3] = c
		



	def createGrid(self):
		# Créer une liste pour stocker les points des lignes horizontales et verticales
		subdivided_points = []

		self.rowSize = np.zeros(self.nRows)
		self.colSize = np.zeros(self.nCols)

		# Diviser les côtés du quadrilatère en nCols points
		for j in range(self.nRows):

			x1 = self.polygon[0][0] + ((2*j+1) * (self.polygon[3][0] - self.polygon[0][0]) / (2 * self.nRows))
			y1 = self.polygon[0][1] + ((2*j+1) * (self.polygon[3][1] - self.polygon[0][1]) / (2 * self.nRows))

			x2 = self.polygon[1][0] + ((2*j+1) * (self.polygon[2][0] - self.polygon[1][0]) / (2 * self.nRows))
			y2 = self.polygon[1][1] + ((2*j+1) * (self.polygon[2][1] - self.polygon[1][1]) / (2 * self.nRows))


			self.rowSize[j] = (x2-x1)/(2 * self.nCols)

			# On ne s'intéresse qu'aux points situés à l'intérieur du quadrilatère, pas ses côtés
			for i in range(self.nCols):
				x = x1 + (2*i+1) * (x2 - x1) / (2 * self.nCols)
				y = y1 + (2*i+1) * (y2 - y1) / (2 * self.nCols)
				subdivided_points.append((x, y))

		
		for i in range(self.nCols):
			y1 = self.polygon[0][1] + ((2*i+1) * (self.polygon[1][1] - self.polygon[0][1]) / (2 * self.nRows))
			y2 = self.polygon[3][1] + ((2*i+1) * (self.polygon[2][1] - self.polygon[3][1]) / (2 * self.nRows))
			self.colSize[i] = (y2-y1)/(2 * self.nRows)
		'''
		# new method : doesn't work perfectly either lol
		left_height = self.polygon[3][1] - self.polygon[0][1]
		right_height = self.polygon[2][1] - self.polygon[1][1]
		h_ratio = right_height / left_height
		
		for i in range(self.nCols):
			self.colSize[i] = ((2*i+1) * left_height + (self.nRows - 2*i+1) * right_height) / (2 * self.nRows)
		'''
		return subdivided_points


					
	def drawQuad(self):
		
		self.image_viewer.delete('rect')
		if self.rect_start and self.rect_end:
			x0, y0 = self.rect_start
			x1, y1 = self.rect_end
			self.image_viewer.create_rectangle(x0, y0, x1, y1, outline="red", tag="rect")



	def drawPolygon(self):
		# Draw the polygon on the image viewer
		self.image_viewer.delete('polygon')
		self.image_viewer.delete('selectionGrid')
		if len(self.polygon) > 1:
			self.image_viewer.create_polygon(self.polygon, outline="red", fill="", tag="polygon")



	def drawGrid(self):
		# Draw the grid on the image viewer AND get the values in the CSV file
		self.image_viewer.delete('selectionGrid')
		self.D = np.zeros_like(self.D)
		self.tableau.delete(*self.tableau.get_children())
		self.patche_num = 0
	
		gridSize = self.nCols * self.nRows
		temp = []

		for k in range(gridSize):
			point = self.selectionGrid[k]
			indexi = k // self.nCols
			indexj = k % self.nCols

			topleft = point[0] - self.rowsScale * self.rowSize[indexi], point[1] - self.colsScale * self.colSize[indexj]
			bottomright = point[0] + self.rowsScale * self.rowSize[indexi], point[1] + self.colsScale * self.colSize[indexj]
			self.image_viewer.create_rectangle(topleft[0], topleft[1], bottomright[0], bottomright[1], outline="blue", fill="", tag="selectionGrid")
			temp.append([topleft, bottomright])


		for k in range(gridSize):
			# for each box, take the "start" and "end" x-y values
			start = np.round(temp[k][0])
			end = np.round(temp[k][1])

			# then fix the pixel alignement (due to window scaling), and convert the result to int
			start = (int(start[0]/self.image_viewer.x_scale), int(start[1]/self.image_viewer.y_scale))
			end = (int(end[0]/self.image_viewer.x_scale), int(end[1]/self.image_viewer.y_scale))

			# display the values to debug
			'''
			print(k)
			print("start, ", start)
			print("end, ", end)
			'''
			self.moy(start, end)

		self.patche_num = 0 #au cas où le joueur changerait de mode de sélection





	# Moyenne de la valeur des pixel dans le carré sélectionné ; cas d'un rectangle
	def moy(self, start, end):
		if self.patche_num == 0 :
			self.tableau.delete(*self.tableau.get_children())
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
