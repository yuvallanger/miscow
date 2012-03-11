import sys
import scipy as sp
import numpy as np
import scipy.signal
import matplotlib
import matplotlib.pyplot
from PySide import QtCore, QtGui
import Image

## globals

# Board size
global N, S_cost, R_cost, benefit, S_rad, C_rad, S_len, C_len, S_counter, C_counter, S_th, C_th, S, R, C, tick

## functions

def diffuse(b,c,direction):
    row = (sp.array((0,0,1,1))+c[0])%b.shape[0]
    col = (sp.array((0,1,0,1))+c[1])%b.shape[1]
    if direction:
        b[row,col] = b[row[[1,2,3,0]], col[[1,2,3,0]]]
    else:
        b[row,col] = b[row[[2,3,0,1]], col[[2,3,0,1]]]

def competiroll(N):
    """draw two competitor positions"""
    # We'll use relative positions to compute exact positions of 2nd competitor cell
    NEIGHBOUR_ROW = sp.array([-1,  0,  1, -1,  0,  1, -1,  1])
    NEIGHBOUR_COL = sp.array([-1, -1, -1,  1,  1,  1,  0,  0])
    NEIGHBOUR_REL_POS = sp.array(zip(NEIGHBOUR_ROW, NEIGHBOUR_COL))
    c1 = sp.random.randint(N, size=2)
    c2 = c1 + NEIGHBOUR_REL_POS[sp.random.randint(8, size=1)[0]]
    return c1, c2


## settings

# Board size
N = 20

S_cost = 3
R_cost = 8
C_cost = 30

# cooperation benefit, in ratio
benefit = 0.3

# radius
S_rad = 1
C_rad = 1

# diameter of the convolution matrix
diameter = lambda x: 2 * x + 1
S_len = diameter(S_rad)
C_len = diameter(C_rad)

# the convolution matrix used to count neighbours
S_counter = sp.ones((S_len, S_len))
C_counter = sp.ones((C_len, C_len)) # convolution matrix used to count cells that produce public goods

# neighbours effects' thresholds
S_th = 3 # quorum threshold
C_th = 3 # Cooperation threshold. Above it, public goods makes a difference.

# A cell can be Signalling and/or Receptive and/or Cooperative
S = sp.rand(N, N) < 0.5
R = sp.rand(N, N) < 0.5
C = sp.rand(N, N) < 0.5

# we'll increase this by one every time two cells compete.
tick = 0

## QtSide stuff

app = QtGui.QApplication([])

data = np.random.random( (N, N ,3))
imagify_data()

## main stuff

while_count = 0

def mainstuff():
    print "while_count", while_count
    ## compete
    competitor_1, competitor_2 = competiroll(N)
    # competitor_2's coordinates in a torus:
    competitor_2t = competitor_2 % N
    # we'll run this until we get a pair of competitors that are actually different:
    while ((R[competitor_1[0],competitor_1[1]] == R[competitor_2t[0], competitor_2t[1]]) and
           (S[competitor_1[0],competitor_1[1]] == S[competitor_2t[0], competitor_2t[1]]) and
           (C[competitor_1[0],competitor_1[1]] == C[competitor_2t[0], competitor_2t[1]])):
        competitor_1, competitor_2 = competiroll(N)
        competitor_2t = competitor_2 % N
        # time passes:
        tick += 1
    print "competitor_1, competitor_2"
    print competitor_1, competitor_2
    # here we produce torusified versions of the boards.
    # for signallers, we take both S_rad and C_rad around our competitors because,
    # signallers affect receptive && cooperating cells which affect our competitors
    S_sub = S[sp.arange(- S_rad - C_rad, S_rad + C_rad + 1)%N,:][:, sp.arange(- S_rad - C_rad, S_rad + C_rad + 1)%N]
    R_sub = R[sp.arange(- C_rad, C_rad + 1)%N, :][:, sp.arange(- C_rad, C_rad + 1)%N]
    C_sub = C[sp.arange(- C_rad, C_rad + 1)%N, :][:, sp.arange(- C_rad, C_rad + 1)%N]
    print "S_sub.shape, R_sub.shape, C_sub.shape"
    print S_sub.shape, R_sub.shape, C_sub.shape
    # we count how many signallers are within each cell's neighbourhood
    S_conv = sp.signal.convolve2d(S_sub, S_counter, mode='valid')
    # a cell will produce common goods if it's receptive and cooperative and signal in its neighborhood is above threshold
    cooping_cells = (C_sub == R_sub) == (S_conv > S_th)
    # how many cooperators around each competitor?
    print "cooping_cells"
    print cooping_cells.shape
    print cooping_cells
    C_conv = sp.signal.convolve2d(cooping_cells, C_counter, mode='valid')
    # Public goods effect.
    # G for Goods
    G = (C_conv > C_th)
    print "G.shape", G.shape
    # all cells for which the effect of goods is above threshold is True in G.
    # M for Metabolism
    cost_board = S_cost * S + R_cost * R + C_cost * C
    M = G * (1 - benefit) * cost_board
    # all false in G don't benefit from public goods (G^True flips values)
    M += (G^True) *  cost_board
    if M[competitor_1[0], competitor_1[1]] > M[competitor_2t[0], competitor_2t[1]]:
        C[competitor_1[0], competitor_1[1]] = C[competitor_2t[0], competitor_2t[1]]
        S[competitor_1[0], competitor_1[1]] = S[competitor_2t[0], competitor_2t[1]]
        R[competitor_1[0], competitor_1[1]] = R[competitor_2t[0], competitor_2t[1]]
    elif M[competitor_1[0], competitor_1[1]] == M[competitor_2t[0], competitor_2t[1]]:
        print 'buga'
    else:
        C[competitor_2t[0], competitor_2t[1]] = C[competitor_1[0], competitor_1[1]]
        S[competitor_2t[0], competitor_2t[1]] = S[competitor_1[0], competitor_1[1]]
        R[competitor_2t[0], competitor_2t[1]] = R[competitor_1[0], competitor_1[1]]
    mats.set_data(S+R*2+C*3)
    matplotlib.pyplot.ion()
    matplotlib.pyplot.show()
    matplotlib.pyplot.ioff()
    ## mutate
    if sp.random.random()>0.1:
        coords = sp.random.randint(N, size=2)
        B = [C, R, S][sp.random.randint(3)]
        B[coords[0], coords[1]] = sp.random.randint(2)
    data = 3*C + 2*R + S
    tick += 1
    while_count += 1

## process data

def imagify_data():
    img = Image.fromarray(data, 'RGB')
    img = img.resize((500,500))
    imgstr_data = img.tostring()
    image = QtGui.QImage(imgstr_data, N, N, QtGui.QImage.Format_ARGB32)
    pix = QtGui.QPixmap.fromImage(image)
    lbl = QtGui.QLabel()
    lbl.setPixmap(pix)
    lbl.show()

## update display

def update_display():
    return None

## QtSide main loop

app.exec_()
