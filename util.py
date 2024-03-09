"""
Jefftools - Jeffrey Fan
Utils

Includes a buncha math stuff like trigonometry functions but defined in degrees (because I like degrees more)
It also has a Vector class which makes handling positions EXTREMELY easy
    Using dunder methos (__), it makes using them just like normal numbers!
    I've used this vector class before in my other python games
    It can add, subtract, multiply, divide, get distance, direction, rotate around, etc...
There's also some other miscellanous functions that I believe go here
"""


import os
from time import time
from math import sin as _msin, cos as _mcos, atan2 as _matan2, radians as _rads, degrees as _degs, sqrt, floor, ceil
from random import randint, uniform as randfloat, choice

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = ""

MAIN = os.path.split(os.path.abspath(__file__))[0]

import pygame as pg
from pygame.locals import *


# this is to prevent pycharms warnings lol
time()
randfloat(0, 0)
choice([None])
QUIT


PRECISION = 0.01
FRICTION = 0.75

def lerp(a, b, p):
    return a + p*(b - a)

def lerpp(a, b, p):
    if abs(a - b) > PRECISION:
        return lerp(a, b, p)
    return b

B64 = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
def jargon(l):
    return "".join([B64[randint(0, len(B64)-1)] for _ in range(l)])

def unijargon(l, q):
    j = None
    while j is None or j in q:
        j = jargon(l)
    return j

def bind(f, a=None, kw=None):
    a = list(a) if is_arr(a) else []
    kw = kw if is_dict(kw) else {}
    def _f(*_, **__):
        return f(*a, **kw)
    return _f

def anglerel(a, b):
    a = (a if is_num(a) else 0) % 360
    b = (b if is_num(b) else 0) % 360
    r = (b - a) % 360
    if r > 180:
        r -= 360
    return r

def updatedict(d1, d2):
    if not (is_dict(d1) and is_dict(d2)):
        return None
    for k, v in d2.items():
        d1[k] = v
    return d1


def sin(x):
    return _msin(_rads(x))
def cos(x):
    return _mcos(_rads(x))
def atan2(x, y):
    return _degs(_matan2(y, x))

def sign(x):
    if x > 0:
        return +1
    if x < 0:
        return -1
    return 0

def is_int(x):
    return isinstance(x, (int,))
def is_float(x):
    return isinstance(x, (float,))
def is_num(x):
    return is_int(x) or is_float(x)
def is_list(x):
    return isinstance(x, (list,))
def is_tup(x):
    return isinstance(x, (tuple,))
def is_arr(x):
    return is_list(x) or is_tup(x)
def is_dict(x):
    return isinstance(x, (dict,))
def is_str(x):
    return isinstance(x, (str,))
def is_surf(x):
    return isinstance(x, pg.Surface)

def ensure_int(x, d=0):
    return x if is_int(x) else d
def ensure_float(x, d=0.0):
    return x if is_float(x) else d
def ensure_num(x, d=0):
    return x if is_num(x) else d
def ensure_list(x, d=None):
    return x if is_list(x) else (list() if d is None else d)
def ensure_tup(x, d=tuple()):
    return x if is_tup(x) else d
def ensure_arr(x, d=None):
    return x if is_arr(x) else (list() if d is None else d)
def ensure_dict(x, d=None):
    return x if is_dict(x) else (dict() if d is None else d)
def ensure_str(x, d=""):
    return x if is_str(x) else d
def ensure_surf(x, d=None):
    return x if is_surf(x) else (pg.Surface((0, 0)) if d is None else d)

def scale_surf(surf, p, smooth=True):
    return (pg.transform.smoothscale if smooth else pg.transform.scale)(surf, (V(surf.get_size()) * p).ceil().xy)


class Vector:
    def __init__(self, *a):
        if len(a) == 0:
            a = [0]
        if len(a) == 1:
            a = a[0]
            if is_arr(a):
                a = V(*list(a)).xy
            elif isinstance(a, V):
                a = a.xy
            elif is_num(a):
                a = [a, a]
            else:
                a = [0, 0]
        a = list(a)
        if len(a) > 2:
            a = [0, 0]

        self._x = self._y = 0
        self.xy = a

    def setx(self, v):
        self.x = v
        return self
    def sety(self, v):
        self.y = v
        return self
    def setxy(self, v):
        self.xy = v
        return self

    @property
    def x(self):
        return self._x
    @x.setter
    def x(self, v):
        self._x = v if is_num(v) else 0
    @property
    def y(self):
        return self._y
    @y.setter
    def y(self, v):
        self._y = v if is_num(v) else 0
    @property
    def xy(self):
        return self.x, self.y
    @xy.setter
    def xy(self, v):
        v = v if is_arr(v) else []
        if len(v) != 2:
            return
        self.x, self.y = v

    def __add__(self, v):
        v = V(v)
        return V(self.x + v.x, self.y + v.y)
    __radd__ = __add__
    def __sub__(self, v):
        v = V(v)
        return V(self.x - v.x, self.y - v.y)
    def __rsub__(self, v):
        return V(v) - self
    def __mul__(self, v):
        v = V(v)
        return V(self.x * v.x, self.y * v.y)
    __rmul__ = __mul__
    def __truediv__(self, v):
        v = V(v)
        return V(self.x / v.x, self.y / v.y)
    def __rtruediv__(self, v):
        return V(v) / self
    def __pow__(self, v):
        v = V(v)
        return V(self.x ** v.x, self.y ** v.y)
    def __rpow__(self, v):
        return V(v) ** self

    def __neg__(self):
        return V(-self.x, -self.y)

    def __eq__(self, o):
        o = V(o)
        return self.x == o.x and self.y == o.y

    def map(self, f, a=None, kw=None):
        a = list(a) if is_arr(a) else []
        kw = kw if is_dict(kw) else {}
        return V(f(self.x, *a, **kw), f(self.y, *a, **kw))
    def abs(self):
        return self.map(abs)
    def floor(self):
        return self.map(floor)
    def ceil(self):
        return self.map(ceil)
    def round(self, n=0):
        return self.map(round, a=(n,))

    def dist(self, v):
        v = V(v)
        return sqrt(sum(((self - v) ** 2).xy))
    def toward(self, v):
        v = V(v)
        return (-atan2(*(self - v).xy) - 90) % 360
    def rotateorigin(self, d):
        return V.dir(d + 90, self.x) + V.dir(d, self.y)
    def rotate(self, d, o=0):
        o = V(o)
        return o + (self - o).rotateorigin(d)

    @staticmethod
    def dir(d, m=1):
        return V(sin(d), cos(d)) * m

    def __str__(self):
        return f"<{self.x}, {self.y}>"
    def __format__(self, _):
        return str(self)
    def __repr__(self):
        return str(self)

V = Vector
