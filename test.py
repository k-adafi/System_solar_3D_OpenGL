from OpenGL.GL import *
from OpenGL.GLUT import *

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glutSwapBuffers()

glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(1000, 600)
glutCreateWindow(b"Test OpenGL")
glClearColor(0.0, 0.0, 0.0, 1.0)
glutDisplayFunc(display)
glutMainLoop()
