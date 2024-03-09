"""
Jeffgine - Jeffrey Fan
Game Engine

An entire game engine designed by me to help make actual game development easy!
The engine has much more code compared to the main.py file, which is good as it makes main.py easy to read
There is quite some boilerplate code to prevent users from inputting something 'stupid'
    ... Which means I could publish this as a python package if I wanted to ...

Enjoy reading the code. You might not finish :P

Features include:
- GameObject system for consistency and repeatability
    - All objects on-screen inherit from GameObject and it's subclasses
    - Camera GameObject included into Game, which affects GraphicsNodes
- Event system built into GameObjects for easy handling of hover, collision, update, and death
- GameNode system so features are entirely modular
    - GraphicsNode for rendering images onto screen (affected by built-in camera)
    - HitboxNode for in-game collisions
        Optimizations for speed include chunking and collision filters using groups
"""

from util import *


ASSETS = os.path.join(MAIN, "assets")


class Object:
    def conf(self, **kw):
        for name, value in kw.items():
            self.__setattr__(name, value)
        return self


class Event(Object):
    def __init__(self, name, data=None):
        super().__init__()

        self._name = None
        self._data = {}

        self.name = name
        self.data = data

    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, v):
        self._name = v if is_str(v) else None
    @property
    def data(self):
        return self._data
    @data.setter
    def data(self, v):
        self._data = v if is_dict(v) else {}

    def __str__(self):
        return f"Event<{self.name}:{self.data}>"
    def __format__(self, _):
        return str(self)
    def __repr__(self):
        return str(self)


class EventTarget(Object):
    def __init__(self):
        super().__init__()

        self._handlers = {}

    def add_handler(self, event, func):
        event = str(event)
        self._handlers[event] = self._handlers.get(event, [])
        if func in self._handlers[event]:
            return
        self._handlers[event].append(func)
    def rem_handler(self, event, func):
        event = str(event)
        if event not in self._handlers:
            return
        if func not in self._handlers[event]:
            return
        self._handlers[event].remove(func)
    def post_event(self, event):
        if not isinstance(event, Event):
            event = Event(str(event))
        if event.name in self._handlers:
            handlers = self._handlers[event.name]
            [h(event) for h in handlers]
        self._propagate(event)

    def _propagate(self, event):
        pass


class GameObject(EventTarget):
    def __init__(self, pos, hp, vel=0, name=None):
        super().__init__()

        self._GAME = None
        self._ID = None

        self._name = None
        self.name = name

        self._frozen = False

        self._pos = V()
        self._vel = V()
        self.pos = pos
        self.vel = vel

        self._hpmax = self._hp = 0
        self.hpmax = hp
        self.hp = self.hpmax

        self._nodes = []

        self._remove = False
        self.remove = False

        self.g = GraphicsNode(self, None)
        self.h = HitboxNode(self, 0)

    @property
    def GAME(self):
        return self._GAME
    @property
    def ID(self):
        return self._ID

    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, v):
        self._name = v if is_str(v) else None

    @property
    def frozen(self):
        return self._frozen
    @frozen.setter
    def frozen(self, v):
        self._frozen = bool(v)

    def add_game(self, game):
        if not isinstance(game, Game):
            return None
        return game.add_go(self)
    def rem_game(self):
        if not isinstance(self.GAME, Game):
            return None
        return self.GAME.rem_go(self)

    def add_node(self, node):
        if not isinstance(node, GameNode):
            return None
        if node in self._nodes:
            return None
        node._o = self
        self._nodes.append(node)
        return node
    def rem_node(self, node):
        if not isinstance(node, GameNode):
            return None
        if node not in self._nodes:
            return None
        node._o = None
        self._nodes.remove(node)
        return node
    @property
    def nodes(self):
        return self._nodes.copy()

    @property
    def pos(self):
        return self._pos
    @pos.setter
    def pos(self, v):
        self._pos = V(v)
    @property
    def x(self):
        return self.pos.x
    @x.setter
    def x(self, v):
        self.pos.x = v
    @property
    def y(self):
        return self.pos.y
    @y.setter
    def y(self, v):
        self.pos.y = v

    @property
    def vel(self):
        return self._vel
    @vel.setter
    def vel(self, v):
        self._vel = V(v)
    @property
    def vx(self):
        return self.vel.x
    @vx.setter
    def vx(self, v):
        self.vel.x = v
    @property
    def vy(self):
        return self.vel.y
    @vy.setter
    def vy(self, v):
        self.vel.y = v

    @property
    def hpmax(self):
        return self._hpmax
    @hpmax.setter
    def hpmax(self, v):
        self._hpmax = max(0, v if is_num(v) else 0)
        self.hp = self.hp
    @property
    def hp(self):
        return self._hp
    @hp.setter
    def hp(self, v):
        self._hp = min(self.hpmax, max(0, v if is_num(v) else 0))

    @property
    def remove(self):
        return self._remove
    @remove.setter
    def remove(self, v):
        self._remove = bool(v)

    @property
    def hover(self):
        return self.GAME.lasthovering is self

    def _propagate(self, event):
        for node in self._nodes:
            node.post_event(event)

    def update(self, data):
        if self.frozen:
            return
        self.vx = lerpp(self.vx, 0, 1-FRICTION)
        self.x += self.vx
        self.vy = lerpp(self.vy, 0, 1-FRICTION)
        self.y += self.vy
        for node in self._nodes:
            if node.enabled:
                node.update(data)
        self.post_event(Event("update", {"data": data}))
        if self.hp <= 0:
            self.post_event(Event("death"))
            if self.hp <= 0:
                return True
        return False

    def _more(self, more):
        return []

    def __str__(self):
        more = []
        if is_str(self.name):
            more.append(self.name)
        more.extend(self._more(more))
        more = "".join([f":{v}" for v in more])
        return f"GameObject<{self.__class__.__name__}:{self.ID}{more}>"
    def __format__(self, _):
        return str(self)
    def __repr__(self):
        return str(self)


class GameNode(EventTarget):
    def __init__(self, o):
        super().__init__()

        self._o = None
        o.add_node(self) if isinstance(o, GameObject) else None

        self._enabled = False
        self.enabled = True

    @property
    def o(self):
        return self._o
    @property
    def GAME(self):
        return self.o.GAME
    @property
    def ID(self):
        return self.o.ID

    @property
    def enabled(self):
        return self._enabled
    @enabled.setter
    def enabled(self, v):
        self._enabled = bool(v)

    @property
    def disabled(self):
        return not self.enabled
    @disabled.setter
    def disabled(self, v):
        self.enabled = not v

    def update(self, data):
        pass

    def __str__(self):
        return f"GameNode<{self.__class__.__name__}:[{self.o}]>"
    def __format__(self, _):
        return str(self)
    def __repr__(self):
        return str(self)


