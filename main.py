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


print("Lancement de l'application...")

class CelestialBody:
    def __init__(self, name, distance, orbital_period, rotation_period, radius, color, texture_path=None, moons=None):
        self.name = name
        self.distance = distance  # distance from parent (AU scaled)
        self.orbital_period = orbital_period  # Earth year (Révolution)
        self.rotation_period = rotation_period  # Earth days (Rotation)
        self.radius = radius  # Earth radii scaled
        self.color = color
        self.texture_id = None
        self.moons = moons or []
        
        if texture_path and os.path.exists(texture_path):
            self.load_texture(texture_path)
        
        # Current angles
        self.orbit_angle = np.random.uniform(0, 360)  # Start with random position
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
        # Update angles based on time
        if self.orbital_period > 0:  # Only update orbit if orbital_period is positive
            self.orbit_angle += (360 / (self.orbital_period * 10)) * time_scale  # Adjusted for better visualization
        
        if self.rotation_period > 0:  # Only update rotation if rotation_period is positive
            self.rotation_angle += (360 / (self.rotation_period * 10)) * time_scale  # Adjusted for better visualization
            
        for moon in self.moons:
            moon.update(time_scale)
    
    def draw(self):
        glPushMatrix()
        
        # Orbital position
        glRotatef(self.orbit_angle, 0, 1, 0)
        glTranslatef(self.distance, 0, 0)
        
        # Rotation
        glRotatef(self.rotation_angle, 0, 1, 0)
        
        # Draw the body
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
            glColor3f(*self.color)
            glutSolidSphere(self.radius, 32, 32)
        
        # Draw moons
        for moon in self.moons:
            moon.draw()
        
        glPopMatrix()



def load_skybox_texture(path):
    """Charge uniquement la texture des étoiles, ignore les autres"""
    if "2k_stars_milky_way" not in path:
        return None  # Ne charge pas les autres textures
        
    try:
        img = Image.open(path).convert("RGB")
        img_data = np.array(img, dtype=np.uint8)
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.size[0], img.size[1], 
                    0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
        return texture_id
    except Exception as e:
        print(f"Erreur de chargement de la texture des étoiles : {e}")
        return None
    
    
