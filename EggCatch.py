# Egg Catch
#
# Control a bird and catch eggs falling off the screen. Dodge bombs and rocks.

import pygame, time, sys, random
from pygame.locals import *

pygame.init()

WINDOWWIDTH = 708
WINDOWHEIGHT = 591

# Frames per second variables
FPS = 30
FPSCLOCK = pygame.time.Clock()

#-Game images-------
BIRD_LEFTUP_IMG = pygame.image.load("bird_left_up.png")
BIRD_LEFTDOWN_IMG = pygame.image.load("bird_left_down.png")
BIRD_RIGHTUP_IMG = pygame.image.load("bird_right_up.png")
BIRD_RIGHTDOWN_IMG = pygame.image.load("bird_right_down.png")
BIRD_IMGWIDTH, BIRD_IMGHEIGHT = 100, 60

NRMLEGG_IMG = pygame.image.load("white_egg.png")
GOLDEGG_IMG = pygame.image.load("gold_egg.png")
BLUEEGG_IMG = pygame.image.load("blue_egg.png")
ROCK_IMG = pygame.image.load("rock.png")
BOMB_IMG = pygame.image.load("bomb.png")
EGG_IMGWIDTH = 15
ROCK_IMGWIDTH = 30
BOMB_IMGWIDTH = 25
OBJ_HEIGHT = 22

BACKGROUND_IMG = pygame.image.load("background.png")
GAMEOVER_IMG = pygame.image.load("game_over_screen.png")
GAMEICON_IMG = pygame.image.load("game_icon.png")
#-------------------

# How much images on the screen move in various directions
PLAYER_MVSPEED_HORIZONTAL = 3
PLAYER_MVSPEED_UP = 7
PLAYER_MVSPEED_DOWN = 3
PLAYER_MVSPEED_DOWN_EXTRA = 2
OBJ_MVSPEED_DOWN = 2

# Position of the player at the start of the game and when the screen is reset
PLAYERSTART_POS_X = WINDOWWIDTH - 50
PLAYERSTART_POS_Y = 0

# 3 possible x positions of falling objects and the starting y position
OBJSTART_POS_X = [160, 382, 585]
OBJSTART_POS_Y = 0 - int(OBJ_HEIGHT/2)

# Duration of events in seconds
FLYMODE_TIME = .1
FALLPAUSE_TIME = 1
POINTSMODE_TIME = 10

# How many lives the player starts with
STARTINGLIVES = 10

# Direction variables
LEFT = "LEFT"
RIGHT = "RIGHT"
UP = "UP"
DOWN = "DOWN"

# How many points the egg types are worth
POINTS_EGG_NRML = 1
POINTS_EGG_GOLD = 5

# Min and max points lost when the player collides with a rock
ROCKPOINTS_MIN = 1
ROCKPOINTS_MAX = 5

# Falling object types
EGG_NRML = "EGG_NRML"
EGG_GOLD = "EGG_GOLD"
EGG_BLUE = "EGG_BLUE"
ROCK = "ROCK"
BOMB = "BOMB"

# Likelihood of objects falling as percentages
PROB_NEWOBJ = 1
PROB_EGG_NRML = 35
PROB_EGG_GOLD = 11
PROB_EGG_BLUE = 14
PROB_ROCK = 35
PROB_BOMB = 15

# Font variables
FONTCOLOR = (255, 255, 255) # white
FONTCOLOR2 = (160, 5, 5) # red
FONT = pygame.font.SysFont("shruti", 25)
FONTSMALL = pygame.font.SysFont("shruti", 15)

