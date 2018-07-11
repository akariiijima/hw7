#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import json
import logging
import random
import webapp2
import time

# Reads json description of the board and provides simple interface.
class Game:
	# Takes json or a board directly.
	def __init__(self, body=None, board=None):
                if body:
		        game = json.loads(body)
                        self._board = game["board"]
                else:
                        self._board = board

	# Returns piece on the board.
	# 0 for no pieces, 1 for player 1, 2 for player 2.
	# None for coordinate out of scope.
	def Pos(self, x, y):
		return Pos(self._board["Pieces"], x, y)

	# Returns who plays next.
	def Next(self):
		return self._board["Next"]

	# Returns the array of valid moves for next player.
	# Each move is a dict
	#   "Where": [x,y]
	#   "As": player number
	def ValidMoves(self):
                moves = []
                for y in xrange(1,9):
                        for x in xrange(1,9):
                                move = {"Where": [x,y],
                                        "As": self.Next()}
                                if self.NextBoardPosition(move):
                                        moves.append(move)
                return moves

	# Helper function of NextBoardPosition.  It looks towards
	# (delta_x, delta_y) direction for one of our own pieces and
	# flips pieces in between if the move is valid. Returns True
	# if pieces are captured in this direction, False otherwise.
	def __UpdateBoardDirection(self, new_board, x, y, delta_x, delta_y):
		player = self.Next()
		opponent = 3 - player
		look_x = x + delta_x
		look_y = y + delta_y
		flip_list = []
		while Pos(new_board, look_x, look_y) == opponent:
			flip_list.append([look_x, look_y])
			look_x += delta_x
			look_y += delta_y
		if Pos(new_board, look_x, look_y) == player and len(flip_list) > 0:
                        # there's a continuous line of our opponents
                        # pieces between our own pieces at
                        # [look_x,look_y] and the newly placed one at
                        # [x,y], making it a legal move.
			SetPos(new_board, x, y, player)
			for flip_move in flip_list:
				flip_x = flip_move[0]
				flip_y = flip_move[1]
				SetPos(new_board, flip_x, flip_y, player)
                        return True
                return False

	# Takes a move dict and return the new Game state after that move.
	# Returns None if the move itself is invalid.
	def NextBoardPosition(self, move):
		x = move["Where"][0]
		y = move["Where"][1]
                if self.Pos(x, y) != 0:
                        # x,y is already occupied.
                        return None
		new_board = copy.deepcopy(self._board)
                pieces = new_board["Pieces"]

		if not (self.__UpdateBoardDirection(pieces, x, y, 1, 0)
                        | self.__UpdateBoardDirection(pieces, x, y, 0, 1)
		        | self.__UpdateBoardDirection(pieces, x, y, -1, 0)
		        | self.__UpdateBoardDirection(pieces, x, y, 0, -1)
		        | self.__UpdateBoardDirection(pieces, x, y, 1, 1)
		        | self.__UpdateBoardDirection(pieces, x, y, -1, 1)
		        | self.__UpdateBoardDirection(pieces, x, y, 1, -1)
		        | self.__UpdateBoardDirection(pieces, x, y, -1, -1)):
                        # Nothing was captured. Move is invalid.
                        return None
                
                # Something was captured. Move is valid.
                new_board["Next"] = 3 - self.Next()
		#return Game(board=new_board)
                return new_board

# Returns piece on the board.
# 0 for no pieces, 1 for player 1, 2 for player 2.
# None for coordinate out of scope.
#
# Pos and SetPos takes care of converting coordinate from 1-indexed to
# 0-indexed that is actually used in the underlying arrays.
def Pos(board, x, y):
	if 1 <= x and x <= 8 and 1 <= y and y <= 8:
		return board[y-1][x-1]
	return None

# Set piece on the board at (x,y) coordinate
def SetPos(board, x, y, piece):
	if x < 1 or 8 < x or y < 1 or 8 < y or piece not in [0,1,2]:
		return False
	board[y-1][x-1] = piece

# Debug function to pretty print the array representation of board.
def PrettyPrint(board, nl="<br>"):
	s = ""
	for row in board:
		for piece in row:
			s += str(piece)
		s += nl
	return s

def PrettyMove(move):
	m = move["Where"]
	return '%s%d' % (chr(ord('A') + m[0] - 1), m[1])

