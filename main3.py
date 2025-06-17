from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_STROKE_ROMAN, GLUT_BITMAP_9_BY_15
from PIL import Image
import numpy as np
import math
import time
import os
import ctypes

# --- AJOUT ---
background_texture_id = None

# Fonction pour le chargement de l'image de fond
def load_background_texture(image_path):
    global background_texture_id
    try:
        img = Image.open(image_path).convert("RGB")
        img_data = np.array(img, dtype=np.uint8)

        background_texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, background_texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.size[0], img.size[1], 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
    except Exception as e:
        print(f"Erreur chargement image de fond: {e}")

# Fonction pour le dessin de l'image de fond
def draw_background():
    global background_texture_id
    if not background_texture_id:
        return

    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(-1, 1, -1, 1, -1, 1)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, background_texture_id)

    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(-1, -1)
    glTexCoord2f(1, 0); glVertex2f( 1, -1)
    glTexCoord2f(1, 1); glVertex2f( 1,  1)
    glTexCoord2f(0, 1); glVertex2f(-1,  1)
    glEnd()

    glDisable(GL_TEXTURE_2D)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)


class CelestialBody:
    def __init__(self, name, distance, orbital_period, rotation_period, radius, color, texture_path=None, moons=None):
        self.name = name
        self.distance = distance
        self.orbital_period = orbital_period
        self.rotation_period = rotation_period
        self.radius = radius
        self.color = color
        self.texture_id = None
        self.moons = moons or []
        self.illumination = 1.0  # Facteur d'éclairage (1 = pleinement éclairé, 0 = dans l'ombre)
        
        if texture_path and os.path.exists(texture_path):
            self.load_texture(texture_path)
        
        self.orbit_angle = np.random.uniform(0, 360)
        self.rotation_angle = 0
    
    _texture_cache = {}  # Cache partagé entre toutes les instances

    def load_texture(self, texture_path):
        if texture_path in CelestialBody._texture_cache:
            self.texture_id = CelestialBody._texture_cache[texture_path]
            return

        try:
            img = Image.open(texture_path).convert("RGB")
            img_data = np.array(img, dtype=np.uint8)
        except Exception as e:
            print(f"Erreur lors du chargement de {texture_path} : {e}")
            return

        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)  # Ajout du mipmapping
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGB, img.size[0], img.size[1], 
                        GL_RGB, GL_UNSIGNED_BYTE, img_data)
        
        CelestialBody._texture_cache[texture_path] = self.texture_id
        
        
    def update(self, time_scale):
        if self.orbital_period > 0:
            self.orbit_angle += (360 / (self.orbital_period * 10)) * time_scale
        
        if self.rotation_period > 0:
            self.rotation_angle += (360 / (self.rotation_period * 10)) * time_scale
            
        for moon in self.moons:
            moon.update(time_scale)
    

    def draw_saturn_rings(self):
        glPushMatrix()
        glRotatef(-26.7, 1, 0, 0)  # Inclinaison exacte de Saturne (26.7 degrés)
        
        # Sauvegarde des états OpenGL
        glPushAttrib(GL_ENABLE_BIT | GL_LIGHTING_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Anneau principal avec transparence
        self.draw_flat_ring(1.5, 2.5, (0.9, 0.85, 0.7, 0.8), 128)
        
        # Division de Cassini
        self.draw_flat_ring(1.8, 1.9, (0.1, 0.1, 0.1, 1.0), 64)
        
        # Anneau extérieur
        self.draw_flat_ring(2.2, 2.8, (0.7, 0.65, 0.6, 0.7), 128)
        
        # Restauration des états OpenGL
        glPopAttrib()
        glPopMatrix()

    def draw_uranus_rings(self):
        glPushMatrix()
        glRotatef(98, 1, 0, 0)  # Inclinaison exacte d'Uranus (98 degrés)
        
        # Sauvegarde des états OpenGL
        glPushAttrib(GL_ENABLE_BIT | GL_LIGHTING_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Anneaux plus fins et sombres comme dans la réalité
        self.draw_flat_ring(1.1, 1.3, (0.4, 0.4, 0.5, 0.6), 64)
        self.draw_flat_ring(1.4, 1.6, (0.3, 0.3, 0.4, 0.5), 64)
        self.draw_flat_ring(1.7, 1.9, (0.2, 0.2, 0.3, 0.4), 64)
        
        # Restauration des états OpenGL
        glPopAttrib()
        glPopMatrix()

    def draw_flat_ring(self, inner_radius, outer_radius, color, segments):
        """Dessine un anneau plat avec quadrilatères et transparence"""
        glColor4f(*color)
        glBegin(GL_QUAD_STRIP)
        
        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            x = math.cos(angle)
            z = math.sin(angle)
            
            # Point intérieur
            glVertex3f(x * inner_radius, 0, z * inner_radius)
            # Point extérieur
            glVertex3f(x * outer_radius, 0, z * outer_radius)
        
        glEnd()
        
        
    def draw_sun_glow(self):
        if self != solar_system.sun:
            return
            
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Utilisation d'un display list pour optimiser le rendu
        if not hasattr(self, 'glow_display_list'):
            self.glow_display_list = glGenLists(1)
            glNewList(self.glow_display_list, GL_COMPILE)
            
            # Couche interne (haute intensité)
            glColor4f(1.0, 0.9, 0.7, 0.4)
            glutSolidSphere(self.radius * 1.5, 24, 24)  # Réduction des segments
            
            # Couche moyenne
            glColor4f(1.0, 0.7, 0.4, 0.3)
            glutSolidSphere(self.radius * 2.0, 20, 20)
            
            # Couche externe (faible intensité)
            glColor4f(1.0, 0.5, 0.2, 0.2)
            glutSolidSphere(self.radius * 2.5, 16, 16)
            
            glEndList()
        
        glCallList(self.glow_display_list)
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glDisable(GL_BLEND) 
            
    
    # Dans la classe CelestialBody, modifier la méthode update_illumination
    def update_illumination(self, sun_position):
        """Calcule l'éclairage en fonction de la position du soleil avec un modèle plus réaliste"""
        if self == solar_system.sun:
            self.illumination = 1.0
            return
            
        angle_rad = math.radians(self.orbit_angle)
        planet_pos = np.array([
            self.distance * math.cos(angle_rad),
            0,
            self.distance * math.sin(angle_rad)
        ])
        
        # Calcul du vecteur soleil -> planète et de la normale
        sun_to_planet = planet_pos - sun_position
        sun_to_planet_normalized = sun_to_planet / np.linalg.norm(sun_to_planet)
        normal = planet_pos / np.linalg.norm(planet_pos)
        
        # Produit scalaire pour déterminer l'angle entre la normale et la direction du soleil
        dot_product = np.dot(normal, sun_to_planet_normalized)
        
        # Modèle d'éclairage amélioré
        if dot_product > 0:  # Côté jour
            # Transition plus nette avec fonction sigmoïde
            illumination = 1.0 / (1.0 + math.exp(-12 * (dot_product - 0.5)))
            self.illumination = max(0.1, illumination)  # Minimum pour voir les détails
        else:  # Côté nuit
            # Éclairage très faible avec possibilité d'effet de lumière réfléchie
            self.illumination = 0.02 + 0.01 * abs(dot_product)
        
        # Mise à jour des lunes
        for moon in self.moons:
            moon.update_illumination(planet_pos)
            

    def draw(self):
        glPushMatrix()
        glRotatef(self.orbit_angle, 0, 1, 0)
        glTranslatef(self.distance, 0, 0)
        
        # Dessiner la planète d'abord
        if self != solar_system.sun:
            glRotatef(self.rotation_angle, 0, 1, 0)
            
            # Configuration du matériau avec éclairage dynamique
            ambient = [0.1, 0.1, 0.1, 1.0]  # Faible lumière ambiante
            diffuse = [
                self.color[0] * self.illumination,
                self.color[1] * self.illumination,
                self.color[2] * self.illumination,
                1.0
            ]
            
            glMaterialfv(GL_FRONT, GL_AMBIENT, ambient)
            glMaterialfv(GL_FRONT, GL_DIFFUSE, diffuse)
            glMaterialfv(GL_FRONT, GL_SPECULAR, [0.3, 0.3, 0.3, 1.0])
            glMaterialfv(GL_FRONT, GL_SHININESS, [30.0])
        else:
            # Dessiner le glow avant le soleil pour un meilleur effet
            self.draw_sun_glow()
            
            # Configuration spéciale pour le soleil (émet sa propre lumière)
            glMaterialfv(GL_FRONT, GL_EMISSION, [0.8, 0.7, 0.6, 1.0])
            glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [1.0, 0.9, 0.7, 1.0])
        
        # Dessin de la sphère (planète ou soleil)
        if self.texture_id:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            quad = gluNewQuadric()
            gluQuadricTexture(quad, GL_TRUE)
            gluQuadricNormals(quad, GLU_SMOOTH)
            gluSphere(quad, self.radius, 32, 32)
            gluDeleteQuadric(quad)
            glDisable(GL_TEXTURE_2D)
        else:
            glutSolidSphere(self.radius, 32, 32)
        
        # Réinitialiser les propriétés d'émission pour les autres objets
        if self == solar_system.sun:
            glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])
        
        # Dessiner les anneaux APRÈS la planète mais avant les lunes
        if self.name == "Saturne":
            self.draw_saturn_rings()
        elif self.name == "Uranus":
            self.draw_uranus_rings()
        
        # Dessiner les lunes
        for moon in self.moons:
            moon.draw()
        
        glPopMatrix()
    