class GraphicsNode(GameNode):
    def __init__(self, o, image, d=0, offset=0, z=0, cam=True):
        super().__init__(o)

        self.add_handler("add", lambda e: self._config())

        self._image_dir_cache = []

        self._image = None
        self._image_masks = []
        self._showmask = -1
        self._show = {"§": True}
        self._alpha = {"§": 1}
        self._d = 0
        self._offset = V()
        self._z = 0
        self._cam = True

        self._alignx = 0
        self._aligny = 0

        self.image = image
        self.showmask = -1
        self.d = d
        self.offset = offset
        self.z = z
        self.cam = cam

    @property
    def image(self):
        return self._image
    @image.setter
    def image(self, v):
        v = v if is_surf(v) else None
        if self._image == v:
            return
        self._image = v
        self._config()

    @property
    def showmask(self):
        return self._showmask
    @showmask.setter
    def showmask(self, v):
        self._showmask = max(-1, v if is_int(v) else -1)

    @property
    def show(self):
        return self.get_show("§")
    @show.setter
    def show(self, v):
        self.set_show("§", v)

    @property
    def alpha(self):
        return self.get_alpha("§")
    @alpha.setter
    def alpha(self, v):
        self.set_alpha("§", v)

    @property
    def trueshow(self):
        return all(self._show.values())
    @property
    def truealpha(self):
        a = 1
        for a0 in self._alpha.values():
            a *= a0
        return a

    def set_show(self, name, v):
        name = str(name)
        self._show[name] = bool(v)
        self.post_event(Event("showset", {"n": name, "v": self.get_show(name)}))
        return self
    def get_show(self, name):
        return self._show[name] if name in self._show else None
    def rem_show(self, name):
        name = str(name)
        if name != "§":
            self._show.pop(name, None)
        self.post_event(Event("showrem", {"n": name}))
        return self

    def set_alpha(self, name, v):
        name = str(name)
        self._alpha[name] = min(1, max(0, v if is_num(v) else 0))
        self.post_event(Event("showset", {"n": name, "v": self.get_alpha(name)}))
        return self
    def get_alpha(self, name):
        return self._alpha[name] if name in self._alpha else None
    def rem_alpha(self, name):
        name = str(name)
        if name != "§":
            self._alpha.pop(name, None)
        self.post_event(Event("alpharem", {"n": name}))
        return self

    @property
    def d(self):
        return self._d
    @d.setter
    def d(self, v):
        self._d = (v if is_num(v) else 0) % 360

    @property
    def offset(self):
        return self._offset
    @offset.setter
    def offset(self, v):
        self._offset = V(v)
    @property
    def ox(self):
        return self.offset.x
    @ox.setter
    def ox(self, v):
        self.offset.x = v
    @property
    def oy(self):
        return self.offset.y
    @oy.setter
    def oy(self, v):
        self.offset.y = v

    @property
    def z(self):
        return self._z
    @z.setter
    def z(self, v):
        self._z = v if is_int(v) else 0

    @property
    def cam(self):
        return self._cam
    @cam.setter
    def cam(self, v):
        self._cam = bool(v)

    @property
    def alignx(self):
        return self._alignx
    @alignx.setter
    def alignx(self, v):
        self._alignx = min(+1, max(-1, v if is_int(v) else 0))
    @property
    def aligny(self):
        return self._aligny
    @aligny.setter
    def aligny(self, v):
        self._aligny = min(+1, max(-1, v if is_int(v) else 0))

    def _config(self):
        self._image_dir_cache = []
        self._image_masks = []
        if isinstance(self.GAME, Game):
            for theme in self.GAME.theme:
                self._image_dir_cache.append({})
                surf = self.image
                if is_surf(surf):
                    mask = pg.mask.from_surface(surf)
                    surf = mask.to_surface(setcolor=theme, unsetcolor=(0, 0, 0, 0))
                self._image_masks.append(surf)
            self._image_dir_cache.append({})

    def _render(self, image, pos):
        return self.GAME.surf.blit(
            image,
            pos.xy,
        )

    def render(self):
        if not self.trueshow:
            return
        image = [*self._image_masks, self.image][self.showmask]
        image_dir = self._image_dir_cache[self.showmask]
        empty = False
        if not is_surf(image):
            empty = True
            image = pg.Surface((0, 0)).convert_alpha()
        if not empty:
            if round(self.d) in image_dir:
                image = image_dir[round(self.d)]
            else:
                image = image_dir[round(self.d)] = pg.transform.rotate(image, -self.d)
        image.set_alpha(255 * self.truealpha)
        o = self.o
        pos = o.pos + self.offset
        if self.cam and isinstance(self.GAME.CAM, Camera):
            pos = self.GAME.CAM.w2s(pos)
        pos.x -= [0.5, 0, 1][self.alignx] * image.get_width()
        pos.y -= [0.5, 1, 0][self.aligny] * image.get_height()
        rect = self._render(image, pos)
        if rect.collidepoint(o.GAME.mouse.xy):
            o.GAME._hovering = o


