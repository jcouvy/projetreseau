


symbols = [' ', 'O', 'X']
EMPTY = 0
J1 = 1
J2 = 2
NB_CELLS=9

class grid:
    cells = []
    def __init__(self):
        self.cells = []
        for i in range(NB_CELLS):
            self.cells.append(EMPTY)

    def play(self, player, cellNum):
        assert(0<= cellNum and cellNum < NB_CELLS)
        assert(self.cells[cellNum] == EMPTY)
        self.cells[cellNum] = player

    """ Display the state of the game
        Example of output : 
        -------
        |O| |X|
        -------
        |X|O| |
        -------
        | | |O| 
        -------
    """
    def display(self):
        print("-------------")
        for i in range(3):
            print("|",symbols[self.cells[i*3]], "|",  symbols[self.cells[i*3+1]], "|",  symbols[self.cells[i*3+2]], "|");
            print("-------------")


    """ Test if 'player' wins the game"""
    def winner(self, player):
        assert(player==J1 or player==J2)
        # horizontal line
        for y in range(3): 
            if self.cells[y*3] == player and self.cells[y*3+1] == player and self.cells[y*3+2] == player:
                    return True
        # vertical line
        for x in range(3): 
            if self.cells[x] == player and self.cells[3+x] == player and self.cells[6+x] == player:
                    return True
        #diagonals :
        if self.cells[0] == player and self.cells[4] == player and self.cells[8] == player:
            return True
        if self.cells[2] == player and self.cells[4] == player and self.cells[6] == player:
            return True
        return False
    
    """ Return the state of the game: -1 if the game is not over, EMPTY if DRAW; J1 if player 1 wins and J2 if player 2 wins.
    """
    def gameOver(self):
        if self.winner(J1):
            return J1
        if self.winner(J2):
            return J2
        for i in range(NB_CELLS):
            if(self.cells[i]== EMPTY):
                return -1
        return 0
