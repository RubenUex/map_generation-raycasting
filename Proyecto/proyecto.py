import cv2
import numpy as np
import pygame
import math

"""
-----------GENERACIÓN DE MAPA-------------
"""

image = cv2.imread("./imagenes/lineas5.jpg", cv2.IMREAD_GRAYSCALE)
image_height, image_width= image.shape
IMAGE_SCALING_RATIO = 0.2
NEW_IMAGE_HEIGHT, NEW_IMAGE_WIDTH = int(image_height*IMAGE_SCALING_RATIO), int(image_width*IMAGE_SCALING_RATIO)
image = cv2.resize(image, (NEW_IMAGE_WIDTH, NEW_IMAGE_HEIGHT))
_, image_transformed = cv2.threshold(image, 120, 255, cv2.THRESH_BINARY_INV)

matrix_borders_width = 1
matrix_borders_height = 1
image_divisions_x = 20
image_divisions_y = 20
matrix_borders = np.zeros((matrix_borders_width, matrix_borders_height))
def update_matrix(divisions_x, divisions_y):
	global image_divisions_x
	global image_divisions_y
	global matrix_borders_width
	global matrix_borders_height
	global matrix_borders
	image_divisions_x = divisions_x
	image_divisions_y = divisions_y
	matrix_borders_width = int(NEW_IMAGE_WIDTH/image_divisions_x)
	matrix_borders_height = int(NEW_IMAGE_HEIGHT/image_divisions_y)
	matrix_borders = np.zeros((matrix_borders_width, matrix_borders_height))
	lines = cv2.HoughLinesP(image_transformed, 1, 0.01, 0, np.array([]), 25, 35)
	for line in lines:
		for x1, y1, x2, y2 in line:
			cv2.line(matrix_borders, (int(x1/image_divisions_x), int(y1/image_divisions_y)), (int(x2/image_divisions_x), int(y2/image_divisions_y)), 255)
	image_borders = cv2.resize(matrix_borders, (matrix_borders_width * image_divisions_x, matrix_borders_height * image_divisions_y), interpolation = cv2.INTER_NEAREST)
	cv2.imshow("Mapa generado", image_borders)

def update_matrix_size(size):
	update_matrix(int(NEW_IMAGE_WIDTH/size), int(NEW_IMAGE_HEIGHT/size))

update_matrix_size(20)
cv2.createTrackbar("Size", "Mapa generado", 20, 50, update_matrix_size)
cv2.setTrackbarMin("Size", "Mapa generado", 10)
cv2.setTrackbarMax("Size", "Mapa generado", 50)

cv2.imshow("Imagen original", image)

cv2.waitKey(0)
cv2.destroyAllWindows()

#El mapa estará rodeado siempre de una barrera de 1s, para controlar cualquier error de generación.
map = np.ones((matrix_borders_width + 2, matrix_borders_height + 2))
map[1:matrix_borders_width + 1, 1:matrix_borders_height + 1] = matrix_borders[:, :]

"""
-----------RAY CASTING-------------
"""

map_width = len(map)
map_height = len(map[0])
screen_width = 600
screen_height = 600
NUMBER_OF_TILES = min(map_width, map_height)
TILE_SIZE = min(screen_width, screen_height) / NUMBER_OF_TILES
TILE_DRAW_SIZE = TILE_SIZE - 1 #El número que se resta está para ver los bordes de las baldosas.
CLOCK = pygame.time.Clock()
WINDOW = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Actividad ID - Ruben Vazquez Angamarca")
MAP_COLOR_BACKGROUND = (0, 0, 0)
COLOR_WALL = (92, 78, 70)
MAP_COLOR_WALL_HIT = (153, 85, 46)
COLOR_GROUND = (189, 199, 182)
MAP_COLOR_PLAYER = (204, 72, 76)
MAP_COLOR_PLAYER_LINES = (169, 91, 219)
MAP_COLOR_RAY = (88, 186, 222)
MAP_COLOR_TEXT = (58, 165, 222)
POV_COLOR_TEXT = (30, 30, 30)
POV_COLOR_BACKGROUND = (188, 241, 255)
NUMBER_OF_RAYS = int(screen_width / 8)
POV_WALL_STEP = screen_width / NUMBER_OF_RAYS
POV_WALL_MAX_HEIGHT = screen_height * 50
POV_SHADOW_RATE = 0.00001
PLAYER_SPEED = 4 #Actúa como la hipotenusa al calcular el movimiento
player_angle = 0
TURN_SPEED = 0.1
FOV = math.pi / 3
HALF_FOV = FOV / 2
FIRST_RAY_ANGLE = player_angle - HALF_FOV
RAY_STEP_ANGLE = FOV / NUMBER_OF_RAYS
#La profundidad máxima posible es la hipotenusa del mapa (esquina a esquina)
MAX_RAY_DEPTH = int(math.sqrt(map_width * map_width + map_height * map_height) * TILE_SIZE)
start_x = -1
start_y = -1
keepPlaying = True
map_mode = True

def initialize_game():
	found_spot = False
	pygame.init()
	smallest_dimension = min(map_height, map_width)
	for tile in range(int(smallest_dimension/2)):
		row_col_1 = int(smallest_dimension / 2 + tile)
		row_col_2 = int(smallest_dimension / 2 - tile)
		if (map[row_col_1][row_col_1] == 0):
			found_spot = True
			player_row = row_col_1
			player_column = row_col_1
			break
		elif (map[row_col_2][row_col_2] == 0):
			found_spot = True
			player_row = row_col_2
			player_column = row_col_2
			break
		elif (map[row_col_1][row_col_2] == 0):
			found_spot = True
			player_row = row_col_1
			player_column = row_col_2
			break
		elif (map[row_col_2][row_col_1] == 0):
			found_spot = True
			player_row = row_col_2
			player_column = row_col_1
			break
	if (found_spot):
		return (player_column * TILE_SIZE) + (TILE_SIZE / 2), (player_row * TILE_SIZE) + (TILE_SIZE / 2)
	else:
		return -1, -1