class HitboxNode(GameNode):
    def __init__(self, o, size, offset=0):
        super().__init__(o)

        self._group = None
        self._group_collide = []

        self._alignx = 0
        self._aligny = 0

        self._size = V()
        self._offset = V()

        self.size = size
        self.offset = offset

        self._colliding = {}
        self._colliding_walls = {}

    @property
    def size(self):
        return self._size
    @size.setter
    def size(self, v):
        self._size = V(v)

    @property
    def offset(self):
        return self._offset
    @offset.setter
    def offset(self, v):
        self._offset = V(v)
    @property
    def ox(self):
        return self.offset.x
    @ox.setter
    def ox(self, v):
        self.offset.x = v
    @property
    def oy(self):
        return self.offset.y
    @oy.setter
    def oy(self, v):
        self.offset.y = v

    @property
    def alignx(self):
        return self._alignx
    @alignx.setter
    def alignx(self, v):
        self._alignx = min(+1, max(-1, v if is_int(v) else 0))
    @property
    def aligny(self):
        return self._aligny
    @aligny.setter
    def aligny(self, v):
        self._aligny = min(+1, max(-1, v if is_int(v) else 0))

    @property
    def rect(self):
        offset = (
            self.size.x * [0.5, 0, 1][self.alignx],
            self.size.y * [0.5, 1, 0][self.aligny],
        )
        return pg.Rect(
            (self.o.pos + self.offset - offset).ceil().xy,
            self.size.ceil().xy,
        )

    @property
    def group(self):
        return self._group
    @group.setter
    def group(self, v):
        self._group = v if is_str(v) else None

    def add_group_collide(self, group):
        group = str(group)
        if group in self._group_collide:
            return
        self._group_collide.append(group)
    def rem_group_collide(self, group):
        group = str(group)
        if group not in self._group_collide:
            return
        self._group_collide.remove(group)
    def set_group_collide(self, groups):
        groups = groups if is_arr(groups) else []
        groups = [str(g) for g in groups]
        self._group_collide = groups

    @property
    def gridrect(self):
        rect = self.rect
        if V(rect.size) == 0:
            return pg.Rect((0, 0), (0, 0))
        r, l = max(rect.right, rect.left), min(rect.right, rect.left)
        u, d = max(rect.top, rect.bottom), min(rect.top, rect.bottom)
        p = 1
        r, l = ceil(r/self.GAME.gridsize)+p, floor(l/self.GAME.gridsize)-p
        u, d = ceil(u/self.GAME.gridsize)+p, floor(d/self.GAME.gridsize)-p
        rect = pg.Rect((l, d), (r-l, u-d))
        return rect

    @property
    def colliding(self):
        return self._colliding.copy()
    @property
    def colliding_walls(self):
        return self._colliding_walls.copy()

    def update(self, _):
        o = self.o
        gos = []
        gridrect = self.gridrect
        for group in self._group_collide:
            if group not in self.GAME.groups:
                continue
            for x in range(gridrect.left, gridrect.right+1):
                for y in range(gridrect.top, gridrect.bottom+1):
                    for go in self.GAME.groups[group].get((x, y), []):
                        if go is o:
                            continue
                        if go in gos:
                            continue
                        gos.append(go)
        for go in gos:
            ID = go.ID
            rect = self.rect
            if rect.colliderect(go.h.rect) and go.h.enabled:
                if ID not in self._colliding:
                    self._colliding[ID] = True
                    o.post_event(Event("collideenter", {"id": ID, "go": go}))
                else:
                    o.post_event(Event("collide", {"id": ID, "go": go}))
                if o.ID not in go.h.colliding:
                    go.h.colliding[ID] = True
                    go.post_event(Event("collideenter", {"id": o.ID, "go": o}))
                else:
                    go.post_event(Event("collide", {"id": o.ID, "go": o}))
            else:
                if ID in self.colliding:
                    self.colliding.pop(ID)
                    o.post_event(Event("collideleave", {"id": ID, "go": go}))
                if o.ID in go.h.colliding:
                    go.h.colliding.pop(o.ID)
                    go.post_event(Event("collideleave", {"id": o.ID, "go": o}))
        for name, w in o.GAME.walls.items():
            rect = self.rect
            if rect.colliderect(w):
                wr, wl = max(w.right, w.left), min(w.right, w.left)
                wt, wb = max(w.top, w.bottom), min(w.top, w.bottom)
                rr, rl = max(rect.right, rect.left), min(rect.right, rect.left)
                rt, rb = max(rect.top, rect.bottom), min(rect.top, rect.bottom)
                shifts = [
                    ((+1, 0), wr - rl),
                    ((-1, 0), wl - rr),
                    ((0, +1), wt - rb),
                    ((0, -1), wb - rt),
                ]
                j = -1
                for i, shift in enumerate(shifts):
                    if sign(shift[1]) != sum(shift[0]):
                        continue
                    if j == -1 or abs(shift[1]) < abs(shifts[j][1]):
                        j = i
                if j >= 0:
                    o.pos += V(shifts[j][0]).abs() * shifts[j][1]
                    if name not in self._colliding_walls:
                        self._colliding_walls[name] = True
                        o.post_event(Event("wallenter", {"name": name, "w": w}))
                    else:
                        o.post_event(Event("wall", {"name": name, "w": w}))
            else:
                if name in self._colliding_walls:
                    self._colliding_walls.pop(name)
                    o.post_event(Event("wallleave", {"name": name, "w": w}))


class RaycastNode(GameNode):
    def __init__(self, o, d, offset=0):
        super().__init__(o)

        self._group = None
        self._group_collide = []

        self._limit = 2**10

        self._d = 0
        self._offset = V()

        self.d = d
        self.offset = offset

    @property
    def d(self):
        return self._d
    @d.setter
    def d(self, v):
        self._d = (v if is_num(v) else 0) % 360

    @property
    def offset(self):
        return self._offset
    @offset.setter
    def offset(self, v):
        self._offset = V(v)
    @property
    def ox(self):
        return self.offset.x
    @ox.setter
    def ox(self, v):
        self.offset.x = v
    @property
    def oy(self):
        return self.offset.y
    @oy.setter
    def oy(self, v):
        self.offset.y = v

    @property
    def limit(self):
        return self._limit
    @limit.setter
    def limit(self, v):
        self._limit = max(0, v if is_num(v) else 0)

    def add_group_collide(self, group):
        group = str(group)
        if group in self._group_collide:
            return
        self._group_collide.append(group)
    def rem_group_collide(self, group):
        group = str(group)
        if group not in self._group_collide:
            return
        self._group_collide.remove(group)
    def set_group_collide(self, groups):
        groups = groups if is_arr(groups) else []
        groups = [str(g) for g in groups]
        self._group_collide = groups

    def shoot(self, size):
        size = V(size)
        pos = self.o.pos + self.offset
        dist = 0
        while dist < self.limit:
            gos = []
            minstep = self.limit
            minobj = None
            for ID, go in self.GAME.gos.items():
                if go.h.disabled:
                    continue
                if go.h.group not in self._group_collide:
                    continue
                if go is self.o:
                    continue
                if go in gos:
                    continue
                gos.append(go)
                rect = go.h.rect
                step = max(0, round(pos.dist(rect.center)-min(rect.size), 3))
                if step < minstep:
                    minstep = step
                    minobj = go
            if "walls" in self._group_collide:
                for name, w in self.GAME.walls.items():
                    step = max(0, round(pos.dist(w.center)-min(w.size), 3))
                    if step < minstep:
                        minstep = step
                        minobj = name, w
            dist += minstep
            pos += V.dir(self.d, minstep)
            rect = pg.Rect((0, 0), (0, 0))
            rect.size = size.xy
            rect.center = pos.xy
            if isinstance(minobj, GameObject):
                if minstep <= 0 or minobj.h.rect.colliderect(rect):
                    return dist, (minobj.ID, minobj), None
            elif is_tup(minobj):
                if len(minobj) == 2:
                    name, w = minobj
                    if isinstance(w, pg.Rect):
                        if minstep <= 0 or w.colliderect(rect):
                            return dist, None, (str(name), w)
        return self.limit, None, None


