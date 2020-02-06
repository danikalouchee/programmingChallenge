import nimbleProgrammingChallenge as npc
import numpy as np
import multiprocessing as mp
import os
from PIL import Image
import ctypes

red_rgb = (255,0,0)
# 100x100 solid black rgb images
blackimage = Image.open("blackimg.png")
#np array of black 100x100 solid image
np_blackimg = np.array(blackimage)
# water marked black 100x100 image
wmImg = Image.open("wmImg.png")
# water marked & filled white circle black 100x100 image
fillCircImg = Image.open("fillCirimg.png")
#water marked & filled white circle black 100x100 np array
np_fullCirc = np.array(fillCircImg)
blueimage = Image.new('RGB', (100,100), color = 'blue')


def test_get_complementary():
    assert npc.get_complementary(red_rgb) == ((0,255,255))

def test_getRadius():
    assert npc.getRadius(blackimage) == 25

def test_rgb2name():
    assert npc.rgb2name(red_rgb) == 'red'

def test_randColor():
    assert npc.randColor(['#FFFFFF', '#000000']) == ((0,0,0)) or ((255,255,255))

def test_createRbgImg():
    assert npc.createRbgImg(100,100,(0,0,255)) == blueimage

def test_detColor():
    assert npc.detColor(blackimage) == ((0,0,0))

def test_findCenter():
    assert npc.findCenter(100,100) == (50,50)

def test_watermarkImgColor():
    wmImg = npc.watermarkImgColor(blackimage,'black')
    np_wmImg = np.array(wmImg)
    assert np.array_equal(wmImg,np_wmImg)

def test_fillCircle():
    np_wmImg = np.array(wmImg)
    check = npc.fillCircle(np_wmImg,50,50,25,(255,255,255))
    assert np.array_equal(check, np_fullCirc)

def test_createFinalImgs():
    queue_a = mp.Queue()
    queue_b = mp.Queue()
    queue_a.put(blackimage)
    npc.createFinalImgs(queue_a,queue_b,100,100)
    finalImg = queue_b.get()
    assert np.array_equal(finalImg, np_fullCirc)

def test_createAllImgs():
    queue_a = mp.Queue()
    npc.createAllImgs(queue_a,1, 100, 100,['#000000','#000000'])
    rgbImg = queue_a.get()
    np_rgbImg = np.array(rgbImg)
    assert np.array_equal(np_rgbImg,np_blackimg)