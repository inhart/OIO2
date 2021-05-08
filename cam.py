import sys
import pygame
import pygame.camera
import pygame.image
import os
import pigpio
import numpy
import cv2


color_light = (170,170,170)
color_dark = (100,100,100)

orangeyellow = 14
bluegreen  = 15
switch = 21

pr_state = False

name = ''



cam_w =2592
cam_h = 1944
pygame.init()

escena = 0
scr_ancho = pygame.display.Info().current_w
scr_alto = pygame.display.Info().current_h
sqared = scr_ancho//8
pos = [(scr_ancho-sqared,scr_alto*i/4) for i in range(4)]
nombres = ['Click','Flip','Switch','Quit']

screen = pygame.display.set_mode((scr_ancho,scr_alto),pygame.FULLSCREEN)

pygame.camera.init()
cam_list = pygame.camera.list_cameras()
cam = pygame.camera.Camera(cam_list[0],(cam_w,cam_h))
cam.start()
fstate = False
    # pi is initialized as the pigpio object
try:
    pi=pigpio.pi()
    pi.set_mode(orangeyellow,pigpio.OUTPUT)
    pi.set_mode(bluegreen,pigpio.OUTPUT)
    pi.set_mode(switch,pigpio.INPUT)
    #set a pull-up resistor on the switch pin
    pi.set_pull_up_down(switch,pigpio.PUD_UP)
except:
    os.system('sudo pigpiod')
finally:
    pi=pigpio.pi()
    pi.set_mode(orangeyellow,pigpio.OUTPUT)
    pi.set_mode(bluegreen,pigpio.OUTPUT)
    pi.set_mode(switch,pigpio.INPUT)
    #set a pull-up resistor on the switch pin
    pi.set_pull_up_down(switch,pigpio.PUD_UP)
    # Defining functions for putting off each LED
def click(ima):
    global name
    ima = remove_glare(ima)
    pygame.image.save(ima, './imagenes/'+ name + '/'+ str(len(os.listdir(f'./imagenes/{name}')))+ '-' + name+ '-'+ fstate*'D' + (not fstate)*'I' + '.jpg')


def normalON():
        # orangeyellow is ON and the other is OFF
    pi.write(orangeyellow,0)
    pi.write(bluegreen,1)

def secondaryON():
        # toggle
    pi.write(orangeyellow,1)
    pi.write(bluegreen,0)
        
def allOff():
    pi.write(bluegreen,0)
    pi.write(orangeyellow,0)
    
def readSwitch(imag,prstate):
    
    state = not bool(pi.read(switch))
    
    if not state:
        return False
    else:
        if prstate ==False:
            click(imag)
            return True
        else:
            return True
    
    
try:
    os.mkdir('imagenes')
except:
    pass


def remove_glare(im):
    im = pygame.surfarray.array3d(im)
    im = cv2.cvtColor(im, cv2.COLOR_RGB2BGR)
    im = numpy.fliplr(im)
    im = numpy.rot90(im)
    x = cam_w
    y = cam_h
    w = 100
    thresh = 0.9
   # generate binary image mask - dilated circles around the saturated bright spots at the center
    temp = im[y-w:y+w, x-w:x+w,1]  # single channel
    ret, temp_mask = cv2.threshold(temp, thresh*256, 255, cv2.THRESH_BINARY)
    kernel = numpy.ones((25,25), 'uint8')
    temp_mask = cv2.dilate(temp_mask, kernel)

    # perform the inpainting...
    im[y-w:y+w, x-w:x+w,:] = cv2.inpaint(im[y-w:y+w, x-w:x+w,:], temp_mask, 1, cv2.INPAINT_TELEA)
    
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    im = numpy.fliplr(im)
    im = numpy.rot90(im)
    im = pygame.surfarray.make_surface(im)

    # return file
    return im