class SolarSystem:
    def __init__(self):
        texture_dir = "Texture/"
        if not os.path.exists(texture_dir):
            print(f"ATTENTION: Le dossier {texture_dir} n'existe pas")
            os.makedirs(texture_dir, exist_ok=True)
        
        # Suppression du chargement de la skybox
        self.skybox_texture = None
        
        # Configuration des planètes (sans distinction intérieur/extérieur)
        self.sun = CelestialBody(
            "Soleil", 0, 0, 25, 2.0, (1.0, 0.8, 0.0), 
            texture_path=os.path.join(texture_dir, "2k_sun.jpg")
        )
        
        self.mercury = CelestialBody(
            "Mercure", 4, 10, 70, 0.4, (0.7, 0.7, 0.7),
            texture_path=os.path.join(texture_dir, "2k_mercury.jpg")
        )
        
        self.venus = CelestialBody(
            "Venus", 7, 120, 243, 0.6, (0.9, 0.7, 0.2),
            texture_path=os.path.join(texture_dir, "2k_venus_surface.jpg")
        )
        
        self.earth = CelestialBody(
            "Terre", 10, 365, 4, 0.6, (0.2, 0.2, 1.0),
            texture_path=os.path.join(texture_dir, "2k_earth_daymap.jpg"),
            moons=[
                CelestialBody("Moon", 1.5, 7.3, 27.3, 0.15, (0.8, 0.8, 0.8),
                             texture_path=os.path.join(texture_dir, "2k_moon.jpg"))
            ]
        )
        
        self.mars = CelestialBody(
            "Mars", 15, 687, 3, 0.5, (0.8, 0.4, 0.1),
            texture_path=os.path.join(texture_dir, "2k_mars.jpg"),
            moons=[
                CelestialBody("Phobos", 0.8, 3.319, 3.319, 0.05, (0.6, 0.6, 0.6)),
                CelestialBody("Deimos", 1.2, 5.262, 5.262, 0.03, (0.6, 0.6, 0.6))
            ]
        )
        
        self.jupiter = CelestialBody(
            "Jupiter", 20, 433, 3, 1.2, (0.8, 0.6, 0.4),
            texture_path=os.path.join(texture_dir, "2k_jupiter.jpg"),
            moons=[
                CelestialBody("Io", 1.5, 1.769, 1.769, 0.1, (0.9, 0.8, 0.5)),
                CelestialBody("Europa", 2.0, 3.551, 3.551, 0.08, (0.8, 0.8, 0.9)),
                CelestialBody("Ganymede", 2.5, 7.155, 7.155, 0.12, (0.7, 0.7, 0.8)),
                CelestialBody("Callisto", 3.0, 16.689, 16.689, 0.11, (0.6, 0.6, 0.7))
            ]
        )
        
        self.saturn = CelestialBody(
            "Saturne", 25, 10759, 3, 1.0, (0.9, 0.8, 0.6),
            texture_path=os.path.join(texture_dir, "2k_saturn.jpg"),
            moons=[
                CelestialBody("Titan", 2.2, 15.945, 15.945, 0.15, (0.8, 0.7, 0.5)),
                CelestialBody("Rhea", 1.5, 4.518, 4.518, 0.08, (0.8, 0.8, 0.8)),
                CelestialBody("Iapetus", 3.0, 79.33, 79.33, 0.07, (0.6, 0.6, 0.6))
            ]
        )
        
        self.uranus = CelestialBody(
            "Uranus", 28, 30687, 3, 0.7, (0.5, 0.8, 0.9),
            texture_path=os.path.join(texture_dir, "2k_uranus.jpg"),
            moons=[
                CelestialBody("Titania", 0.9, 8.706, 8.706, 0.08, (0.8, 0.8, 0.8)),
                CelestialBody("Oberon", 1.1, 13.463, 13.463, 0.07, (0.7, 0.7, 0.7))
            ]
        )

        self.neptune = CelestialBody(
            "Neptune", 30, 60190, 3, 0.7, (0.2, 0.3, 0.9),
            texture_path=os.path.join(texture_dir, "2k_neptune.jpg"),
            moons=[
                CelestialBody("Triton", 1.2, 5.877, 5.877, 0.1, (0.7, 0.8, 0.9))
            ]
        )
        
        self.pluto = CelestialBody(
            "Pluton", 35, 90560, 6.39, 0.2, (0.8, 0.6, 0.4),
            texture_path=os.path.join(texture_dir, "2k_pluton.jpeg"),
            moons=[
                CelestialBody("Charon", 0.4, 6.387, 6.387, 0.1, (0.7, 0.7, 0.7))
            ]
        )
        
        self.planets = [self.mercury, self.venus, self.earth, self.mars, 
                       self.jupiter, self.saturn, self.uranus, self.neptune, self.pluto]
        
        self.last_time = time.time()
        self.time_scale = 1.0

    def update(self):
        current_time = time.time()
        delta_time = current_time - self.last_time
        self.last_time = current_time
        
        # Mettre à jour les positions
        for planet in self.planets:
            planet.update(self.time_scale)
        
        # Mettre à jour l'éclairage
        sun_position = np.array([0, 0, 0])  # Le soleil est à l'origine
        for planet in self.planets:
            planet.update_illumination(sun_position)
    
    def draw(self):
        # Draw the sun
        glPushMatrix()
        glRotatef(self.sun.rotation_angle, 0, 1, 0)
        self.sun.draw()
        glPopMatrix()
        
        # Draw planets
        for planet in self.planets:
            planet.draw()
        
        # Draw orbital paths
        self.draw_orbits()
    
    def draw_orbits(self):
        glDisable(GL_LIGHTING)
        glColor3f(0.5, 0.5, 0.5)
        
        for planet in self.planets:
            glPushMatrix()
            glBegin(GL_LINE_LOOP)
            for i in range(360):
                angle = math.radians(i)
                x = planet.distance * math.cos(angle)
                z = planet.distance * math.sin(angle)
                glVertex3f(x, 0, z)
            glEnd()
            glPopMatrix()
        
        glEnable(GL_LIGHTING)


