import tkinter as tk
from tkinter import ttk, filedialog

from Interface.imageViewer import ImageViewer

from PIL import Image
from PIL.TiffTags import TAGS

from Algo.registration2 import registration
from Algo.fausseCouleur import fausseCouleur, fausseCouleur2Points
from Algo.spectro import cubeMS

from parameter import Parameter
from Interface.configuration import ConfigurationR, ConfigurationD

import numpy as np
import cv2

import threading
import queue
import time

PAD = 10
COLOR_MENU = '#D6DCDB'


class Interface(tk.Tk):
	
	def __init__(self):

		super().__init__()

		self.title("Analyse multispectrale")
		self.wm_state("zoomed")
		self.update()
		# print(self.winfo_width(), self.winfo_height())
		# print(self.winfo_screenwidth(), self.winfo_screenheight())
		self.wm_minsize(int(self.winfo_screenwidth() * 0.3), int(self.winfo_screenheight() * 0.3))
		#self.resizable(False, False)
		
		# Variables
		self.file = ""
		self.img_tiff = None
		self.height = self.winfo_height()
		self.width = self.winfo_width
		self.window_resized = False
		self.tmp_height = 0
		self.tiff_array_16bits = None
		self.tiff_array_8bits = None
		self.img_tiff_data = {}
		self.is_FC_display = False
		self.parameters = Parameter(self)

		# Widgets
		self.createMenuBar()
		self.displayFrameLoad()
		self.initStyles()


	# Barre de menu en haut
	def createMenuBar(self):

		self.frame_menu_bar = tk.Frame(self)
		self.menu_bar = tk.Menu(self.frame_menu_bar)
		self.config(menu=self.menu_bar)

		self.menu_file = tk.Menu(self.menu_bar, tearoff=0)
		self.menu_file.add_command(label='Ouvrir', command=self.loadImagesTiff)
		self.menu_file.add_command(label='Sauvegarder', command=self.saveImages)
		self.menu_file.entryconfig("Sauvegarder", state="disabled")

		self.menu_configure = tk.Menu(self.menu_bar, tearoff=0)
		self.menu_configure.add_command(label='Réflectance', command=lambda : ConfigurationR(self, self.parameters))
		self.menu_configure.add_command(label='Patches', command=lambda : ConfigurationD(self, self.parameters))
		self.menu_configure.add_command(label='Blanc', command=self.parameters.whiteFiles)
		self.menu_configure.add_command(label='Noir', command=self.parameters.blackFile)

		self.menu_bar.add_cascade(label='Fichier', menu=self.menu_file)
		self.menu_bar.add_cascade(label='Configuration', menu=self.menu_configure)


	# Que pour le début
	def displayFrameLoad(self):

		#Init
		self.frame_laod = tk.Frame(self)
		self.image_folder = tk.PhotoImage(file='icons/folder.png') 
		self.btn_load_image = ttk.Button(self.frame_laod, takefocus=False, compound='left',
										 text="Charger un fichier tiff", cursor="hand2",
										 image=self.image_folder, command=self.loadImagesTiff)

		self.frame_laod.place(rely=.5, relx=.5, anchor='center')
		self.btn_load_image.pack()


	# Frame principal où est affichée l'image
	def displayFrameMain(self):

		# Init
		self.frame_main = tk.Frame(self)
		self.frame_image = tk.Frame(self.frame_main)

		self.image_viewer = ImageViewer(self.frame_image, parameters=self.parameters, root=self)
		self.frame_controls = tk.Frame(self.frame_main, name='controls')
		self.btn_next_img = ttk.Button(self.frame_controls, text='>', takefocus=False, 
									   cursor="hand2", command=self.nextImage)
		self.btn_prev_img = ttk.Button(self.frame_controls, text='<', takefocus=False,
									   cursor="hand2", command=self.prevImage)
		self.var_frame_info = tk.StringVar()
		self.var_frame_info.set('1/' + str(self.image_viewer.nb_frame))
		self.label_frame_number = ttk.Label(self.frame_controls, textvariable=self.var_frame_info)
		self.frame_separation = tk.Frame(self)

		self.frame_main.pack(side='left', fill='both', expand=True)
		self.frame_controls.pack(pady=PAD, side='bottom')
		self.frame_image.pack(fill='both', expand=True, pady=PAD)
		self.image_viewer.pack()
		
		self.btn_prev_img.pack(side='left', padx=2*PAD, ipady=5, anchor='w')
		self.label_frame_number.pack(side='left')
		self.btn_next_img.pack(side='left', padx=2*PAD, ipady=5)

		self.frame_separation.pack(side='left', fill='y')


	# Menu principal
	def displayFrameMenu(self):

		self.frame_menu = tk.Frame(self, width=300, bg=COLOR_MENU)
		self.frame_menu.pack_propagate(False)

		self.btn_registration = ttk.Button(self.frame_menu, takefocus=False, text='Recalage',
										   cursor='hand2', command=self.displayMenuRegistration, style='M.TButton')

		self.btn_fausses_couleurs = ttk.Button(self.frame_menu, takefocus=False, text='Fausses couleurs',
										   	   cursor='hand2', command=self.displayMenuFaussesCouleurs, style='M.TButton')

		self.btn_cube_MS = ttk.Button(self.frame_menu, takefocus=False, text='Cube MS',
										   	   cursor='hand2', command=self.displayMenuMS, style='M.TButton')

		self.btn_back = ttk.Button(self.frame_menu, takefocus=False, text='<',
								   cursor='hand2', command=self.backToMainMenu, style='M.TButton')

		self.frame_menu.pack(side='right', fill='y')
		self.btn_registration.pack(fill='x', ipady=PAD)
		self.btn_fausses_couleurs.pack(fill='x', ipady=PAD)
		self.btn_cube_MS.pack(fill='x', ipady=PAD)


	# Menu pour la registration
	def displayMenuRegistration(self):

		self.clearFrame(self.frame_menu, unpack=True)

		self.frame_imref =tk.Frame(self.frame_menu, bg=COLOR_MENU)
		self.frame_imref.grid_columnconfigure(1, weight=1)
		self.frame_imref.grid_columnconfigure(0, weight=1)

		self.var_entry = tk.StringVar()
		self.entry_im_ref = ttk.Entry(self.frame_imref, width=15)
		self.entry_im_ref.insert(0, '1')
		self.btn_enter_registration = ttk.Button(self.frame_menu, takefocus=False, cursor='hand2',
												 text="Entrer", command=self.registrationImage, style='M.TButton')

		self.frame_menu.pack(side='right', fill='y')
		self.btn_back.pack(anchor='w', side='top')

		self.frame_imref.pack(fill='x', pady=PAD)
		ttk.Label(self.frame_imref, text='Image de référence : ', style='M.TLabel').grid(row=0, column=0, sticky='w', padx=5)
		self.entry_im_ref.grid(row=0, column=1, sticky='e', padx=PAD)

		self.btn_enter_registration.pack(side='bottom', pady=PAD, padx=PAD, fill='x', ipady=PAD)


	# Retourne au menu principal
	def backToMainMenu(self):

		self.clearFrame(self.frame_menu, unpack=True)
		self.displayFrameMenu()
		self.image_viewer.unbindFCFonctions()
		self.image_viewer.unbindMSFonctions()


	# Menu pour les fausses couleurs
	def displayMenuFaussesCouleurs(self):	

		self.clearFrame(self.frame_menu, unpack=True)

		if not self.is_FC_display:
			self.image_viewer.bind("<Button-1>", self.image_viewer.clickOnImageFC)

		# Selection ROIS
		self.frame_ROIS = tk.Frame(self.frame_menu, background=COLOR_MENU)
		for i in range(2):
			self.frame_ROIS.grid_columnconfigure(i, weight=1)

		self.nb_ROIS_entry = ttk.Combobox(self.frame_ROIS, values=[2, 3], width=15)
		self.nb_ROIS_entry.set(self.parameters.nb_ROIS)
		self.nb_ROIS_entry.bind('<<ComboboxSelected>>', self.selectNbROIS)

		self.size_ROIS_var = tk.StringVar()
		self.size_ROIS_entry = tk.Entry(self.frame_ROIS, textvariable=self.size_ROIS_var, width=18)
		self.size_ROIS_var.set(self.parameters.size_ROIS)
		# Met à jour le rayon des ROIS lorsque la valeur change
		self.size_ROIS_var.trace('w', lambda name, index, mode, var=self.size_ROIS_var: self.selectSizeROIS(var))

		# Gestions points fausses couleurs
		self.frame_coord = tk.Frame(self.frame_menu, background=COLOR_MENU)
		for i in range(3):
			self.frame_coord.grid_columnconfigure(i, weight=1)

		self.text_labelx = [tk.StringVar() for i in range(3)]
		self.text_labely = [tk.StringVar() for i in range(3)]
		self.labelsx = [ttk.Label(self.frame_coord, textvariable=self.text_labelx[i], style='M.TLabel') for i in range(3)]
		self.labelsy = [ttk.Label(self.frame_coord, textvariable=self.text_labely[i], style='M.TLabel') for i in range(3)]
		self.btn_delete_coord1 = ttk.Button(self.frame_coord, takefocus=False, cursor='hand2',
										   text='X', command=lambda: self.deleteCoord(0), style='M.TButton')
		self.btn_delete_coord2 = ttk.Button(self.frame_coord, takefocus=False, cursor='hand2',
										   text='X', command=lambda: self.deleteCoord(1), style='M.TButton')
		self.btn_delete_coord3 = ttk.Button(self.frame_coord, takefocus=False, cursor='hand2',
										   text='X', command=lambda: self.deleteCoord(2), style='M.TButton')

		self.btn_enter_FC = ttk.Button(self.frame_menu, takefocus=False, cursor='hand2',
									   text='Entrer', command=self.fausseCouleurImage, style='M.TButton')


		self.frame_menu.pack(side='right', fill='y')

		self.btn_back.pack(anchor='w')

		self.frame_ROIS.pack(pady=PAD, fill='x')

		ttk.Label(self.frame_ROIS, text='Nombre de ROIS', style='M.TLabel').grid(row=0, column=0, pady=5, sticky='w', padx=5)
		self.nb_ROIS_entry.grid(row=0, column=1, pady=5, padx=PAD)
		ttk.Label(self.frame_ROIS, text='Rayon des ROIS', style='M.TLabel').grid(row=1, column=0, pady=5, sticky='w', padx=5)
		self.size_ROIS_entry.grid(row=1, column=1, pady=5)

		self.frame_coord.pack(pady=PAD, fill='x')

		for i in range(self.parameters.nb_ROIS):
			self.labelsx[i].grid(row=i, column=0, pady=5, padx=PAD)
			self.labelsy[i].grid(row=i, column=1, pady=5, padx=PAD)
			self.text_labelx[i].set('x : ')
			self.text_labely[i].set('y : ')

		self.btn_delete_coord1.grid(row=0, column=2, pady=5, padx=PAD, sticky='e')
		self.btn_delete_coord2.grid(row=1, column=2, pady=5, padx=PAD, sticky='e')

		if self.parameters.nb_ROIS == 3:
			self.btn_delete_coord3.grid(row=2, column=2, pady=5, padx=PAD, sticky='e')

		self.btn_enter_FC.pack(side='bottom', pady=PAD, padx=PAD, fill='x', ipady=PAD)


	# Affiche le menu Cube Multispectral
	def displayMenuMS(self):
		
		self.clearFrame(self.frame_menu, unpack=True)

		self.btn_enter_MS = ttk.Button(self.frame_menu, takefocus=False, cursor='hand2',
									   text='Entrer', style='M.TButton', command=self.imagesSpectro)
		self.var_error = tk.StringVar()
		self.error_label = ttk.Label(self.frame_menu, textvariable=self.var_error, style='Error.TLabel')

		self.frame_R = tk.Frame(self.frame_menu, bg=COLOR_MENU)
		self.R_label = ttk.Label(self.frame_R, text="Réflectance des patches", style='M.TLabel')
		self.R_entry = tk.Entry(self.frame_R)
		self.R_entry.insert(0, self.parameters.R_file)
		self.btn_load_R = ttk.Button(self.frame_R, takefocus=False, cursor='hand2',
									   text='...', style='M.TButton', command=lambda : ConfigurationR(self, self.parameters))

		self.frame_D = tk.Frame(self.frame_menu, bg=COLOR_MENU)
		self.D_label = ttk.Label(self.frame_D, text="Couleurs des patches", style='M.TLabel')
		self.D_entry = tk.Entry(self.frame_D)
		if self.parameters.D.shape != (0, 0):
			self.D_entry.insert(0, self.parameters.D)
		self.btn_load_D = ttk.Button(self.frame_D, takefocus=False, cursor='hand2',
									   text='...', style='M.TButton', command=lambda : ConfigurationD(self, self.parameters))

		self.frame_white = tk.Frame(self.frame_menu, bg=COLOR_MENU)
		self.white_var = tk.StringVar()
		self.white_label = ttk.Label(self.frame_white, style='M.TLabel', textvariable=self.white_var)
		self.white_var.set("Images blanches " + '(' + str(len(self.parameters.white_files)) + ' fichiers)')
		self.white_entry = tk.Entry(self.frame_white)
		self.white_entry.insert(0, self.parameters.white_files)
		self.btn_load_white = ttk.Button(self.frame_white, takefocus=False, cursor='hand2',
									   text='...', style='M.TButton', command=self.parameters.whiteFiles)

		self.frame_black = tk.Frame(self.frame_menu, bg=COLOR_MENU)
		self.black_label = ttk.Label(self.frame_black, text="Image noire", style='M.TLabel')
		self.black_entry = tk.Entry(self.frame_black)
		self.black_entry.insert(0, self.parameters.black_file)
		self.btn_load_black = ttk.Button(self.frame_black, takefocus=False, cursor='hand2',
									   text='...', style='M.TButton', command=self.parameters.blackFile)

		self.frame_nb_img = tk.Frame(self.frame_menu, bg=COLOR_MENU)
		self.nb_img_label = ttk.Label(self.frame_nb_img, text="Nombres d'images à éditer", style='M.TLabel')
		self.nb_img_entry = tk.Entry(self.frame_nb_img)
		self.nb_img_entry.insert(0, 20)

		self.frame_menu.pack(side='right', fill='y')
		self.btn_back.pack(anchor='w')

		self.frame_R.pack(fill='x', pady=PAD)
		self.R_label.pack(side='top', anchor='w', padx=5)
		self.R_entry.pack(fill='x', side='left', expand=True, padx=5)
		self.btn_load_R.pack(side='right', padx=5)

		self.frame_D.pack(fill='x', pady=PAD)
		self.D_label.pack(side='top', anchor='w', padx=5)
		self.D_entry.pack(fill='x', side='left', expand=True, padx=5)
		self.btn_load_D.pack(side='right', padx=5)

		self.frame_white.pack(fill='x', pady=PAD)
		self.white_label.pack(side='top', anchor='w', padx=5)
		self.white_entry.pack(fill='x', side='left', expand=True, padx=5)
		self.btn_load_white.pack(side='right', padx=5)

		self.frame_black.pack(fill='x', pady=PAD)
		self.black_label.pack(side='top', anchor='w', padx=5)
		self.black_entry.pack(fill='x', side='left', expand=True, padx=5)
		self.btn_load_black.pack(side='right', padx=5)

		self.frame_nb_img.pack(fill='x', pady=PAD)
		self.nb_img_label.pack(side='top', anchor='w', padx=5, pady=5)
		self.nb_img_entry.pack(fill='x', side='left', expand=True, padx=5)

		self.btn_enter_MS.pack(side='bottom', pady=PAD, padx=PAD, fill='x', ipady=PAD)


	# Styles de cerains widgets
	def initStyles(self):

		self.style = ttk.Style()

		self.style.configure('M.TLabel', background=COLOR_MENU)
		self.style.configure('M.TButton', background=COLOR_MENU)
		self.style.configure('Error.TLabel', background=COLOR_MENU, foreground='red')


	# Affiche barre de progression
	def displayProgressBar(self, text):

		self.clearFrame(self.frame_main)

		self.frame_prg = tk.Frame(self.frame_main)
		self.prg_bar = ttk.Progressbar(self.frame_main, orient='horizontal', mode='determinate', length=280, maximum=100.1)
		self.label_progress_text = ttk.Label(self.frame_main, text=text)
		self.var_progress = tk.StringVar()
		self.label_progress = ttk.Label(self.frame_main, textvariable=self.var_progress)

		self.frame_prg.place(relx=.5, rely=.5, anchor='center')
		self.label_progress_text.pack(pady=10)
		self.prg_bar.pack(pady=10)
		self.label_progress.pack(pady=10)
		self.updateProgressBar(0)


	# Fixe la valeur de la barre de progression
	def updateProgressBar(self, step):

		if self.prg_bar['value'] <= 100.0:
			self.prg_bar.step(step)
			self.var_progress.set(str(self.prg_bar['value']) + '%')
			self.update()


	# Charge fichier TIFF
	def loadImagesTiff(self):

		self.file = filedialog.askopenfilename(filetypes=[('Fichiers TIFF', '*.tif *.tiff'), ('Tous les fichiers', '*.*')])

		# Vérifie si un fichier est selectionné
		if len(self.file) == 0: return
			
		if self.is_FC_display:
			self.is_FC_display = False
			self.label_comb.place_forget()

		# Met à jour l'affichage
		if self.tiff_array_16bits == None: # Si pas d'images déja affichées
			self.menu_file.entryconfig("Sauvegarder", state="normal")
			self.frame_laod.place_forget()
			self.displayFrameMenu()
			self.displayFrameMain()
		else:
			self.backToMainMenu()

		self.getDataImage()
		self.image_viewer.updateImages(self.tiff_array_16bits)
		self.image_viewer.displayImage()


	# Ouvre fichier TIFF et ses métadonnées
	def getDataImage(self):

		# Image
		self.tiff_array_16bits = cv2.imreadmulti(self.file, flags=cv2.IMREAD_ANYDEPTH)[1]
		self.tiff_array_8bits = cv2.imreadmulti(self.file)[1]

		# Metadonnées
		self.img_tiff = Image.open(self.file)
		self.img_tiff_data = {TAGS[key] : self.img_tiff.tag[key] for key in self.img_tiff.tag_v2}
		self.img_tiff_data['ImageWidth'] = self.img_tiff_data['ImageWidth'][0]
		self.img_tiff_data['ImageLength'] = self.img_tiff_data['ImageLength'][0]
		self.img_tiff_data['NbFrame'] = self.img_tiff.n_frames


	# Démarre l'algorithme de recalage des images
	def registrationImage(self):

		try :
			num_img_ref = int(self.entry_im_ref.get()) - 1
		except:
			return

		self.queue_registration = queue.Queue()
		self.queue_offset = queue.Queue()
		self.tiff_registred = []
		self.offsets = []

		self.displayProgressBar("Recalage des images")
		
		# Registration
		self.thread_registration = threading.Thread(target=registration,
													args=(self.tiff_array_8bits, self.queue_registration, self.queue_offset, num_img_ref))
		self.thread_registration.start()

		# Pendant l'algorithme
		while len(self.tiff_registred) < self.image_viewer.nb_frame:
			try:
				r = self.queue_registration.get(timeout=2)
				o = self.queue_offset.get(timeout=2)
			except queue.Empty:
				pass
			else:
				self.tiff_registred.append(r)
				self.offsets.append(o)
				self.updateProgressBar(100/self.image_viewer.nb_frame)

		# Met à jour l'affichage à la fin de l'algo
		self.is_FC_display = False
		self.clearFrame(self.frame_main, unpack=True)
		self.displayFrameMain()
		self.image_viewer.updateImages(self.tiff_registred)
		self.image_viewer.displayImage()
		self.backToMainMenu()


	# Démarre l'algorithme des fausses couleurs
	def fausseCouleurImage(self):

		coord = self.image_viewer.list_points

		# Vérifie si tous les ROIS sont selectionnés
		if np.any(np.all(coord[0:self.parameters.nb_ROIS] == [0, 0], axis=1)):
			ttk.Label(self.frame_menu, text='Sélectionnez tous les ROIS !', style='M.TLabel').pack()
			return

		self.queue_FC = queue.Queue()
		self.img_FC = []
		self.comb_FC = []

		self.displayProgressBar("Edition des images fausses couleurs")

		# Offset si la registration à été faite
		try:
			offsets = self.offsets
		except AttributeError:
			offsets = np.zeros((self.image_viewer.nb_frame, 2))

		# Calcule les meilleurs images fausses couleurs 
		try:
			img_registred = self.tiff_registred
		except:
			if self.parameters.nb_ROIS == 2:
				self.thread_FC = threading.Thread(target=fausseCouleur2Points,
					  			  args=(self.tiff_array_16bits, self.queue_FC, coord, offsets, self.parameters.size_ROIS))
			elif self.parameters.nb_ROIS == 3:
				self.thread_FC = threading.Thread(target=fausseCouleur,
									  			  args=(self.tiff_array_16bits, self.queue_FC, coord, offsets, self.parameters.size_ROIS))
		else:
			if self.parameters.nb_ROIS == 2:
				self.thread_FC = threading.Thread(target=fausseCouleur2Points,
					  			  args=(self.tiff_array_16bits, self.queue_FC, coord, offsets, self.parameters.size_ROIS, img_registred))
			elif self.parameters.nb_ROIS == 3:
				self.thread_FC = threading.Thread(target=fausseCouleur,
									  			  args=(self.tiff_array_16bits, self.queue_FC, coord, offsets, self.parameters.size_ROIS, img_registred))

		self.thread_FC.start()

		# Pendant l'algorithme
		while len(self.img_FC) < 10:
			try:
				fc = self.queue_FC.get(timeout=2)
			except queue.Empty:
				pass
			else:
				self.img_FC.append(fc[0])
				self.comb_FC.append(fc[1])
				self.updateProgressBar(100/10)
		
		# Mise à jour affichage à la fin de l'algorithme
		self.clearFrame(self.frame_main, unpack=True)
		self.displayFrameMain()
		self.image_viewer.updateImages(self.img_FC)
		self.image_viewer.displayImage()
		self.is_FC_display = True
		self.current_comb = tk.StringVar()
		self.label_comb = ttk.Label(self.frame_main, textvariable=self.current_comb)
		self.label_comb.place(x=0, y=0)
		self.current_comb.set("Combinaison de \nl'image fausse couleur : \n" + ", ".join(str(i + 1) for i in self.comb_FC[0]))
		self.backToMainMenu()


	# Cube Multispectral
	def imagesSpectro(self):

		self.nb_imgMS = int(self.nb_img_entry.get()) - 1

		#if not self.checkParamMS(): return
		self.parameters.calcQ()
		self.cube_MS = cubeMS(self.tiff_array_16bits, self.parameters.Q)

		# Mise à jour de l'affichage
		self.clearFrame(self.frame_main, unpack=True)
		self.displayFrameMain()
		self.image_viewer.updateImages(self.cube_MS, k=self.nb_imgMS)
		self.image_viewer.displayImage()
		self.is_FC_display = False
		self.image_viewer.bind("<Button-1>", self.image_viewer.clickOnImageMS)


	# vérifie tous les paramètres avant imagesScpectro
	# Affiche des messages d'erreur
	def checkParamMS(self):

		if self.error_label.winfo_ismapped():
			self.error_label.pack_forget()

		if self.parameters.D.shape == (0, 0) or np.any(np.all(self.parameters.D == np.zeros((1, 16)), axis=1)): # Couleurs des patches
			self.var_error.set("Couleurs des patches imcomplète")
			self.error_label.pack()
			return False

		if self.nb_imgMS > self.parameters.Q.shape[0] or self.nb_imgMS <= 0: # Nombre d'images à afficher
			self.var_error.set("Nombres d'images incorrect")
			self.error_label.pack()
			return False

		return True


	# Affiche l'image suivante
	def nextImage(self):
		
		if self.image_viewer.index_img < self.image_viewer.nb_frame - 1:
			self.image_viewer.index_img += 1
			self.image_viewer.displayImage()
			self.updateLabelFrameInfo()

			if self.is_FC_display:
				self.updateLabelCombInfo()


	# Affiche l'image précédente
	def prevImage(self):
		
		if self.image_viewer.index_img > 0:
			self.image_viewer.index_img -= 1
			self.image_viewer.displayImage()
			self.updateLabelFrameInfo()

			if self.is_FC_display:
				self.updateLabelCombInfo()


	# Affiche le numéro de l'image affichée
	def updateLabelFrameInfo(self):

		self.var_frame_info.set(str(self.image_viewer.index_img + 1) + '/' + str(self.image_viewer.nb_frame))


	# Affiche la combinaison des images multispectrales qui compose l'image fausses couleurs affichées
	def updateLabelCombInfo(self):

		self.current_comb.set("Combinaison de \nl'image fausse couleur : \n" + ", ".join(str(i) for i in self.comb_FC[self.image_viewer.index_img]))


	# Supprime une coordonnées d'un ROIS quand click sur bouton deleteCoord
	def deleteCoord(self, num_point):

		self.text_labelx[num_point].set('x : ')
		self.text_labely[num_point].set('y : ')
		self.image_viewer.deleteCoord(num_point)


	# Pour menu fausses couleurs
	# Met a jour l'affichage en fonction du nombre de ROIS souhaité
	def selectNbROIS(self, event):

		self.parameters.nb_ROIS = int(self.nb_ROIS_entry.get())

		if self.parameters.nb_ROIS == 2:
			self.labelsx[-1].grid_forget()
			self.labelsy[-1].grid_forget()
			self.btn_delete_coord3.grid_forget()
			self.image_viewer.canvas_points[-1].place_forget()
			self.image_viewer.deleteCoord(2)
			self.text_labelx[-1].set('x : ')
			self.text_labely[-1].set('y : ')
		elif self.parameters.nb_ROIS == 3:
			self.labelsx[-1].grid(row=2, column=0)
			self.labelsy[-1].grid(row=2, column=1)
			self.btn_delete_coord3.grid(row=2, column=2, pady=5, padx=PAD, sticky='e')


	# Pour menu fausses couleurs
	# Met a jour la taille des ROIS sur l'image
	def selectSizeROIS(self, var):

		try:
			self.parameters.size_ROIS = int(var.get())
		except ValueError:
			return
		else:
			for canva in self.image_viewer.canvas_points:
				canvas_points.config(width=self.parameters.size_ROIS+1, height=self.parameters.size_ROIS+1)


	# Sauvegarder images affichées en TIFF
	def saveImages(self):

		file_path = filedialog.asksaveasfilename(filetypes=[("Fichiers TIFF", "*.tiff"), ("Tous les fichiers", "*.*")],
												 initialfile="image.TIFF")

		if len(file_path) == 0:
			return
			
		cv2.imwritemulti(file_path, self.image_viewer.imagesToSave())


	# Supprime tous les widgets d'une frame
	def clearFrame(self, frame, unpack=False):
		
		for children in frame.winfo_children():
			try:
				children.pack_forget()
			except:
				try:
					children.grid_forget()
				except:
					children.place_forget()

		if unpack:
			frame.pack_forget()


	# Adapte la taille de l'image à la fenetre
	def onResize(self, event):
			
		# # print(self.tmp_height, self.winfo_height())
		# print(event.type)
		# if self.tmp_height != self.winfo_height():
		# 	self.tmp_height = self.winfo_height()
		# 	return
		#time.sleep(0.1)

		# if (self.winfo_width() != self.width or self.winfo_height() != self.height) and len(self.image_viewer.img_display) > 0:
		# 	self.image_viewer.displayImage()
		# 	self.width = self.winfo_width()

		if (self.winfo_width() != self.width or self.winfo_height() != self.height) and len(self.image_viewer.img_display) > 0:
			# Fenêtre redimensionnée manuellement
			self.image_viewer.displayImage()
			self.width = self.winfo_width()
			self.height = self.winfo_height()

if __name__ == "__main__":

	I = Interface()

	I.mainloop()