class Camera(GameObject):
    def __init__(self, pos, scroll=1/3, fov=1):
        super().__init__(pos, 1)

        self.g.enabled = False

        self.h.enabled = False

        self.add_handler("update", lambda e: self._update())

        self._npos = V()
        self.npos = self.pos

        self._scroll = 0
        self.scroll = scroll

        self._fov = 0
        self.fov = fov
        self._nfov = 0
        self.nfov = self.fov

        self._shake_mag = 0
        self._shake_dir = 0

        self._brightness = 0
        self._hue = 0
        self._bloom = 0

        self.brightness = 0
        self.hue = 0
        self.bloom = 0

    @property
    def npos(self):
        return self._npos
    @npos.setter
    def npos(self, v):
        self._npos = V(v)
    @property
    def nx(self):
        return self.npos.x
    @nx.setter
    def nx(self, v):
        self.npos.x = v
    @property
    def ny(self):
        return self.npos.y
    @ny.setter
    def ny(self, v):
        self.npos.y = v

    @property
    def fov(self):
        return self._fov
    @fov.setter
    def fov(self, v):
        self._fov = max(PRECISION, v if is_num(v) else 0)
    @property
    def nfov(self):
        return self._nfov
    @nfov.setter
    def nfov(self, v):
        self._nfov = max(PRECISION, v if is_num(v) else 0)

    @property
    def scroll(self):
        return self._scroll
    @scroll.setter
    def scroll(self, v):
        self._scroll = v if is_num(v) else 0

    @property
    def shake(self):
        return V.dir(self._shake_dir, self._shake_mag)
    def add_shake(self, mag):
        self._shake_mag = min(8, self._shake_mag + mag)
    def clear_shake(self):
        self._shake_mag = 0

    def w2s(self, v):
        v = V(v)
        if not isinstance(self.GAME, Game):
            return v
        v -= self.pos + self.shake
        v.y *= -1
        v += self.GAME.ssize / 2
        return v

    def s2w(self, v):
        v = V(v)
        if not isinstance(self.GAME, Game):
            return v
        v -= self.GAME.ssize / 2
        v.y *= -1
        v += self.pos + self.shake
        return v

    def _update(self):
        self.x = lerpp(self.x, self.nx, self.scroll)
        self.y = lerpp(self.y, self.ny, self.scroll)
        self.fov = lerpp(self.fov, self.nfov, self.scroll)
        self._shake_mag *= 0.9
        if self._shake_mag < 1:
            self._shake_mag = 0
        self._shake_dir = 45 * randint(0, 8)

    @property
    def brightness(self):
        return self._brightness
    @brightness.setter
    def brightness(self, v):
        self._brightness = min(1, max(-1, v if is_num(v) else 0))

    @property
    def hue(self):
        return self._hue
    @hue.setter
    def hue(self, v):
        self._hue = (v if is_num(v) else 0) % 360

    @property
    def bloom(self):
        return self._bloom
    @bloom.setter
    def bloom(self, v):
        self._bloom = max(0, ceil(v if is_num(v) else 0))

    def apply(self, surf):
        if not is_surf(surf):
            return None
        surf = surf.copy()
        if abs(self.brightness) > 0:
            fill = pg.Surface(surf.get_size()).convert_alpha()
            fill.fill((255, 255, 255) if self.brightness > 0 else (0, 0, 0))
            fill.set_alpha(255 * abs(self.brightness))
            surf.blit(fill, (0, 0))
        if self.hue > 0 or self.bloom > 0:
            bloom = pg.Surface(surf.get_size()).convert_alpha()
            bloom.fill((255, 255, 255, 0))
            pixarr = pg.PixelArray(surf)
            for x in range(surf.get_width()):
                for y in range(surf.get_height()):
                    color = surf.get_at((x, y))
                    hsva = list(color.hsva)
                    hsva[0] = (hsva[0] + self.hue) % 360
                    color.hsva = hsva
                    pixarr[x, y] = color
                    if self.bloom > 0:
                        if x % 2 == 0 and y % 2 == 0:
                            if (color.r+color.g+color.b)/3 > 200:
                                bloom.fill(color, (x-1, y-1, 2, 2))
            pixarr.close()
            if self.bloom > 0:
                bloom = scale_surf(scale_surf(bloom, 1/(2*self.bloom+1)), (2*self.bloom+1))
                surf.blit(bloom, ((V(surf.get_size()) - V(bloom.get_size())) / 2).xy)
        if self.fov != 1:
            surf2 = pg.Surface(surf.get_size()).convert_alpha()
            surf2.fill(surf.get_at((0, 0)))
            surf = scale_surf(surf, 1/self.fov, smooth=False)
            surf2.blit(surf, ((V(surf2.get_size()) - V(surf.get_size())) / 2).xy)
            surf = surf2
        return surf

    def applymouse(self, v):
        v = V(v)
        v -= V(self.GAME.surf.get_size()) / 2
        v *= self.fov
        v += V(self.GAME.surf.get_size()) / 2
        return v


class UIObject(GameObject):
    def __init__(self, mode, pos, image, alignx=0, aligny=0, name=None):
        super().__init__(pos, 1, name=name)

        self.g.z = 10 ** 10
        self.g.cam = False
        self.g.image = image

        self.g.set_show("mode", True)
        self.g.set_alpha("mode", 1)

        self.h.enabled = False

        self.alignx = alignx
        self.aligny = aligny

        self._mode = None
        self.mode = mode

    @property
    def alignx(self):
        return self.g.alignx
    @alignx.setter
    def alignx(self, v):
        self.g.alignx = v
    @property
    def aligny(self):
        return self.g.aligny
    @aligny.setter
    def aligny(self, v):
        self.g.aligny = v

    @property
    def mode(self):
        return self._mode
    @mode.setter
    def mode(self, v):
        self._mode = str(v)

    @property
    def curmode(self):
        return self.GAME.mode == self.mode

    def _more(self, more):
        if len(more) > 0 and hasattr(self, "mode"):
            more[0] = f"{self.mode}={more[0]}"
        return []


class UIButton(UIObject):
    def __init__(self, mode, pos, image, imageh=None, **kw):
        super().__init__(mode, pos, None, **kw)

        self.add_handler("hoverenter", lambda e: self._config(True))
        self.add_handler("hoverleave", lambda e: self._config(False))

        self._hover = False

        self._image = None
        self._imageh = None

        self.image = image
        self.imageh = imageh

    @property
    def image(self):
        return self._image
    @image.setter
    def image(self, v):
        v = v if is_surf(v) else None
        if self.image == v:
            return
        self._image = v
        self._config()
    @property
    def imageh(self):
        return self._imageh
    @imageh.setter
    def imageh(self, v):
        v = v if is_surf(v) else self.image
        if self.imageh == v:
            return
        self._imageh = v
        self._config()

    def _config(self, h=None):
        if h is not None:
            self._hover = bool(h)
        h = self._hover
        self.g.image = self.imageh if h else self.image