# Variables globales
camera_distance = 80
camera_angle = 0
camera_height = 5
camera_x = 0
camera_y = 0
camera_z = 0
left_button_pressed = False
right_button_pressed = False
mouse_x = 0
mouse_y = 0
solar_system = None
selected_body = None
planet_buttons = []
# Ajouter cette variable globale
tracking_mode = False


# Modifier la fonction initialize() pour configurer la lumière du soleil
# Modifications dans la fonction initialize()
def initialize():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_COLOR_MATERIAL)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    
    # Lumière principale (soleil) - plus intense
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 0.0, 0.0, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 0.9, 0.7, 1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.0, 0.0, 0.0, 1.0])  # Pas d'ambiance pour plus de contraste
    glLightfv(GL_LIGHT0, GL_SPECULAR, [0.7, 0.7, 0.7, 1.0])
    
    # Réduction de la lumière ambiante
    glEnable(GL_LIGHT1)
    glLightfv(GL_LIGHT1, GL_POSITION, [0.0, 0.0, 0.0, 1.0])
    glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.02, 0.02, 0.02, 1.0])  # Très faible
    glLightfv(GL_LIGHT1, GL_AMBIENT, [0.02, 0.02, 0.02, 1.0])  # Très faible
    glLightfv(GL_LIGHT1, GL_SPECULAR, [0.0, 0.0, 0.0, 1.0])
    
    # Configuration des matériaux
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.3, 0.3, 0.3, 1.0])
    glMaterialfv(GL_FRONT, GL_SHININESS, [30.0])
    glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])
    
    # Amélioration de la qualité de rendu
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glEnable(GL_POLYGON_SMOOTH)
    glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
    glShadeModel(GL_SMOOTH)
    

