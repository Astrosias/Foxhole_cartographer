import numpy as np
from mss import mss
from datetime import datetime
import os
import pickle
from tkinter import *
from tkinter import ttk, filedialog
from threading import Thread
import mouse
import time
import math



root = Tk()
root.withdraw()
WIDTH, HEIGHT = root.winfo_screenwidth(), root.winfo_screenheight()
print("Width: {0}, Height: {1}".format(WIDTH, HEIGHT))
current_region_var = StringVar(root, "Acrithia")
current_altitude_var = StringVar(root, "")

current_region = ""
current_altitude = 0
coordinates = [0, 0]
hexes_list = ['Acrithia', 'AllodsBight', 'AshFields', 'BasinSionnach', 'CallahansPassage', 'CallumsCape',
			  'ClansheadValley', 'Deadlands', 'DrownedVale', 'EndlessShore', 'FarranacCoast', 'FishermansRow',
			  'Godcrofts', 'GreatMarch', 'Heartlands', 'HowlCounty', 'Kalokai', 'LinnMercy', 'LochMor',
			  'MarbanHollow', 'MooringCounty', 'MorgensCrossing', 'NevishLine', 'Oarbreaker', 'Origin',
			  'ReachingTrail', 'RedRiver', 'ShackledChasm', 'SpeakingWoods', 'Stonecradle', 'TempestIsland', 'Terminus',
			  'TheFingers', 'UmbralWildwood', 'ViperPit', 'WeatheredExpanse', 'Westgate', 'HomeRegion']
altitudes_list = ["Low (on the ground)", "Medium (vehicle hatch, on top of bunker",
				  "High (window of TH)", "VeryHigh (Top on church, montain...)"]
cursor_itinerary = []


go_up = True
columns = [0, 200, 400, 600, 750, 900, 1000, 1150, 1300, 1500, 1700, 1900]
coef_line = 200
for col in columns:
	if col> 1000:
		coef_line = coef_line + 15
	elif col == 0:
		coef_line = 200
	else:
		coef_line = coef_line - 15
	for line in range(int(math.floor(HEIGHT/coef_line)) + 1):
		if go_up:
			step_line = line * coef_line
		else:
			step_line = line * coef_line
			# step_line = HEIGHT - j * 200 - 1
		cursor_itinerary.append((step_line, col))
		# print((step_line, col))
	go_up = not go_up

cursor_itinerary_webodm = []
columns = [50 * x for x in range(38)]
lines = [50 * x for x in range(21)]
for col in columns:
	for line in lines:
		cursor_itinerary_webodm.append([line, col])


recording = False
save_path = ""


def compute_distance_between_points(pixel1, pixel2):
	return math.sqrt(math.pow(pixel1[0] - pixel2[0], 2) + math.pow(pixel1[1] - pixel2[1], 2))


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


class Radar:

	def __init__(self):
		self.center_screen = [int(abs(math.floor((HEIGHT-1)/2))), int(abs(math.floor((WIDTH-1)/2)))]
		self.center_circle = [-1, -1]
		self.save_path = ""
		self.screen_capture_parameters = {'top': 1, 'left': 1, 'width': WIDTH - 2, 'height': HEIGHT - 2}
		self.sct = mss()
		self.coordinates_tmp = None
		self.coef_line = 1 / 10
		self.coef_col = (1920 / 1080)/40

	def scan_area(self):
		print("SCANNING")
		time.sleep(10)
		mouse.press(button=RIGHT)
		previous_point = self.center_screen
		# for point in cursor_itinerary_webodm:
		for point in cursor_itinerary:
			mouse.move(point[1], point[0])
			if compute_distance_between_points(point, previous_point) > 400:
				time.sleep(4)
				previous_point = point
			time.sleep(1.5)
			self.save_path = save_path
			# print(mouse.is_pressed())
			# print(mouse.is_pressed(button=RIGHT))
			# print(mouse.is_pressed(button=LEFT))
			# if not mouse.is_pressed(button=RIGHT):
			# 	print("Program interrupted, mouse released.")
			# 	break
			frame = np.array(self.sct.grab(monitor=self.screen_capture_parameters))
			date = str(datetime.now())
			date = date.replace(" ", "_")
			date = date.replace(":", "_")
			date = date.replace(".", "_")
			date = date.replace("-", "_")
			tmp_photo = Photo(date, frame, region_tmp=current_region)
			tmp_photo.coordinates = self.compute_position(point)
			tmp_photo.part_of_circle = True
			tmp_photo.altitude = current_altitude.split(" ")[0].lower()
			print("Point: {0}, Coordinates: {1}".format(point, tmp_photo.coordinates))
			print(frame.shape)
			filename = os.path.join(self.save_path, date + current_region + ".pkl")
			pickle.dump(tmp_photo, open(filename, "wb"))
		print("Scan complete, result saved to {}.".format(save_path))

	def compute_position(self, point):
		self.center_circle = [coordinates[0], coordinates[1]]
		print(self.center_circle)
		return self.center_circle
		# return [self.center_circle[0] + (point[0] - self.center_screen[0]) * self.coef_line,
		# 		self.center_circle[1] + (point[1] - self.center_screen[1]) * self.coef_col]


