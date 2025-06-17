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

# --- Variables globales ---
background_texture_id = None
shadow_texture_id = None
shadow_map_size = 2048  # Taille de la texture pour les ombres

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

# Initialisation du shadow mapping
def init_shadow_map():
    global shadow_texture_id
    shadow_texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, shadow_texture_id)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, 
                 shadow_map_size, shadow_map_size, 0,
                 GL_DEPTH_COMPONENT, GL_UNSIGNED_BYTE, None)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    
    # Création du framebuffer pour les ombres
    shadow_fbo = glGenFramebuffers(1)
    glBindFramebuffer(GL_FRAMEBUFFER, shadow_fbo)
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, shadow_texture_id, 0)
    
    glDrawBuffer(GL_NONE)
    glReadBuffer(GL_NONE)
    
    status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
    if status != GL_FRAMEBUFFER_COMPLETE:
        print("Erreur lors de la création du framebuffer pour les ombres")
    
    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    return shadow_fbo

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
    
    def load_texture(self, texture_path):
        try:
            img = Image.open(texture_path).convert("RGB")
            img_data = np.array(img, dtype=np.uint8)
        except Exception as e:
            print(f"Erreur lors du chargement de {texture_path} : {e}")
            return

        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.size[0], img.size[1], 
                     0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
    
    def update(self, time_scale):
        if self.orbital_period > 0:
            self.orbit_angle += (360 / (self.orbital_period * 10)) * time_scale
        
        if self.rotation_period > 0:
            self.rotation_angle += (360 / (self.rotation_period * 10)) * time_scale
            
        for moon in self.moons:
            moon.update(time_scale)
    
    def draw_saturn_rings():
        glPushMatrix()
        glRotatef(-30, 1, 0, 0)  # Inclinaison des anneaux
        glColor3f(0.8, 0.7, 0.6)
        glutSolidTorus(0.2, 1.5, 32, 32)  # Anneau intérieur
        glutSolidTorus(0.15, 2.0, 32, 32) # Anneau extérieur
        glPopMatrix()       
            
    def update_illumination(self, sun_position):
        """Calcule l'éclairage en fonction de la position du soleil"""
        if self == solar_system.sun:
            self.illumination = 1.0
            return
            
        # Position actuelle de la planète
        angle_rad = math.radians(self.orbit_angle)
        planet_pos = np.array([
            self.distance * math.cos(angle_rad),
            0,
            self.distance * math.sin(angle_rad)
        ])
        
        # Vecteur soleil -> planète
        sun_to_planet = planet_pos - sun_position
        sun_to_planet_normalized = sun_to_planet / np.linalg.norm(sun_to_planet)
        
        # Normal à la surface (pointe vers l'extérieur de la planète)
        normal = planet_pos / np.linalg.norm(planet_pos)
        
        # Calcul de l'éclairage (modèle de Lambert amélioré)
        dot_product = max(0, np.dot(normal, sun_to_planet_normalized))
        self.illumination = 0.2 + 0.8 * dot_product  # 0.2 = lumière ambiante
        
        # Mettre à jour l'éclairage des lunes
        for moon in self.moons:
            moon.update_illumination(planet_pos)

    def draw(self, shadow_pass=False):
        glPushMatrix()
        glRotatef(self.orbit_angle, 0, 1, 0)
        glTranslatef(self.distance, 0, 0)
        
        if self != solar_system.sun:
            glRotatef(self.rotation_angle, 0, 1, 0)
            
            if not shadow_pass:
                # Configuration du matériau pour les planètes
                glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, 
                            [self.color[0]*self.illumination, 
                             self.color[1]*self.illumination,
                             self.color[2]*self.illumination, 1.0])
        else:
            if not shadow_pass:
                # Configuration spéciale pour le soleil (émet sa propre lumière)
                glMaterialfv(GL_FRONT, GL_EMISSION, [0.8, 0.7, 0.6, 1.0])
                glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [1.0, 0.9, 0.7, 1.0])
        
        if not shadow_pass and self.texture_id:
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
        if not shadow_pass and self == solar_system.sun:
            glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])
        
        for moon in self.moons:
            moon.draw(shadow_pass)
        
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
        self.shadow_fbo = init_shadow_map()

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
    
    def render_shadow_map(self):
        """Rend la carte d'ombres depuis la perspective du soleil"""
        glBindFramebuffer(GL_FRAMEBUFFER, self.shadow_fbo)
        glViewport(0, 0, shadow_map_size, shadow_map_size)
        
        glClear(GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        
        # Configuration de la vue depuis le soleil
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        # Vue orthographique couvrant tout le système solaire
        gluOrtho2D(-40, 40, -40, 40)
        glOrtho(-40, 40, -40, 40, -100, 100)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0, 10, 0,   # Position du soleil
                  0, 0, 0,    # Centre de la scène
                  0, 0, 1)    # Orientation
        
        # Dessiner tous les objets (sauf le soleil) en mode ombre
        for planet in self.planets:
            planet.draw(shadow_pass=True)
            for moon in planet.moons:
                moon.draw(shadow_pass=True)
        
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
    
    def draw(self):
        # Étape 1: Rendu de la carte d'ombres
        self.render_shadow_map()
        
        # Étape 2: Rendu normal de la scène
        glViewport(0, 0, glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT))
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Dessiner le soleil
        glPushMatrix()
        glRotatef(self.sun.rotation_angle, 0, 1, 0)
        self.sun.draw()
        glPopMatrix()
        
        # Dessiner les planètes avec ombres
        for planet in self.planets:
            planet.draw()
        
        # Dessiner les orbites
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
tracking_mode = False