# Commande par souris
def mouse(button, state, x, y):
    global left_button_pressed, right_button_pressed, mouse_x, mouse_y, camera_distance, selected_body, tracking_mode
    
    
    mouse_x, mouse_y = x, y
    
    # if button == GLUT_LEFT_BUTTON:
    #     left_button_pressed = (state == GLUT_DOWN)
        
    #     if state == GLUT_DOWN:
    #         # Conversion correcte des coordonnées Y pour la détection des boutons
    #         window_height = glutGet(GLUT_WINDOW_HEIGHT)
    #         gl_y = window_height - y  # Conversion coordonnées OpenGL
            
    #         # Vérifier si on a cliqué sur un bouton
    #         for btn in planet_buttons:
    #             if (btn['x'] <= x <= btn['x'] + btn['width'] and 
    #                 btn['y'] <= gl_y <= btn['y'] + btn['height']):
    #                 selected_body = btn['body']
    #                 print(f"Sélectionné: {selected_body.name}")  # Debug
    #                 break
    #         else:
    #             selected_body = None
                
    # elif button == GLUT_RIGHT_BUTTON:
    #     right_button_pressed = (state == GLUT_DOWN)
    
    
    if button == GLUT_LEFT_BUTTON:
        left_button_pressed = (state == GLUT_DOWN)
        tracking_mode = False  # Désactive le suivi lors de la rotation manuelle
    elif button == GLUT_RIGHT_BUTTON:
        right_button_pressed = (state == GLUT_DOWN)
        tracking_mode = False  # Désactive le suivi lors du déplacement manuel
    elif button == 3:  # Roulette vers le haut (zoom avant)
        camera_distance = max(5, camera_distance - 2)
    elif button == 4:  # Roulette vers le bas (zoom arrière)
        camera_distance += 2
    
    glutPostRedisplay()
    

