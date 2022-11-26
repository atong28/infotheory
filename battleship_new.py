import numpy as np
from numpy import unravel_index
import copy

################################################################################
# Text color presets.                                                          #
################################################################################
class bcolors:
    RED = '\u001b[31;1m'
    BLUE = '\u001b[34;1m'
    YELLOW = '\u001b[33;1m'
    GREEN = '\u001b[32;1m'
    MAGENTA = '\u001b[35;1m'
    CYAN = '\u001b[36;1m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\u001b[0m'

def isHit(board):
    
    board.hitMode = False
    # iterate through all squares. if there is a ship that is hit but not sunk, activate hitMode
    for x in range(Board.BOARD_SIZE):
        for y in range(Board.BOARD_SIZE):
            if board.gameState[x,y] == 2 and board.guessState[x,y] == 0:
                board.hitMode = True
                return

################################################################################
# Evaluates the guess probability state.                                       #
################################################################################
def evalBoard(board):
    board.probState = np.zeros((Board.BOARD_SIZE, Board.BOARD_SIZE), dtype='int64')
    board.probTotal = 1

    isHit(board)
    
    # check if there are ships left
    shipsLeft = False
    for ship in board.ships:
        if not ship.sunk: 
            shipsLeft = True
            break

    # if in hitmode, iterate through all possible orientations for each ship and then recurse through each orientation to find its probability weighting
    if board.hitMode:
        
        # if there are no ships left, this is an impossible setup. return probTotal = 0
        if not shipsLeft: 
            board.probTotal = 0
            return
        
        for i in range(len(board.ships)):
            ship = board.ships[i]
            if ship.sunk: continue
            
            # test for all horizontal ships
            orientation = 0
            for x in range(Board.BOARD_SIZE):
                for y in range(Board.BOARD_SIZE - ship.size + 1):
                    # if the ship collides with a miss block or a sunken ship block, it is not a valid location
                    if overlaps(x, y, orientation, ship.size, board.guessState): continue
                    
                    # ship does not collide with hit point, then do nothing
                    if sum(board.gameState[x,y:y+ship.size]) == 0: continue
                    
                    # may use multiplier. here for now.
                    # multiplier = (sum(board.gameState[x,y:y+ship.size]) ** 2)
                    
                    # create a ghost board that assumes this ship placed as is
                    ghostBoard = copy.deepcopy(board)
                    
                    
                    # sink the ship, removing it from calculation 
                    ghostBoard.ships[i].sunk = True
                    
                    # modify the ghost board's board state to account for ship placement (essentially, assumes sunk ship at this location)
                    ghostBoard.guessState[x,y:y+ship.size] = 1
                    ghostBoard.gameState[x,y:y+ship.size] = 2
                    
                    # evaluate the ghost board state and find probTotal
                    evalBoard(ghostBoard)
                    # throw away tempBoard. we do not need it here because that is the prob state in a future
                    
                    # print("Temp Ghost Board:")
                    # print(ghostBoard)
                    
                    # add totals, and do the same for the probability board
                    board.probTotal += ghostBoard.probTotal
                    board.probState[x,y:y+ship.size] += ghostBoard.probTotal
                    
            # same thing for vertical ships
            orientation = 1
            for x in range(Board.BOARD_SIZE - ship.size + 1):
                for y in range(Board.BOARD_SIZE):
                    # if the ship collides with a miss block or a sunken ship block, it is not a valid location
                    if overlaps(x, y, orientation, ship.size, board.guessState): continue
                    
                    # ship does not collide with hit point, then do nothing
                    if sum(board.gameState[x:x+ship.size,y]) == 0: continue
                    
                    # may use multiplier. here for now.
                    # multiplier = (sum(board.gameState[x:x+ship.size,y]) ** 2)
                    
                    # create a ghost board that assumes this ship placed as is
                    ghostBoard = copy.deepcopy(board)
                    
                    # sink the ship, removing it from calculation 
                    ghostBoard.ships[i].sunk = True
                    
                    # modify the ghost board's board state to account for ship placement (essentially, assumes sunk ship at this location)
                    ghostBoard.guessState[x:x+ship.size,y] = 1
                    ghostBoard.gameState[x:x+ship.size,y] = 2
                    
                    
                    
                    # evaluate the ghost board state and find probTotal
                    evalBoard(ghostBoard)
                    # throw away tempBoard. we do not need it here because that is the prob state in a future
                    
                    # add totals, and do the same for the probability board
                    board.probTotal += ghostBoard.probTotal
                    board.probState[x:x+ship.size,y] += ghostBoard.probTotal
    
    # if not in hitmode, sum up all possible orientations for each ship and multiply them together to estimate possible boards remaining
    else:
        
        # if there are no hit points and no ships left, return 1 (1 possibility)
        if not shipsLeft: 
            return
        
        for ship in board.ships:
            counter = 0
            if ship.sunk: continue
            
            # test for all horizontal
            orientation = 0
            for x in range(Board.BOARD_SIZE):
                for y in range(Board.BOARD_SIZE - ship.size + 1):
                    # if the ship collides with a miss block or a sunken ship block, it is not a valid location
                    if overlaps(x, y, orientation, ship.size, board.guessState): continue
                    
                    # increment possible location
                    board.probState[x,y:y+ship.size] += 1
                    counter += 1
                    
            # test for all vertical
            orientation = 1
            for x in range(Board.BOARD_SIZE - ship.size + 1):
                for y in range(Board.BOARD_SIZE):
                    if overlaps(x, y, orientation, ship.size, board.guessState): continue
                    # since the ship is a valid placement, if the sum here is positive, it travels over a hit but not sunk ship
                    
                    # increment possible location
                    board.probState[x:x+ship.size,y] += 1
                    counter += 1
            
            # multiply together! if counter is still at 0, this board state is impossible anyways
            board.probTotal *= counter

    # removes probability for ships that are already hit but not sunk
    for x in range(Board.BOARD_SIZE):
        for y in range(Board.BOARD_SIZE):
            if board.gameState[x,y] == 2 and board.guessState[x,y] == 0:
                board.probState[x,y] = 0

