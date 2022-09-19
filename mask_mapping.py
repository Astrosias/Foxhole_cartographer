import pickle
from tkinter import *
import math
from difflib import SequenceMatcher
from PIL import Image

vipshome = 'D:\\Programmes\\libvips\\vips-dev-8.13\\bin'
import os
os.environ['PATH'] = vipshome + ';' + os.environ['PATH']
import pyvips


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


def distance(point1, point2):
	return math.sqrt((point1[0] - point2[0])*(point1[0] - point2[0]) + (point1[1] - point2[1])*(point1[1] - point2[1]))


def compute_angle(p1, p2):
	# p1 = [p1[1], p1[0]]
	# p2 = [p2[1], p2[0]]
	print(p1, p2)
	delta_x = p2[0] - p1[0]
	delta_y = p2[1] - p1[1]
	# print(p1, p2, atan2(delta_y, delta_x))
	res = 360 * math.atan2(delta_y, delta_x) / (2 * math.pi)
	# if res < 0:
	# 	# res = 2 * math.pi + res
	# 	res = 360 + res
	return res


def compute_linear_trajectory(previous_traj, point_2, speed: int):
	point = previous_traj[-1]
	time_tmp = len(previous_traj)
	theta = compute_angle(point, point_2)
	theta_cos = (2 * math.pi / 360) * theta
	# theta = theta - 90
	# if theta < 0:
	# 	theta = theta + 360
	dist_tmp = distance(point, point_2)
	# print(dist_tmp)
	delta_x = speed * math.cos(theta_cos)
	delta_y = speed * math.sin(theta_cos)
	print(point, point_2, speed, theta_cos)
	while speed + 1 < dist_tmp <= distance(previous_traj[-1], point_2):
		point = [point[0] + delta_x, point[1] + delta_y, - theta]
		previous_traj.append(point)
		dist_tmp = distance(point, point_2)
		time_tmp = time_tmp + 1
	previous_traj.append([point_2[0], point_2[1], - theta])
	return previous_traj

bas_objects_dict = {"pillbox": ["pile", "box", "boxe"], "bunker": ["c\u0153ur"], "tour de guet": [], "antichar": ["t-shirt"],
					"mitrailleuse": ["railleuse", "travailleuse"], "batterie": ["patrie", "ma\u00e7onnerie", "bàthory"],
					"fusil": ["fusible"], "radar": [], "tonnerre": [], "facility": [], "artillerie": [], "rail": ["rails", "raï"]}


precise_objects = {"pillbox": ["at", "mg", "rf"], "facility": ["mine"]}
orientations = ["nordouest", "nordest", "sudouest", "sudest", "nord", "sud", "ouest", "est"]
factions = ["bleu", "verte", "vert", "colonial", "warden", "le", "vers", "verre", "verres"]
tiers = ["1", "2", "3", "un", "deux", "de", "trois", "troie"]
icons_path = r"D:\Documents Bis\Foxhole_IA\icons_mapping"
masks_path = r"D:\Documents Bis\Foxhole_IA\global_maps\transparent_masks"

rail_network = []
rail_size = 50