# Start screen variables
STRTSCREEN_COLOR = (0, 0, 0) # black
STRTSCREEN_IMGLIST = [NRMLEGG_IMG, GOLDEGG_IMG, BLUEEGG_IMG, ROCK_IMG, BOMB_IMG, ""]
STRTSCREEN_IMGPOSX = int(WINDOWWIDTH/3)
STRTSCREEN_TXTPOSX = int(STRTSCREEN_IMGPOSX) + 40
STRTSCREEN_NRMLEGGMSG = "WORTH " + str(POINTS_EGG_NRML) + " POINT"
STRTSCREEN_GOLDEGGMSG = "WORTH " + str(POINTS_EGG_GOLD) + " POINTS"
STRTSCREEN_BLUEEGGMSG = "x2 SCORE FOR " + str(POINTSMODE_TIME) + " SECONDS"
STRTSCREEN_ROCKMSG = "MAKES EGGS CRACK"
STRTSCREEN_BOMBMSG = "CAUSES EXPLOSION AND ENDS GAME"
STRTSCREEN_BEGINMSG = "PRESS THE SPACEBAR TO CONTINUE"

# Set up the display and font, run the game function
def main():
    global DISPLAYSURF

    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    pygame.display.set_caption("Egg Catch")
    pygame.display.set_icon(GAMEICON_IMG)
    pygame.mouse.set_visible(False)

    runGame()
        
# Main game loop
def runGame():
    # Player character format: dict with top left coordinates, direction player is facing, position
    # of wings, number of lives, and score
    startScreen()
    
    playerChar = {"x":PLAYERSTART_POS_X, "y":PLAYERSTART_POS_Y,
                  "dir":LEFT,
                  "wings":DOWN,
                  "lives":STARTINGLIVES,
                  "score":0}
    fallingObjs = []
    
    flyMode, flyModeTimer = False, False
    dropMode = False
    doublePointsMode, doublePointsModeTimer = False, False
    
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYUP:
                if event.key in (K_UP, K_w):
                    flyMode, flyModeTimer = startFlyMode(playerChar, flyMode, flyModeTimer)
                elif event.key in (K_LEFT, K_a):
                    playerChar["dir"] = LEFT
                elif event.key in (K_RIGHT, K_d):
                    playerChar["dir"] = RIGHT
                elif event.key in (K_DOWN, K_s):
                    dropMode = False
            elif event.type == KEYDOWN and event.key in (K_DOWN, K_s):
                dropMode = True

        if flyMode:
            flyMode, flyModeTimer = checkFlyMode(playerChar, flyMode, flyModeTimer)
        if doublePointsMode:
            doublePointsMode, doublePointsModeTimer = checkDoublePointsMode(doublePointsMode,
                                                                            doublePointsModeTimer)

        fallingObjs = generateNewObj(fallingObjs)
        fallingObjs = updatePos(playerChar, flyMode, dropMode, fallingObjs)
        fallingObjs, playerChar["score"], doublePointsMode, doublePointsModeTimer = objCollisions(
            playerChar,
            fallingObjs,
            playerChar["score"],
            doublePointsMode,
            doublePointsModeTimer)

        if isPlayerOffScreen(playerChar["y"]):
            fallingObjs = loseLife(playerChar, fallingObjs, doublePointsMode, doublePointsModeTimer)
        if playerChar["lives"] < 0:
            gameOver()
            return
        
        draw(playerChar, fallingObjs, doublePointsMode, doublePointsModeTimer)
        pygame.display.update()
        FPSCLOCK.tick(FPS)

# May generate a new falling object based on probability
def generateNewObj(fallingObjs):
    randomNum = random.randint(0, 100)
    
    if randomNum <= PROB_NEWOBJ:
        randomNum = random.randint(1, 100)
        x, y = random.choice(OBJSTART_POS_X), OBJSTART_POS_Y
        
        if randomNum < PROB_EGG_NRML:
            # Falling object format: dict w/ type of obj, center coordinates, and amount of points
            # object is worth (default)
            newObj = {"type":EGG_NRML, "x":x, "y":y, "points":POINTS_EGG_NRML}
        elif randomNum < PROB_EGG_NRML + PROB_EGG_GOLD:
            newObj = {"type":EGG_GOLD, "x":x, "y":y, "points":POINTS_EGG_GOLD}
        elif randomNum < PROB_EGG_NRML + PROB_EGG_GOLD + PROB_EGG_BLUE:
            newObj = {"type":EGG_BLUE, "x":x, "y":y, "points":0}
        elif randomNum < PROB_EGG_NRML + PROB_EGG_GOLD + PROB_EGG_BLUE + PROB_ROCK:
            newObj = {"type":ROCK, "x":x, "y":y, "points":0}
        elif randomNum < PROB_EGG_NRML + PROB_EGG_GOLD + PROB_EGG_BLUE + PROB_ROCK + PROB_BOMB:
            newObj = {"type":BOMB, "x":x, "y":y, "points":0}
            
        fallingObjs.append(newObj)
    return fallingObjs

