"""
Blob Blast - Jeffrey Fan
Game

PREFERRED IF YOU RUN ON PERSONAL DEVICE AND NOT ON REPL
AS THERE IS PLENTY OF LAG AND NO SOUND AVAILABLE ON REPL

This is one of my most ambitious projects yet
For this, I made basically an ENTIRE GAME ENGINE (in engine.py) and vectors (in util.py)
    I did not use PyGame sprites because I found they had no camera, were super hard to work with, and
    the coordinates were different, so that +y meant down instead of up.
Read about those in their respective files (at the top)
Check out CREDITS.md for credits relating to the sounds used
ALL ART IS DONE BY ME

You can also read this file if you want
    It's mostly game logic in this file - which is good because most of the rendering is hidden inside engine.py :)

"""


import json

from util import *

from engine import *
BaseGame = Game


ENEMIES = {}

NSEWMAP = ["c", "e", "w", "n", "s", "ne", "nw", "se", "sw"]
NSEWORD = ["n", "ne", "e", "se", "s", "sw", "w", "nw", "n"]


def dir2str(d):
    d -= 22.5
    d /= 45
    for i, s in enumerate(NSEWORD):
        if d < i:
            return s
    return "c"


class LaserNode(GraphicsNode):
    def __init__(self, o, fg, width=8):
        super().__init__(o, None)

        self._fg = -1
        self._width = 0
        self._dist = 0

        self.fg = fg
        self.width = width
        self.d = 0
        self.dist = 0

    @property
    def fg(self):
        return self._fg
    @fg.setter
    def fg(self, v):
        self._fg = max(-1, v if is_int(v) else -1)

    @property
    def width(self):
        return self._width
    @width.setter
    def width(self, v):
        self._width = max(0, v if is_num(v) else 0)

    @property
    def dist(self):
        return self._dist
    @dist.setter
    def dist(self, v):
        self._dist = max(0, v if is_num(v) else 0)

    def _render(self, _, __):
        d = self.d
        pos1 = self.o.pos + self.offset
        pos2 = pos1 + V.dir(d, self.dist)
        move = V.dir(d+90, self.width/2)
        poslist = [pos1+move, pos1-move, pos2-move, pos2+move]
        poslist = [self.GAME.CAM.w2s(pos).xy for pos in poslist]
        color = (0, 0, 0, 0) if self.fg < 0 else self.GAME.theme[self.fg],
        rect0 = pg.draw.polygon(
            self.GAME.surf,
            color,
            poslist,
        )
        rect1 = pg.draw.circle(
            self.GAME.surf,
            color,
            self.GAME.CAM.w2s(pos1).xy,
            ceil(self.width/2 + 2),
        )
        rect2 = pg.draw.circle(
            self.GAME.surf,
            color,
            self.GAME.CAM.w2s(pos2).xy,
            ceil(self.width/2 + 2),
        )
        return rect0.union(rect1).union(rect2)


class CircleNode(GraphicsNode):
    def __init__(self, o, fg, rad):
        super().__init__(o, None)

        self._fg = -1
        self._rad = 0

        self.fg = fg
        self.rad = rad

    @property
    def fg(self):
        return self._fg
    @fg.setter
    def fg(self, v):
        self._fg = max(-1, v if is_int(v) else -1)

    @property
    def rad(self):
        return self._rad
    @rad.setter
    def rad(self, v):
        self._rad = max(0, v if is_num(v) else 0)

    def _render(self, _, pos):
        return pg.draw.circle(
            self.GAME.surf,
            (0, 0, 0, 0) if self.fg < 0 else self.GAME.theme[self.fg],
            pos.xy,
            self.rad,
        )


class ShooterNode(GameNode):
    def __init__(self, o, ammomax=0, cooldowntime=0, reloadtime=0):
        super().__init__(o)

        self._shooting = False

        self._ammomax = 0
        self._ammo = 0
        self._cooldowntime = 0
        self._cooldown = 0
        self._reloadtime = 0
        self._reload = 0

        self.ammomax = ammomax
        self.ammo = 0
        self.cooldowntime = cooldowntime
        self.cooldown = 0
        self.reloadtime = reloadtime
        self.reload = 0

    @property
    def shooting(self):
        return self._shooting
    @shooting.setter
    def shooting(self, v):
        self._shooting = bool(v)

    @property
    def ammomax(self):
        return self._ammomax
    @ammomax.setter
    def ammomax(self, v):
        self._ammomax = max(0, v if is_int(v) else 0)
        self.ammo = self.ammo
    @property
    def ammo(self):
        return self._ammo
    @ammo.setter
    def ammo(self, v):
        self._ammo = min(self.ammomax, max(0, v if is_int(v) else 0))

    @property
    def cooldowntime(self):
        return self._cooldowntime
    @cooldowntime.setter
    def cooldowntime(self, v):
        self._cooldowntime = max(0, v if is_int(v) else 0)
        self.cooldown = self.cooldown
    @property
    def cooldown(self):
        return self._cooldown
    @cooldown.setter
    def cooldown(self, v):
        self._cooldown = min(self.cooldowntime, max(0, v if is_int(v) else 0))

    @property
    def reloadtime(self):
        return self._reloadtime
    @reloadtime.setter
    def reloadtime(self, v):
        self._reloadtime = max(0, v if is_int(v) else 0)
        self.reload = self.reload
    @property
    def reload(self):
        return self._reload
    @reload.setter
    def reload(self, v):
        self._reload = min(self.reloadtime, max(0, v if is_int(v) else 0))

    def update(self, _):
        if self.cooldown > 0:
            self.cooldown -= 1
        else:
            if self.shooting:
                if self.ammo > 0:
                    self.ammo -= 1
                    self.cooldown = self.cooldowntime
                    self.o.post_event(Event("shoot"))
        if self.ammo == 0:
            if self.reload < self.reloadtime:
                self.reload += 1
            else:
                self.ammo = self.ammomax
                self.reload = 0


class Player(Entity):
    def __init__(self, pos):
        super().__init__("player", pos, 25)

        self.g.aligny = 1
        self.g2 = GraphicsNode(self, None)

        self.h.size = (5, 3)
        self.h.add_group_collide("enemy")
        self.h.add_group_collide("enemy-bullet")
        self.h.add_group_collide("player")

        self.add_handler("collideenter", self._collide)
        self.add_handler("shoot", lambda e: self._shoot())
        self.add_handler("update", lambda e: self._update())
        self.add_handler("death", lambda e: self._death())

        self.d = 0

        self.score = 0

        self.shooter = ShooterNode(self, 10, 15, 120)

        self._fd = 0
        self._powerupmax = 0
        self._powerup = 0

        self.fd = 0
        self.powerup = 0

        self._timer = 0

    @property
    def fd(self):
        return self._fd
    @fd.setter
    def fd(self, v):
        self._fd = (v if is_num(v) else 0) % 360

    @property
    def powerupmax(self):
        return self._powerupmax
    @property
    def powerup(self):
        return self._powerup
    @powerup.setter
    def powerup(self, v):
        self._powerup = max(0, v if is_num(v) else 0)
        if self._powerup > 0:
            if self._powerup > self._powerupmax:
                self._powerupmax = self._powerup
                self.GAME.add_sound(Sound("powerup.mp3"))
        else:
            self._powerupmax = 0

    @property
    def haspowerup(self):
        return self.powerup > 0

    def _shoot(self):
        self.doknockback(self.d + 180, 2 if self.haspowerup else 3)
        self.GAME.CAM.add_shake(1 if self.haspowerup else 2)
        self.GAME.add_go_q(Bullet(
            self,
            3,
            self.pos + self.g2.offset,
            self.d,
            1 if self.haspowerup else 1,
            0.35 if self.haspowerup else 0.25,
        ))
        sound = self.GAME.add_sound(Sound("explosion1.mp3"))
        sound.volume = [0.3, 0.5][self.shooter.ammo % 2]

    def _collide(self, e):
        go = e.data["go"]
        if not isinstance(go, Entity):
            return
        if self.team is None or go.team is None or self.team != go.team:
            if go.damage <= 0:
                return
            self.dodamage(go, go.damage)
            go.doknockback(self.pos.toward(go.pos), 2)
            sound = self.GAME.add_sound(Sound("damage3.mp3"))
            sound.volume = 1
            self.GAME.add_go_q(ParticleText(self.pos, 15, f"-{go.damage}", 3))
            self._flash = 10
        else:
            pass

    def _death(self):
        self.GAME.explode(self.pos, 8, (0.25, 3), 3, (0,))
        lastdamaged = self.lastdamaged
        if isinstance(lastdamaged, Entity):
            lastdamaged.addscore(self.score)

    def _update(self):
        if self.haspowerup:
            self.powerup -= 1
            self.hp += 0.025
        self.shooter.shooting = self.GAME.playershooting or self.haspowerup
        self.shooter.cooldowntime = 5 if self.haspowerup else 15
        self.shooter.reloadtime = 0 if self.haspowerup else 120
        """
        move = V()
        if self.GAME.pressed[K_RIGHT] or self.GAME.pressed[K_d]:
            move.x += 1
        if self.GAME.pressed[K_LEFT] or self.GAME.pressed[K_a]:
            move.x -= 1
        if self.GAME.pressed[K_UP] or self.GAME.pressed[K_w]:
            move.y += 1
        if self.GAME.pressed[K_DOWN] or self.GAME.pressed[K_s]:
            move.y -= 1
        if move.dist(0) > 0:
            self.vel += 0.25 * (move / move.dist(0))
        """
        if self.vel.dist(0) > 0.25:
            self.fd = V().toward(self.vel) + 180
        ds = dir2str(self.fd)
        self.g.image = self.GAME.gettex(
            f"player-{ds}",
            (2+NSEWMAP.index(ds), 12),
            (7/8, 10/8),
        )
        self.d = self.pos.toward(self.GAME.CAM.s2w(self.GAME.mouse))
        d = self.d
        for i in range(9):
            if abs((45*i) - d) < 5:
                d = 45*i
        self.g2.image = self.GAME.gettex("gun", (13, 12), (1, 2))
        self.g2.z = self.g.z + (1 if abs(180-d) < 90 else -1)
        self.g2.d = d
        self.g2.offset = V.dir(d, 8) + (0, 4)
        self.g.showmask = self.g2.showmask = [-1, 0, 3][ceil(time() / 0.1) % 3] if self.haspowerup else -1
        if self._timer > 0:
            self._timer -= 1
        else:
            self._timer = 15
            if self.haspowerup:
                image = pg.Surface((3, 3)).convert_alpha()
                image.fill(self.GAME.theme[3])
                go = self.GAME.add_go_q(ParticleImage(
                    self.pos,
                    60,
                    image,
                ))
                go.vel += V.dir(randint(0, 360), 0.25)
                go.updatefunc = lambda _go, _t: (
                    _go.conf(vel=_go.vel+V.dir(V().toward(_go.vel), 0.1*(1-_t))),
                    _go.g.conf(alpha=1-_t),
                )