def initialize():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_COLOR_MATERIAL)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    
    # Configuration améliorée de la lumière du soleil
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 0.0, 0.0, 1.0])  # Positionnée au soleil
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 0.9, 0.7, 1.0])   # Couleur chaude du soleil
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.1, 0.1, 0.1, 1.0])   # Lumière ambiante réduite
    glLightfv(GL_LIGHT0, GL_SPECULAR, [0.7, 0.7, 0.7, 1.0])  # Reflets
    
    # Configuration des matériaux
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.3, 0.3, 0.3, 1.0])
    glMaterialfv(GL_FRONT, GL_SHININESS, [30.0])
    glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])
    
    # Configuration du lissage
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glEnable(GL_POLYGON_SMOOTH)
    glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST)

def mouse(button, state, x, y):
    global left_button_pressed, right_button_pressed, mouse_x, mouse_y, camera_distance, selected_body, tracking_mode
    
    mouse_x, mouse_y = x, y
    
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
        text_bytes = (ctypes.c_ubyte * len(text))(*[ord(c) for c in text])
        total_width += glutBitmapLength(GLUT_BITMAP_9_BY_15, text_bytes)
    total_width += len(planet_shortcuts) * 10  # Ajouter l'espacement
    
    start_x = (window_width - total_width) // 4
    
    y_bottom = 20  # Position en bas
    x_pos = start_x
    
    for text, body in planet_shortcuts:
        if selected_body == body:
            glColor3f(0, 1, 1)  # Cyan for selected
        else:
            glColor3f(1, 1, 1)  # White for others
            
        glRasterPos2f(x_pos, y_bottom)
        for char in text:
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
        
        text_bytes = (ctypes.c_ubyte * len(text))(*[ord(c) for c in text])
        text_width = glutBitmapLength(GLUT_BITMAP_9_BY_15, text_bytes)
        x_pos += text_width + 12  # 12px spacing
    
    # Restore previous matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_LIGHTING)

def get_body_position(body):
    """Retourne la position (x, z) actuelle d'un corps céleste."""
    if body == solar_system.sun:
        return (0, 0)
    
    angle_rad = math.radians(body.orbit_angle)
    x = body.distance * math.cos(angle_rad)
    z = body.distance * math.sin(angle_rad)
    return (x, z)

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

def update_camera_tracking():
    """Met à jour la position de la caméra pour suivre la planète sélectionnée."""
    global camera_x, camera_z, camera_angle
    
    if not tracking_mode or not selected_body:
        return
    
    if selected_body == solar_system.sun:
        return
    
    angle_rad = math.radians(selected_body.orbit_angle)
    orbit_x = selected_body.distance * math.cos(angle_rad)
    orbit_z = selected_body.distance * math.sin(angle_rad)
    
    # Mise à jour plus rapide pour un meilleur suivi
    smoothing_factor = 0.3  # Augmenté pour un suivi plus rapide
    camera_x = camera_x * (1 - smoothing_factor) + orbit_x * smoothing_factor
    camera_z = camera_z * (1 - smoothing_factor) + orbit_z * smoothing_factor
    
    # Mise à jour de l'angle pour continuer à regarder la planète
    camera_angle = math.degrees(math.atan2(orbit_x - camera_x, orbit_z - camera_z))

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