def record_screen():
	global radar
	global recording
	global t1
	recording = True
	time.sleep(6)
	if 	t1.is_alive():
		print("Currently recording")
		recording = True
	else:
		t1 = Thread(target=radar.scan_area)
		t1.start()
		print("Starting the recording")


def validate_coordinates(x, y):
	global coordinates
	coordinates[0] = int(x)
	coordinates[1] = int(y)


def get_save_path():
	global save_path
	save_path = filedialog.askdirectory()
	label_save_folder_value['text'] = save_path


def stop_recording():
	global recording
	recording = False


def get_selected_region(*args):
	global current_region
	# current_region = hexes_list[listbox_regions.curselection()[0]]
	current_region = current_region_var.get()
	label_current_hex_value['text'] = current_region


def get_selected_altitude(*args):
	global current_altitude
	# current_region = hexes_list[listbox_regions.curselection()[0]]
	current_altitude = current_altitude_var.get()
	label_current_altitude_value['text'] = current_altitude


if __name__ == "__main__":
	radar = Radar()
	t1 = Thread(target=radar.scan_area)

	root = Tk()
	notebook = ttk.Notebook(root)

	hexes = Variable(root, hexes_list)
	altitudes = Variable(root, altitudes_list)

	label_current_hex = Label(root, text="Current region: ")
	label_current_hex_value = Label(root, text="FishermansRow")
	label_current_pos = Label(root, text="Current coordinates: ")
	label_current_posx = Label(root, text="line: ")
	entry_current_posx = Entry(root, text="")
	label_current_posy = Label(root, text="column: ")
	entry_current_posy = Entry(root, text="")
	label_current_altitude = Label(root, text="Current altitude: ")
	label_current_altitude_value = Label(root, text="")

	label_save_folder = Label(root, text="Choose where to save the screenshots: ")
	label_save_folder_value = Label(root, text="...")

	optionlist_regions = OptionMenu(root, current_region_var, *hexes_list, command=get_selected_region)
	optionlist_altitudes = OptionMenu(root, current_altitude_var, *altitudes_list, command=get_selected_altitude())
	label_save_folder.grid(column=1, row=1)
	label_save_folder_value.grid(column=2, row=1)
	button_get_path = Button(root, text="Browse", command=lambda: get_save_path())
	button_get_path.grid(column=3, row=1)

	label_current_hex.grid(column=1, row=3)
	label_current_hex_value.grid(column=2, row=3)
	optionlist_regions.grid(column=3, row=3)
	label_current_pos.grid(column=1, row=4)
	label_current_posx.grid(column=2, row=4)
	entry_current_posx.grid(column=3, row=4)
	label_current_posy.grid(column=4, row=4)
	entry_current_posy.grid(column=5, row=4)
	label_current_altitude.grid(column=1, row=5)
	label_current_altitude_value.grid(column=5, row=5)
	optionlist_altitudes.grid(column=3, row=5)


	button_validate_altitude = Button(root, text="Validate Altitude",
								   command=lambda: get_selected_altitude())
	button_validate_altitude.grid(column=3, row=6)
	button_validate_coord = Button(root, text="Validate Coordinates",
								   command=lambda: validate_coordinates(entry_current_posx.get(), entry_current_posy.get()))
	button_validate_coord.grid(column=3, row=7)
	button_record = Button(root, text="Start", command=lambda: record_screen())
	button_record.grid(column=1, row=8)
	button_stop = Button(root, text="Stop", command=lambda: stop_recording())
	button_stop.grid(column=2, row=8)

	# listbox_regions.bind('<<ListboxSelect>>', get_selection)

	root.mainloop()
