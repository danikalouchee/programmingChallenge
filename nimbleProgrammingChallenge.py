import multiprocessing as mp
from multiprocessing import Process, Value
from ipdb import set_trace as debug
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import random
import time
import numpy as np
import cv2
import ctypes
import webcolors
import os

font = cv2.FONT_HERSHEY_SIMPLEX 

def createRbgImg(height, width,rgb):
    """
    Creates a RBG numpy array of a solid color.

    Parameters:
    height(int): Height inputted by user
    width(int): Width inputted by user
    rgb(tuple): RBG color code

    Returns:
    image(PIL Image): solid rbg image

    """
    array = np.zeros([height,width,3], dtype=np.uint8)
    array[:] = rgb
    image = Image.fromarray(array)

    return image

def randColor(colors):
    """ 
    Randomly choose between global hex list of colors and converts color to rgb.

    Parameters:
    colors(list): list of hex colors

    Returns:
    rgb(tuple): rgb code of the random color picked

    """
    ran_hex = random.choice(colors)
    rgb = webcolors.hex_to_rgb(ran_hex)
    return rgb

def createAllImgs(queue_a,num_images, height, width, colors):
    """ 
    Process ones start function.
    For the amount of images asked it will create rbg image with random color and then add to queue_a. 

    Parameters:
    queue_a (multiprocessing.Queue): Queue that is shared among processes where the solid rgb image is passed to
    num_images (int): Amount of images (user input)
    height (int): Height of the images (user input)
    width (int): width of the images (user input)

    """
    n = 0
    for n in range(num_images):
        rgb = randColor(colors)
        image = createRbgImg(height, width,rgb)
        # put image in queue & pass to p2
        queue_a.put(image)

def detColor(image):
    """
    Insepct the image and determine its color and returns rgb color.

    Parameters:
    image(PIL image): Image that needs color determined
    
    Return:
    rgb(tuple): RGB color code of solid image

    """
    # get rgb color from img pix
    x = 3
    y = 4
    pix = image.load()
    rgb = pix[x, y]
    return rgb

def rgb2name(rgb):
    """ 
    Takes rbg color and returns color name. 

    Parameters:
    rgb(tuple): RGB color code of solid image

    Return:
    color(str): Name of the rgb color

    """
    color = webcolors.rgb_to_name(rgb)
    if color == 'magenta':
        color = 'fuchsia'
    if color == 'cyan':
        color = 'aqua'
    return color

def getRadius(image):
    """
    Calculates radius of 1/4 the minimum img dimension from image size. 

    Parameters:
    image(PIL image): This image gives us the width and height to get radius of 1/4 of its dimension

    Returns:
    r(int): radius of 1/4 image dimensions

    """
    w, h = image.size
    r = w * 0.25
    r = int(r)
    return r

def watermarkImgColor(image, colorName):
    """
    Open image then watermark the image with colors name.

    Parameters:
    image(PIL image): rgb PIL image that will get watermarked
    colorName(str): Color name of the solid rgb image

    """
    cvimage = np.array(image)
    wmImg = cv2.putText(cvimage, str(colorName), (0, 25), font, 1, (128, 128, 128))
    return wmImg

def findCenter(height,width):
    """ 
    Finds the X,Y coordinates of the center of the image.
    If the image is black it creates another rgb image that is white to get coordinates. 

    Parameters:
    height (int): Height of the images (user input)
    width (int): width of the images (user input)

    Returns:
    X,Y (int): coordinates of the center of the image
    
    """
    X = int(width/2)
    Y = int(height/2)
    return X,Y

def fillCircle(image,X,Y,r,comp):
    """ 
    Creates a filled circle of the images complementary color in the center of the image. 

    Parameters:
    image(numpy.ndarray): array image
    X,Y(int): coordinates of the center of the image
    r(int): radius of the filled circle
    comp(tuple): RGB code of complementary color

    """
    cv2.circle(image,(X,Y),r,comp,-1)
    return image