# Update the coordinates of images on the screen
def updatePos(playerChar, flyMode, dropMode, fallingObjs):
    updateBirdPos(playerChar, flyMode, dropMode)
    fallingObjs = updateObjsPos(playerChar, fallingObjs)
    return fallingObjs
    
# Update the avatar's coordinates
def updateBirdPos(playerChar, flyMode, dropMode):
    horizontalMovement(playerChar)
    verticalMovement(playerChar, flyMode, dropMode)

# Update the falling objects' coordinates
def updateObjsPos(playerChar, fallingObjs):
    for obj in fallingObjs:
        objPos = fallingObjs.index(obj)
        fallingObjs[objPos]["y"] += OBJ_MVSPEED_DOWN
        
        if isObjOffScreen(obj["y"]):
            fallingObjs.remove(obj)
            objType = obj["type"]
            if objType in (EGG_NRML, EGG_GOLD, EGG_BLUE):
                playerChar["lives"] -= 1
    return fallingObjs
    
# Add or subtract from the avatar's x coordinate based on its direction and make it wrap around if
# it has gone off of the screen
def horizontalMovement(playerChar):
    direction = playerChar["dir"]
    if direction == RIGHT:
        playerChar["x"] += PLAYER_MVSPEED_HORIZONTAL
    elif direction == LEFT:
        playerChar["x"] -= PLAYER_MVSPEED_HORIZONTAL

    offSide = isPlayerOffLeftRightSide(playerChar["x"])
    if offSide == LEFT:
        playerChar["x"] = WINDOWWIDTH
    elif offSide == RIGHT:
        playerChar["x"] = 0 - BIRD_IMGWIDTH

# Make gravity affect the avatar by adding to its y coordinate. If the bird is flapping or falling
# extra quickly, adjust the y coordinate appropriately.
def verticalMovement(playerChar, flyMode, dropMode):
    playerChar["y"] += PLAYER_MVSPEED_DOWN
    
    if flyMode:
        moveAmount = PLAYER_MVSPEED_UP
        if isPlayerOffTopSide(playerChar["y"] - moveAmount):
            playerChar["y"] = 0
        else:
            playerChar["y"] -= moveAmount
    elif dropMode:
        playerChar["y"] += PLAYER_MVSPEED_DOWN_EXTRA

# Check if a falling object has gone off the bottom side of the screen
def isObjOffScreen(objY):
    if objY > WINDOWHEIGHT + int(OBJ_HEIGHT/2):
        return True
    return False

# Begin the timer for the player to move up
def startFlyMode(playerChar, flyMode, flyModeTimer):
    playerChar["wings"] = UP
    flyMode = True
    flyModeTimer = time.time()
    return flyMode, flyModeTimer

# Check if the time for fly mode has elapsed. If it has, end it
def checkFlyMode(playerChar, flyMode, flyModeTimer):
    if time.time() - flyModeTimer >= FLYMODE_TIME:
        playerChar["wings"] = DOWN
        flyMode = False
        flyModeTimer = 0
    return flyMode, flyModeTimer

# Begin the timer for 2x points mode
def startDoublePointsMode(doublePointsMode, doublePointsModeTimer):
    doublePointsMode = True
    doublePointsModeTimer = time.time()
    return doublePointsMode, doublePointsModeTimer

