#!/usr/bin/python3
# -*- coding: utf-8 -*-

import math
from tkinter import *
from tkinter import ttk
from base.components import *
import sv_ttk

def solve(
    initialVelocity,
    angle,
    in_degree=True,
    reference_frame=True,
    positive_physics=True,
    return_tuple=False,
):
    """
    referenceFrame refer to whether the up is positive, down is negative;
    if you set referenceFrame False, then down it positive, up is negative
    Indegree refer to whether you use radian or degree measurements
    ReturnTuple = True, then return (time hanging, horizontal displacement), false, return a string contain above informations
    positivePhysics refer to whether you want use 9.81 as g, or 9.8 as g. True, then use 9.81. False, then use 9.80
    InitialiVelocity refer to velocity when project is throwed. It does not refer to any single components of its
    Angle measure refer to measure from velocity to ground
    This script assume the project will fall back to ground
    """

    vi = initialVelocity
    theta = 0
    if in_degree:
        theta = angle / 180 * math.pi

    vix = initialVelocity * math.cos(theta)
    viy = initialVelocity * math.sin(theta)

    if not reference_frame:
        if vix > 0 or viy > 0:
            raise TypeError("Initial Velocity can't be negative")
        else:
            g = 9.81 if positive_physics else 9.80
    else:
        g = -9.81 if positive_physics else -9.80

    t_half = abs(viy / g)
    t_hang = 2 * t_half

    dx = t_hang * vix
    return (
        t_hang,
        dx
        if return_tuple
        else f"The time in the air is {t_hang:.2f}, the horizontal displacemnet is {dx:.2f}",
    )

main = Tk()
sv_ttk.set_theme('light')
main.title("Projectile Calculator")

# Create a entry that only allow input to be float
angle = ttk.Entry(main, width=20, textvariable=StringVar(), justify=CENTER, validate="key", validatecommand=main.register(sv_ttk.validate_float))