class Enemy(Entity):
    def __init__(self, t, pos):
        super().__init__("enemy", pos, 1)

        self.g.aligny = 1

        self.h.add_group_collide("player")
        self.h.add_group_collide("player-bullet")
        self.h.add_group_collide("enemy")
        self.h.aligny = -1

        self.add_handler("collideenter", self._collide)
        self.add_handler("shoot", lambda e: self._shoot())
        self.add_handler("update", lambda e: self._update())
        self.add_handler("death", lambda e: self._death())

        self.shooter = ShooterNode(self)

        self._t = str(t)

        self._sd = 0
        self.sd = 0

        self.ENEMY = ENEMIES.get(self._t, {})
        self.ENEMY = self.ENEMY if is_dict(self.ENEMY) else {}

        self._speed = 0

        self.hpmax = self.ENEMY.get("hp", 0)
        self.hp = self.hpmax

        self.speed = self.ENEMY.get("speed", 0)
        self.weight = self.ENEMY.get("weight", 0)
        self.score = self.ENEMY.get("score", 0)

        self.shooter.ammomax = self.ENEMY.get("ammomax", 0)
        self.shooter.cooldowntime = self.ENEMY.get("cooldowntime", 0)
        self.shooter.reloadtime = self.ENEMY.get("reloadtime", 0)

        self.h.size = self.ENEMY.get("box", 0)

        self._image_pos = V(self.ENEMY.get("image", [0, 0])[0]) + (2, 14)
        self._image_size = V(self.ENEMY.get("image", [0, 0])[1])

        self._data = {}

        self._init()

    @property
    def t(self):
        return self._t

    @property
    def sd(self):
        return self._sd
    @sd.setter
    def sd(self, v):
        self._sd = (v if is_num(v) else 0) % 360

    @property
    def speed(self):
        return self._speed
    @speed.setter
    def speed(self, v):
        self._speed = max(0, v if is_num(v) else 0)

    def _init(self):
        if self.t == "boss":
            gface = self._data["gface"] = GraphicsNode(self, None)
            gcrown = self._data["gcrown"] = GraphicsNode(self, None)
            gskelet = self._data["gskelet"] = GraphicsNode(self, None)
            gface.aligny = gcrown.aligny = gskelet.aligny = 1

            gshadow = self._data["gshadow"] = GraphicsNode(self, None)
            gshadow.aligny = 1
            glaser = self._data["glaser"] = LaserNode(self, 3, 0)
            glaser.oy = 4
            ggun = self._data["ggun"] = GraphicsNode(self, None)
            ggun.oy = 4

            rc = self._data["rc"] = RaycastNode(self, 0)
            rc.oy = 4
            rc.add_group_collide("player")

            self._data["stage"] = self._data["nstage"] = 0
            self._data["attackqueue"] = []
            self._data["curattack"] = None
            self._data["pushattack"] = lambda name, data: self._data["attackqueue"].append((str(name), updatedict(data if is_dict(data) else {}, {"time": 0})))
            self._data["pullattack"] = lambda: updatedict(self._data, {"curattack": self._data["attackqueue"].pop(0) if len(self._data["attackqueue"]) > 0 else None})
            self._data["pushattack"]("wait", {"timer": 1*60, "onend": lambda: updatedict(self._data, {"nstage": 1})})
            self._data["died"] = False

            self.damage = 3
            return

    def _shoot(self):
        if self.t == "cannon":
            self.doknockback(self.d + 180, 2)
            self.GAME.add_go_q(Bullet(
                self,
                1,
                self.pos + (0, 12),
                self.sd,
                1,
                0.25,
            ))
            sound = self.GAME.add_sound(Sound("explosion3.mp3"))
            sound.volume = 1
            return
        if self.t == "boss":
            ggun = self._data["ggun"]
            x = 4 * ((self.shooter.ammo / ((self.shooter.ammomax-1)/2)) - 1)
            d = ggun.d+90
            self.doknockback(d + 180, 0.25)
            self.GAME.CAM.add_shake(0.5)
            self.GAME.add_go_q(Bullet(
                self,
                0,
                self.pos + ggun.offset + V.dir(d, 12) + V.dir(d+90, x),
                d + randfloat(-7.5, 7.5),
                0.5,
                0.5,
            ))
            sound = self.GAME.add_sound(Sound("explosion3.mp3"))
            sound.volume = 0.25
            return

    def _collide(self, e):
        go = e.data["go"]
        if not isinstance(go, Entity):
            return
        if self.team is None or go.team is None or self.team != go.team:
            if go.damage <= 0:
                return
            self.dodamage(go, go.damage)
            go.doknockback(self.pos.toward(go.pos), 2)
            sound = self.GAME.add_sound(Sound("damage2.mp3"))
            sound.volume = 1
            self.GAME.add_go_q(ParticleText(self.pos, 15, f"-{go.damage}", 3))
            self._flash = 10
        else:
            self.doknockback(go.pos.toward(self.pos), 1)

    def _death(self):
        if self.t == "boss":
            if not self._data["died"]:
                self._data["stage"] = self._data["nstage"] = 0
                self._data["died"] = True
                self._data["attackqueue"].clear()
                self._data["curattack"] = None
                self._data["pushattack"]("death", {"timer": 3*60})
                self.hpmax = 1000 * 1000
                self.hp = 1000
                self.damage = 0
                return
        self.GAME.explode(self.pos, 8, (0.5, 4), 4, (1,))
        lastdamaged = self.lastdamaged
        if isinstance(lastdamaged, Entity):
            lastdamaged.addscore(self.score)

    def _update(self):
        ds = "c"
        if isinstance(self.GAME.PLAYER, Player):
            self.d = self.pos.toward(self.GAME.PLAYER.pos)
            self.vel += V.dir(self.d, self.speed)
            ds = dir2str(self.d)
        if self.t == "boss":
            ds = "c"
        self.g.image = self.GAME.gettex(
            f"enemy{self._t}-{ds}",
            self._image_pos + (NSEWMAP.index(ds) * (self._image_size.x/8), 0),
            self._image_size/8,
        )
        if self.t == "cannon":
            self.shooter.shooting = False
            if isinstance(self.GAME.PLAYER, Player):
                self.sd = (self.pos + (0, 12)).toward(self.GAME.PLAYER.pos)
                self.shooter.shooting = True
            return
        if self.t == "boss":
            ds = dir2str(self.d)
            bodyoffset = V()
            faceimage = self.GAME.gettex(f"{self.t}-face", self._image_pos + (0, 3), (2, 1))
            faceoffsets = {}
            for ds2 in NSEWMAP:
                faceoffsets[ds2] = V(
                    (+1 if "e" in ds2 else 0) + (-1 if "w" in ds2 else 0),
                    (+1 if "n" in ds2 else 0) + (-1 if "s" in ds2 else 0),
                )
            faceoffset = faceoffsets[ds]
            gunimage = self.GAME.gettex(f"{self.t}-gun", self._image_pos + (0, 5), (3, 2))

            g = self.g
            gface = self._data["gface"]
            gcrown = self._data["gcrown"]
            gskelet = self._data["gskelet"]
            glaser = self._data["glaser"]
            gshadow = self._data["gshadow"]
            ggun = self._data["ggun"]

            gface.enabled = gcrown.enabled = True
            gskelet.enabled = False

            glaser.enabled = gshadow.enabled = ggun.enabled = False

            if is_tup(self._data["curattack"]):
                name, data = self._data["curattack"]
                data["timer"] = data.get("timer", 0)
                first = data["time"] == 0
                data["time"] += 1
                last = data["time"] > data["timer"]
                if name == "wait":
                    pass
                elif name == "stun":
                    self.hp = data["hplock"]
                    ds = NSEWORD[floor(time() / 0.1) % (len(NSEWORD)-1)]
                    faceoffset = faceoffsets[ds]
                    faceimage = self.GAME.gettex(f"{self.t}-face-stun", self._image_pos + (2, 3), (2, 1))
                elif name == "death":
                    if first:
                        data["skelet"] = 0
                        data["t"] = time()
                    t = lerp(0.25, 0.05, data["time"] / data["timer"])
                    if time() > data["t"]:
                        data["t"] += t
                        data["skelet"] = 1 - data["skelet"]
                    g.showmask = [-1, 0][data["skelet"]]
                    gface.enabled = False
                    gskelet.enabled = data["skelet"]
                    if last:
                        self.dodamage(self.lastdamaged, self.hpmax)
                        self.GAME.boom(self.pos, 16, 16)
                elif name == "laser":
                    warn = data["time"] <= data.get("warn", 0)
                    if first:
                        data["d"] = self.d
                    glaser.enabled = True
                    rc = self._data["rc"]
                    r = 0
                    if isinstance(self.GAME.PLAYER, Player):
                        r = anglerel(data["d"], (self.pos + rc.offset).toward(self.GAME.PLAYER.pos))
                    data["d"] += (sign(r) * min(abs(r) * 0.01, 0.3))
                    glaser.d = rc.d = data["d"]
                    glaser.width = 8
                    dist, godata, wdata = rc.shoot(glaser.width)
                    glaser.dist = dist
                    if warn:
                        glaser.fg = 3
                        glaser.enabled = [False, True][ceil(time() / 0.1) % 2]
                    else:
                        faceimage = self.GAME.gettex(f"{self.t}-face-barf", self._image_pos + (4, 3), (3, 1))
                        faceoffset.setxy((0, 4))
                        glaser.fg = [0, 3][ceil(time() / 0.1) % 2]
                        if data["time"] % 15 == 0:
                            self.GAME.CAM.add_shake(3)
                            if is_tup(godata):
                                ID, go = godata
                                if isinstance(go, Entity):
                                    go.dodamage(self, 1)
                                    go.doknockback(V.dir(glaser.d, 0.5))
                                    self.doknockback(-V.dir(glaser.d, 0.5))
                elif name == "smash":
                    faceimage = self.GAME.gettex(f"{self.t}-face-yell", self._image_pos + (0, 4), (2, 1))
                    gshadow.enabled = True
                    if first:
                        data["from"] = V(self.pos)
                        self.h.enabled = False
                    self.pos = lerp(data["from"], data.get("to", data["from"]), data["time"]/data["timer"])
                    bodyoffset.sety(32 * sin(180 * (data["time"]/data["timer"])))
                    if last:
                        self.h.enabled = True
                        self.GAME.CAM.add_shake(4)
                elif name == "gun":
                    faceimage = self.GAME.gettex(f"{self.t}-face-yell", self._image_pos + (0, 4), (2, 1))
                    ggun.enabled = True
                    warn = data["time"] <= data.get("warn", 0)
                    if first:
                        data["d"] = self.d
                        self.shooter.ammomax = 4
                        self.shooter.cooldowntime = 2
                        self.shooter.reloadtime = 2
                    if last:
                        self.shooter.ammomax = 0
                        self.shooter.cooldowntime = 0
                        self.shooter.reloadtime = 0
                    ggun.offset = V.dir(data["d"], 16) + (0, 4)
                    r = 0
                    if isinstance(self.GAME.PLAYER, Player):
                        r = anglerel(data["d"], (self.pos + ggun.offset).toward(self.GAME.PLAYER.pos))
                    data["d"] += (sign(r) * min(abs(r) * 0.025, 0.5))
                    if not warn:
                        self.shooter.shooting = True
                        i = min(self.shooter.ammo, 3)
                        gunimage = self.GAME.gettex(f"{self.t}-gun-{i}", self._image_pos + (3, 5 + 2*i), (3, 2))
                    ggun.d = data["d"] - 90
                    ggun.showmask = [-1, 3][ceil(time() / 0.1) % 2] if warn else -1
                    if last:
                        self.shooter.shooting = False
                elif name == "spawn":
                    faceimage = self.GAME.gettex(f"{self.t}-face-yell", self._image_pos + (0, 4), (2, 1))
                    if first:
                        for i in range(data["n"]):
                            self.GAME.add_go_q(Enemy(data["t"], self.pos + V.dir(360 * (i / data["n"]), 4)))
                elif name == "summon":
                    faceimage = self.GAME.gettex(f"{self.t}-face-yell", self._image_pos + (0, 4), (2, 1))
                    if first:
                        for i in range(data["n"]):
                            pos = (randfloat(-0.5, 0.5), randfloat(-0.5, 0.5)) * self.GAME.GAMESIZE
                            self.GAME.add_go_q(EnemySummoner(data["t"], pos, 2*60))
                elif name == "explode":
                    faceimage = self.GAME.gettex(f"{self.t}-face-yell", self._image_pos + (0, 4), (2, 1))
                    if first:
                        for i in range(data["n"]):
                            self.GAME.add_go_q(Bullet(
                                self,
                                1,
                                self.pos,
                                360 * (i / data["n"]),
                                1,
                                0.5,
                            ))
                    g.showmask = [-1, 3][ceil(time() / 0.1) % 2]
                if last:
                    if "onend" in data:
                        if callable(data["onend"]):
                            data["onend"]()
                    self._data["curattack"] = None
            else:
                if isinstance(self.GAME.PLAYER, Player):
                    self._data["pullattack"]()

            if self._data["stage"] != self._data["nstage"]:
                self._data["stage"] = self._data["nstage"]
                self._data["attackqueue"].clear()
                if self._data["stage"] > 1:
                    hplock = (self.hpmax * (1 - ((self._data["stage"]-1) / 5))) - 1
                    self._data["pushattack"]("stun", {"timer": 3*60, "hplock": hplock})
                if self._data["stage"] == 1:
                    # smash
                    pass
                elif self._data["stage"] == 2:
                    # summon
                    self._data["pushattack"]("smash", {"timer": 1*60, "to": V(0, self.GAME.GAMEH/2 - 16)})
                    self._data["pushattack"]("wait", {"timer": 0.5*60})
                    pass
                elif self._data["stage"] == 3:
                    # smash + laser
                    pass
                elif self._data["stage"] == 4:
                    # explosive smash
                    pass
                elif self._data["stage"] == 5:
                    # gun + spawn
                    pass
            if 5 >= self._data["stage"] > 0:
                self._data["nstage"] = 1 + floor(5 * (1 - (self.hp / self.hpmax)))
                if len(self._data["attackqueue"]) == 0 and isinstance(self.GAME.PLAYER, Player):
                    if self._data["stage"] == 1:
                        # smash
                        self._data["pushattack"]("wait", {"timer": 0.5*60})
                        self._data["pushattack"]("smash", {"timer": 1*60, "to": V(self.GAME.PLAYER.pos)})
                        self._data["pushattack"]("wait", {"timer": 0.5*60})
                    elif self._data["stage"] == 2:
                        # summon
                        n = 0
                        for ID, go in self.GAME.gos.items():
                            if isinstance(go, Enemy):
                                if go is not self:
                                    n += 1
                        if n < 15:
                            self._data["pushattack"]("summon", {"timer": 1*60, "n": 3, "t": "basic"})
                        self._data["pushattack"]("wait", {"timer": 5*60})
                        self._data["pushattack"]("wait", {"timer": 0.5*60})
                    elif self._data["stage"] == 3:
                        # smash + laser
                        self._data["pushattack"]("wait", {"timer": 1*60})
                        self._data["pushattack"]("smash", {"timer": 1*60, "to": V(self.GAME.PLAYER.pos)})
                        self._data["pushattack"]("laser", {"timer": 5*60, "warn": 1*60})
                    elif self._data["stage"] == 4:
                        # explosive smash
                        self._data["pushattack"]("wait", {"timer": 0.5*60})
                        self._data["pushattack"]("smash", {"timer": 1*60, "to": V(self.GAME.PLAYER.pos)})
                        self._data["pushattack"]("explode", {"timer": 0.5*60, "n": 15})
                        self._data["pushattack"]("wait", {"timer": 0.5*60})
                    elif self._data["stage"] == 5:
                        # gun + spawn
                        self._data["pushattack"]("wait", {"timer": 5*60})
                        self._data["pushattack"]("smash", {"timer": 1*60, "to": V(self.GAME.PLAYER.pos)})
                        n = 0
                        for ID, go in self.GAME.gos.items():
                            if isinstance(go, Enemy):
                                if go is not self:
                                    n += 1
                        if n < 6:
                            self._data["pushattack"]("spawn", {"timer": 0.5*60, "n": 3, "t": "basic"})
                        self._data["pushattack"]("gun", {"timer": 4*60, "warn": 1*60})

            i = floor(5 * ((time() / 1) % 1))

            gface.image = faceimage
            gcrown.image = self.GAME.gettex(f"{self.t}-crown-{i}", self._image_pos + (4 + 2*i, 1), (2, 2))
            gskelet.image = self.GAME.gettex(f"{self.t}-skull", self._image_pos + (7, 3), (4, 3))
            gshadow.image = self.GAME.gettex(f"{self.t}-shadow", self._image_pos + (4, 4), (3, 1))
            ggun.image = gunimage

            gface.z = gcrown.z = gskelet.z = self.g.z + 1
            glaser.z = 10 ** 5
            gshadow.z = -(10 ** 10)
            ggun.z = self.g.z + (1 if abs(180-(ggun.d+90)) < 90 else -1)

            g.offset = bodyoffset
            gface.offset = bodyoffset + V(0, 2) + faceoffset
            gcrown.offset = bodyoffset + (0, 14 + round(1 * sin(360*(time()/5))))

            gshadow.alpha = 0.5
            return