class MainHandler(webapp2.RequestHandler):
    # Handling GET request, just for debugging purposes.
    # If you open this handler directly, it will show you the
    # HTML form here and let you copy-paste some game's JSON
    # here for testing.
    def get(self):
        if not self.request.get('json'):
          self.response.write("""
<body><form method=get>
Paste JSON here:<p/><textarea name=json cols=80 rows=24></textarea>
<p/><input type=submit>
</form>
</body>
""")
          return
        else:
          g = Game(self.request.get('json'))
          self.pickMove(g)

    def post(self):
    	# Reads JSON representation of the board and store as the object.
    	g = Game(self.request.body)
        # Do the picking of a move and print the result.
        self.pickMove(g)

        
    def pickMove(self, g):
        # Gets all valid moves.
    	valid_moves = g.ValidMoves()  
        
        def count_black(board):
                score = 0
                corner = [0,0,0,0]
               
                for y in xrange(0,8):
                        for x in xrange(0,8):
                                if board["Pieces"][y][x] == 1:
                                        score += 1
                                if (x==2 or x==5) and (y==2 or y==5) and board["Pieces"][y][x]==1:#filled center corner
                                        score += 1
                                if (x==0 or x==7) and (y==0 or y==7) and board["Pieces"][y][x]==1:#filled corner
                                        score += 10
                                        if x==0 and y==0:
                                                corner[0] += 1
                                        if x==7 and y==0:
                                                corner[1] += 1
                                        if x==0 and y==7:
                                                corner[2] += 1
                                        if x==7 and y==7:
                                                corner[3] += 1
                filled_path_order0 = 0
                filled_path_count0 = 0
                filled_path_order1 = 0
                filled_path_order2 = 0
                for y in xrange(0,8):
                        for x in xrange(0,8):
                                if filled_path_count0 == 6:
                                        filled_path_count0 = 0
                                        filled_path_order0 = 0
                                #blanked corner process
                                if (x==0 or x==1) and (y==0 or y==1) and corner[0] == 0 and board["Pieces"][y][x]==1:
                                        score -= 20
                                if (x==6 or x==7) and (y==0 or y==1) and corner[1] == 0 and board["Pieces"][y][x]==1:
                                        score -= 20
                                if (x==0 or x==1) and (y==6 or y==7) and corner[2] == 0 and board["Pieces"][y][x]==1:
                                        score -= 20
                                if (x==6 or x==7) and (y==6 or y==7) and corner[3] == 0 and board["Pieces"][y][x]==1:
                                        score -= 20
                                #filled corner process(check 4 edges)
                                if ((y==0 and x!=0 and x!=7) or (x==0 and y!=0 and y!=7)) and corner[0] != 0:
                                        filled_path_count0 += 1
                                        if board["Pieces"][y][x]==1 and filled_path_order0 == 0:
                                                score += 10
                                        else:
                                                filled_path_order0 = 1
                                if (x==7 and y!=0 and y!=7) and corner[1] != 0:
                                        if board["Pieces"][y][x]==1 and filled_path_order1 == 0:
                                                score += 10
                                        else:
                                                filled_path_order1 = 1
                                if (y==7 and x!=0 and x!=7) and corner[2] != 0:
                                        if board["Pieces"][y][x]==1 and filled_path_order2 == 0:
                                                score += 10
                                        else:
                                                filled_path_order2 = 1

                filled_path_order3 = 0
                filled_path_count3 = 0
                filled_path_order1 = 0
                filled_path_order2 = 0
                for y in reversed(xrange(0,8)):
                        for x in reversed(xrange(0,8)):
                                if filled_path_count3 == 6:
                                        filled_path_count3 = 0
                                        filled_path_order3 = 0
                                #filled corner process(check 4 edges)
                                if ((y==7 and x!=0 and x!=7) or (x==7 and y!=0 and y!=7)) and corner[3] != 0:
                                        filled_path_count3 += 1
                                        if board["Pieces"][y][x]==1 and filled_path_order3 == 0:
                                                score += 10
                                        else:
                                                filled_path_order3 = 1
                                if (y==0 and x!=0 and x!=7) and corner[1] != 0:
                                        if board["Pieces"][y][x]==1 and filled_path_order1 == 0:
                                                score += 10
                                        else:
                                                filled_path_order1 = 1
                                if (x==0 and y!=0 and y!=7) and corner[2] != 0:
                                        if board["Pieces"][y][x]==1 and filled_path_order2 == 0:
                                                score += 10
                                        else:
                                                filled_path_order2 = 1                            
                                        
                                                
                return score



        
        def count_white(board):
                score = 0
                corner = [0,0,0,0]
               
                for y in xrange(0,8):
                        for x in xrange(0,8):
                                if board["Pieces"][y][x] == 2:
                                        score += 1
                                if (x==2 or x==5) and (y==2 or y==5) and board["Pieces"][y][x]==2:#filled center corner
                                        score += 1
                                if (x==0 or x==7) and (y==0 or y==7) and board["Pieces"][y][x]==2:#filled corner
                                        score += 10
                                        if x==0 and y==0:
                                                corner[0] += 1
                                        if x==7 and y==0:
                                                corner[1] += 1
                                        if x==0 and y==7:
                                                corner[2] += 1
                                        if x==7 and y==7:
                                                corner[3] += 1
                filled_path_order0 = 0
                filled_path_count0 = 0
                filled_path_order1 = 0
                filled_path_order2 = 0
                for y in xrange(0,8):
                        for x in xrange(0,8):
                                if filled_path_count0 == 6:
                                        filled_path_count0 = 0
                                        filled_path_order0 = 0
                                #blanked corner process
                                if (x==0 or x==1) and (y==0 or y==1) and corner[0] == 0 and board["Pieces"][y][x]==2:
                                        score -= 20
                                if (x==6 or x==7) and (y==0 or y==1) and corner[1] == 0 and board["Pieces"][y][x]==2:
                                        score -= 20
                                if (x==0 or x==1) and (y==6 or y==7) and corner[2] == 0 and board["Pieces"][y][x]==2:
                                        score -= 20
                                if (x==6 or x==7) and (y==6 or y==7) and corner[3] == 0 and board["Pieces"][y][x]==2:
                                        score -= 20
                                #filled corner process(check 4 edges)
                                if ((y==0 and x!=0 and x!=7) or (x==0 and y!=0 and y!=7)) and corner[0] != 0:
                                        filled_path_count0 += 1
                                        if board["Pieces"][y][x]==2 and filled_path_order0 == 0:
                                                score += 10
                                        else:
                                                filled_path_order0 = 1
                                if (x==7 and y!=0 and y!=7) and corner[1] != 0:
                                        if board["Pieces"][y][x]==2 and filled_path_order1 == 0:
                                                score += 10
                                        else:
                                                filled_path_order1 = 1
                                if (y==7 and x!=0 and x!=7) and corner[2] != 0:
                                        if board["Pieces"][y][x]==2 and filled_path_order2 == 0:
                                                score += 10
                                        else:
                                                filled_path_order2 = 1

                filled_path_order3 = 0
                filled_path_count3 = 0
                filled_path_order1 = 0
                filled_path_order2 = 0
                for y in reversed(xrange(0,8)):
                        for x in reversed(xrange(0,8)):
                                if filled_path_count3 == 6:
                                        filled_path_count3 = 0
                                        filled_path_order3 = 0
                                #filled corner process(check 4 edges)
                                if ((y==7 and x!=0 and x!=7) or (x==7 and y!=0 and y!=7)) and corner[3] != 0:
                                        filled_path_count3 += 1
                                        if board["Pieces"][y][x]==2 and filled_path_order3 == 0:
                                                score += 10
                                        else:
                                                filled_path_order3 = 1
                                if (y==0 and x!=0 and x!=7) and corner[1] != 0:
                                        if board["Pieces"][y][x]==2 and filled_path_order1 == 0:
                                                score += 10
                                        else:
                                                filled_path_order1 = 1
                                if (x==0 and y!=0 and y!=7) and corner[2] != 0:
                                        if board["Pieces"][y][x]==2 and filled_path_order2 == 0:
                                                score += 10
                                        else:
                                                filled_path_order2 = 1                            
                                        
                                                
                return score


        def checked_moves(moves):
                checked_moves = []
                for i in xrange(len(moves)):
                        for y in xrange(3,7):
                                for x in xrange(3,7):
                                        if moves[i]["Where"] == [x,y]:
                                                checked_moves.append(moves[i])
                if len(checked_moves) == 0:
                        return moves
                else:
                        return checked_moves         

        def min_max(board,depth,g,time1):#player1 gets min, player2 gets max
                time2 = time.time()
                if time2 - time1 > 15:#Stop min_max over 15s
                        return "stop",{}
                if depth < 1:#Repeat min_max until depth > 100
		        return  count_white(board) - count_black(board),{}
                #moves = checked_moves(g.ValidMoves())#Select priority center valid moves but there are no choice, select all valid moves
                moves = g.ValidMoves()
                best_score = 1000 if board["Next"] == 1 else -1000
                best_move = {}
    	        for i in range(len(moves)):
                        next_board = g.NextBoardPosition(moves[i])
                        score,move = min_max(next_board,depth-1,g,time1)
                        if score == "stop":#timeout process
                                best_move = {}
                                best_score = "stop"
                                break
                        if board["Next"] == 1:#player1 process
                                if score < best_score:
                                        best_score = score
                                        best_move = moves[i]
                        if board["Next"] == 2:#player2 process
                                if score > best_score:
                                        best_score = score
                                        best_move = moves[i]
                return best_score,best_move 
        
        
    	if len(valid_moves) == 0:
    		# Passes if no valid moves.
    		self.response.write("PASS")
    	else:
    		# Chooses a valid move randomly if available.
                # TO STEP STUDENTS:
                # You'll probably want to change how this works, to do something
                # more clever than just picking a random move.
	    	#move1 = random.choice(valid_moves)
                move = []
                time1 = time.time()
                for i in range(1,6):
                        (best_score, best_move) = min_max(g._board,i,g,time1)
                        if best_move == {}:
                                break
                        else:
                                move.append(best_move)

                time2 = time.time()
                logging.info("============= wow!! ==============")
                logging.info(move)
                logging.info(time1)
                logging.info(time2)
                logging.info("============= wow!! ==============")
    		self.response.write(PrettyMove(move[len(move)-1]))
                #self.response.write(PrettyMove(best_move))

app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)