class SolarSystem:
    def __init__(self):
        # Vérifier si le dossier Texture existe
        texture_dir = "Texture/"
        if not os.path.exists(texture_dir):
            print(f"ATTENTION: Le dossier {texture_dir} n'existe pas")
            os.makedirs(texture_dir, exist_ok=True)
        
        # Charger la texture du ciel (avec vérification)
        skybox_path = os.path.join(texture_dir, "2k_stars_milky_way.jpg")
        self.skybox_path = skybox_path  # Stocker le chemin pour référence ultérieure
        if os.path.exists(skybox_path):
            self.skybox_texture = load_skybox_texture(skybox_path)
        else:
            print(f"ATTENTION: Texture de fond non trouvée à {skybox_path}")
            self.skybox_texture = None
        
        # Initialiser saturn_rings avant de l'utiliser
        self.saturn_rings = {
            'inner_radius': 1.0,  # Augmenté pour mieux correspondre à la taille de Saturne
            'outer_radius': 2.0,  # Augmenté pour mieux correspondre à la taille de Saturne
            'texture_id': None
        }
                
        # Charger la texture des anneaux si elle existe
        ring_texture_path = os.path.join(texture_dir, "2k_saturn_ring_alpha.png")
        if os.path.exists(ring_texture_path):
            try:
                img = Image.open(ring_texture_path).convert("RGBA")
                img_data = np.array(img, np.uint8)
                self.saturn_rings['texture_id'] = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, self.saturn_rings['texture_id'])
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.size[0], img.size[1], 
                             0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
            except Exception as e:
                print(f"Erreur lors du chargement de la texture des anneaux: {e}")
        
        # Configuration des planètes avec des paramètres ajustés pour un meilleur mouvement
        self.sun = CelestialBody(
            "Soleil", 0, 0, 25, 2.0, (1.0, 0.8, 0.0), 
            texture_path=os.path.join(texture_dir, "2k_sun.jpg")
        )
        
        # Planètes intérieures (mouvement plus rapide)
        self.mercury = CelestialBody(
            "Mercure", 4, 88, 58.6, 0.4, (0.7, 0.7, 0.7),
            texture_path=os.path.join(texture_dir, "2k_mercury.jpg")
        )
        
        self.venus = CelestialBody(
            "Venus", 7, 225, 243, 0.6, (0.9, 0.7, 0.2),
            texture_path=os.path.join(texture_dir, "2k_venus_surface.jpg")
        )
        
        self.earth = CelestialBody(
            "Terre", 10, 365.25, 1, 0.6, (0.2, 0.2, 1.0),
            texture_path=os.path.join(texture_dir, "2k_earth_daymap.jpg"),
            moons=[
                CelestialBody("Moon", 1.5, 27.3, 27.3, 0.15, (0.8, 0.8, 0.8),
                             texture_path=os.path.join(texture_dir, "2k_moon.jpg"))
            ]
        )
        
        self.mars = CelestialBody(
            "Mars", 15, 687, 1.03, 0.5, (0.8, 0.4, 0.1),
            texture_path=os.path.join(texture_dir, "2k_mars.jpg"),
            moons=[
                CelestialBody("Phobos", 0.8, 0.319, 0.319, 0.05, (0.6, 0.6, 0.6)),
                CelestialBody("Deimos", 1.2, 1.262, 1.262, 0.03, (0.6, 0.6, 0.6))
            ]
        )
        
        # Planètes extérieures avec des paramètres ajustés pour un meilleur mouvement
        self.jupiter = CelestialBody(
            "Jupiter", 20, 4333, 0.41, 1.2, (0.8, 0.6, 0.4),
            texture_path=os.path.join(texture_dir, "2k_jupiter.jpg"),
            moons=[
                CelestialBody("Io", 1.5, 1.769, 1.769, 0.1, (0.9, 0.8, 0.5)),
                CelestialBody("Europa", 2.0, 3.551, 3.551, 0.08, (0.8, 0.8, 0.9)),
                CelestialBody("Ganymede", 2.5, 7.155, 7.155, 0.12, (0.7, 0.7, 0.8)),
                CelestialBody("Callisto", 3.0, 16.689, 16.689, 0.11, (0.6, 0.6, 0.7))
            ]
        )
        
        self.saturn = CelestialBody(
            "Saturne", 25, 10759, 0.45, 1.0, (0.9, 0.8, 0.6),
            texture_path=os.path.join(texture_dir, "2k_saturn.jpg"),
            moons=[
                CelestialBody("Titan", 2.2, 15.945, 15.945, 0.15, (0.8, 0.7, 0.5)),
                CelestialBody("Rhea", 1.5, 4.518, 4.518, 0.08, (0.8, 0.8, 0.8)),
                CelestialBody("Iapetus", 3.0, 79.33, 79.33, 0.07, (0.6, 0.6, 0.6))
            ]
        )
        
        self.uranus = CelestialBody(
            "Uranus", 28, 30687, 0.72, 0.7, (0.5, 0.8, 0.9),
            texture_path=os.path.join(texture_dir, "2k_uranus.jpg"),
            moons=[
                CelestialBody("Titania", 0.9, 8.706, 8.706, 0.08, (0.8, 0.8, 0.8)),
                CelestialBody("Oberon", 1.1, 13.463, 13.463, 0.07, (0.7, 0.7, 0.7))
            ]
        )

        self.neptune = CelestialBody(
            "Neptune", 30, 60190, 0.67, 0.7, (0.2, 0.3, 0.9),
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
        
        # Time management
        self.last_time = time.time()
        self.time_scale = 1.0  # Vitesse par défaut plus raisonnable

    def update(self):
        current_time = time.time()
        delta_time = current_time - self.last_time
        self.last_time = current_time
        
        # Pas besoin de mettre à jour le soleil car il ne bouge pas
        for planet in self.planets:
            planet.update(self.time_scale)
    
    def draw(self):
        # Draw the sun
        glPushMatrix()
        glRotatef(self.sun.rotation_angle, 0, 1, 0)
        self.sun.draw()
        glPopMatrix()
        
        # Draw planets
        for planet in self.planets:
            planet.draw()
        
        # Special case: Saturn's rings - MODIFIÉ
        glPushMatrix()
        # Position at Saturn's location
        glRotatef(self.saturn.orbit_angle, 0, 1, 0)
        glTranslatef(self.saturn.distance, 0, 0)
        
        if self.saturn_rings['texture_id']:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.saturn_rings['texture_id'])
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            # Dessiner un anneau avec un disque troué
            quad = gluNewQuadric()
            gluQuadricTexture(quad, GL_TRUE)
            gluQuadricOrientation(quad, GLU_OUTSIDE)
            glRotatef(90, 1, 0, 0)  # Orienter horizontalement
            gluDisk(quad, self.saturn_rings['inner_radius'], 
                    self.saturn_rings['outer_radius'], 64, 1)
            gluDeleteQuadric(quad)
            
            glDisable(GL_BLEND)
            glDisable(GL_TEXTURE_2D)
        glPopMatrix()
        
        # Draw orbital paths
        self.draw_orbits()
    
    def draw_orbits(self):
        glDisable(GL_LIGHTING)
        glColor3f(0.5, 0.5, 0.5)
        
        for planet in self.planets:
            glPushMatrix()
            
            # Draw orbit circle
            glBegin(GL_LINE_LOOP)
            for i in range(360):
                angle = math.radians(i)
                x = planet.distance * math.cos(angle)
                z = planet.distance * math.sin(angle)
                glVertex3f(x, 0, z)
            glEnd()
            
            glPopMatrix()
        
        glEnable(GL_LIGHTING)
        
        
    def draw_skybox(self):
        """Dessine uniquement le fond d'étoiles"""
        if not hasattr(self, 'skybox_texture') or not self.skybox_texture:
            return

        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.skybox_texture)
        
        quad = gluNewQuadric()
        gluQuadricTexture(quad, GL_TRUE)
        gluQuadricOrientation(quad, GLU_INSIDE)
        gluSphere(quad, 1000, 64, 64)
        gluDeleteQuadric(quad)
        
        glDisable(GL_TEXTURE_2D)
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