# Check if the time for double points mode has elapsed. If it has, end it
def checkDoublePointsMode(doublePointsMode, doublePointsModeTimer):
    if time.time() - doublePointsModeTimer >= POINTSMODE_TIME:
        doublePointsMode = False
        doublePointsModeTimer = 0
    return doublePointsMode, doublePointsModeTimer

# Check whether or not the bird has moved completely off of the left or right side of the screen
def isPlayerOffLeftRightSide(playerX):
    if playerX < 0 - BIRD_IMGWIDTH:
        return LEFT
    elif playerX > WINDOWWIDTH:
        return RIGHT
    return None

# Check if the player character has moved off of the top of the screen
def isPlayerOffTopSide(playerY):
    if playerY < 0:
        return True

# Check if the player has fallen off of the screen
def isPlayerOffScreen(playerY):
    if playerY > WINDOWHEIGHT:
        return True

# Get object collisions with the player and handle them
def objCollisions(playerChar, fallingObjs, score, doublePointsMode, doublePointsModeTimer):
    collidedObjs = getObjCollisions(playerChar, fallingObjs)
    if collidedObjs:
        score, doublePointsMode, doublePointsModeTimer = handleObjCollisions(collidedObjs, score,
                                                                             doublePointsMode,
                                                                             doublePointsModeTimer)
        fallingObjs = removeCollidedObjs(collidedObjs, fallingObjs)
    return fallingObjs, score, doublePointsMode, doublePointsModeTimer
    
# Get player collisions with the falling objects
def getObjCollisions(playerChar, fallingObjs):
    collidedObjs = []
    playerX, playerY = playerChar["x"], playerChar["y"]
    playerRect = pygame.Rect((playerX, playerY), (BIRD_IMGWIDTH, BIRD_IMGHEIGHT))
    
    for obj in fallingObjs:
        objX, objY = obj["x"], obj["y"]
        if obj["type"] in (EGG_NRML, EGG_GOLD, EGG_BLUE):
            objRect = pygame.Rect((objX, objY), (EGG_IMGWIDTH, OBJ_HEIGHT))
        elif obj["type"] == ROCK:
            objRect = pygame.Rect((objX, objY), (ROCK_IMGWIDTH, OBJ_HEIGHT))
        elif obj["type"] == BOMB:
            objRect = pygame.Rect((objX, objY), (BOMB_IMGWIDTH, OBJ_HEIGHT))

        if playerRect.colliderect(objRect):
            collidedObjs.append(obj)
    return collidedObjs

# Handle collisions between the player and falling objects
def handleObjCollisions(collidedObjs, score, doublePointsMode, doublePointsModeTimer):
    for obj in collidedObjs:
        if doublePointsMode:
            pointsToAdd = obj["points"] * 2
        else:
            pointsToAdd = obj["points"]
        score += pointsToAdd

        if obj["type"] == EGG_BLUE:
            # If the player collides with a blue egg, eggs are worth double points
            doublePointsMode, doublePointsModeTimer = startDoublePointsMode(doublePointsMode,
                                                                            doublePointsModeTimer)
        elif obj["type"] == ROCK:
            # If the player collides with a rock, a random number of points are lost to simulate
            # eggs cracking
            pointsLost = random.randint(ROCKPOINTS_MIN, ROCKPOINTS_MAX)
            score -= pointsLost
            if score < 0:
                score = 0
        elif obj["type"] == BOMB:
            # If the player collides with a bomb, the game is over
            gameOver()
    return score, doublePointsMode, doublePointsModeTimer

# Remove the objects that the player has collided with from the list of falling objects
def removeCollidedObjs(collidedObjs, fallingObjs):
    newFallingObjs = [obj for obj in fallingObjs if obj not in collidedObjs]
    return newFallingObjs
    
# Draw the background, the player character,  
def draw(playerChar, fallingObjs, doublePointsMode, doublePointsModeTimer):
    drawBg()
    drawBird(playerChar)
    drawFallingObjs(fallingObjs)
    drawInfo(playerChar, doublePointsMode, doublePointsModeTimer)