class EnemySummoner(Entity):
    def __init__(self, t, pos, duration):
        super().__init__("enemy", pos, 1)

        self.add_handler("update", lambda e: self._update())
        self.add_handler("death", lambda e: self._death())

        self._t = t

        self._duration = 0

        self.duration = duration

        self._timer = 0

    @property
    def t(self):
        return self._t

    @property
    def duration(self):
        return self._duration
    @duration.setter
    def duration(self, v):
        self._duration = max(0, v if is_num(v) else 0)

    @property
    def timer(self):
        return self._timer
    @timer.setter
    def timer(self, v):
        self._timer = min(self.duration, max(0, v if is_num(v) else 0))

    def _death(self):
        self.GAME.explode(self.GAME.add_go_q(Enemy(
            self.t,
            self.pos,
        )).pos, 8, (0.5, 4), 4, (1,))
        self.GAME.add_sound(Sound("explosion3.mp3"))
        self.GAME.CAM.add_shake(4)

    def _update(self):
        self.timer += 1
        self.g.image = self.GAME.gettex("cross-1", (0, 4), (1, 1))
        self.g.alpha = round((self.timer / 30) % 1)
        if self.timer >= self.duration:
            self.hp = 0


class Bullet(Entity):
    def __init__(self, parent, fg, pos, d, damage, speed):
        super().__init__(f"{parent.team}-bullet", pos, 1)

        self.h.size = (4, 4)
        self.h.add_group_collide({"player": "enemy", "enemy": "player"}.get(parent.team, None))

        self.add_handler("add", lambda e: self._config())
        self.add_handler("collideenter", self._collide)
        self.add_handler("wallenter", self._collide_wall)
        self.add_handler("update", lambda e: self._update())
        self.add_handler("death", lambda e: self._death())

        self.parent = parent

        self.d = d
        self.damage = damage

        self._fg = 0
        self._speed = 0

        self.fg = fg
        self.speed = speed

    @property
    def fg(self):
        return self._fg
    @fg.setter
    def fg(self, v):
        v = max(0, v if is_int(v) else 0)
        if self.fg == v:
            return
        self._fg = v
        self._config()

    @property
    def speed(self):
        return self._speed
    @speed.setter
    def speed(self, v):
        self._speed = max(0, v if is_num(v) else 0)

    def _config(self):
        if not isinstance(self.GAME, Game):
            self.g.image = None
            return
        image = self.GAME.gettex("bullet", (14, 12), (4/8, 5/8))
        mask = pg.mask.from_surface(image)
        image = mask.to_surface(setcolor=self.GAME.theme[self.fg], unsetcolor=(0, 0, 0, 0))
        self.g.image = image

    def _collide(self, e):
        go = e.data["go"]
        if not isinstance(go, Entity):
            return
        if self.team is None or go.team is None or self.team != go.team:
            if go.damage <= 0:
                return
            self.dodamage(go, go.damage)
            go.doknockback(self.vel)
            # self.GAME.add_go_q(ParticleText(self.pos, 15, f"-{go.damage}", 3))
            # self._flash = 10
        else:
            pass

    def _collide_wall(self, _):
        self.hp = 0

    def _death(self):
        self.GAME.explode(self.pos, 4, (0.25, 3), 3, (self.fg,))
        # lastdamaged = self.lastdamaged
        # if isinstance(lastdamaged, Entity):
        #     lastdamaged.addscore(self.score)

    def _update(self):
        self.g.d = self.d
        self.vel += V.dir(self.d, self.speed)