# Commande par souris
def mouse(button, state, x, y):
    global left_button_pressed, right_button_pressed, mouse_x, mouse_y, camera_distance, selected_body
    
    mouse_x, mouse_y = x, y
    
    if button == GLUT_LEFT_BUTTON:
        left_button_pressed = (state == GLUT_DOWN)
        
        if state == GLUT_DOWN:
            # Conversion correcte des coordonnées Y pour la détection des boutons
            window_height = glutGet(GLUT_WINDOW_HEIGHT)
            gl_y = window_height - y  # Conversion coordonnées OpenGL
            
            # Vérifier si on a cliqué sur un bouton
            for btn in planet_buttons:
                if (btn['x'] <= x <= btn['x'] + btn['width'] and 
                    btn['y'] <= gl_y <= btn['y'] + btn['height']):
                    selected_body = btn['body']
                    print(f"Sélectionné: {selected_body.name}")  # Debug
                    break
            else:
                selected_body = None
                
    elif button == GLUT_RIGHT_BUTTON:
        right_button_pressed = (state == GLUT_DOWN)
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
    
    # Position de la caméra avec les nouvelles fonctionnalités
    cam_x = math.sin(math.radians(camera_angle)) * camera_distance + camera_x
    cam_z = math.cos(math.radians(camera_angle)) * camera_distance + camera_z
    look_y = camera_height + camera_y
    
    gluLookAt(cam_x, look_y, cam_z, 
              camera_x, camera_y, camera_z, 
              0, 1, 0)
    
    # Dessine le fond en premier
    solar_system.draw_skybox()
    
    # Dessine le système solaire
    solar_system.draw()
    
    # Affiche les infos
    show_info()
    
    
    # Dessiner les boutons

    

    # Afficher le nom du corps sélectionné au-dessus de l'objet
    if selected_body:
        glDisable(GL_LIGHTING)
        glColor3f(1, 1, 1)
        
        # Positionner le texte
        glPushMatrix()
        
        if selected_body == solar_system.sun:
            glTranslatef(0, selected_body.radius + 1, 0)
        else:
            # Pour les planètes et lunes
            glRotatef(selected_body.orbit_angle, 0, 1, 0)
            glTranslatef(selected_body.distance, selected_body.radius + 0.5, 0)
        
        # Orientation face à la caméra
        glRotatef(-camera_angle, 0, 1, 0)
        glRotatef(-camera_height, 1, 0, 0)
        glScalef(0.002, 0.002, 0.002)
        
        # Dessiner le texte
        for char in selected_body.name:
            glutStrokeCharacter(GLUT_STROKE_ROMAN, ord(char))
        glPopMatrix()
        
        glEnable(GL_LIGHTING)
    
    glutSwapBuffers()

#Affichage des information pour l'utilisateur
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
    
    
# Affichage des listes de planètes
# def show_planete_name():

# Variables globales pour l'interface
planet_buttons = []
# Variables globales (modifiées)
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
selected_body = None  # Pour suivre la sélection actuelle