class UIText(UIObject):
    def __init__(self, mode, pos, text, fg=-1, bg=-1, space=1, size=1, **kw):
        super().__init__(mode, pos, None, **kw)

        self.add_handler("add", lambda e: self._config())

        self._text = None
        self._fg = 0
        self._bg = 0
        self._space = 1
        self._size = 1

        self.text = text
        self.fg = fg
        self.bg = bg
        self.space = space
        self.size = size

    @property
    def text(self):
        return self._text
    @text.setter
    def text(self, v):
        v = str(v)
        if self.text == v:
            return
        self._text = v
        self._config()

    @property
    def fg(self):
        return self._fg
    @fg.setter
    def fg(self, v):
        v = max(-1, v if is_int(v) else -1)
        if self.fg == v:
            return
        self._fg = v
        self._config()
    @property
    def bg(self):
        return self._bg
    @bg.setter
    def bg(self, v):
        v = max(-1, v if is_int(v) else -1)
        if self.bg == v:
            return
        self._bg = v
        self._config()

    @property
    def space(self):
        return self._space
    @space.setter
    def space(self, v):
        v = max(0, v if is_int(v) else 0)
        if self.space == v:
            return
        self._space = v
        self._config()

    @property
    def size(self):
        return self._size
    @size.setter
    def size(self, v):
        v = max(0, v if is_int(v) else 1)
        if self.size == v:
            return
        self._size = v
        self._config()

    def _config(self):
        if not isinstance(self.GAME, Game):
            self.g.image = None
            return
        self.g.image = self.GAME.text(self.text, fg=self.fg, bg=self.bg, space=self.space, size=self.size)


class UITextButton(UIText):
    def __init__(self, mode, pos, text, fg=-1, bg=-1, space=1, size=False, texth=None, fgh=None, bgh=None, spaceh=None, sizeh=None, **kw):
        super().__init__(mode, pos, text, fg, bg, space, size, **kw)

        self.add_handler("hoverenter", lambda e: self._config(True))
        self.add_handler("hoverleave", lambda e: self._config(False))

        self._hover = False

        self._texth = None
        self._fgh = None
        self._bgh = None
        self._spaceh = None
        self._sizeh = None

        self.texth = texth
        self.fgh = fgh
        self.bgh = bgh
        self.spaceh = spaceh
        self.sizeh = sizeh

    @property
    def texth(self):
        return self._texth
    @texth.setter
    def texth(self, v):
        v = v if is_str(v) else self.text
        if self.texth == v:
            return
        self._texth = v
        self._config()

    @property
    def fgh(self):
        return self._fgh
    @fgh.setter
    def fgh(self, v):
        v = max(-1, v) if is_int(v) else self.fg
        if self.fgh == v:
            return
        self._fgh = v
        self._config()
    @property
    def bgh(self):
        return self._bgh
    @bgh.setter
    def bgh(self, v):
        v = max(-1, v) if is_int(v) else self.bg
        if self.bgh == v:
            return
        self._bgh = v
        self._config()

    @property
    def spaceh(self):
        return self._spaceh
    @spaceh.setter
    def spaceh(self, v):
        v = max(0, v) if is_int(v) else self.space
        if self.spaceh == v:
            return
        self._spaceh = v
        self._config()

    @property
    def sizeh(self):
        return self._sizeh
    @sizeh.setter
    def sizeh(self, v):
        v = max(0, v if is_int(v) else self.size)
        if self.sizeh == v:
            return
        self._sizeh = v
        self._config()

    def _config(self, h=None):
        if h is not None:
            self._hover = bool(h)
        if not isinstance(self.GAME, Game):
            self.g.image = None
            return
        self.g.image = self.GAME.text(
            self.texth if self._hover else self.text,
            fg=self.fgh if self._hover else self.fg, bg=self.bgh if self._hover else self.bg,
            space=self.spaceh if self._hover else self.space, size=self.sizeh if self._hover else self.size,
        )


class UIBar(UIObject):
    def __init__(self, mode, pos, size, outline, bg, fg, fgf=None, p=0, **kw):
        super().__init__(mode, pos, None, **kw)

        self.add_handler("add", lambda e: self._config())
        self.add_handler("update", lambda e: self._update())

        self._markers = []

        self._size = V()

        self._outline = 0
        self._bg = -1
        self._fg = -1
        self._fgf = -1
        self._p = 0

        self.size = size

        self.outline = outline
        self.bg = bg
        self.fg = fg
        self.fgf = fgf
        self.p = p

        self._flash = 0

    @property
    def size(self):
        return self._size
    @size.setter
    def size(self, v):
        v = V(v)
        if self.size == v:
            return
        self._size = v
        self._config()
    @property
    def sw(self):
        return self.size.x
    @sw.setter
    def sw(self, v):
        self.size.x = v
        self._config()
    @property
    def sh(self):
        return self.size.y
    @sh.setter
    def sh(self, v):
        self.size.y = v
        self._config()

    @property
    def outline(self):
        return self._outline
    @outline.setter
    def outline(self, v):
        v = max(-1, v if is_int(v) else -1)
        if self.outline == v:
            return
        self._outline = v
        self._config()

    @property
    def bg(self):
        return self._bg
    @bg.setter
    def bg(self, v):
        self._bg = max(-1, v if is_int(v) else -1)
    @property
    def fg(self):
        return self._fg
    @fg.setter
    def fg(self, v):
        v = max(-1, v if is_int(v) else -1)
        if self.fg == v:
            return
        self._fg = v
        self._config()
    @property
    def fgf(self):
        return self._fgf
    @fgf.setter
    def fgf(self, v):
        v = max(-1, v if is_int(v) else -1)
        if self.fgf == v:
            return
        self._fgf = v
        self._config()

    @property
    def p(self):
        return self._p
    @p.setter
    def p(self, v):
        v = min(1, max(0, v if is_num(v) else 0))
        if self.p == v:
            return
        self._p = v
        self._flash = 10
        self._config()

    def add_marker(self, m):
        m = min(1, max(0, m if is_num(m) else 0))
        if m in self._markers:
            return self
        self._markers.append(m)
        self._config()
        return self
    def rem_marker(self, m):
        m = min(1, max(0, m if is_num(m) else 0))
        if m not in self._markers:
            return self
        self._markers.remove(m)
        self._config()
        return self
    def get_markers(self):
        return self._markers.copy()
    def set_markers(self, ml):
        ml = list(ml) if is_arr(ml) else []
        ml = [min(1, max(0, m if is_num(m) else 0)) for m in ml]
        self._markers.clear()
        for m in ml:
            self.add_marker(m)
        return self

    def _update(self):
        if self._flash > 0:
            self._flash -= 1
            self._config()

    def _config(self):
        size = self.size.ceil()
        surf = pg.Surface((size+2).xy).convert_alpha()
        if isinstance(self.GAME, Game):
            outline = (0, 0, 0, 0) if self.outline < 0 else self.GAME.theme[self.outline]
            bg = (0, 0, 0, 0) if self.bg < 0 else self.GAME.theme[self.bg]
            fg = (0, 0, 0, 0) if self.fg < 0 else self.GAME.theme[self.fg]
            fgf = (0, 0, 0, 0) if self.fgf < 0 else self.GAME.theme[self.fgf]
            surf.fill(outline)
            surf.fill(
                bg,
                (
                    (1, 1),
                    size.xy,
                ),
            )
            surf.fill(
                pg.Color(fg).lerp(pg.Color(fgf), round(self._flash/10)),
                (
                    (1, 1),
                    (size * (self.p, 1)).round().xy,
                ),
            )
            for m in self._markers:
                surf.fill(
                    bg,
                    (
                        ((1, 1) + (size * (m, 0)).round()).xy,
                        (1, size.y),
                    ),
                )
        self.g.image = surf