def draw_map():
	for row in range(map_width):
		for column in range(map_height):
			if (map[row][column] != 0):
				pygame.draw.rect(WINDOW, COLOR_WALL, (column * TILE_SIZE, row * TILE_SIZE, TILE_DRAW_SIZE, TILE_DRAW_SIZE))
			else:
				pygame.draw.rect(WINDOW, COLOR_GROUND, (column * TILE_SIZE, row * TILE_SIZE, TILE_DRAW_SIZE, TILE_DRAW_SIZE))
			pygame.draw.circle(WINDOW, MAP_COLOR_PLAYER, (int(player_x), int(player_y)), 8)
			
def ray_cast():
	ray_angle = player_angle - HALF_FOV
	for ray in range(NUMBER_OF_RAYS):
		for depth in range(MAX_RAY_DEPTH):
			ray_x = player_x - math.sin(ray_angle) * depth
			ray_y = player_y + math.cos(ray_angle) * depth
			ray_row = int(ray_y / TILE_SIZE)
			ray_column = int(ray_x / TILE_SIZE)
			if (map[ray_row][ray_column] != 0):
				if (map_mode):
					pygame.draw.line(WINDOW, MAP_COLOR_RAY, (player_x, player_y), (ray_x, ray_y))
					pygame.draw.rect(WINDOW, MAP_COLOR_WALL_HIT, 
						(ray_column * TILE_SIZE, ray_row * TILE_SIZE, TILE_DRAW_SIZE, TILE_DRAW_SIZE))
				else:
					#Por cada canal (RGB), voy oscureciendo el color según la distancia de la pared.
					#Sumo 1 para evitar la división por 0 y para asegurar que el resultado siempre es menor que "channel"
					#porque así todas las divisiones son mayores que 1. Si no, podría obtener números mayores a 255.
					color_wall_ray = tuple(channel / (1 + (depth * depth * POV_SHADOW_RATE)) for channel in COLOR_WALL)
					depth *= math.cos(player_angle - ray_angle)
					if (depth == 0):
						wall_height = POV_WALL_MAX_HEIGHT
					else:
						wall_height = POV_WALL_MAX_HEIGHT / depth
					pygame.draw.rect(WINDOW, (color_wall_ray), (ray * POV_WALL_STEP, (screen_height / 2) - (wall_height / 2), POV_WALL_STEP, wall_height))
				break
		ray_angle += RAY_STEP_ANGLE


start_x, start_y = initialize_game()
if ((start_x == -1) | (start_y == -1)):
	print("Error: no se pudo encontrar ninguna baldosa libre.")
	pygame.quit()
	exit(0)

player_x = start_x
player_y = start_y
while (keepPlaying):
	for event in pygame.event.get():
		if (event.type == pygame.KEYDOWN):
			if (event.key == pygame.K_SPACE):
				map_mode = not map_mode
	if (map_mode):
		draw_map()
	ray_cast()
	CLOCK.tick(60)
	keys = pygame.key.get_pressed()
	movement_x = movement_y = 0
	movement_sine = PLAYER_SPEED * math.sin(player_angle)
	movement_cosine = PLAYER_SPEED * math.cos(player_angle)
	if (keys[pygame.K_q]):
		keepPlaying = False
	if (keys[pygame.K_w]):
		movement_x += -movement_sine
		movement_y += movement_cosine
	if (keys[pygame.K_a]):
		movement_x += movement_cosine
		movement_y += movement_sine
	if (keys[pygame.K_s]):
		movement_x += movement_sine
		movement_y += -movement_cosine
	if (keys[pygame.K_d]):
		movement_x += -movement_cosine
		movement_y += -movement_sine
	if (keys[pygame.K_RIGHT]):
		player_angle += TURN_SPEED
	if (keys[pygame.K_LEFT]):
		player_angle -= TURN_SPEED
	player_x += movement_x
	player_y += movement_y
	if (map[int(player_y/TILE_SIZE)][int(player_x/TILE_SIZE)] != 0):
		player_x -= movement_x
		player_y -= movement_y

	font = pygame.font.SysFont('Monospace Regular', 30)
	if (map_mode):
		text_color = MAP_COLOR_TEXT
	else:
		text_color = POV_COLOR_TEXT
	textsurface_tip_1 = font.render("Pulsa 'q' para salir.", False, text_color)
	textsurface_tip_2 = font.render("Pulsa la barra espaciadora para cambiar de vista.", False, text_color)
	WINDOW.blit(textsurface_tip_1, (0, 0))
	WINDOW.blit(textsurface_tip_2, (0, textsurface_tip_1.get_height() + 5))
	pygame.display.flip()
	if (map_mode):
		pygame.draw.rect(WINDOW, MAP_COLOR_BACKGROUND, (0, 0, screen_width, screen_height))
	else:
		pygame.draw.rect(WINDOW, POV_COLOR_BACKGROUND, (0, 0, screen_width, screen_height/2))
		pygame.draw.rect(WINDOW, COLOR_GROUND, (0, screen_height/2, screen_width, screen_height/2))