# Put up the background picture
def drawBg():
    bgRect = BACKGROUND_IMG.get_rect()
    DISPLAYSURF.blit(BACKGROUND_IMG, bgRect)

# Put a bird picture on the screen based on the player's coordinates, direction, and wing position
def drawBird(playerChar):
    birdX, birdY = playerChar["x"], playerChar["y"]
    direction, wingsPos = playerChar["dir"], playerChar["wings"]

    if direction == LEFT:
        if wingsPos == UP:
            birdImg = BIRD_LEFTUP_IMG
        elif wingsPos == DOWN:
            birdImg = BIRD_LEFTDOWN_IMG
    elif direction == RIGHT:
        if wingsPos == UP:
            birdImg = BIRD_RIGHTUP_IMG
        elif wingsPos == DOWN:
            birdImg = BIRD_RIGHTDOWN_IMG

    birdRect = birdImg.get_rect()
    birdRect.topleft = (birdX, birdY)
    DISPLAYSURF.blit(birdImg, birdRect)

# Draw the falling objects on the screen
def drawFallingObjs(fallingObjs):
    for obj in fallingObjs:
        objX, objY = obj["x"], obj["y"]
        
        if obj["type"] == EGG_NRML:
            objImg = NRMLEGG_IMG
        elif obj["type"] == EGG_GOLD:
            objImg = GOLDEGG_IMG
        elif obj["type"] == EGG_BLUE:
            objImg = BLUEEGG_IMG
        elif obj["type"] == ROCK:
            objImg = ROCK_IMG
        elif obj["type"] == BOMB:
            objImg = BOMB_IMG

        objRect = objImg.get_rect()
        objRect.center = (objX, objY)
        DISPLAYSURF.blit(objImg, objRect)
        
# Draw the number of lives remaining and the number of eggs caught on the board
def drawInfo(playerChar, doublePointsMode, doublePointsModeTimer):
    livesText = "Lives: " + str(playerChar["lives"])
    scoreText = "Score: " + str(playerChar["score"])

    livesSurf = FONT.render(livesText, True, FONTCOLOR)
    livesRect = livesSurf.get_rect()
    livesRect.topleft = (0, 0)
    DISPLAYSURF.blit(livesSurf, livesRect)

    scoreSurf = FONT.render(scoreText, True, FONTCOLOR)
    scoreRect = scoreSurf.get_rect()
    scoreRect.topleft = (0, livesRect.bottom)
    DISPLAYSURF.blit(scoreSurf, scoreRect)

    if doublePointsMode:
        timeRemaining = 10 - int(time.time() - doublePointsModeTimer)
        pointsModeText = "Points x2: " + str(timeRemaining)
        
        pointsModeSurf = FONT.render(pointsModeText, True, FONTCOLOR2)
        pointsModeRect = pointsModeSurf.get_rect()
        pointsModeRect.topleft = (0, scoreRect.bottom)
        DISPLAYSURF.blit(pointsModeSurf, pointsModeRect)

# Subtract 1 from the player's number of lives, pause, and reset the screen
def loseLife(playerChar, fallingObjs, doublePointsMode, doublePointsModeTimer):
    playerChar["lives"] -= 1
    time.sleep(FALLPAUSE_TIME)
    fallingObjs, doublePointsMode, doublePointsModeTimer = resetScreen(playerChar,
                                                                       fallingObjs,
                                                                       doublePointsMode,
                                                                       doublePointsModeTimer)
    return fallingObjs, doublePointsMode, doublePointsModeTimer

# Restart the player at the starting point
def resetScreen(playerChar, fallingObjs, doublePointsMode, doublePointsModeTimer):
    playerChar["x"], playerChar["y"] = PLAYERSTART_POS_X, PLAYERSTART_POS_Y
    fallingObjs = []
    doublePointsMode, doublePointsModeTimer = False, False
    return fallingObjs, doublePointsMode, doublePointsModeTimer