class Potion(Entity):
    def __init__(self, pos, duration, powerupduration):
        super().__init__("potion", pos, 1)

        self.h.size = (6, 7)
        self.h.add_group_collide("player")

        self.add_handler("collideenter", self._collide)
        self.add_handler("update", lambda e: self._update())
        self.add_handler("death", lambda e: self._death())

        self.damage = 0

        self._duration = 0
        self._powerupduration = 0
        self._timer = 0

        self.duration = duration
        self.powerupduration = powerupduration

    @property
    def duration(self):
        return self._duration
    @duration.setter
    def duration(self, v):
        self._duration = max(0, v if is_num(v) else 0)

    @property
    def powerupduration(self):
        return self._powerupduration
    @powerupduration.setter
    def powerupduration(self, v):
        self._powerupduration = max(0, v if is_num(v) else 0)

    def _collide(self, e):
        go = e.data["go"]
        if not isinstance(go, Entity):
            return
        if isinstance(go, Player):
            go.powerup = self.powerupduration
            self.hp = 0

    def _death(self):
        self.GAME.explode(self.pos, 8, (0.25, 3), 3, (3,))
        # lastdamaged = self.lastdamaged
        # if isinstance(lastdamaged, Entity):
        #     lastdamaged.addscore(self.score)

    def _update(self):
        self.g.image = self.GAME.gettex("potion", (15, 12), (1, 1))
        self._timer += 1
        if self._timer % 15 == 0:
            image = pg.Surface((3, 3)).convert_alpha()
            image.fill(self.GAME.theme[3])
            go = self.GAME.add_go_q(ParticleImage(
                self.pos,
                60,
                image,
            ))
            go.vel += V.dir(randint(0, 360), 0.1)
            go.updatefunc = lambda _go, _t: (
                _go.conf(vel=_go.vel+V.dir(V().toward(_go.vel), 0.05*(1-_t))),
                _go.g.conf(alpha=1-_t),
            )
        self.g.showmask = -1
        if self._timer > self.duration-2.5*60:
            self.g.showmask = [-1, 3][round((self._timer / 15) % 1)]
        if self._timer > self.duration:
            self.hp = 0


class ParticleImage(Particle):
    def __init__(self, pos, duration, image, **kw):
        super().__init__(pos, 0, duration, **kw)

        self.g.image = image


class ParticleText(ParticleImage):
    def __init__(self, pos, duration, text, fg, bg=-1, space=1, size=1):
        super().__init__(
            pos, duration, None,
            initfunc=lambda _: self._this_init(), updatefunc=lambda _, t: self._this_update(t),
            timefunc=lambda _, t: self._easeio(t),
        )

        self._text = ""
        self._fg = -1
        self._bg = -1
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
        v = max(0, v if is_num(v) else 1)
        if self.size == v:
            return
        self._size = v
        self._config()

    def _easeio(self, t):
        if t < 0.5:
            return Particle.easeout(None, t/0.5)
        return 1

    def _config(self):
        if not isinstance(self.GAME, Game):
            self.g.image = None
            return
        self.g.image = self.GAME.text(self.text, fg=self.fg, bg=self.bg, space=self.space, size=self.size)

    def _this_init(self):
        self._config()

    def _this_update(self, t):
        self.g.oy = 8*t


class ParticleBoom(ParticleImage):
    def __init__(self, pos, rad, boomtime, waittime):
        super().__init__(
            pos, 0, None,
            updatefunc=lambda _, t: self._this_update(t*self.duration),
        )

        self.g = CircleNode(self, -1, 0)

        self._rad = 0
        self._boomtime = 0
        self._waittime = 0

        self.rad = rad
        self.boomtime = boomtime
        self.waittime = waittime

    @property
    def boomtime(self):
        return self._boomtime
    @boomtime.setter
    def boomtime(self, v):
        self._boomtime = max(0, v if is_num(v) else 0)
        self.duration = self.waittime + self.boomtime
    @property
    def waittime(self):
        return self._waittime
    @waittime.setter
    def waittime(self, v):
        self._waittime = max(0, v if is_num(v) else 0)
        self.duration = self.waittime + self.boomtime

    @property
    def rad(self):
        return self._rad
    @rad.setter
    def rad(self, v):
        self._rad = max(0, v if is_num(v) else 0)

    def _this_update(self, t):
        if t < self.waittime:
            self.g.enabled = False
            return
        t -= self.waittime
        t /= self.boomtime
        self.g.enabled = True
        self.g.rad = self.rad * Particle.easeout(None, t)
        self.g.fg = [0, 3][ceil(time() / 0.1) % 2]


