from math import pi, sin, cos

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence
from panda3d.core import Point3, Fog, GeoMipTerrain, Texture, TextureStage


class Terrain():
    def __init__(self, showBase):
        self.showBase = showBase
        self.terrains = {}
        showBase.taskMgr.add(self.updateTerrainTask, "update")
    
    # Add a task to keep updating the terrain
    def updateTerrainTask(self, task):
        pos = self.showBase.pandaActor.getPos()
        x = int(pos.getX() + 64) // 128
        y = int(pos.getY() + 64) // 128
        self.createTiles(x, y)
        return task.cont

    def createTiles(self, x, y):
        for i in range(x-2, x+3):
            for j in range(y-2, y+3):
                if not f"{i},{j}" in self.terrains:
                    self.terrains[f"{i},{j}"] = self.createTile(i, j)

    def createTile(self, x, y):
        # Set up the GeoMipTerrain
        terrain = GeoMipTerrain("terrain")
        terrain.setHeightfield("./height-map.png")
        # Set terrain properties
        terrain.setBlockSize(32)
        terrain.setNear(40)
        terrain.setFar(100)
        terrain.setFocalPoint(self.showBase.camera)
        #terrain.setAutoFlatten(GeoMipTerrain.AFMStrong)
        terrain.getRoot().setScale(1, 1, 1)
        terrain.getRoot().setPos(x * 128 - 64, y * 128 - 64, 0)
        terrain.getRoot().setTexture(TextureStage.getDefault(), self.showBase.loader.loadTexture("./grass-texture.png"))
        terrain.getRoot().setTexScale(TextureStage.getDefault(), 50)
        # Store the root NodePath for convenience
        root = terrain.getRoot()
        root.reparentTo(self.showBase.render)
        root.setSz(100)
        # Generate it.
        terrain.generate()
        return terrain


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        # Disable the camera trackball controls.
        self.disableMouse()

        self.setBackgroundColor(0.5,0.5,0.5)
        self.terrain = Terrain(self)

        # Add a fog
        fog = Fog("A linear-mode Fog node")
        fog.setMode(Fog.MExponential)
        fog.setColor(0.5,0.5,0.5)
        fog.setExpDensity(0.01)
        self.render.setFog(fog)

        # helper maps for storing times
        self.lastPositioningTime = {}
        self.lastTurningTime = {}

        # Load and transform the panda actor.
        self.pandaActor = Actor("models/panda-model", {"walk": "models/panda-walk4"})
        self.pandaActor.setScale(0.005, 0.005, 0.005)
        self.pandaActor.reparentTo(self.render)
        
        # setup keyboard events
        self.accept('arrow_up', self.pandaGo, [1])
        self.accept('arrow_up-up', self.pandaStop, [1])
        self.accept('arrow_down', self.pandaGo, [-1])
        self.accept('arrow_down-up', self.pandaStop, [-1])
        self.accept('arrow_left', self.pandaTurn, [-1])
        self.accept('arrow_left-up', self.pandaStopTurning, [-1])
        self.accept('arrow_right', self.pandaTurn, [1])
        self.accept('arrow_right-up', self.pandaStopTurning, [1])

        # add task for moving the camera
        self.taskMgr.add(self.spinCameraByPanda, "SpinCameraTask")

    def pandaGo(self, direction):
        self.lastPositioningTime[direction] = 0
        # add task for moving panda forward or back
        self.taskMgr.add(self.pandaPositioningTask, f"PandaPositioningTask{direction}", extraArgs=[direction], appendTask=True)
        # resume the walk animation from the last position
        frame = self.pandaActor.getCurrentFrame('walk')
        frame = 0 if frame == None else frame
        self.pandaActor.setPlayRate(8 * direction, "walk")
        self.pandaActor.pose("walk", float(frame))
        self.pandaActor.loop("walk", restart=False)
    
    def pandaTurn(self, direction):
        self.lastTurningTime[direction] = 0
        # add task for turning panda left or right
        self.taskMgr.add(self.pandaTurningTask, f"PandaTurningTask{direction}", extraArgs=[direction], appendTask=True)

    def pandaStop(self, direction):
        # remove the task that is moving panda
        self.taskMgr.remove(f"PandaPositioningTask{direction}")
        # stop the walk animation
        self.pandaActor.stop("walk")
    
    def pandaStopTurning(self, direction):
        # remove the task that is turning panda
        self.taskMgr.remove(f"PandaTurningTask{direction}")

    def pandaPositioningTask(self, direction, task):
        if task.time > self.lastPositioningTime[direction]:
            distance = -3000 * (task.time - self.lastPositioningTime[direction]) * direction * (min(task.time, 1))
            self.pandaActor.setPlayRate(8 * direction * min(task.time, 1), "walk")
            self.pandaActor.setPos(self.pandaActor, 0, distance, 0)
            self.lastPositioningTime[direction] = task.time
        return Task.cont

    def pandaTurningTask(self, direction, task):
        if task.time > self.lastTurningTime[direction]:
            hpr = self.pandaActor.getHpr()
            hpr.setX(-80 * (task.time - self.lastTurningTime[direction]) * direction)
            self.pandaActor.setHpr(self.pandaActor, hpr)
            self.lastTurningTime[direction] = task.time
        return Task.cont

    # Define a procedure to move the camera.
    def spinCameraByPanda(self, task):
        if (self.pandaActor):
            posX = self.pandaActor.getPos().getXy().getX()
            posY = self.pandaActor.getPos().getXy().getY()
            hprX = self.pandaActor.getHpr().getX()
            angle = 180 + hprX
            self.camera.setPos(20 * sin(angle * (pi / 180.0)) + posX, -20 * cos(angle * (pi / 180.0)) + posY, 8)
            self.camera.setHpr(angle, -10, 0)
        return Task.cont


app = MyApp()
app.run()