def mouseOver(cuad):
    mouse = pygame.mouse.get_pos()
    if cuad.posix < mouse[0] < (cuad.posix+cuad.width):
        if cuad.posiy < mouse[1] < (cuad.posiy+cuad.height):
            return True
    return False
        
    
def blitar(cuadrado):
    if mouseOver(cuadrado) and escena != 0:
        cuadrado.surf.fill(color_dark)
        
    else:
        cuadrado.surf.fill(cuadrado.color)
    screen.blit(cuadrado.surf, cuadrado.pos)
    screen.blit(cuadrado.text , (cuadrado.pos[0], cuadrado.pos[1]+cuadrado.height/2))
    
class Square(pygame.sprite.Sprite):
	def __init__(self, mensaje, posi, color=(255,255,255),colortxt=(0,0,0), txt_size=25):
		super(Square, self).__init__()
		
		# Define the dimension of the surface
		# Here we are making squares of side 25px
		self.surf = pygame.Surface((scr_ancho-sqared, scr_alto/4))
		self.dim = (scr_ancho-sqared, scr_alto/4)
		self.width = self.dim[0]
		self.height = self.dim[1]
		self.pos = posi
		self.posix, self.posiy = self.pos
		self.txtcolor = colortxt
		self.mensaje = mensaje
		self.txt_size = txt_size
		# Define the color of the surface using RGB color coding.
		self.color = color  
		self.surf.fill(self.color)
		self.rect = self.surf.get_rect()
		
		self.smallfont = pygame.font.SysFont('Corbel',self.txt_size)
		self.text = self.smallfont.render(mensaje , True , self.txtcolor)
		
		
		
		

def firstScene():
   global screen
   global name
   screen.fill((0,0,0))
   intro = Square(f'{name}', ((scr_ancho//2)//(1+len(name)),scr_alto//3),(0,0,0),(255,255,255),txt_size=scr_alto//2)
   intro.surf.fill((0,0,0))
   blitar(intro)
   for event in pygame.event.get():
       if event.type == pygame.KEYDOWN:
           if event.key == 27:
               cam.stop()
               allOff()
               pygame.quit()
               sys.exit()
           if event.key == 13:
               global escena
               escena += 1
               try:
                   os.mkdir('./imagenes/'+ name)
               except:
                   pass
               
                
               return
           else:
               
               name += event.unicode.upper()
           print(event)
   pygame.display.update()
   
def Capture():
   
   squares = [Square(nombres[i],pos[i]) for i in range(4)]
   image1 = cam.get_image()
   
   
   global fstate
   if fstate:
       image1 = pygame.transform.flip(image1,False,True)
       secondaryON()
   else:
       normalON()
       
   for i in range(len(squares)):
       blitar(squares[i])
   
   for event in pygame.event.get():
          if event.type == pygame.MOUSEBUTTONDOWN:
              
              for cuadra in squares:
                  if mouseOver(cuadra):
                      if cuadra.mensaje == 'Click':
                          click(image1)
                      if cuadra.mensaje == 'Flip':
                          fstate = not fstate
                      if cuadra.mensaje == 'Switch':
                          global escena
                          name = ''
                          escena = 0
                          
                          
                      if cuadra.mensaje == 'Quit':
                          cam.stop()
                          allOff()
                          pygame.quit()
                          sys.exit()
                        
                      
          if event.type == pygame.KEYDOWN:
              if event.key == 27:
                cam.stop()
                allOff()
                pygame.quit()
                sys.exit()            
          if event.type == pygame.QUIT:
              cam.stop()
              pygame.quit()
              sys.exit()
   global pr_state
   pr_state = readSwitch(image1,pr_state)
   image1 = pygame.transform.scale(image1,(scr_ancho-sqared,scr_alto)) 
   screen.blit(image1,(0,0))
   pygame.display.update()

   
def main():
    while True:
       if escena == 0:
           firstScene()
       if escena == 1:
           Capture()
       
       

main()   