################################################################################
# Tests if a ship overlaps a given board.                                      #
################################################################################
def overlaps(x, y, orientation, shipSize, board):
    if orientation == 0:
        if sum(board[x,y:y+shipSize]) == 0: return False
    else:
        if sum(board[x:x+shipSize,y]) == 0: return False
    return True

################################################################################
# BATTLESHIP CLASS: Runs the game.                                             #
# ---------------------------------------------------------------------------- #
# INSTANCE VARIABLES:                                                          #
# - board:   Stores the Board class that the game runs on.                     #
# - counter: Counts the number of moves the player has made.                   #
# - win:     True if player has won. Terminates the game.                      #
################################################################################
class Battleship():

    ############################################################################
    # Runs the Battleship game.                                                #
    ############################################################################
    def __init__(self, generateRandom, manual, numRounds):
        self.board = Board(generateRandom)
        self.counter = 0
        self.win = False
        self.autoMove = unravel_index(self.board.probState.argmax(), self.board.probState.shape)
        self.autoResults = np.zeros(100, dtype='int64')
        
        # modifiable
        self.autoRounds = numRounds

        # if manual, just run one round; play moves until win
        if manual:

            # print information
            print(self.board)

            if self.board.hitMode:
                print(f"{bcolors.BOLD + bcolors.GREEN}HIT MODE: Next best move at ({self.autoMove[0]},{self.autoMove[1]}).")         
            else:
                print(f"{bcolors.BOLD + bcolors.BLUE}SEARCH MODE: Next best move at ({self.autoMove[0]},{self.autoMove[1]}).")   

            # launch!
            while not self.win:
                self.playManual()
            print(f"Congratulations, you won in {self.counter} moves!")
            
        # run and reset after each game
        else:
            for i in range(self.autoRounds):
                if i % 10 == 0: print(f"{bcolors.CYAN}Run {i} completed.")
                while not self.win:
                    self.playAuto()
                self.autoResults[self.counter] += 1
                self.board.reset()
                self.board.generate()
                self.counter = 0
                self.win = False
            
            # analyze stats
            expectedMoves = 0
            print(f"{bcolors.BLUE + bcolors.BOLD}In {self.autoRounds} simulations, here is the distribution of game moves:")
            for i in range(100):
                if self.autoResults[i] == 0: continue
                print(f"{bcolors.GREEN}{i} moves: {self.autoResults[i]} game(s)")
                expectedMoves += i * self.autoResults[i] / self.autoRounds
                
            print(f"{bcolors.BLUE + bcolors.BOLD}The number of mean moves was {bcolors.YELLOW}{expectedMoves}.")
            
            # print for google sheets formatting
            printSheet = ""
            while (len(printSheet) != 1) and (printSheet != "y" and printSheet != "n"):
                printSheet = str.lower(input(f"{bcolors.BLUE + bcolors.BOLD}Would you like to print the list for spreadsheet formatting? Press Y for yes, N for no. First starts at 0. "))
            if printSheet == "y":
                for i in range(100):
                    print(self.autoResults[i])
        
    ############################################################################
    # Plays one move in manual mode.                                           #
    ############################################################################
    def playManual(self):
        nextMove = tuple(input("Enter row, col [format: xy, where x:[0,9], y:[0,9]]: "))
        self.board.move(int(nextMove[0]), int(nextMove[1]))
        self.counter += 1
        
        # print information
        print(self.board)

        if self.board.hitMode:
            print(f"{bcolors.BOLD + bcolors.GREEN}HIT MODE")         
        else:
            print(f"{bcolors.BOLD + bcolors.BLUE}SEARCH MODE")   

        bestMove = unravel_index(self.board.probState.argmax(), self.board.probState.shape)
        print(f'Next best move at ({bestMove[0]},{bestMove[1]}).')

        # check for win
        for ship in self.board.ships:
            if not ship.sunk:
                return
        self.win = True

    ############################################################################
    # Plays one move in auto mode.                                             #
    ############################################################################
    def playAuto(self):
        self.board.move(self.autoMove[0],self.autoMove[1])
        self.counter += 1
        
        nextMove = tuple(str(np.argmax(self.board.probState)).zfill(2))
        self.autoMove = (int(nextMove[0]), int(nextMove[1]))

        # Check for win
        for ship in self.board.ships:
            if not ship.sunk:
                return
        self.win = True
        