class Entity(GameObject):
    def __init__(self, team, pos, hp):
        super().__init__(pos, hp)

        self.h.group = team

        self.add_handler("update", lambda e: self._update_core())

        self._knockback = V()
        self._lastdamaged = None
        self._parent = None

        self._damage = 1
        self._weight = 1
        self._score = 0

        self._team = None
        self._d = 0

        self.team = team
        self.d = 0

        self._flash = 0

    @property
    def team(self):
        return self._team
    @team.setter
    def team(self, v):
        self._team = v if is_str(v) else None

    @property
    def d(self):
        return self._d
    @d.setter
    def d(self, v):
        self._d = (v if is_num(v) else 0) % 360

    @property
    def damage(self):
        return self._damage
    @damage.setter
    def damage(self, v):
        self._damage = max(0, v if is_num(v) else 0)

    @property
    def weight(self):
        return self._weight
    @weight.setter
    def weight(self, v):
        self._weight = max(PRECISION, v if is_num(v) else 0)

    @property
    def score(self):
        return self._score
    @score.setter
    def score(self, v):
        self._score = max(0, v if is_num(v) else 0)

    @property
    def parent(self):
        return self._parent
    @parent.setter
    def parent(self, v):
        self._parent = v if isinstance(v, Entity) else None

    @property
    def lastdamaged(self):
        return self._lastdamaged
    def dodamage(self, e, a):
        self._lastdamaged = e if isinstance(e, Entity) else None
        self.hp -= a
        self.post_event(Event("dodamage", {"e": e, "a": a}))
    def doknockback(self, *a):
        if len(a) == 1:
            v = V(a[0]) / self._weight
        elif len(a) == 2:
            v = V.dir(*a) / self._weight
        else:
            return
        self.vel += v
        self.post_event(Event("doknockback", {"v": v}))
    def addscore(self, s):
        if isinstance(self.parent, Entity):
            self.parent.addscore(s)
        s = s if is_num(s) else 0
        self.score += s
        self.post_event(Event("addscore", {"s": s}))

    def _update_core(self):
        self.g.showmask = -1
        if self._flash > 0:
            self._flash -= 1
            self.g.showmask = 3
        self.g.z = ceil(-self.y)


class Particle(GameObject):
    def __init__(self, pos, vel, duration, initfunc=None, updatefunc=None, timefunc=None):
        super().__init__(pos, 1, vel)

        self.g.z = 10 ** 5

        self.add_handler("add", lambda e: self._init())
        self.add_handler("update", lambda e: self._update())

        self._i = 0

        self._duration = 0
        self._initfunc = None
        self._updatefunc = None
        self._timefunc = None

        self.duration = duration
        self.initfunc = initfunc
        self.updatefunc = updatefunc
        self.timefunc = timefunc

    @property
    def duration(self):
        return self._duration
    @duration.setter
    def duration(self, v):
        self._duration = max(0, v if is_num(v) else 0)

    @property
    def initfunc(self):
        return self._initfunc
    @initfunc.setter
    def initfunc(self, v):
        self._initfunc = v if callable(v) else None
    @property
    def updatefunc(self):
        return self._updatefunc
    @updatefunc.setter
    def updatefunc(self, v):
        self._updatefunc = v if callable(v) else None
    @property
    def timefunc(self):
        return self._timefunc
    @timefunc.setter
    def timefunc(self, v):
        self._timefunc = v if callable(v) else None

    def _init(self):
        if callable(self.initfunc):
            self.initfunc(self)

    def _update(self):
        if self._i > self.duration:
            self.hp = 0
            return
        t = self._i / self.duration
        t = (self.timefunc if callable(self.timefunc) else self.linear)(self, t)
        if callable(self.updatefunc):
            self.updatefunc(self, t)
        self._i += 1

    @staticmethod
    def linear(_, x):
        return x
    @staticmethod
    def easein(_, x):
        return 1 - cos(x * 90)
    @staticmethod
    def easeout(_, x):
        return sin(x * 90)
    @staticmethod
    def easeinout(_, x):
        return -(cos(180 * x) - 1) / 2


class Sound(EventTarget):
    def __init__(self, name):
        super().__init__()

        self._GAME = None
        self._ID = None

        self._name = None
        self._sound = None
        self._volume = {"§": 1}
        self._starttime = None

        self.name = name

    @property
    def GAME(self):
        return self._GAME
    @property
    def ID(self):
        return self._ID

    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, v):
        v = str(v)
        if self.name == v:
            return
        self._name = v
        if isinstance(self._sound, pg.mixer.Sound):
            self._sound.stop()
        self._sound = pg.mixer.Sound(os.path.join(ASSETS, self.name))

    @property
    def length(self):
        if isinstance(self._sound, pg.mixer.Sound):
            return self._sound.get_length()
        return None

    def set_volume(self, name, v):
        name = str(name)
        self._volume[name] = min(1, max(0, v if is_num(v) else 0))
        self._config()
        self.post_event(Event("volumeset", {"n": name, "v": self.get_volume(name)}))
        return self
    def get_volume(self, name):
        return self._volume[name] if name in self._volume else None
    def rem_volume(self, name):
        name = str(name)
        if name != "§":
            self._volume.pop(name, None)
        self._config()
        self.post_event(Event("volumerem", {"n": name}))
        return self

    @property
    def volume(self):
        return self.get_volume("§")
    @volume.setter
    def volume(self, v):
        self.set_volume("§", v)
    @property
    def truevolume(self):
        v = 1
        for v0 in self._volume.values():
            v *= v0
        return v

    def _config(self):
        if not isinstance(self._sound, pg.mixer.Sound):
            return
        self._sound.set_volume(self.truevolume)

    @property
    def started(self):
        return is_num(self._starttime)
    @property
    def playing(self):
        return self.started and (time() - self._starttime) <= self.length
    @property
    def finished(self):
        return self.started and (time() - self._starttime) > self.length

    def play(self):
        if not isinstance(self._sound, pg.mixer.Sound):
            return self
        self.post_event(Event("play"))
        self._starttime = time()
        self._sound.play()
        return self
    def stop(self):
        if not isinstance(self._sound, pg.mixer.Sound):
            return self
        self.post_event(Event("stop"))
        self._starttime = None
        self._sound.stop()
        return self


