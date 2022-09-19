import numpy as np
from mss import mss
import time
from datetime import datetime
import os
import pickle
from tkinter import *
from tkinter import ttk, filedialog
from threading import Thread
import cv2
import matplotlib.pyplot as plt

lower_squad_boundary_HSV = np.array([60, 0, 100])
upper_squad_boundary_HSV = np.array([90, 255, 255])
orange_RGB = [219, 154, 113]

root = Tk()
root.withdraw()
WIDTH, HEIGHT = root.winfo_screenwidth(), root.winfo_screenheight()
current_region_var = StringVar(root, "Acrithia")

current_region = ""
hexes_list = ['Acrithia', 'AllodsBight', 'AshFields', 'BasinSionnach', 'CallahansPassage', 'CallumsCape',
			  'ClansheadValley', 'Deadlands', 'DrownedVale', 'EndlessShore', 'FarranacCoast', 'FishermansRow',
			  'Godcrofts', 'GreatMarch', 'Heartlands', 'HowlCounty', 'Kalokai', 'LinnMercy', 'LochMor',
			  'MarbanHollow', 'MooringCounty', 'MorgensCrossing', 'NevishLine', 'Oarbreaker', 'Origin',
			  'ReachingTrail', 'RedRiver', 'ShackledChasm', 'SpeakingWoods', 'Stonecradle', 'TempestIsland', 'Terminus',
			  'TheFingers', 'UmbralWildwood', 'ViperPit', 'WeatheredExpanse', 'Westgate', 'HomeRegion']
recording = False
save_path = ""
top_info_coordinates = {'top': 18, 'left': 18, 'width': 145, 'height': 145}
icons_path = "D:\Documents Bis\Foxhole_IA\icons_vehicles"


class Photo:

	def __init__(self, date_tmp: str, picture_tmp: np.ndarray, region_tmp: str):
		self.date = date_tmp
		self.coordinates = [-1, -1]
		self.picture = picture_tmp
		self.region = region_tmp
		self.angle = -1
		self.resolution = (WIDTH, HEIGHT)
		self.part_of_circle = False
		self.altitude = 0


class Camera:

	def __init__(self):
		self.period = 1
		self.save_path = "images_created"
		self.screen_capture_parameters = {'top' : 1, 'left' : 1, 'width' : WIDTH - 2, 'height' : HEIGHT - 2}
		self.sct = mss()

	def run(self):
		global recording
		global save_path
		while True:
			time.sleep(self.period)
			if not recording:
				continue
			self.save_path = save_path
			frame = np.array(self.sct.grab(monitor=self.screen_capture_parameters))
			date = str(datetime.now())
			date = date.replace(" ", "_")
			date = date.replace(":", "_")
			date = date.replace(".", "_")
			date = date.replace("-", "_")
			tmp_photo = Photo(date, frame, region_tmp=current_region)
			print(frame.shape)
			# print(frame[917][163])
			# print(self._is_in_vehicle(frame))
			if current_region == "":
				print("No region selected, not recording.")
			# elif self._has_marker(frame):
			elif self._is_in_vehicle(frame):
				filename = os.path.join(self.save_path, date + current_region + ".pkl")
				pickle.dump(tmp_photo, open(filename, "wb"))
			else:
				print("You are not in a vehicle, not recording.")

	def _has_marker(self, frame_tmp):
		pixel = frame_tmp[917][163]
		if pixel[2] > 225 or pixel[2] < 200:
			return False
		if pixel[1] > 160 or pixel[1] < 140:
			return False
		if pixel[0] > 120 or pixel[0] < 106:
			return False
		return True

	def _is_in_vehicle(self, image: np.ndarray):
		# icon = image[54:54+50, 31:31+50]
		icon = image[17:17+75, 17:17+75]
		icon = cv2.cvtColor(icon.astype(np.uint8), cv2.COLOR_RGB2GRAY)
		_, icon = cv2.threshold(icon, 100, 100, cv2.THRESH_TOZERO )
		# cv2.imwrite("result.png", icon)
		# cv2.imshow("icon", icon)
		# cv2.waitKey(0) & 0xFF
		for icon_path in os.listdir(icons_path):
			icon_tmp = cv2.imread(os.path.join(icons_path, icon_path), cv2.IMREAD_GRAYSCALE)
			# icon_tmp = cv2.cvtColor(icon_tmp.astype(np.uint8), cv2.COLOR_RGB2GRAY)
			heat_map = cv2.matchTemplate(icon, icon_tmp, cv2.TM_CCOEFF_NORMED)
			if heat_map [0][0] > 0.22:
				print(icon_path)
				return True
		return False


def record_screen():
	global cam
	global recording
	global t1
	recording = True
	if 	t1.is_alive():
		recording = True
	else:
		t1.start()


def get_save_path():
	global save_path
	save_path = filedialog.askdirectory()
	label_save_folder_value['text'] = save_path


def stop_recording():
	global recording
	recording = False


def get_selection(*args):
	global current_region
	# current_region = hexes_list[listbox_regions.curselection()[0]]
	current_region = current_region_var.get()
	label_current_hex_value['text'] = current_region


if __name__ == "__main__":
	cam = Camera()
	t1 = Thread(target=cam.run)

	root = Tk()
	notebook = ttk.Notebook(root)

	hexes = Variable(root, hexes_list)

	label_current_hex = Label(root, text="Current region: ")
	label_current_hex_value = Label(root, text="FishermansRow")

	label_save_folder = Label(root, text="Choose where to save the screenshots: ")
	label_save_folder_value = Label(root, text="...")

	optionlist_regions = OptionMenu(root, current_region_var, *hexes_list, command=get_selection)
	label_save_folder.grid(column=1, row=1)
	label_save_folder_value.grid(column=2, row=1)
	button_get_path = Button(root, text="Browse", command=lambda: get_save_path())
	button_get_path.grid(column=3, row=1)

	label_current_hex.grid(column=1, row=3)
	label_current_hex_value.grid(column=2, row=3)
	optionlist_regions.grid(column=3, row=3)

	button_record = Button(root, text="Start", command=lambda: record_screen())
	button_record.grid(column=1, row=4)
	button_stop = Button(root, text="Stop", command=lambda: stop_recording())
	button_stop.grid(column=2, row=4)

	# listbox_regions.bind('<<ListboxSelect>>', get_selection)

	root.mainloop()