def motion(x, y):
    global camera_angle, camera_height, mouse_x, mouse_y, camera_x, camera_y, camera_z
    
    dx = x - mouse_x
    dy = y - mouse_y
    
    if left_button_pressed:  # Rotation de la vue
        camera_angle += dx * 0.5
        camera_height -= dy * 0.1
    elif right_button_pressed:  # Déplacement latéral
        camera_x += dx * 0.01
        camera_y -= dy * 0.01
    
    mouse_x, mouse_y = x, y
    glutPostRedisplay()
    

# Modifier la fonction display() pour supprimer l'affichage du texte
# Modifier la fonction display() pour mettre à jour la lumière
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    draw_background()

    # Mettre à jour la position de la lumière (toujours au soleil)
    glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 0.0, 0.0, 1.0])
    
    # Position de la caméra
    cam_x = math.sin(math.radians(camera_angle)) * camera_distance + camera_x
    cam_z = math.cos(math.radians(camera_angle)) * camera_distance + camera_z
    look_y = camera_height + camera_y

    gluLookAt(cam_x, look_y, cam_z,
              camera_x, camera_y, camera_z,
              0, 1, 0)

    # Dessiner le système solaire
    solar_system.draw()
    show_info()

    glutSwapBuffers()
    

# Affichage des information pour l'utilisateur
def show_info():
    glDisable(GL_LIGHTING)
    glColor3f(1, 1, 1)
    
    # Set up orthographic projection for text
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, glutGet(GLUT_WINDOW_WIDTH), 0, glutGet(GLUT_WINDOW_HEIGHT))
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    window_width = glutGet(GLUT_WINDOW_WIDTH)
    window_height = glutGet(GLUT_WINDOW_HEIGHT)
    
    # Display controls at top left
    text_lines = [
        "Système Solaire 3D - Contrôles:",
        "Zoom: Molette souris ou +/-",
        "Rotation: Clic gauche + déplacement de la souris",
        "Déplacement: Clic droit + déplacement de la souris",
        "Vues prédéfinies: h (haut), b (bas), g (gauche), d (droite), f (face), r (arrière)",
        "P (pause), Q (quitter)"
    ]
    
    y_pos = window_height - 20  # Commence en haut
    for line in text_lines:
        glRasterPos2f(10, y_pos)
        for char in line:
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
        y_pos -= 15  # Descend pour chaque ligne
    
    # Display planet shortcuts at bottom
    planet_shortcuts = [
        ("Soleil: Alt+S", solar_system.sun),
        ("Mercure: Alt+M", solar_system.mercury),
        ("Venus: Alt+V", solar_system.venus),
        ("Terre: Alt+T", solar_system.earth),
        ("Mars: Shift+M", solar_system.mars),
        ("Jupiter: Alt+J", solar_system.jupiter),
        ("Saturne: Shift+S", solar_system.saturn),
        ("Uranus: Alt+U", solar_system.uranus),
        ("Neptune: Alt+N", solar_system.neptune),
        ("Pluton: Shift+N", solar_system.pluto)
    ]
    
    # Calculate starting position for centered text
    total_width = 0
    for text, _ in planet_shortcuts:
        # Convertir le texte en tableau de caractères (bytes) pour glutBitmapLength
        text_bytes = (ctypes.c_ubyte * len(text))(*[ord(c) for c in text])
        total_width += glutBitmapLength(GLUT_BITMAP_9_BY_15, text_bytes)
    total_width += len(planet_shortcuts) * 10  # Ajouter l'espacement
    
    start_x = (window_width - total_width) // 4
    
    y_bottom = 20  # Position en bas
    x_pos = start_x
    
    for text, body in planet_shortcuts:
        # Change color if this is the selected body
        if selected_body == body:
            glColor3f(0, 1, 1)  # Cyan for selected
        else:
            glColor3f(1, 1, 1)  # White for others
            
        glRasterPos2f(x_pos, y_bottom)
        for char in text:
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
        
        # Add spacing between items
        text_bytes = (ctypes.c_ubyte * len(text))(*[ord(c) for c in text])
        text_width = glutBitmapLength(GLUT_BITMAP_9_BY_15, text_bytes)
        x_pos += text_width + 12  # 12px spacing
    
    # Restore previous matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_LIGHTING)    