class Game(EventTarget):
    def __init__(self, title, size):
        super().__init__()

        pg.display.set_caption(title)

        self.surf = pg.Surface(V(size).ceil().xy).convert_alpha()

        textures = pg.image.load(os.path.join(ASSETS, "textures.png")).convert_alpha()
        self.textures = pg.Surface((8*((V(textures.get_size())/8).ceil()+2)).xy).convert_alpha()
        self.textures.fill((0, 0, 0, 0))
        self.textures.blit(textures, (8, 8))
        self.texturescache = {}

        self.themetex = self.gettex("§themetex", (0, 0), (1, 1))
        self.otheme = [
            self.themetex.get_at((x*2, 0))
            for x in range(4)
        ]
        self.theme = self.otheme.copy()
        self.themei = 0
        self._chars = []

        self.pressed = []
        self.keydown = {}
        self.keyup = {}

        self._gos = {}
        self._go_addq = []
        self._go_remq = []

        self._walls = {}
        self._groups = {}
        self._gridsize = 16

        self._CAM = None
        self.CAM = Camera(0)

        self._mouse = V()
        self._hovering = None
        self._lasthovering = None
        self._mousedown = False
        self._lastmousedown = False

        self._mode = None
        self._mode_alpha = {}

        self._sounds = {}
        self._sound_addq = []
        self._sound_remq = []
        self._volume = 1

        self.set_theme(0)

    def _propagate(self, event):
        for ID, go in self._gos.items():
            go.post_event(event)
        for ID, sound in self._sounds.items():
            sound.post_event(event)

    @property
    def mode(self):
        return self._mode
    @mode.setter
    def mode(self, v):
        v = str(v)
        if self.mode == v:
            return
        lm = self.mode
        self._mode = v
        m = self.mode
        self._mode_alpha[m] = 0
        self._lm_mode(m, lm)
        self._m_mode(m, lm)
        self.post_event(Event("modeset", {"lm": lm, "m": m}))

    def _lm_mode(self, m, lm):
        pass
    def _m_mode(self, m, lm):
        pass

    def replace(self, image, lasttheme, theme):
        pixarr = pg.PixelArray(image)
        for i in range(4):
            pixarr.replace(lasttheme[i], theme[i])
        pixarr.close()
        return image

    def gettex(self, name, pos=0, size=0, clip=True):
        opt = (clip,)
        if name in self.texturescache:
            if is_dict(self.texturescache[name]):
                if opt in self.texturescache[name]:
                    return self.texturescache[name][opt]
            elif is_surf(self.texturescache[name]):
                return self.texturescache[name]
            else:
                return pg.Surface((0, 0))
        else:
            self.texturescache[name] = {}
        pos = (V(pos) + 1) * 8
        size = V(size) * 8
        surf = pg.Surface(size.ceil().xy).convert_alpha()
        surf.fill((0, 0, 0, 0))
        surf.blit(self.textures, (-pos).xy)
        if not name.startswith("§"):
            self.replace(surf, self.otheme, self.theme)
        if clip:
            rect = surf.get_bounding_rect()
            surf2 = pg.Surface(rect.size).convert_alpha()
            surf2.fill((0, 0, 0, 0))
            surf2.blit(surf, (-V(rect.topleft)).xy)
            surf = surf2
        self.texturescache[name][opt] = surf
        return surf

    def set_theme(self, themei):
        if not is_int(themei):
            return
        themei = max(0, themei)
        lasttheme = self.theme.copy()
        theme = [
            self.themetex.get_at((x*2, themei))
            for x in range(4)
        ]
        for name, surfs in self.texturescache.items():
            if name.startswith("§"):
                continue
            if is_dict(surfs):
                for opt, surf in surfs.items():
                    self.replace(surf, lasttheme, theme)
            elif is_surf(surfs):
                self.replace(surfs, lasttheme, theme)
        self.theme = theme
        self.themei = themei
        for ID, go in self._gos.items():
            for node in go.nodes:
                self._set_theme(vars(node), lasttheme, theme)
            self._set_theme(vars(go), lasttheme, theme)
        self.post_event(Event("themeset", {"themei": themei}))
    def _set_theme(self, o, lasttheme, theme):
        if is_arr(o):
            for v in o:
                self._set_theme(v, lasttheme, theme)
            return
        if is_dict(o):
            for k, v in o.items():
                self._set_theme(v, lasttheme, theme)
            return
        if is_surf(o):
            self.replace(o, lasttheme, theme)
            return

    def text(self, text, fg, bg=-1, space=1, size=1):
        fg = min(len(self.theme)-1, max(-1, fg if is_int(fg) else -1))
        bg = min(len(self.theme)-1, max(-1, bg if is_int(fg) else -1))
        size = min(len(self._chars)-1, max(0, size if is_int(size) else 1))
        surf = pg.Surface((0, 0)).convert_alpha()
        chars = self._chars[size][max(0, fg)]
        x = 0
        for c in str(text).lower():
            ctex = chars[c] if c in chars else chars["§"]
            if x + ctex.get_width() > surf.get_width():
                surf2 = pg.Surface((x + ctex.get_width(), surf.get_height())).convert_alpha()
                surf2.fill((0, 0, 0, 0))
                if bg >= 0:
                    surf2.fill(
                        self.theme[bg],
                        ((0, 0), (surf2.get_width(), 5)),
                    )
                surf2.blit(surf, (0, 0))
                surf = surf2
            if ctex.get_height() > surf.get_height():
                surf2 = pg.Surface((surf.get_width(), ctex.get_height())).convert_alpha()
                surf2.fill((0, 0, 0, 0))
                if bg >= 0:
                    surf2.fill(
                        self.theme[bg],
                        ((0, 0), (surf2.get_width(), 5)),
                    )
                surf2.blit(surf, (0, 0))
                surf = surf2
            if fg >= 0:
                surf.blit(ctex, (x, 0))
            x += ctex.get_width() + space
        return surf

    def add_go_q(self, go):
        self._go_addq.append(go)
        return go
    def rem_go_q(self, go):
        self._go_remq.append(go)
        return go
    def add_go(self, go):
        if not isinstance(go, GameObject):
            return None
        if self.has_go(go):
            return None
        ID = unijargon(5, self._gos)
        go._ID = ID
        go._GAME = self
        self._gos[ID] = go
        go.post_event(Event("add", {"game": self}))
        return go
    def rem_go(self, go):
        if not isinstance(go, GameObject):
            return None
        if not self.has_go(go):
            return None
        ID = go.ID
        go._ID = None
        go._GAME = None
        self._gos.pop(ID, None)
        go.post_event(Event("rem", {"game": self}))
        return go
    def has_go(self, go):
        if not isinstance(go, GameObject):
            return False
        if go.GAME is not self:
            return False
        if go.ID is None:
            return False
        if go.ID not in self._gos:
            return False
        if self._gos[go.ID] is not go:
            return False
        return True
    @property
    def gos(self):
        return self._gos.copy()

    def set_wall(self, rect, name=None):
        if not is_str(name):
            name = unijargon(5, self._walls)
        self._walls[name] = pg.Rect(rect)
    def get_wall(self, name):
        if name in self._walls:
            return self._walls[name]
        return None
    def rem_wall(self, name):
        if name in self._walls:
            return self._walls.pop(name)
        return None
    @property
    def walls(self):
        return self._walls.copy()

    @property
    def CAM(self):
        return self._CAM
    @CAM.setter
    def CAM(self, v):
        if not isinstance(v, Camera):
            return
        self.rem_go(self.CAM)
        self._CAM = self.add_go(v)

    def getappliedsurf(self):
        surf = self.surf.copy()
        if isinstance(self.CAM, Camera):
            surf = self.CAM.apply(surf)
        return surf

    @property
    def ssize(self):
        return V(self.surf.get_size())
    @property
    def sw(self):
        return self.ssize.x
    @property
    def sh(self):
        return self.ssize.y

    @property
    def mouse(self):
        return self._mouse
    @property
    def mousedown(self):
        return self._mousedown

    @property
    def volume(self):
        return self._volume
    @volume.setter
    def volume(self, v):
        self._volume = min(1, max(0, v if is_num(v) else 0))
    def add_sound_q(self, sound):
        self._sound_addq.append(sound)
        return sound
    def rem_sound_q(self, sound):
        self._sound_remq.append(sound)
        return sound
    def add_sound(self, sound):
        if not isinstance(sound, Sound):
            return None
        if self.has_sound(sound):
            return None
        ID = unijargon(5, self._sounds)
        sound._ID = ID
        sound._GAME = self
        self._sounds[ID] = sound
        sound.set_volume("game", 0)
        return sound
    def rem_sound(self, sound):
        if not isinstance(sound, Sound):
            return None
        if not self.has_sound(sound):
            return None
        ID = sound.ID
        sound._ID = None
        sound._GAME = None
        self._sounds.pop(ID, None)
        sound.rem_volume("game")
        return sound
    def has_sound(self, sound):
        if not isinstance(sound, Sound):
            return False
        if sound.GAME is not self:
            return False
        if sound.ID is None:
            return False
        if sound.ID not in self._sounds:
            return False
        if self._sounds[sound.ID] is not sound:
            return False
        return True
    @property
    def sounds(self):
        return self._sounds.copy()

    @property
    def hovering(self):
        return self._lasthovering

    @property
    def gridsize(self):
        return self._gridsize
    @property
    def groups(self):
        return self._groups.copy()

    def update(self, mouse):
        self._mouse = V(self.CAM.applymouse(mouse) if isinstance(self.CAM, Camera) else mouse)
        self.keydown.clear()
        self.keyup.clear()
        events = pg.event.get()
        for e in events:
            if e.type == QUIT:
                return True
            elif e.type == KEYDOWN:
                self.keydown[e.key] = True
            elif e.type == KEYUP:
                self.keyup[e.key] = True
        self.pressed = pg.key.get_pressed()
        [self.add_go(go) for go in self._go_addq]
        self._go_addq.clear()
        self._groups = {}
        for ID, go in self._gos.items():
            self._groups[go.h.group] = self._groups.get(go.h.group, {})
            gridrect = go.h.gridrect
            r, l = gridrect.right, gridrect.left
            u, d = gridrect.bottom, gridrect.top
            if r == l or u == d:
                continue
            for x in range(l, r+1):
                for y in range(d, u+1):
                    self._groups[go.h.group][(x, y)] = self._groups[go.h.group].get((x, y), [])
                    self._groups[go.h.group][(x, y)].append(go)
        for ID, go in self._gos.items():
            if go.update(None):
                self.rem_go_q(go)
        [self.rem_go(go) for go in self._go_remq]
        self._go_remq.clear()
        for m, a in list(self._mode_alpha.items()):
            self._mode_alpha[m] = min(10, max(0, a + [-1, +1][int(m == self.mode)]))
        self._mode_alpha["*all"] = 10
        [self.add_sound(sound) for sound in self._sound_addq]
        self._sound_addq.clear()
        for ID, sound in self._sounds.items():
            sound.set_volume("game", self.volume)
            if sound.started:
                if sound.finished:
                    sound.stop()
                    self.rem_sound_q(sound)
            else:
                sound.play()
        [self.rem_sound(sound) for sound in self._sound_remq]
        self._sound_remq.clear()
        if self._update(events):
            return True
        return False

    def _update(self, events):
        pass

    def render(self):
        self._hovering = None
        self.surf.fill(self.theme[0])
        zorder = {}
        for ID, go in self._gos.items():
            for node in go.nodes:
                if not isinstance(node, GraphicsNode):
                    continue
                if node.disabled:
                    continue
                zorder[node.z] = zorder.get(node.z, [])
                zorder[node.z].append(node)
        zorder = sorted(list(zorder.items()))
        for z, nodes in zorder:
            for node in nodes:
                node.render()
        """
        for group, data in self._groups.items():
            for pos, gos in data.items():
                pg.draw.rect(
                    self.surf,
                    (255, 0, 0),
                    (
                        (self.CAM.w2s(V(pos) * self._gridsize) - self._gridsize/2).xy,
                        V(self._gridsize).xy,
                    ),
                    width=1,
                )
        """
        self._mousedown = bool(pg.mouse.get_pressed(3)[0])
        if self._lasthovering != self._hovering:
            if isinstance(self._lasthovering, GameObject):
                self._lasthovering.post_event(Event("hoverleave", {"pos": self.mouse}))
                if self._lastmousedown:
                    self._lasthovering.post_event(Event("mouseup", {"pos": self.mouse}))
            self._lasthovering = self._hovering
            self._lastmousedown = self._mousedown
            if isinstance(self._lasthovering, GameObject):
                self._lasthovering.post_event(Event("hoverenter", {"pos": self.mouse}))
                if self._lastmousedown:
                    self._lasthovering.post_event(Event("mousedown", {"pos": self.mouse}))
        if isinstance(self._lasthovering, GameObject):
            self._lasthovering.post_event(Event("hover", {"pos": self.mouse}))
            if self._lastmousedown != self._mousedown:
                self._lastmousedown = self._mousedown
                self._lasthovering.post_event(
                    Event("mousedown" if self._lastmousedown else "mouseup", {"pos": self.mouse}))
            if self._lastmousedown:
                self._lasthovering.post_event(Event("mouse", {"pos": self.mouse}))
        self._render()

    def _render(self):
        pass


__all__ = [
    "Object",
    "Event",
    "EventTarget",
    "GameObject",
    "GameNode",
    "GraphicsNode",
    "HitboxNode",
    "RaycastNode",
    "Camera",
    "UIObject",
    "UIButton",
    "UIText",
    "UITextButton",
    "UIBar",
    "Entity",
    "Particle",
    "Sound",
    "Game",
]
  