# At the beginning of each game, show a screen displaying value of each falling object until the
# spacebar is pressed
def startScreen():
    objPosY1 = int(WINDOWHEIGHT / (len(STRTSCREEN_IMGLIST) + 1))
    objPosY = [objPosY1]
    for i in range(2, len(STRTSCREEN_IMGLIST) + 1):
        newPosY = int(objPosY1 * i)
        objPosY.append(newPosY)

    nrmlEggSurf = FONTSMALL.render(STRTSCREEN_NRMLEGGMSG, True, FONTCOLOR)
    nrmlEggRect = nrmlEggSurf.get_rect()
    nrmlEggRect.topleft = (STRTSCREEN_TXTPOSX, objPosY[0])

    goldEggSurf = FONTSMALL.render(STRTSCREEN_GOLDEGGMSG, True, FONTCOLOR)
    goldEggRect = goldEggSurf.get_rect()
    goldEggRect.topleft = (STRTSCREEN_TXTPOSX, objPosY[1])

    blueEggSurf = FONTSMALL.render(STRTSCREEN_BLUEEGGMSG, True, FONTCOLOR)
    blueEggRect = blueEggSurf.get_rect()
    blueEggRect.topleft = (STRTSCREEN_TXTPOSX, objPosY[2])

    rockSurf = FONTSMALL.render(STRTSCREEN_ROCKMSG, True, FONTCOLOR)
    rockRect = rockSurf.get_rect()
    rockRect.topleft = (STRTSCREEN_TXTPOSX, objPosY[3])

    bombSurf = FONTSMALL.render(STRTSCREEN_BOMBMSG, True, FONTCOLOR)
    bombRect = bombSurf.get_rect()
    bombRect.topleft = (STRTSCREEN_TXTPOSX, objPosY[4])

    beginSurf = FONT.render(STRTSCREEN_BEGINMSG, True, FONTCOLOR)
    beginRect = beginSurf.get_rect()
    beginRect.topleft = (int(WINDOWWIDTH/5), objPosY[5])

    textSurfsAndRects = [(nrmlEggSurf, nrmlEggRect),
                         (goldEggSurf, goldEggRect),
                         (blueEggSurf, blueEggRect),
                         (rockSurf, rockRect),
                         (bombSurf, bombRect),
                         (beginSurf, beginRect)]
    
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYUP and event.key == K_SPACE:
                return

        DISPLAYSURF.fill(STRTSCREEN_COLOR)
        for i in range(len(STRTSCREEN_IMGLIST)):
            img = STRTSCREEN_IMGLIST[i]
            yPos = objPosY[i]
            textSurf, textRect = textSurfsAndRects[i][0], textSurfsAndRects[i][1]

            if img != "":
                if img in (NRMLEGG_IMG, GOLDEGG_IMG, BLUEEGG_IMG):
                    imgRect = pygame.Rect(STRTSCREEN_IMGPOSX, yPos, EGG_IMGWIDTH, OBJ_HEIGHT)
                elif img == ROCK_IMG:
                    imgRect = pygame.Rect(STRTSCREEN_IMGPOSX, yPos, ROCK_IMGWIDTH, OBJ_HEIGHT)
                elif img == BOMB_IMG:
                    imgRect = pygame.Rect(STRTSCREEN_IMGPOSX, yPos, BOMB_IMGWIDTH, OBJ_HEIGHT)
                DISPLAYSURF.blit(img, imgRect)
            DISPLAYSURF.blit(textSurf, textRect)
            
        pygame.display.update()
        FPSCLOCK.tick(FPS)
    
# Show the game over screen and wait for the player to press the spacebar, starting a new game
def gameOver():
    overRect = GAMEOVER_IMG.get_rect()

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYUP and event.key == K_SPACE:
                runGame()

        DISPLAYSURF.blit(GAMEOVER_IMG, overRect)
        pygame.display.update()
        FPSCLOCK.tick(FPS)
            
if __name__ == "__main__":
    main()