# Fonction pour calculer la position orbitale actuelle d'une planète :
def get_body_position(body):
    """Retourne la position (x, z) actuelle d'un corps céleste."""
    if body == solar_system.sun:
        return (0, 0)
    
    angle_rad = math.radians(body.orbit_angle)
    x = body.distance * math.cos(angle_rad)
    z = body.distance * math.sin(angle_rad)
    return (x, z)    

# [Les autres fonctions (mouse, motion, keyboard, etc.) restent identiques]
#Touche de commande par clavier
def keyboard(key, x, y):
    global camera_distance, camera_height, camera_angle, camera_x, camera_z, selected_body, tracking_mode
    
    key = key.decode('utf-8').lower()
    
    if key == '+':
        camera_distance = max(5, camera_distance * 0.9)
        tracking_mode = False
    elif key == '-':
        camera_distance *= 1.1
        tracking_mode = False
    elif key == 'q':
        os._exit(0)
    elif key == 'p':
        solar_system.time_scale = 0 if solar_system.time_scale > 0 else 0.5
    
    # Commandes de sélection des corps célestes
    elif key == 's' and glutGetModifiers() == GLUT_ACTIVE_ALT:
        selected_body = solar_system.sun
        center_camera_on_body(selected_body)
    elif key == 'm' and glutGetModifiers() == GLUT_ACTIVE_ALT:
        selected_body = solar_system.mercury
        center_camera_on_body(selected_body)
    elif key == 'v' and glutGetModifiers() == GLUT_ACTIVE_ALT:
        selected_body = solar_system.venus
        center_camera_on_body(selected_body)
    elif key == 't' and glutGetModifiers() == GLUT_ACTIVE_ALT:
        selected_body = solar_system.earth
        center_camera_on_body(selected_body)
    elif key == 'm' and glutGetModifiers() == GLUT_ACTIVE_SHIFT:
        selected_body = solar_system.mars
        center_camera_on_body(selected_body)
    elif key == 'j' and glutGetModifiers() == GLUT_ACTIVE_ALT:
        selected_body = solar_system.jupiter
        center_camera_on_body(selected_body)
    elif key == 's' and glutGetModifiers() == GLUT_ACTIVE_SHIFT:
        selected_body = solar_system.saturn
        center_camera_on_body(selected_body)
    elif key == 'u' and glutGetModifiers() == GLUT_ACTIVE_ALT:
        selected_body = solar_system.uranus
        center_camera_on_body(selected_body)
    elif key == 'n' and glutGetModifiers() == GLUT_ACTIVE_ALT:
        selected_body = solar_system.neptune
        center_camera_on_body(selected_body)
    elif key == 'n' and glutGetModifiers() == GLUT_ACTIVE_SHIFT:
        selected_body = solar_system.pluto
        center_camera_on_body(selected_body)
    
    # Vues prédéfinies
    elif key == 'h':  # Vue de haut
        camera_angle = 0
        camera_height = 50
        camera_distance = 30
        camera_x = camera_y = camera_z = 0
    elif key == 'b':  # Vue de bas
        camera_angle = 0
        camera_height = -50
        camera_distance = 30
        camera_x = camera_y = camera_z = 0
    elif key == 'g':  # Vue à gauche
        camera_angle = 90
        camera_height = 5
        camera_distance = 30
        camera_x = camera_y = camera_z = 0
    elif key == 'd':  # Vue à droite
        camera_angle = 270
        camera_height = 5
        camera_distance = 30
        camera_x = camera_y = camera_z = 0
    elif key == 'f':  # Vue avant
        camera_angle = 0
        camera_height = 5
        camera_distance = 30
        camera_x = camera_y = camera_z = 0
    elif key == 'r':  # Vue arrière
        camera_angle = 180
        camera_height = 5
        camera_distance = 30
        camera_x = camera_y = camera_z = 0
    
    glutPostRedisplay()