def createFinalImgs(queue_a, queue_b, height, width):
    """
    Proccess twos start function.
    Watermarks the solid rgb image and draws filled circle of complementary color in middle of the image then puts image in queue_b.

    Parameters:
    queue_a (multiprocessing.Queue): Queue that is shared among processes to get images from process one
    queue_b (multiprocessing.Queue): Queue that is shared among processes where the watermarked and filled circle image is passed to
    height (int): Height of the images (user input)
    width (int): width of the images (user input)

    """
    #put process to sleep until queue_a has image
    if queue_a.empty():
        time.sleep(1)
    while not queue_a.empty():
        #grab first image from queue
        image = queue_a.get()
        #get color of solid img
        rgb = detColor(image)
        #gets color name for watermark 
        colorName = rgb2name(rgb)
        #gets comp and returns bgr of comp
        bgr_comp = get_complementary(rgb)
        #watermark img with color name
        wmimg = watermarkImgColor(image, colorName)
        #get radius
        r = getRadius(image)
        #Find center of Image
        X,Y = findCenter(height, width)
        #Fill circle with comp color
        final_img = fillCircle(wmimg,X,Y,r,bgr_comp)
        # pass image to queue_b
        queue_b.put(final_img)

def get_complementary(rgb):
    """
    Gets complementary color from rgb color then returns bgr code.

    Parameters:
    rgb(tuple): rgb code to get complementary color.

    Returns:
    comp2rgb(tuple): rgb code that is the complementary of param rgb
    """
    #change rgb to hex
    color = webcolors.rgb_to_hex(rgb)

    # strip the # from the beginning
    color = color[1:]
 
    # convert the string into hex
    color = int(color, 16)
    comp_color = 0xFFFFFF ^ color
    # convert the color back to hex by prefixing a #
    comp_color = "#%06X" % comp_color
    #make hex to rgb
    comp2rgb = webcolors.hex_to_rgb(comp_color)

    return comp2rgb

def displayImgs(array_a, height, width,event_quit):
    """
    Process 3 start function.
    Continually reads from array_a, makes numpy array from array_a, reshapes and then displays.

    Parameters:
    array_a (multiprocessing.array): large array that stores images from queue_b
    height (multiprocessing.Value): Height of the images (user input)
    width (multiprocessing.Value): width of the images (user input)
    event_quit (multiprocessing.Event): Allows proccess 3 to continually read from array_a until signaled to stop. 

    """
    while not event_quit.is_set():
        w_arr = array_a.get_obj()
        np_arr = np.frombuffer(w_arr,dtype=np.uint8)
        fixed_nparr = np_arr.reshape(height,width,3)
        cv2.imshow('img',fixed_nparr)
        cv2.waitKey(1)

def main():
    event_quit = mp.Event()
    num = input("Type a number of random images I should generate: ")
    h = input("Enter height: ")
    w = input("Enter width: ")
    #check if correct inputs
    try:
        numVal = int(num)
        if(numVal < 0 or numVal == 0):
            print("You did not enter a positive number for number of images")
            quit()
        hVal = int(h)
        if(hVal < 0 or hVal == 0):
            print("You did not enter a positive number for height")
            quit()
        wVal = int(w)
        if(wVal < 0 or wVal == 0):
            print("You did not enter a positive number for width")
            quit()
    except ValueError:
        print("You did not enter an integer")
        quit()

    # hex of yellow, white, black, lime, aqua, fuschia & blue
    colors = ['#FFFF00', '#FFFFFF', '#000000', '#00FF00', '#FF0000', '#00FFFF', '#FF00FF', '#0000FF']
    num_images = Value('i', int(num))
    height = Value('i', int(h))
    width = Value('i', int(w))
    queue_a = mp.Queue()
    queue_b = mp.Queue()
    n = num_images.value
    h = height.value
    w = width.value
    array_a = mp.Array(ctypes.c_uint8,(height.value*width.value)*3)

    p1 = Process(target=createAllImgs, args=(queue_a,n, h, w, colors))
    p2 = Process(target=createFinalImgs, args=(queue_a, queue_b, h, w))
    p3 = Process(target=displayImgs, args=(array_a,h,w,event_quit))

    p1.start()
    p2.start()
    p3.start()

    w_arr = array_a.get_obj()
    np_arr = np.frombuffer(w_arr,dtype=np.uint8)
    fixed_nparr = np_arr.reshape(h,w,3)
    
    x = queue_b.get()
    x = cv2.cvtColor(x, cv2.COLOR_RGB2BGR)
    np.copyto(fixed_nparr,x)
    for img in range(n-1):
        userin = input("press enter or q to quit: ")
        if userin == "":
            x = queue_b.get()
            x = cv2.cvtColor(x, cv2.COLOR_RGB2BGR)
            np.copyto(fixed_nparr,x)
        elif userin is 'q':
            event_quit.set()
            p1.terminate()
            p2.terminate()
            p3.terminate()
            quit()
    time.sleep(1)
    event_quit.set()
    p1.join()
    p2.join()
    p3.join()
    quit()

if __name__ == '__main__':
    main()