################################################################################
# BOARD CLASS: Stores the game state with both the actual ship allocation and  #
# the guessed state.                                                           #
# ---------------------------------------------------------------------------- #
# CONSTANTS                                                                    #
# - BOARD_SIZE: The size of the allocated board.                               #
# - DEFAULT_SHIP_SIZES: The sizes of the ships available to allocate.          #
# ---------------------------------------------------------------------------- #
# INSTANCE VARIABLES:                                                          #
# - hiddenState:    The array that stores the actual allocation. 0 indicates   #
#                   nothing. 1 indicates a ship exists there.                  #
# - guessState:     The array that stores the guessed allocation. 0 indicates  #
#                   possible/confirmed, 1 indicates missed/not possible.       #
# - gameState:      The same thing as guessState, except 0 for not checked,    #
#                   1 for missed, 2 for hit.                                   #
# - probState:      Higher for more likely spots for ships.                    #
# - ships:          The array that stores Ship objects.                        #
# - generateRandom: True if the array is to be generated at random.            #
################################################################################
class Board():
    BOARD_SIZE = 10
    DEFAULT_SHIP_SIZES = [5,4,3,3,2]
    
    ############################################################################
    # Initiates a board. Resets first, then generates, and then evaluates.     #
    ############################################################################
    def __init__(self, generateRandom, hiddenState = None, guessState = None, gameState = None):

        self.generateRandom = generateRandom
        self.hitMode = False

        self.reset()
        
        if self.generateRandom:
            self.generate()
        else:
            for ship in self.DEFAULT_SHIP_SIZES:
                result = tuple(input(f"Input the coordinates and orientation for ship of size {ship} e.g. [xyo], [12h], [34v]: "))
                
                x = int(result[0])
                y = int(result[1])
                o = 0
                if result[2] == 'v': o = 1
                
                if o == 0:
                    self.hiddenState[x,y:y+ship] = 1
                else:
                    self.hiddenState[x:x+ship,y] = 1
                self.ships.append(Ship(ship, x, y, o))
        evalBoard(self)

    ############################################################################
    # Resets the board state.                                                  #
    # Clears hiddenState, guessState, ships                                    #
    ############################################################################
    def reset(self):
        self.hiddenState = np.zeros((self.BOARD_SIZE, self.BOARD_SIZE), dtype='int64')
        self.guessState = np.zeros((self.BOARD_SIZE, self.BOARD_SIZE), dtype='int64')
        self.gameState = np.zeros((self.BOARD_SIZE, self.BOARD_SIZE), dtype='int64')
        self.ships = []

    ############################################################################
    # Generates an orientation of ships by random. Only used after a reset.    #
    # adjacent: True if ships may touch. False if ships cannot.                #
    ############################################################################
    def generate(self):
        for shipSize in self.DEFAULT_SHIP_SIZES:
            while True:
                orientation = np.random.randint(2)
                
                if orientation == 0:
                    x = np.random.randint(self.BOARD_SIZE)
                    y = np.random.randint(self.BOARD_SIZE - shipSize + 1)
                else:
                    x = np.random.randint(self.BOARD_SIZE - shipSize + 1)
                    y = np.random.randint(self.BOARD_SIZE)

                if not overlaps(x, y, orientation, shipSize, self.hiddenState):
                    if orientation == 0:
                        self.hiddenState[x,y:y+shipSize] = 1
                    else:
                        self.hiddenState[x:x+shipSize,y] = 1
                    break
            self.ships.append(Ship(shipSize, x, y, orientation))

    ############################################################################
    # String representation of the board state.                                #
    ############################################################################
    def __str__(self):

        # board values
        string = f'''{bcolors.BOLD+bcolors.YELLOW+bcolors.UNDERLINE}    HIDDEN BOARD          GUESS BOARD           GAME BOARD     '''
        for row in range(self.BOARD_SIZE):
            string += f"{bcolors.RESET}\n"
            for i in range(self.BOARD_SIZE):
                match self.hiddenState[row,i]:
                    case 0:
                        string += f"{bcolors.BLUE}0 "
                    case 1:
                        string += f"{bcolors.RED}1 "
            string += f"{bcolors.RESET}| "
            for i in range(self.BOARD_SIZE):
                match self.guessState[row,i]:
                    case 0:
                        string += f"{bcolors.BLUE}0 "
                    case 1:
                        string += f"{bcolors.RED}1 "
            string += f"{bcolors.RESET}| "
            for i in range(self.BOARD_SIZE):
                match self.gameState[row,i]:
                    case 0:
                        string += f"{bcolors.BLUE}0 "
                    case 1:
                        string += f"{bcolors.RED}1 "
                    case 2:
                        string += f"{bcolors.GREEN}2 "
        
        # if at the end of the game, do not print!
        if self.probTotal == 0: return string

        # print the information matrix values, color coded on greyscale of 24 values
        string += f'\n{bcolors.BOLD+bcolors.YELLOW+bcolors.UNDERLINE}                      PROBABILITY MATRIX                       '
        
        pMatrix = self.probState / sum(sum(self.probState))

        colorMatrix = pMatrix / np.amax(pMatrix) * 7
        string += bcolors.RESET
        for i in range(self.BOARD_SIZE):
            string += '\n  '
            for j in range(self.BOARD_SIZE):
                # string += f"\033[38;5;{248 + int(colorMatrix[i,j])}m{str(round(pMatrix[i,j],3)).ljust(5, '0')} "
                # string += f"\033[38;5;{248 + int(colorMatrix[i,j])}m{str(self.probState[i,j]).zfill(5)} "
                string += f"{str(round(pMatrix[i,j], 3)).ljust(5, '0')} "
        return string

    ############################################################################
    # Checks at (x,y) to see if a ship is hit.                                 #
    ############################################################################
    def move(self, x, y):
        
        # if hit
        if self.hiddenState[x,y] == 1:
            
            # find ship and do hit
            for ship in self.ships:
                if ship.overlap(x,y):
                    
                    # update ship hit
                    ship.hit(x,y)
                    
                    # guessState should remain 0 for purposes of algorithm
                    if not ship.sunk:
                        self.gameState[x,y] = 2
                        continue
                        
                    # if ship is sunk, update board states
                    if ship.orientation == 0:
                        self.guessState[ship.x,ship.y:ship.y+ship.size] = 1
                        self.gameState[ship.x,ship.y:ship.y+ship.size] = 2
                    else:
                        self.guessState[ship.x:ship.x+ship.size,ship.y] = 1
                        self.gameState[ship.x:ship.x+ship.size,ship.y] = 2
                            
        # if miss
        else:
            self.guessState[x,y] = 1
            self.gameState[x,y] = 1
            
        # re-evaluate the board in new state
        evalBoard(self)

