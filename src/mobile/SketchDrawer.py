import math

import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.path import Path

# Change Font Size Here
fs = 10
cut = 0.5

def getRectangle(ax, x1, y1, x2, y2):
    global fs
    vertices = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (0, 0)]
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
    path = Path(vertices, codes)
    patch = patches.PathPatch(path, facecolor='white', linewidth=0.3)
    ax.add_patch(patch)


def dimenLine(ax, x1, y1, x2, y2, height=0, value=-1):
    global fs
    length = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    halflength = length / 2
    midx = (x1 + x2) / 2
    midy = (y1 + y2) / 2

    ax.arrow(midx, midy, halflength, 0, color='k', head_width=0.1, head_length=0.2, fc='k', ec='k', linewidth=0.3,
             length_includes_head=True)
    ax.arrow(midx, midy, -halflength, 0, color='k', head_width=0.1, head_length=0.2, fc='k', ec='k',
             linewidth=0.3, length_includes_head=True)

    if value == -1:
        value = length / 2
        ax.text(midx, midy + 0.1, f'{value:.2f} cm', fontsize=fs)
    else:
        ax.text(midx, midy + 0.1, f'{value} cm', fontsize=fs)

    ax.arrow(x1, y1, 0, -0.3, color='k', linewidth=0.3)
    ax.arrow(x1, y1, 0, 0.3, color='k', linewidth=0.3)
    ax.arrow(x2, y2, 0, -0.3, color='k', linewidth=0.3)
    ax.arrow(x2, y2, 0, 0.3, color='k', linewidth=0.3)


def generateGraph(mass1, mass2, mass3, length, path,
                  radius=1,
                  height=3,
                  ThicknessOfDowel=0.3,
                  ):
    # Initialization of Axes and Figure
    ## Initialization
    fig, ax = plt.subplots()
    ax.set_aspect('equal', adjustable='box')
    ## Set Axis to Center
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    ax.xaxis.set_ticks_position('bottom')
    ax.spines['bottom'].set_position(('data', 0))
    ax.yaxis.set_ticks_position('left')
    ax.spines['left'].set_position(('data', 0))
    plt.axis('off')
    ## Determine Size of Figure
    heightOfDowel = height + 4
    plt.rcParams['figure.figsize'] = (length + radius * 4 + cut * 4, heightOfDowel + 5)
    plt.rcParams['figure.dpi'] = 300
    plt.xlim(-radius * 2 + cut * 2, length + radius * 2 + cut * 2)
    plt.ylim(0, heightOfDowel + 5)

    # Drawing
    ## 3 Objs, cir1 = Mass1, cird = Dowel Mass, cir3 = Mass3

    cir1 = plt.Circle((cut, height), radius, color='black', fill=False)
    ax.text(cut - radius + 0.2 * radius, height - 0.25 * radius, f'Mass of Obj1\n{mass1:.2f} g', fontsize=fs)
    cird = plt.Circle((length / 2, height + 1), radius, color='black', fill=False, linestyle='--')
    ax.text(length / 2 - radius + 0.2 * radius, height + 1 - 0.25 * radius, f'Mass of Dowel\n{mass2:.2f} g', fontsize=fs)
    cir2 = plt.Circle((length - cut, height), radius, color='black', fill=False)
    ax.text(length - radius - cut + 0.2 * radius, height - 0.25 * radius, f'Mass of Obj2\n{mass3:.2f} g', fontsize=fs)

    ax.add_patch(cir1)
    ax.add_patch(cird)
    ax.add_patch(cir2)

    ## Dowel

    getRectangle(ax, 0, heightOfDowel + ThicknessOfDowel, length, heightOfDowel)

    ## Dimensional Lines

    place = (mass1 * length - mass1 * 2 * cut + mass2 * 0.5 * length - mass2 * cut) / (mass1 + mass2 + mass3)

    lenh = length / 2 - cut
    lenc = length - cut * 2
    lenc2 = length / 2 - cut

    dimenLine(ax, cut, heightOfDowel - 0.3, length / 2, heightOfDowel - 0.3,
              value=lenh)  # Dimension line for down, Left dowel
    dimenLine(ax, length / 2, heightOfDowel - 0.3, length - cut, heightOfDowel - 0.3,
              value=lenh)  # Dimension line for right, Up dowel

    dimenLine(ax, cut, heightOfDowel + ThicknessOfDowel + 0.3, place, heightOfDowel + ThicknessOfDowel + 0.3, value='x')
    dimenLine(ax, place, heightOfDowel - 0.9, length / 2, heightOfDowel - 0.9, value=f"{lenc2} - x")
    dimenLine(ax, place, heightOfDowel + ThicknessOfDowel + 0.3, length - cut, heightOfDowel + ThicknessOfDowel + 0.3,
              value=f"{lenc} - x")  # measure from left end to middle fulcrum

    plt.plot([cut, cut], [heightOfDowel, height + radius], color='k', linewidth=0.3)
    plt.plot([length / 2, length / 2], [heightOfDowel, height + radius + radius], linestyle='--', color='k',
             linewidth=0.3)
    plt.plot([length - cut, length - cut], [heightOfDowel, height + radius], color='k', linewidth=0.3)

    plt.plot([place, place], [heightOfDowel + ThicknessOfDowel, heightOfDowel + ThicknessOfDowel + 15], color='k',
             linewidth=0.3)  # String

    plt.savefig(path)