def analyse_sentence(sentence: str):
	sentence = sentence.lower()
	print(sentence)
	name = ""
	final_faction = ""

	for obj in bas_objects_dict.keys():
		if " " in obj:
			if obj in sentence:
				name = obj
				break
		elif fuzzy_search(obj, sentence, 0.9):
			name = obj
			break
		else:
			for word in bas_objects_dict[obj]:
				if fuzzy_search(word, sentence, 0.9):
					name = obj
					break
	if name == "rail":
		return name, 0
	if name in precise_objects.keys():
		for word in precise_objects[name]:
			if fuzzy_search(word, sentence, 0.9):
				name = name + "_" + word
				break

	sentence = sentence.replace(name, "", 1)

	if name == "":
		raise ValueError("The sentence does not have any object.")
	for obj_bis in precise_objects:
		if sentence.find(obj_bis) >= 0:
			# properties["object"] = properties["object"] + "_" + obj_bis
			name = name + "_" + obj_bis
			sentence = sentence.replace(obj_bis, "", 1)
			break
	for faction in factions:
		if sentence.find(faction) >= 0:
			sentence = sentence.replace(faction, "", 1)
			if faction == "bleu" or faction == "warden" or faction == "le":
				# properties["faction"] = "warden"
				final_faction = "warden"
			else:
				# properties["faction"] = "colonial"
				final_faction = "colonial"
			break
	for nb in tiers:
		if sentence.find(nb) >= 0:
			if nb == "1" or nb == "un":
				# properties["tier"] = "1"
				name = name + "_" + "1"
			elif nb == "2" or nb == "de" or nb == "deux":
				# properties["tier"] = "2"
				name = name + "_" + "2"
			else:
				# properties["tier"] = "3"
				name = name + "_" + "3"
			# name = name + "_" + properties["tier"]
			break
	name = name.replace("batterie_3", "")

	direction = ""
	angle = 0
	sentence = sentence.replace("-", "")
	sentence = sentence.replace(" ", "")

	for direction_ in orientations:
		if sentence.find(direction_) > 0:
			direction = direction_
			break

	print("direction: ", direction)

	if direction == "nordest":
		angle = 7 * 45
	elif direction == "sudest":
		angle = 5 * 45
	elif direction == "sudouest":
		angle = 3 * 45
	elif direction == "nordouest":
		angle = 1 * 45
	elif direction == "ouest":
		angle = 2 * 45
	elif direction == "est":
		angle = 6 * 45
	elif direction == "sud":
		angle = 4 * 45
	elif direction == "nord":
		angle = 0
	else:
		print("No angle found, setting angle at 0")
		angle = 0

	path = os.path.join(icons_path, final_faction, name + ".png")

	return path, angle


class EditorHighRes:
	"""

	"""

	def __init__(self, path_tmp: str):
		"""
		:param path_tmp:
		"""
		self.main_map_path = path_tmp
		self.id = 0
		# print(path_tmp)
		self.main_map_path_save = path_tmp.split(".")[0] + "save_bis" + ".png"
		self.main_map = pyvips.Image.new_from_file(self.main_map_path)
		self.working_image = None
		self.offset = [0, 0]
		self.icon_path = ""
		self.coordinates = [0, 0]
		self.angle = 0

	def update_working_icon(self, coords, new_path: str, angle: float):
		self.icon_path = new_path
		self.coordinates = coords
		self.angle = angle
		self.working_image = Image.open(self.icon_path, 'r')

	def rotate_image(self):
		"""
		Given an angle in rad, rotates the working image.
		:param angle: In rad
		"""
		print("rotation angle: {}".format(self.angle))
		self.working_image = self.working_image.rotate(angle=self.angle, expand=True)

	def _switch_to_pyvips(self):
		"""
		It is impossible (with my limited hardware) to process 100MB and more images with only cv2 and PIL.
		Thus, we use pyvips, a python port of libvips, to deal with the full maps.
		You'll probably have a problem here, your installation needs to be similar to mine to work:
		Python 3.9, 64bits. Libvips Windows, 64bits.

		The working image is saved to a temporary file, so that we only have to add images once, when every images
		corresponding to the current region has been processed. This is done beacuse writing back the global map is what
		takes 90% of the compilation time.
		"""
		self.id = self.id + 1
		self.temporary_path = r"D:\Documents Bis\Foxhole_IA\tmp/temporary_image" + str(self.id) + ".png"
		self.working_image.save(self.temporary_path)
		# self.coordinates = self.current_photo.coordinates[1] * 40, self.current_photo.coordinates[0] * 40
		self.offset = [int(math.floor(self.coordinates[0] - self.working_image.size[0] / 2)),
					   int(math.floor(self.coordinates[1] - self.working_image.size[1] / 2)),
					   int(math.ceil(self.coordinates[0] + self.working_image.size[0] / 2)),
					   int(math.ceil(self.coordinates[1] + self.working_image.size[1] / 2))]
		self.working_image = pyvips.Image.new_from_file(self.temporary_path, access='sequential')

	def add_image_to_map(self):
		"""
		Adds the working image to the global map.
		The changes won't apply until the global map is saved using EditorHighRes.save_main_map.
		:return:
		"""
		offset_size = self.offset[2] - self.offset[0], self.offset[3] - self.offset[1]
		# print(self.offset)
		print("Real coordinates: ", self.coordinates)
		print("self.offset size: {}	".format(offset_size))
		# self.main_map = self.main_map.insert(500, 10, 10)
		# self.main_map = self.main_map.insert(self.working_image, self.offset[0], self.offset[1])
		self.main_map = self.main_map.composite2(self.working_image, "over", x=self.offset[0], y=self.offset[1])
		# print("Does main map has alpha ? ", self.main_map)

	def process_new_photo(self, coords, new_path, angle):
		"""
		:param photo: A cartographer.Photo object
		:param angle: The rotation angle, in rad
		:param legacy_coords: The coordinates retrieved by the gps, on a small map.
		:return:
		"""
		self.update_working_icon(coords, new_path, angle)
		self.rotate_image()
		self._switch_to_pyvips()
		self.add_image_to_map()

	def save_main_map(self):
		"""
		Writes all the changes applied to the global map to a new image.
		This takes a lot of time.
		:return:
		"""
		self.main_map.write_to_file(self.main_map_path_save)