################################################################################
# SHIP CLASS: Stores individual ship object information.                       #
# ---------------------------------------------------------------------------- #
# INSTANCE VARIABLES:                                                          #
# x, y: Coordinates of the top lerft corner of the ship.                       #
# orientation: 0 = horizontal (along the y-axis), 1 = vertical (along x-axis)  #
# sunk: True if the ship is fully sunk.                                        #
# partsHit: An array, 1 if the part of the ship has been hit, 0 otherwise      #
################################################################################
class Ship():
    def __init__(self, size, x, y, orientation):
        self.size = size
        self.x = x
        self.y = y
        self.orientation = orientation
        self.sunk = False
        self.partsHit = [0] * size

    def __str__(self):
        return f'Ship of size {self.size} at ({self.x},{self.y}) facing direction {self.orientation}, sunk: {self.sunk}'
    
    def __eq__(self, other):
        return type(self) == type(other) and self.size == other.size and self.x == other.x and self.y == other.y and self.orientation == other.orientation

    ############################################################################
    # Returns true if the provided coordinate is on the ship.                  #
    ############################################################################
    def overlap(self, x, y):
        if self.orientation == 0:
            return self.y <= y < self.y+self.size and self.x == x
        else:
            return self.x <= x < self.x+self.size and self.y  == y
    
    ############################################################################
    # Updates instance variables when it is hit at the given coordinates.      #
    # Doesn't check whether the x,y are valid. Make sure to precede with       #
    # the overlap function.                                                    #
    ############################################################################
    def hit(self, x, y):
        if self.orientation == 0:
            self.partsHit[y - self.y] = 1
        else:
            self.partsHit[x - self.x] = 1
        if sum(self.partsHit) == self.size:
            self.sunk = True

if __name__ == '__main__':
    print(f"{bcolors.MAGENTA+bcolors.BOLD+bcolors.UNDERLINE}                                   WELCOME TO BATTLESHIP!")
    print(f"{bcolors.RESET+bcolors.MAGENTA+bcolors.BOLD}=========================================================================================")
    
    # parse random generation rule
    gen = ""
    generateRandom = False
    manualMode = True
    while (len(gen) != 1) and (gen != "y" and gen != "n"):
        gen = str.lower(input(f"{bcolors.CYAN}Would you like to generate a board randomly? Press Y for random, N for manual generation. "))
    if gen == "y": 
        generateRandom = True
    
        # parse manual mode rule
        manual = ""
        while (len(manual) != 1) and (manual != "y" and manual != "n"):
            manual = str.lower(input(f"{bcolors.CYAN}Would you like run the mode manually or automatically run for more results? Press Y for manual, N for auto. "))
        if manual == "n":
            manualMode = False
            # find number
            while True:
                try:
                    numRounds = int(input(f"{bcolors.CYAN}How many rounds would you like to run? "))
                finally:
                    break

    # run it!
    game = Battleship(generateRandom, manualMode, numRounds)