import os.path
import time
import cv2
import numpy as np
from mss import mss
import pytesseract
import pickle
import speech_recognition as sr
from tkinter import *
from tkinter import ttk
from datetime import datetime
import pyttsx3
import math
from threading import Thread
from difflib import SequenceMatcher
from GPS import Light_GPS
import pydirectinput

pytesseract.pytesseract.tesseract_cmd = r'D:\Programmes\Tesseract\tesseract.exe'

icons_dict = {"bunker": 0}
colors = []
keywords = []
dumping_path = "result_scouting.pkl"
root = Tk()
root.withdraw()
WIDTH, HEIGHT = root.winfo_screenwidth(), root.winfo_screenheight()
hexes_list = ['Acrithia', 'AllodsBight', 'AshFields', 'BasinSionnach', 'CallahansPassage', 'CallumsCape',
			  'ClansheadValley', 'Deadlands', 'DrownedVale', 'EndlessShore', 'FarranacCoast', 'FishermansRow',
			  'Godcrofts', 'GreatMarch', 'Heartlands', 'HowlCounty', 'Kalokai', 'LinnMercy', 'LochMor',
			  'MarbanHollow', 'MooringCounty', 'MorgensCrossing', 'NevishLine', 'Oarbreaker', 'Origin',
			  'ReachingTrail', 'RedRiver', 'ShackledChasm', 'SpeakingWoods', 'Stonecradle', 'TempestIsland', 'Terminus',
			  'TheFingers', 'UmbralWildwood', 'ViperPit', 'WeatheredExpanse', 'Westgate', 'HomeRegion']
current_region_var = StringVar(root, "Acrithia")
gps_maps_path = r"D:\Documents Bis\Foxhole_IA\hexes_maps_fullmap\png_files"


def fuzzy_search(search_key, text, strictness):
	lines = text.split("\n")
	for i, line in enumerate(lines):
		words = line.split()
		for word in words:
			similarity = SequenceMatcher(None, word, search_key)
			if similarity.ratio() > strictness:
				# return " '{}' matches: '{}' in line {}".format(search_key, word, i + 1)
				return True
			return False