class Game(BaseGame):
    def __init__(self):
        super().__init__("Blob Blast", V(200 + 16, 120 + 16) * 1)

        icon = self.gettex("icon", (8, 5), (1, 2))
        icon = pg.transform.scale(icon, (V(icon.get_size()) * 10).ceil().xy)
        icon2 = pg.Surface((V(max(icon.get_size())) + 30).xy).convert_alpha()
        icon2.fill((0, 0, 0, 0))
        icon2.blit(icon, ((V(icon2.get_size()) - V(icon.get_size())) / 2).xy)
        pg.display.set_icon(icon2)

        widths_small = {
            "DEFAULT": 3,
            "HEIGHT": 3,
            "i": 1, "l": 2, "m": 5, "n": 4, "w": 5,
            "!": 1, "[": 2, "]": 2, ";": 1, ":": 1, "'": 1, ",": 1, ".": 1, "?": 2, " ": 2,
        }
        widths_medium = widths_small.copy()
        widths_medium["HEIGHT"] = 5
        widths_large = {
            "DEFAULT": 4,
            "HEIGHT": 8,
            "i": 2, "m": 6, "n": 5, "w": 6,
            "!": 2, "+": 5, "[": 3, "]": 3, ";": 2, ":": 2, "'": 2, "\"": 5, ",": 2, ".": 2, " ": 3,
        }
        widths = [widths_small, widths_medium, widths_large]
        chars = "abcdefghijklmnopqrstuvwxyz0123456789!-_=+[];:'\",<.>/?§ "
        for size, width in enumerate(widths):
            self._chars.append([])
            for theme in self.theme:
                self._chars[-1].append({})
                x = 0
                for c in chars:
                    w = width.get(c, width["DEFAULT"])
                    tex = self.gettex(f"§{c}-{size}", V(7, 0+size) + (x/8, 0), V(w, width["HEIGHT"]+1)/8, clip=False)
                    mask = pg.mask.from_surface(tex.copy())
                    tex = mask.to_surface(setcolor=theme, unsetcolor=(0, 0, 0, 0))
                    self._chars[-1][-1][c] = tex
                    x += w + 1
        for i, icon in enumerate(["camera", "box", "cross", "volume", "expand", "minimize"]):
            tex = self.gettex(f"§{icon}-base", (0, 1+i), (1, 1))
            mask = pg.mask.from_surface(tex.copy())
            for j, theme in enumerate(self.theme):
                tex = mask.to_surface(setcolor=theme, unsetcolor=(0, 0, 0, 0))
                self.texturescache[f"{icon}-{j}"] = tex

        self.volume = 1

        self._GAMESIZE = V()
        self.GAMESIZE = V(self.surf.get_size()) - 32

        self._PLAYER = None
        self._playerautofire = False

        self._gamestate = {
            "spawntime": 0,
            "highscore": 0,
            "score": 0,
            "potionspawntime": 0,
            "potion": None,
            "bossscoreper": 300,
            "bossscore": 0,
            "notiftime": 0,
            "notif": "",
            "difficulty": 1,
        }

        INTRO = self.gettex("intro", (27, 4), (2, 4), clip=False)
        INTROANIM = [self.gettex(f"introanim-{i}", (27 + 2*(i+1), 4), (2, 4), clip=False) for i in range(12)]
        INTROANIM.append(None)
        self.add_go(UIObject(
            "intro",
            self.ssize/2,
            INTRO,
            name="intro",
        ))
        ui = self.add_go(UIObject(
            "intro",
            self.ssize/2,
            None,
            name="introanim",
        ))
        ui.add_handler(
            "update",
            bind(
                lambda _ui, _t: None if not _ui.curmode else (
                    (
                        self.conf(mode="title"),
                    ) if time() - _t > 2 else (
                        _ui.g.conf(image=INTROANIM[round((len(INTROANIM)-1) * min(1, (time() - _t) / 1))]),
                    )
                ),
                (ui, time()),
            ),
        )

        OK = self.gettex("ok", (2, 6), (3, 1))
        OKh = self.gettex("okh", (2, 7), (3, 1))
        totalheight = sum([
            5, 3,
            5, 1, 5, 3,
            max([OK.get_height(), OKh.get_height()]),
        ])
        y = (self.sh - totalheight) / 2
        ui = self.add_go(UIText(
            "warning",
            (self.sw/2, y),
            "WARNING",
            3,
            aligny=-1,
            name="title",
        ))
        y += ui.g.image.get_height() + 3
        ui = self.add_go(UIText(
            "warning",
            (self.sw/2, y),
            "Running on Repl can be extremely laggy",
            2,
            aligny=-1,
            name="desc1",
        ))
        y += ui.g.image.get_height() + 1
        ui = self.add_go(UIText(
            "warning",
            (self.sw/2, y),
            "Running on your own device is often faster",
            2,
            aligny=-1,
            name="desc2",
        ))
        y += ui.g.image.get_height() + 3
        ui = self.add_go(UIButton(
            "warning",
            (self.sw/2, y),
            OK,
            OKh,
            aligny=-1,
            name="ok",
        ))
        ui.add_handler("mouseup", lambda e: self.conf(mode="title"))
        FILL = pg.Surface(self.ssize.xy).convert_alpha()
        FILL.fill(self.theme[0])
        for mode in ("intro", "warning"):
            ui = self.add_go(UIObject(
                mode,
                self.ssize / 2,
                FILL,
                name="fill",
            ))
            ui.g.z -= 1

        LOGO = self.gettex("logo", (2, 1), (5, 3))
        PLAY = self.gettex("play", (2, 4), (3, 1))
        PLAYh = self.gettex("playh", (2, 5), (3, 1))
        OPTIONS = self.gettex("options", (2, 8), (5, 1))
        OPTIONSh = self.gettex("optionsh", (2, 9), (5, 1))
        QUIT_ = self.gettex("quit", (5, 6), (3, 1))
        QUITh = self.gettex("quith", (5, 7), (3, 1))
        # RADIO1 = self.gettex("radio1", (10, 8), (4/8, 4/8))
        # RADIO2 = self.gettex("radio2", (10 + 4/8, 8), (4/8, 4/8))
        # RADIO3 = self.gettex("radio3", (10, 8 + 4/8), (4/8, 4/8))
        totalheight = sum([
            LOGO.get_height(), 3,
            3, 1, 5, 4,
            max(PLAY.get_height(), PLAYh.get_height()), 1,
            max(OPTIONS.get_height(), OPTIONSh.get_height()), 1,
            max(QUIT_.get_height(), QUITh.get_height()),
        ])
        y = (self.sh - totalheight) / 2
        ui = self.add_go(UIObject(
            "title",
            (self.sw/2, y),
            LOGO,
            aligny=-1,
            name="logo",
        ))
        ui.add_handler(
            "update",
            bind(
                lambda _ui, _pos: None if not _ui.curmode else _ui.conf(
                    pos=_pos + (0, round(1 * sin(360*(time()/5)))),
                ),
                (ui, ui.pos),
            ),
        )
        y += LOGO.get_height() + 3
        ui = self.add_go(UIText(
            "title",
            (self.sw/2, y),
            "HighScore:",
            1,
            size=0,
            aligny=-1,
            name="highscore",
        ))
        y += ui.g.image.get_height() + 1
        ui = self.add_go(UIText(
            "title",
            (self.sw/2, y),
            "0",
            3,
            aligny=-1,
            name="highscore#",
        ))
        ui.add_handler(
            "update",
            bind(
                lambda _ui, _data: None if not _ui.curmode else (
                    (
                        updatedict(_data, {"score": 0}),
                    ) if self.mode != _ui.mode else (
                        updatedict(_data, {"score": lerp(_data.get("score", 0), self._gamestate["highscore"], 0.25)}),
                        _ui.conf(text=round(_data.get("score", 0))),
                    )),
                (ui, {}),
            ),
        )
        y += ui.g.image.get_height() + 4
        ui = self.add_go(UIButton(
            "title",
            (self.sw/2, y),
            PLAY,
            PLAYh,
            aligny=-1,
            name="play",
        ))
        ui.add_handler("mouseup", lambda e: self.conf(mode="game"))
        y += ui.g.image.get_height() + 1
        ui = self.add_go(UIButton(
            "title",
            (self.sw/2, y),
            OPTIONS,
            OPTIONSh,
            aligny=-1,
            name="options",
        ))
        ui.add_handler("mouseup", lambda e: self.conf(mode="options"))
        y += ui.g.image.get_height() + 1
        ui = self.add_go(UIButton(
            "title",
            (self.sw/2, y),
            QUIT_,
            QUITh,
            aligny=-1,
            name="quit",
        ))
        ui.add_handler("mouseup", lambda e: pg.event.post(pg.event.Event(QUIT)))
        y = self.sh - (self.sh - self.GAMEH)/2 - 2
        for i, T in enumerate(reversed(["You're too tired to move", "Maybe use your rocket launcher?"])):
            ui = self.add_go(UIText(
                "title",
                (self.sw/2, y),
                T,
                1,
                size=0,
                aligny=1,
                name=f"desc{2-i}",
            ))
            y -= ui.g.image.get_height() + 1

        HOME = self.gettex("home", (5, 4), (3, 1))
        HOMEh = self.gettex("homeh", (5, 5), (3, 1))
        VOL = self.gettex("volume-0")
        VOLB1 = self.gettex("volb1", (18, 4), (1/8, 1))
        VOLB2 = self.gettex("volb2", (18 + 2/8, 4), (1/8, 1))
        y = (self.sh - self.GAMEH)/2 + 2
        ui = self.add_go(UIText(
            "options",
            (self.sw/2, y),
            "OPTIONS",
            0,
            aligny=-1,
            name="title",
        ))
        y += ui.g.image.get_height() + 4
        ui = self.add_go(UIText(
            "options",
            ((self.sh - self.GAMEH)/2 + 4, y),
            "CONTROLS",
            1,
            size=0,
            alignx=1,
            aligny=-1,
            name="controls",
        ))
        y += ui.g.image.get_height() + 2
        w = 0
        CONTROLS = [
            ("CLICK / SPACE", "shoot"),
            ("E", "autofire"),
            ("P", "pause / play"),
        ]
        yt = y
        for i, (key, _) in enumerate(CONTROLS):
            ui = self.add_go(UIText(
                "options",
                ((self.sh - self.GAMEH)/2 + 6, yt),
                f"[{key}]",
                1,
                alignx=1,
                aligny=-1,
                name=f"key{i+1}",
            ))
            ui.g.alpha = 0.75
            yt += ui.g.image.get_height() + 2
            w = max(w, ui.g.image.get_width())
        yt = y
        for i, _ in enumerate(CONTROLS):
            ui = self.add_go(UIText(
                "options",
                ((self.sh - self.GAMEH)/2 + 6 + w + 4, yt),
                "-",
                1,
                alignx=1,
                aligny=-1,
                name=f"dash{i+1}"
            ))
            ui.g.alpha = 0.75
            yt += ui.g.image.get_height() + 2
        yt = y
        for i, (_, action) in enumerate(CONTROLS):
            ui = self.add_go(UIText(
                "options",
                ((self.sh - self.GAMEH)/2 + 6 + w + 4 + 3 + 4, yt),
                action,
                1,
                alignx=1,
                aligny=-1,
                name=f"action{i+1}",
            ))
            ui.g.alpha = 0.75
            yt += ui.g.image.get_height() + 2
        y = yt
        y += 6
        ui = self.add_go(UIText(
            "options",
            ((self.sh - self.GAMEH)/2 + 4, y),
            "VOLUME",
            1,
            size=0,
            alignx=1,
            aligny=-1,
            name="volume",
        ))
        y += ui.g.image.get_height() + 2
        x = (self.sh - self.GAMEH)/2 + 6
        ui = self.add_go(UITextButton(
            "options",
            (x, y + 3),
            "+",
            fg=0, fgh=3,
            alignx=1,
            name="volincrease",
        ))
        ui.add_handler("mouseup", lambda e: self.conf(volume=self.volume+0.05))
        x += ui.g.image.get_width() + 2
        ui = self.add_go(UIObject(
            "options",
            (x, y + 3),
            VOL,
            alignx=1,
            name="voltoggle",
        ))
        ui.add_handler(
            "mouseup",
            bind(
                lambda _ui: self.conf(volume=1-self.volume if self.volume in (0, 1) else 0),
                (ui,),
            ),
        )
        x += ui.g.image.get_width() + 2
        for i in range(20):
            ui = self.add_go(UIObject(
                "options",
                (x, y + 3),
                VOLB1,
                alignx=1,
                name=f"volbar{i+1}",
            ))
            ui.add_handler(
                "update",
                bind(
                    lambda _ui, _i, _VOLB1, _VOLB2: None if not _ui.curmode else _ui.g.conf(image=_VOLB1 if _i < round(self.volume*20) else _VOLB2),
                    (ui, i, VOLB1, VOLB2),
                ),
            )
            ui.add_handler(
                "mouseup",
                bind(
                    lambda _ui, _i: self.conf(volume=(_i+1)/20),
                    (ui, i),
                ),
            )
            x += ui.g.image.get_width() + 1
        x += 1
        ui = self.add_go(UITextButton(
            "options",
            (x, y + 3),
            "-",
            fg=0, fgh=3,
            alignx=1,
            name="voldecrease",
        ))
        ui.add_handler("mouseup", lambda e: self.conf(volume=self.volume-0.05))
        y += VOL.get_height()
        y += 6
        ui = self.add_go(UIText(
            "options",
            ((self.sh - self.GAMEH) / 2 + 4, y),
            "THEME",
            1,
            size=0,
            alignx=1,
            aligny=-1,
            name="theme",
        ))
        y += ui.g.image.get_height() + 2
        x = (self.sh - self.GAMEH)/2 + 6
        for i in range(4):
            image = pg.Surface((6, 6)).convert_alpha()
            imageh = image.copy()
            imageh.fill(self.theme[3])
            for j in range(4):
                c = self.themetex.get_at((j*2, i))
                c = pg.Color(min(255, c.r+1), min(255, c.g+1), min(255, c.b+1))
                image.fill(c, ((1+j, 1), (1, 4)))
                imageh.fill(c, ((1+j, 1), (1, 4)))
            ui = self.add_go(UIButton(
                "options",
                (x, y),
                image,
                imageh,
                alignx=1,
                aligny=-1,
                name=f"theme{i+1}",
            ))
            ui.add_handler(
                "mouseup",
                bind(
                    lambda _i: self.set_theme(_i),
                    (i,),
                ),
            )
            x += ui.g.image.get_width()
        ui = self.add_go(UIButton(
            "options",
            (self.sw/2, self.sh - (self.sh - self.GAMEH)/2 - 2),
            HOME,
            HOMEh,
            aligny=1,
            name="home",
        ))
        ui.add_handler("mouseup", lambda e: self.conf(mode="title"))

        HP = self.gettex("hp", (8, 4), (2, 1))
        AMMO1 = self.gettex("ammo1", (8, 7), (4/8, 5/8))
        AMMO2 = self.gettex("ammo2", (8 + 5/8, 7), (4/8, 5/8))
        NOTIFS = {
            "AUTOFIREON": self.gettex("autofireon", (12, 4), (6, 1)),
            "AUTOFIREOFF": self.gettex("autofireoff", (12, 5), (6, 1)),
        }
        self.add_go(UIObject(
            "game",
            (self.ssize - self.GAMESIZE)/2 - 6,
            HP,
            alignx=1,
            aligny=-1,
            name="hpicon",
        ))
        ui = self.add_go(UIBar(
            "game",
            ((self.ssize - self.GAMESIZE)/2 - 6) + (HP.get_width()+1, 0),
            (24, HP.get_height()-2),
            0, 1, 2, 3,
            alignx=1,
            aligny=-1,
            name="hpbar",
        ))
        ui.add_handler(
            "update",
            bind(
                lambda _ui: None if not _ui.curmode else _ui.conf(p=self.PLAYER.hp/self.PLAYER.hpmax if isinstance(self.PLAYER, Player) else 0),
                (ui,),
            ),
        )
        ui = self.add_go(UIBar(
            "game",
            ((self.ssize - self.GAMESIZE)/2 - 6) + (0, 13),
            (3*8, 4),
            0, 1, 2, 2,
            alignx=1,
            aligny=-1,
            name="powerupbar",
        ))
        ui.add_handler(
            "update",
            bind(
                lambda _ui: None if not _ui.curmode else (
                    _ui.conf(
                        p=self.PLAYER.powerup/self.PLAYER.powerupmax if isinstance(self.PLAYER, Player) and self.PLAYER.powerupmax > 0 else 0,
                        fg=[0, 3][ceil(time() / 0.1) % 2], fgf=[0, 3][ceil(time() / 0.1) % 2],
                    ),
                    _ui.g.conf(
                        show=_ui.p > 0,
                    ),
                ),
                (ui,),
            ),
        )
        for i in range(10):
            ui = self.add_go(UIObject(
                "game",
                ((self.ssize - self.GAMESIZE)/2 - 6) + (
                    (i * (max(AMMO1.get_width(), AMMO2.get_width())+1)),
                    HP.get_height() + 1,
                ),
                None,
                alignx=1,
                aligny=-1,
                name=f"ammo{i+1}",
            ))
            ui.add_handler(
                "update",
                bind(
                    lambda _ui, _i, _AMMO1, _AMMO2: None if not _ui.curmode else _ui.g.conf(
                        image=_AMMO1 if isinstance(self.PLAYER, Player) and _i < self.PLAYER.shooter.ammo else _AMMO2,
                    ),
                    (ui, i, AMMO1, AMMO2),
                ),
            )
        ui = self.add_go(UIObject(
            "game",
            (self.sw/2, (self.sh - self.GAMEH)/2 - 6),
            None,
            aligny=-1,
            name="notif",
        ))
        ui.add_handler(
            "update",
            bind(
                lambda _ui, _NOTIFS: None if not _ui.curmode else _ui.g.conf(
                    image=_NOTIFS.get(self._gamestate["notif"], None) if self._gamestate["notiftime"] > 0 else None,
                ),
                (ui, NOTIFS),
            ),
        )
        ui = self.add_go(UIText(
            "game",
            (self.sw - ((self.sh - self.GAMEH)/2 - 6), (self.sh - self.GAMEH)/2 - 6),
            "0",
            3,
            alignx=-1,
            aligny=-1,
            name="score#",
        ))
        ui.add_handler(
            "update",
            bind(
                lambda _ui, _data: None if not _ui.curmode else (
                    (
                        updatedict(_data, {"score": 0}),
                    ) if self.mode != _ui.mode else (
                        updatedict(_data, {"score": lerp(_data.get("score", 0), self._gamestate["score"], 0.25)}),
                        _ui.conf(text=round(_data.get("score", 0))),
                    )),
                (ui, {}),
            ),
        )
        ui = self.add_go(UIBar(
            "game",
            (self.sw/2, self.sh - (self.sh - self.GAMEH)/2 + 8),
            (128, HP.get_height()),
            0, 1, 2, 3,
            aligny=1,
            name="bossbar",
        ))
        for i in range(1, 5):
            ui.add_marker(i / 5)
        ui.add_handler(
            "update",
            bind(
                lambda _ui: (
                    _ui.g.conf(show=False),
                ) if not isinstance(self.BOSS, Enemy) else (
                    _ui.conf(p=self.BOSS.hp / self.BOSS.hpmax),
                    _ui.g.conf(show=True),
                ),
                (ui,),
            ),
        )
        ui = self.add_go(UIText(
            "game",
            (self.sw/2 - 1, ui.y - (HP.get_height()+2)/2),
            "BLOB KING",
            3,
            name="bossbartext",
        ))
        ui.add_handler(
            "update",
            bind(
                lambda _ui: _ui.g.conf(show=isinstance(self.BOSS, Enemy)),
                (ui,),
            ),
        )

        PAUSE = self.gettex("pause", (19, 4), (2, 2))
        totalheight = sum([
            PAUSE.get_height(), 3,
            5, 3,
            max(PLAY.get_height(), PLAYh.get_height()), 1,
            max(QUIT_.get_height(), QUITh.get_height()),
        ])
        y = (self.sh - totalheight) / 2
        ui = self.add_go(UIObject(
            "pause",
            (self.sw/2, y),
            PAUSE,
            aligny=-1,
            name="logo",
        ))
        ui.add_handler("mouseup", lambda e: self.conf(mode="game"))
        y += ui.g.image.get_height() + 3
        ui = self.add_go(UIText(
            "pause",
            (self.sw/2, y),
            "Paused",
            1,
            aligny=-1,
            name="title",
        ))
        y += ui.g.image.get_height() + 3
        ui = self.add_go(UIButton(
            "pause",
            (self.sw/2, y),
            PLAY,
            PLAYh,
            aligny=-1,
            name="play",
        ))
        ui.add_handler("mouseup", lambda e: self.conf(mode="game"))
        y += ui.g.image.get_height() + 1
        ui = self.add_go(UIButton(
            "pause",
            (self.sw/2, y),
            QUIT_,
            QUITh,
            aligny=-1,
            name="quit",
        ))
        ui.add_handler("mouseup", lambda e: (
            self.PLAYER.conf(hp=0) if isinstance(self.PLAYER, Player) else None,
            self.conf(mode="game"),
        ))

        CROWN = self.gettex("crown", (10, 6), (2, 2))
        SKULL = self.gettex("skull", (10, 4), (2, 2))
        totalheight = sum([
            max(CROWN.get_height(), SKULL.get_height()), 3,
            5, 3,
            3, 1, 5, 4,
            max(HOME.get_height(), HOMEh.get_height()),
        ])
        y = (self.sh - totalheight) / 2
        ui1 = self.add_go(UIObject(
            "finish-w",
            (self.sw/2, y),
            CROWN,
            aligny=-1,
            name="logo",
        ))
        ui1.add_handler(
            "update",
            bind(
                lambda _ui, _pos: None if not _ui.curmode else _ui.conf(
                    pos=_pos + (0, round(1 * sin(360*(time()/5)))),
                ),
                (ui1, ui1.pos),
            ),
        )
        ui2 = self.add_go(UIObject(
            "finish-l",
            (self.sw / 2, y),
            SKULL,
            aligny=-1,
            name="logo",
        ))
        ui2.add_handler(
            "update",
            bind(
                lambda _ui, _pos: None if not _ui.curmode else _ui.conf(
                    pos=_pos + (0, round(1 * sin(360 * (time() / 5)))),
                ),
                (ui2, ui2.pos),
            ),
        )
        y += max(ui1.g.image.get_height(), ui2.g.image.get_height()) + 3
        ui1 = self.add_go(UIText(
            "finish-w",
            (self.sw / 2, y),
            "You Won!",
            0,
            aligny=-1,
            name="title",
        ))
        ui2 = self.add_go(UIText(
            "finish-l",
            (self.sw/2, y),
            "You Died!",
            0,
            aligny=-1,
            name="title",
        ))
        y += max(ui1.g.image.get_height(), ui2.g.image.get_height()) + 3
        ui1 = self.add_go(UIText(
            "finish-w",
            (self.sw / 2, y),
            "Score:",
            1,
            size=0,
            aligny=-1,
            name="score",
        ))
        ui2 = self.add_go(UIText(
            "finish-l",
            (self.sw/2, y),
            "Score:",
            1,
            size=0,
            aligny=-1,
            name="score",
        ))
        y += max(ui1.g.image.get_height(), ui2.g.image.get_height()) + 1
        ui1 = self.add_go(UIText(
            "finish-w",
            (self.sw/2, y),
            "0",
            3,
            aligny=-1,
            name="score#",
        ))
        ui1.add_handler(
            "update",
            bind(
                lambda _ui, _data: None if not _ui.curmode else (
                    (
                        updatedict(_data, {"score": 0}),
                    ) if self.mode != _ui.mode else (
                        updatedict(_data, {"score": lerp(_data.get("score", 0), self._gamestate["score"], 0.25)}),
                        _ui.conf(text=round(_data.get("score", 0))),
                    )),
                (ui1, {}),
            ),
        )
        ui2 = self.add_go(UIText(
            "finish-l",
            (self.sw / 2, y),
            "0",
            3,
            aligny=-1,
            name="score#",
        ))
        ui2.add_handler(
            "update",
            bind(
                lambda _ui, _data: None if not _ui.curmode else (
                    (
                        updatedict(_data, {"score": 0}),
                    ) if self.mode != _ui.mode else (
                        updatedict(_data, {"score": lerp(_data.get("score", 0), self._gamestate["score"], 0.25)}),
                        _ui.conf(text=round(_data.get("score", 0))),
                    )),
                (ui2, {}),
            ),
        )
        y += max(ui1.g.image.get_height(), ui2.g.image.get_height()) + 4
        ui1 = self.add_go(UIButton(
            "finish-w",
            (self.sw/2, y),
            HOME,
            HOMEh,
            aligny=-1,
            name="home",
        ))
        ui1.add_handler("mouseup", lambda e: self.conf(mode="title"))
        ui2 = self.add_go(UIButton(
            "finish-l",
            (self.sw/2, y),
            HOME,
            HOMEh,
            aligny=-1,
            name="home",
        ))
        ui2.add_handler("mouseup", lambda e: self.conf(mode="title"))

        BORDER1 = pg.Surface((self.GAMESIZE + 4).xy).convert_alpha()
        BORDER1.fill(self.theme[1])
        BORDER2 = pg.Surface((self.GAMESIZE + 0).xy).convert_alpha()
        BORDER2.fill(self.theme[2])
        ui = self.add_go(UIObject(
            "*all",
            (0, 0),
            BORDER1,
            name="border1",
        ))
        ui.g.z = -(10 ** 10) - 2
        ui.g.cam = True
        ui = self.add_go(UIObject(
            "*all",
            (0, 0),
            BORDER2,
            name="border2",
        ))
        ui.g.z = -(10 ** 10) - 1
        ui.g.cam = True
        CROSS = self.gettex("cross-3", (0, 3), (1, 1))
        ui = self.add_go(UIObject(
            "game",
            (0, 0),
            CROSS,
            name="cross",
        ))
        ui.add_handler(
            "update",
            bind(
                lambda _ui: None if not _ui.curmode else _ui.conf(pos=self.mouse),
                (ui,),
            ),
        )
        for mode in ("title", "options", "pause", "finish-w", "finish-l"):
            ui = self.add_go(UIObject(
                mode,
                self.ssize/2,
                BORDER2,
                name="bg",
            ))
            ui.g.alpha = 0.5
            ui.g.z -= 1

        self.mode = "warning" if "REPL_OWNER" in os.environ else "intro"

    def _lm_mode(self, m, lm):
        pass
    def _m_mode(self, m, lm):
        if m not in ("game", "pause", "finish-w", "finish-l"):
            self.PLAYER = None
            for ID, go in self._gos.items():
                if isinstance(go, Entity):
                    go.dodamage(None, go.hpmax)
        if m == "title":
            return
        if m == "game":
            if lm == "pause":
                return
            self._playerautofire = False
            self.PLAYER = None
            for ID, go in self._gos.items():
                if isinstance(go, Entity):
                    go.dodamage(None, go.hpmax)
            self.PLAYER = Player(0)
            updatedict(self._gamestate, {
                "spawntime": 3*60,
                "potionspawntime": 0,
                "potion": None,
                "bossscore": self._gamestate["bossscoreper"],
            })
            return
        if m == "finish-w":
            return
        if m == "finish-l":
            self.add_sound(Sound("defeat.mp3"))
            return

    @property
    def GAMESIZE(self):
        return self._GAMESIZE
    @GAMESIZE.setter
    def GAMESIZE(self, v):
        self._GAMESIZE = V(v)
        self._config_gamesize()
    @property
    def GAMEW(self):
        return self.GAMESIZE.x
    @GAMEW.setter
    def GAMEW(self, v):
        self.GAMESIZE.x = v
        self._config_gamesize()
    @property
    def GAMEH(self):
        return self.GAMESIZE.y
    @GAMEH.setter
    def GAMEH(self, v):
        self.GAMESIZE.y = v
        self._config_gamesize()

    def _config_gamesize(self):
        pad = 16
        rects = [
            (
                (-self.GAMEW/2 - pad, -self.GAMEH/2 - pad),
                (self.GAMEW + 2*pad, pad),
            ),
            (
                (-self.GAMEW/2 - pad, self.GAMEH/2),
                (self.GAMEW + 2*pad, pad),
            ),
            (
                (-self.GAMEW/2 - pad, -self.GAMEH/2 - pad),
                (pad, self.GAMEH + 2*pad),
            ),
            (
                (self.GAMEW/2, -self.GAMEH/2 - pad),
                (pad, self.GAMEH + 2*pad),
            ),
        ]
        for i in range(4):
            self.set_wall(rects[i], f"border{'nsew'[i]}")

    @property
    def PLAYER(self):
        return self._PLAYER
    @PLAYER.setter
    def PLAYER(self, v):
        self.rem_go(self.PLAYER)
        self._PLAYER = self.add_go(v)

    @property
    def BOSS(self):
        for ID, go in self._gos.items():
            if isinstance(go, Enemy):
                if go.t == "boss":
                    return go
        return None

    @property
    def playershooting(self):
        return self.mousedown or pg.key.get_pressed()[K_SPACE] or self._playerautofire

    def explode(self, pos, n, mags, size, themes, doff=45):
        for d in range(n):
            image = pg.Surface(V(size).ceil().xy).convert_alpha()
            image.fill(self.theme[choice(themes)])
            go = self.add_go_q(ParticleImage(pos, 30, image))
            go.updatefunc = lambda _go, _t: _go.g.conf(alpha=1-_t)
            go.vel = V.dir(doff + (360/n)*d, randfloat(*mags))
    def boom(self, pos, n, size, wait=0):
        self.CAM.add_shake(size * 0.5)
        for i in range(n):
            p = i / (n-1) if n > 0 else 1
            self.add_go_q(ParticleBoom(pos + V.dir(randint(0, 360), size * (1-p)), size * lerp(0.5, 1, p), 10, wait+randint(0, 15)))

    def _update(self, events):
        if self._gamestate["notiftime"] > 0:
            self._gamestate["notiftime"] -= 1
        for ID, go in self._gos.items():
            if isinstance(go, UIObject):
                go.g.set_show("mode", self._mode_alpha.get(go.mode, 0) > 0)
                go.g.set_alpha("mode", self._mode_alpha.get(go.mode, 0) / 10)
            if isinstance(go, Entity):
                go.frozen = self.mode == "pause"
        if self.mode == "game":
            if isinstance(self.PLAYER, Player):
                if self.keydown.get(K_e, False):
                    self._playerautofire = not self._playerautofire
                    self._gamestate["notiftime"] = 2 * 60
                    self._gamestate["notif"] = f"AUTOFIRE{['OFF', 'ON'][int(self._playerautofire)]}"
                if self.keydown.get(K_p, False):
                    self.mode = "pause"
                self._gamestate["score"] = self.PLAYER.score
                self._gamestate["highscore"] = max(self._gamestate["highscore"], self._gamestate["score"])
                if self._gamestate["spawntime"] > 0:
                    self._gamestate["spawntime"] -= 1
                else:
                    self._gamestate["spawntime"] = randint(2*60, 5*60)
                    pos = None
                    while pos is None or self.PLAYER.pos.dist(pos) < 32:
                        pos = self.GAMESIZE * (randfloat(-0.5, 0.5), randfloat(-0.5, 0.5))
                    enemies = []
                    nenemies = {}
                    for ID, go in self._gos.items():
                        if isinstance(go, Enemy):
                            nenemies[go.t] = nenemies.get(go.t, 0) + 1
                    nenemiestotal = sum(nenemies.values())
                    for name, data in ENEMIES.items():
                        if nenemies.get(name, 0) < data.get("limit", 0):
                            enemies.extend([name] * data.get("chance", 0))
                    if not isinstance(self.BOSS, Enemy):
                        if self.PLAYER.score >= self._gamestate["bossscore"]:
                            self._gamestate["spawntime"] = 10*60
                            for ID, go in self._gos.items():
                                if isinstance(go, Enemy):
                                    go.dodamage(None, go.hpmax)
                            self.add_go_q(EnemySummoner("boss", 0, 4*60))
                            self._gamestate["bossscore"] += ENEMIES["boss"].get("score", 0) + self._gamestate["bossscoreper"]
                            go = self.add_go_q(ParticleImage(0, 2*60, self.gettex("bossfight", (12, 6), (4, 3))))
                            go.updatefunc = lambda _go, _t: (
                                _go.conf(
                                    pos=V(0, self.sh/2) * (0 if abs(_t-0.5) < 0.25 else (
                                        1-Particle.easeout(None, _t/0.25) if _t < 0.5 else Particle.easeout(None, (1-_t)/0.25)-1
                                    )),
                                ),
                                _go.g.conf(
                                    alpha=1 if abs(_t-0.5) < 0.25 else (
                                        Particle.easeout(None, _t/0.25) if _t < 0.5 else Particle.easeout(None, (1-_t)/0.25)
                                    ),
                                ),
                            )
                        else:
                            if nenemiestotal < 25 and len(enemies) > 0:
                                self.add_go_q(EnemySummoner(choice(enemies), pos, 2*60))
                potion = self._gamestate["potion"]
                if isinstance(potion, Potion):
                    if potion.hp <= 0:
                        self._gamestate["potion"] = None
                if self._gamestate["potionspawntime"] > 0:
                    self._gamestate["potionspawntime"] -= 1
                else:
                    self._gamestate["potionspawntime"] = 25*60
                    if not isinstance(self._gamestate["potion"], Potion):
                        if self.PLAYER.hp / self.PLAYER.hpmax <= (0.5 if isinstance(self.BOSS, Enemy) else 0.25):
                            pos = None
                            while pos is None or self.PLAYER.pos.dist(pos) < 64:
                                pos = self.GAMESIZE * (randfloat(-0.5, 0.5), randfloat(-0.5, 0.5))
                            self._gamestate["potion"] = self.add_go(Potion(pos, 10*60, 7.5*60))
                if self.PLAYER.hp <= 0:
                    self.PLAYER = None
            else:
                self.mode = "finish-l"
        elif self.mode == "pause":
            if self.keydown.get(K_p, False):
                self.mode = "game"