def compute_offset(dist_azim: tuple):
	dist_azim = dist_azim[0].lower(), dist_azim[1].lower()
	dict_char_int = {"o": "0", "i": "1", "l": "1", "g": "9", "s": "5"}
	for key in dict_char_int.keys():
		dist_azim = dist_azim[0].replace(key, dict_char_int[key]), dist_azim[1].replace(key, dict_char_int[key])
	dist, azim = int(dist_azim[0]), int(dist_azim[1])
	print("dist, azim: ", dist_azim)
	col = math.sin(2*math.pi * azim / 360) * dist * 18.819
	line = -math.cos(2*math.pi * azim / 360) * dist * 18.819

	line = int(math.floor(line))
	col = int(math.floor(col))

	# line, col = col, line

	return col, line


def process_data_folder(path: str):
	all_paths = os.listdir(path)
	all_paths_dict = {}
	for path_tmp in all_paths:
		if path_tmp.endswith(".pkl"):
			region = path_tmp.split("_")[0]
			try:
				all_paths_dict[region].append(os.path.join(path, path_tmp))
			except KeyError:
				all_paths_dict[region] = [os.path.join(path, path_tmp)]

	for region in all_paths_dict.keys():
		print("New region being processed: {0}".format(region))
		print("======================================================================================================")
		path_list = all_paths_dict[region]
		print(masks_path)
		path_to_map = os.path.join(masks_path, "Map" + region + "Hex.png")
		# print(path_to_map)
		my_editor_HR = EditorHighRes(path_tmp=path_to_map)
		for path_tmp in path_list:
			rail_network = []
			dataset = pickle.load(open(path_tmp, "rb"))
			for data in dataset:
				print("---------------------------- NEW POINT ----------------------------")
				print(data)
				try:
					offset = compute_offset(data[1])
					coords = [data[0][1] + offset[0], data[0][0] + offset[1]]
				except ValueError:
					continue
				try:
					path, angle = analyse_sentence(data[2])
				except ValueError as e:
					print("Value error, ", e)
					continue
				print(path)
				if path == "rail":
					if fuzzy_search("début", data[2], 0.9):
						rail_network.append([[coords[0], coords[1], 0]])
					else:
						try:
							# print(rail_network, rail_network[-1])
							# print(coords)
							rail_network[-1] = compute_linear_trajectory(rail_network[-1], coords, speed=rail_size)
						except IndexError:
							print("The railroad should have started before. Starting it now.")
							rail_network.append([[coords[0], coords[1], 0]])
							print(rail_network)
				else:
					my_editor_HR.process_new_photo(coords=coords, new_path=path, angle=angle)
			print(rail_network)
			for section in rail_network:
				for point in section:
					print(point)
					my_editor_HR.process_new_photo(coords=(point[0], point[1]),
												   new_path=os.path.join(icons_path, "neutral", "rail.png"),
												   angle=point[2])

		my_editor_HR.save_main_map()
		print("{} processed.".format(region))


if __name__ == "__main__":
	data_folder = r"D:\Documents Bis\Foxhole_IA\cartographer"
	process_data_folder(data_folder)
	print("Job done")