def find_text(frame: np.ndarray):
	contours, _ = cv2.findContours(frame, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
	coordinates = [0, 0]
	size = 0
	for contour in contours:
		if len(contour) >= size:
			size = len(contour)
			usable_contour = [[pixel[0][0] for pixel in contour], [pixel[0][1] for pixel in contour]]

		coordinates = [int(math.floor(np.mean(usable_contour[0]))), int(math.floor(np.mean(usable_contour[1])))]
	print(coordinates)
	return coordinates


def extract_dist_azim(frame: np.ndarray):
	compass_coordinates = {'top': 20, 'left': 1762, 'width': 133, 'height': 133}
	top_info_coordinates = {'top': 18, 'left': 18, 'width': 350, 'height': 300}
	bottom_info_coordinates = {'top': 975, 'left': 20, 'width': 425, 'height': 90}
	squad_coordinates = {'top': 320, 'left': 1675, 'width': 230, 'height': 435}
	chat_coordinates = {'top': 725, 'left': 1375, 'width': 525, 'height': 300}

	coords_to_remove = [compass_coordinates, top_info_coordinates, squad_coordinates,
						chat_coordinates, bottom_info_coordinates]

	debug_frame = frame

	for coordinates in coords_to_remove:
		height = coordinates['height']
		left = coordinates['left']
		top = coordinates['top']
		width = coordinates['width']
		for line in range(height):
			for col in range(width):
				frame[line + top][col + left] = [0, 0, 0, 0]
	# cv2.imshow("test", frame)
	# cv2.waitKey(0) & 0xFF
	# frame_bw = cv2.inRange(frame, np.array([240, 240, 240, 0]), np.array([255, 255, 255, 255]))
	frame_bw = cv2.inRange(frame, np.array([250, 0, 250, 0]), np.array([255, 10, 255, 255]))
	coordinates = find_text(frame_bw)
	frame = frame[coordinates[1]:coordinates[1] + 100, coordinates[0] - 50:coordinates[0] + 50]

	for i in range(frame.shape[0]):
		for j in range(frame.shape[1]):
			# if i == 0:
			# 	print(frame[i][j][:3])
			if np.std(frame[i][j][:2]) > 4:
				frame[i][j] = [0, 0, 0, 0]
	# cv2.imshow("Frame bis", frame)
	frame = cv2.inRange(frame, np.array([100, 100, 100, 0]), np.array([240, 240, 240, 255]))
	# cv2.imshow("Frame bis", frame)
	# cv2.waitKey(0) & 0xFF
	for i in range(frame.shape[0]):
		for j in range(frame.shape[1]):
			# print(frame_text[i][j])
			if frame[i][j] == 0:
				frame[i][j] = 255
			else:
				frame[i][j] = 0
				for x in range(-1, 2):
					for y in range(-1, 2):
						try:
							frame[i + x][j + y] = max(0, frame[i + x][j + y] - 50)
						except IndexError:
							pass
	# cv2.imshow("Error original", debug_frame)
	# cv2.imshow("Error range", frame)
	# cv2.imshow("Error bw", frame_bw)
	# cv2.waitKey(0) & 0xFF
	text = pytesseract.image_to_string(frame).lower().split("\n")

	# try:
	# 	text = pytesseract.image_to_string(frame).lower().split("\n")
	# except SystemError:
	# 	cv2.imshow("Error original", debug_frame)
	# 	cv2.imshow("Error range", frame)
	# 	cv2.waitKey(0) & 0xFF
	print(text)
	# dist, azim, _ = text.split("\n")
	# dist = dist.split(" ")[1].replace("m", "")
	# azim = azim.split(" ")[1]
	dist, azim = None, None
	index = 0
	while dist is None or azim is None:
		sentence = text[index]
		if fuzzy_search("dist", sentence, 0.5):
			dist = sentence.split(" ")[1].replace("m", "").replace("r", "")
		elif fuzzy_search("azim", sentence, 0.5):
			azim = sentence.split(" ")[1]
		index = index + 1
		if index >= len(text):
			raise ValueError
	return dist, azim


def press(key: str, timing=0.1):
	pydirectinput.press(key)
	time.sleep(timing)


def get_current_position(my_gps: Light_GPS):
	press('n')
	press('space')
	my_gps.get_current_minimap()
	press('n')
	return my_gps.find_coordinates()


class Listener:
	"""

	"""

	def __init__(self):
		self.current_decomposed_sentence = []
		self.reco = sr.Recognizer()
		self.mic = sr.Microphone()
		with self.mic as source:
			self.reco.adjust_for_ambient_noise(source)
		self.stop_listening = None
		self.final_result = []
		self.spotter_coordinates = [0, 0]
		self.screen_capture_parameters = {'top': 1, 'left': 1, 'width': WIDTH - 2, 'height': HEIGHT - 2}
		self.sct = mss()
		self.save_path = ""
		self.index = 0
		self.GPS = None
		self.region = ""

	def callback(self, recognizer, audio):
		# received audio data, now we'll recognize it using Google Speech Recognition
		try:
			# for testing purposes, we're just using the default API key
			# to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
			# instead of `r.recognize_google(audio)`
			res = recognizer.recognize_google(audio, language="fr-FR")
			print(res)
			res = str.lower(res)
			if not fuzzy_search("position", res, 0.9) and self.GPS is None:
				pyttsx3.speak("Aucune position définie.")
				return -1

			if res == "stop stop stop":
				try:
					pickle.dump(self.final_result, open(self.save_path, "wb"))
				except Exception:
					pickle.dump(self.final_result, open("temporary_file.pkl", "wb"))
					pyttsx3.speak("Chemin de sauvegarde corrompu, sauvegarde dans un dossier temporaire.")
				print(self.final_result)
				pyttsx3.speak("Aborting mission inside the current region.")
				exit()
			elif res == "position":
				if self.GPS is None:
					path = os.path.join(gps_maps_path, "Map" + self.region + "Hex.png")
					self.GPS = Light_GPS(full_map_path=path)
				elif self.region not in self.GPS.full_map_path:
					path = os.path.join(gps_maps_path, "Map" + self.region + "Hex.png")
					self.GPS = Light_GPS(full_map_path=path)
				position = get_current_position(my_gps=self.GPS)
				self.spotter_coordinates = 40 * (position[1] - 200), 40 * (position[0] - 200)
				print("New spotter coordinates: {}".format(self.spotter_coordinates))
				print("Updating the current position.")
			elif fuzzy_search("supprime", res, 0.8):
				self.final_result = self.final_result[:-1]
				pyttsx3.speak("Dernier enregistrement supprimé.")
			elif res == "scan" or res == "scanne":
				pass
			else:
				print("Google Speech Recognition thinks you said " + res)
				frame = np.array(self.sct.grab(monitor=self.screen_capture_parameters))

				# dist_azim = extract_dist_azim(frame=frame)
				# self.final_result.append([self.spotter_coordinates, dist_azim, res])
				# pyttsx3.speak(str(dist_azim) + ", " + res)
				try:
					dist_azim = extract_dist_azim(frame=frame)
					self.final_result.append([self.spotter_coordinates, dist_azim, res])
					pyttsx3.speak(str(dist_azim) + ", " + res)
				except (ValueError) as e:
					print(e)
					cv2.imwrite(r"D:\Documents Bis\Foxhole_IA\tmp\temporary_image{}.png".format(self.index), frame)
					pyttsx3.speak("Azimut et distance introuvables.")
					self.index = self.index + 1

		except sr.UnknownValueError:
			print("Google Speech Recognition could not understand audio")
		except sr.RequestError as e:
			print("Could not request results from Google Speech Recognition service; {0}".format(e))
		# except cv2.error:
		# 	print("Dist and azimut could not be retrieved, aborting due to a CV2 error")
		pyttsx3.speak("J'écoute")

	def start(self):
		pyttsx3.speak("Currently listening !")
		print("Currently listening !")
		self.stop_listening = self.reco.listen_in_background(self.mic, self.callback)
		# while True:
		# 	time.sleep(1)

	def stop(self):
		self.stop_listening(wait_for_stop=False)
		print("Pausing the recording.")


# def validate_coordinates(x, y, listener_: Listener):
# 	listener_.spotter_coordinates[0] = int(x)
# 	listener_.spotter_coordinates[1] = int(y)


def start(listenr_: Listener):
	global t1
	time.sleep(6)
	if t1.is_alive():
		print("Currently listening")
	else:
		t1 = Thread(target=listenr_.start())
		t1.start()
		print("Starting to listen")


def stop(listenr_: Listener):
	listenr_.stop()


def get_selected_region(*args):
	global listener_
	date = str(datetime.now())
	date = date.replace(" ", "_")
	date = date.replace(":", "_")
	date = date.replace(".", "_")
	date = date.replace("-", "_")
	listener_.region = current_region_var.get()
	listener_.save_path = listener_.region + "_" + date + "_" + dumping_path
	label_current_hex_value['text'] = listener_.region
	print(listener_.save_path)


if __name__ == "__main__":
	listener_ = Listener()
	t1 = Thread(target=listener_.start)

	root = Tk()
	notebook = ttk.Notebook(root)

	# hexes = Variable(root, hexes_list)
	label_current_hex = Label(root, text="Current region: ")
	label_current_hex_value = Label(root, text="FishermansRow")
	label_current_pos = Label(root, text="Current coordinates: ")
	label_current_posx = Label(root, text="line: ")
	entry_current_posx = Entry(root, text="")
	label_current_posy = Label(root, text="column: ")
	entry_current_posy = Entry(root, text="")
	optionlist_regions = OptionMenu(root, current_region_var, *hexes_list, command=get_selected_region)
	label_current_hex.grid(column=1, row=3)
	label_current_hex_value.grid(column=2, row=3)
	optionlist_regions.grid(column=3, row=3)
	label_current_pos.grid(column=1, row=4)
	label_current_posx.grid(column=2, row=4)
	entry_current_posx.grid(column=3, row=4)
	label_current_posy.grid(column=4, row=4)
	entry_current_posy.grid(column=5, row=4)
	# button_validate_coord = Button(root, text="Validate Coordinates",
	# 							   command=lambda: validate_coordinates(entry_current_posx.get(),
	# 																	entry_current_posy.get(),
	# 																	listener_))
	# button_validate_coord.grid(column=3, row=7)
	button_record = Button(root, text="Start", command=lambda: start(listener_))
	button_record.grid(column=1, row=8)
	button_stop = Button(root, text="Stop", command=lambda: stop(listener_))
	button_stop.grid(column=2, row=8)

	root.mainloop()