def initialize():
    
    global planet_buttons
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glClearColor(0.0, 0.0, 0.0, 0.0)  # Fond transparent (alpha=0)
    
    # Configuration de la lumière (soleil) - suppression des ombres
    light_position = [0.0, 0.0, 0.0, 1.0]
    glLightfv(GL_LIGHT0, GL_POSITION, light_position)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])  # Lumière blanche uniforme
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.5, 0.5, 0.5, 1.0])  # Ambiance plus claire
    glLightfv(GL_LIGHT0, GL_SPECULAR, [0.0, 0.0, 0.0, 1.0])  # Pas de spéculaire
    
    # Désactivation des effets de matériau qui créent des ombres
    glDisable(GL_LIGHT1)
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.0, 0.0, 0.0, 1.0])
    glMaterialfv(GL_FRONT, GL_SHININESS, [0.0])
    
    


#Touche de commande par clavier
def keyboard(key, x, y):
    global camera_distance, camera_height, camera_angle, camera_x, camera_y, camera_z, selected_body
    
    key = key.decode('utf-8').lower()
    
    # Commandes de zoom
    if key == '+':
        camera_distance = max(10, camera_distance - 2)
    elif key == '-':
        camera_distance += 2
    elif key == 'q':
        os._exit(0)
    elif key == 'p':
        solar_system.time_scale = 0 if solar_system.time_scale > 0 else 0.5
    
    # Commandes de sélection des corps célestes
    elif key == 's' and glutGetModifiers() == GLUT_ACTIVE_ALT:  # Alt+S pour Soleil
        selected_body = solar_system.sun
        center_camera_on_body(selected_body)
    elif key == 'm' and glutGetModifiers() == GLUT_ACTIVE_ALT:  # Alt+M pour Mercure
        selected_body = solar_system.mercury
        center_camera_on_body(selected_body)
    elif key == 'v' and glutGetModifiers() == GLUT_ACTIVE_ALT:  # Alt+V pour Venus
        selected_body = solar_system.venus
        center_camera_on_body(selected_body)
    elif key == 't' and glutGetModifiers() == GLUT_ACTIVE_ALT:  # Alt+T pour Terre
        selected_body = solar_system.earth
        center_camera_on_body(selected_body)
    elif key == 'm' and glutGetModifiers() == GLUT_ACTIVE_SHIFT:  # Shift+M pour Mars
        selected_body = solar_system.mars
        center_camera_on_body(selected_body)
    elif key == 'j' and glutGetModifiers() == GLUT_ACTIVE_ALT:  # Alt+J pour Jupiter
        selected_body = solar_system.jupiter
        center_camera_on_body(selected_body)
    elif key == 's' and glutGetModifiers() == GLUT_ACTIVE_SHIFT:  # Shift+S pour Saturne
        selected_body = solar_system.saturn
        center_camera_on_body(selected_body)
    elif key == 'u' and glutGetModifiers() == GLUT_ACTIVE_ALT:  # Alt+U pour Uranus
        selected_body = solar_system.uranus
        center_camera_on_body(selected_body)
    elif key == 'n' and glutGetModifiers() == GLUT_ACTIVE_ALT:  # Alt+N pour Neptune
        selected_body = solar_system.neptune
        center_camera_on_body(selected_body)
    elif key == 'n' and glutGetModifiers() == GLUT_ACTIVE_SHIFT:  # Shift+N pour Pluton
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
    """Centre la caméra sur le corps céleste spécifié"""
    global camera_x, camera_z, camera_distance
    
    if body == solar_system.sun:
        camera_x = 0
        camera_z = 0
        camera_distance = 30  # Distance de vue pour le soleil
    else:
        # Calculer la position orbitale actuelle
        angle_rad = math.radians(body.orbit_angle)
        camera_x = body.distance * math.cos(angle_rad)
        camera_z = body.distance * math.sin(angle_rad)
        camera_distance = 5  # Distance de vue pour les planètes
    
    # Ajuster la hauteur pour une bonne vue
    global camera_height
    camera_height = 5

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
    glutPostRedisplay()

# Configuration initiale
glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH | GLUT_ALPHA)
glutInitWindowSize(1200, 800)
glutCreateWindow(b"System Solar 3D")

# Initialisation
solar_system = SolarSystem()

initialize()

# Configuration des callbacks
glutDisplayFunc(display)
glutReshapeFunc(reshape)
glutKeyboardFunc(keyboard)
glutMouseFunc(mouse)
glutMotionFunc(motion)
glutIdleFunc(idle)

glutMainLoop()