# Fonction de centrage avec zoom dynamique
# Modifier la fonction center_camera_on_body() pour un meilleur suivi
def center_camera_on_body(body):
    """Centre la caméra sur le corps céleste avec un positionnement optimal."""
    global camera_x, camera_z, camera_distance, camera_height, camera_angle, tracking_mode
    
    tracking_mode = True
    
    # Facteurs de configuration
    zoom_base = 8  # Distance de base par unité de rayon
    height_factor = 0.8  # Hauteur de la caméra
    
    if body == solar_system.sun:
        camera_distance = body.radius * zoom_base * 1.5
        camera_height = body.radius * height_factor
        camera_angle = 45
        camera_x = 0
        camera_z = -body.radius * zoom_base * 0.8
    else:
        angle_rad = math.radians(body.orbit_angle)
        orbit_x = body.distance * math.cos(angle_rad)
        orbit_z = body.distance * math.sin(angle_rad)
        
        camera_distance = body.radius * zoom_base
        camera_height = body.radius * height_factor
        
        # Position caméra légèrement en retrait
        camera_x = orbit_x * 0.9
        camera_z = orbit_z * 0.9
        
        # Angle pour regarder vers la planète
        camera_angle = math.degrees(math.atan2(orbit_x - camera_x, orbit_z - camera_z))
    