def main():
    global ENEMIES
    try:
        with open(os.path.join(MAIN, "enemies.json"), "r") as file:
            text = file.read()
        ENEMIES = json.loads(text)
    except:
        pass
    ENEMIES = ENEMIES if is_dict(ENEMIES) else {}

    pg.display.set_mode((V(200 + 16, 120 + 16) * 3).ceil().xy, RESIZABLE)

    clock = pg.time.Clock()

    RUN = True

    game = Game()

    t0 = time()

    while RUN:
        t1 = time()

        t = t1 - t0

        scr = pg.display.get_surface()

        scale = min(*(V(scr.get_size()) / V(game.surf.get_size())).xy)
        size = (V(game.surf.get_size()) * scale).ceil()
        pos = ((V(scr.get_size()) - size) / 2).floor()
        mouse = ((V(pg.mouse.get_pos()) - pos) * (game.surf.get_size() / size)) if sum(size.xy) > 0 else V()

        for _ in range(ceil(t*60) * 0 + 1):
            if game.update(mouse):
                RUN = False
        game.render()

        t0 = t1

        surf = pg.transform.scale(game.getappliedsurf(), size.xy)
        scr.fill(game.surf.get_at((0, 0)))
        scr.blit(surf, pos.xy)

        pg.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    pg.mixer.pre_init()
    pg.init()
    main()
    pg.quit()