# Modifier la fonction update_camera_tracking() pour un suivi plus fluide
def update_camera_tracking():
    global camera_x, camera_z, camera_angle, camera_distance
    
    if not tracking_mode or not selected_body:
        return
    
    if selected_body == solar_system.sun:
        camera_distance = selected_body.radius * 12
        camera_height = selected_body.radius * 0.8
        camera_angle = 45
        camera_x = 0
        camera_z = -selected_body.radius * 10
        return
    
    angle_rad = math.radians(selected_body.orbit_angle)
    target_x = selected_body.distance * math.cos(angle_rad)
    target_z = selected_body.distance * math.sin(angle_rad)
    
    # Facteurs dynamiques en fonction de la distance
    distance_factor = max(0.1, min(1.0, selected_body.distance / 30))
    smoothing_pos = 0.2 * distance_factor
    smoothing_angle = 0.3 * distance_factor
    
    # Mise à jour de la position
    camera_x = camera_x * (1 - smoothing_pos) + target_x * 0.9 * smoothing_pos
    camera_z = camera_z * (1 - smoothing_pos) + target_z * 0.9 * smoothing_pos
    
    # Mise à jour de l'angle
    target_angle = math.degrees(math.atan2(target_x - camera_x, target_z - camera_z))
    angle_diff = (target_angle - camera_angle + 180) % 360 - 180
    camera_angle += angle_diff * smoothing_angle
    
    # Ajustement automatique de la distance
    target_distance = selected_body.radius * 8 + selected_body.distance * 0.3
    camera_distance = camera_distance * 0.95 + target_distance * 0.05


    

def reshape(width, height):
    if height == 0:
        height = 1  # Empêche division par zéro

    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, width / height, 0.1, 1000)
    glMatrixMode(GL_MODELVIEW)

def idle():
    solar_system.update()
    update_camera_tracking()  # Ajout de la mise à jour du suivi
    glutPostRedisplay()


# Fonction main
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1200, 800)
    glutCreateWindow(b"System Solar 3D - Simplified")

    global solar_system
    solar_system = SolarSystem()
    initialize()

    load_background_texture("etoile.jpg")

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()