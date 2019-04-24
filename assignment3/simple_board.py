"""
simple_board.py

Implements a basic Go board with functions to:
- initialize to a given board size
- check if a move is legal
- play a move

The board uses a 1-dimensional representation with padding
"""

import numpy as np
from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER, \
                       PASS, is_black_white, coord_to_point, where1d, \
                       MAXSIZE, NULLPOINT

class SimpleGoBoard(object):

    def get_color(self, point):
        return self.board[point]

    def pt(self, row, col):
        return coord_to_point(row, col, self.size)

    def is_legal(self, point, color):
        """
        Check whether it is legal for color to play on point
        """
        assert is_black_white(color)
        # Special cases
        if point == PASS:
            return True
        elif self.board[point] != EMPTY:
            return False
        if point == self.ko_recapture:
            return False

        # General case: detect captures, suicide
        opp_color = GoBoardUtil.opponent(color)
        self.board[point] = color
        legal = True
        has_capture = self._detect_captures(point, opp_color)
        if not has_capture and not self._stone_has_liberty(point):
            block = self._block_of(point)
            if not self._has_liberty(block): # suicide
                legal = False
        self.board[point] = EMPTY
        return legal

    def _detect_captures(self, point, opp_color):
        """
        Did move on point capture something?
        """
        for nb in self.neighbors_of_color(point, opp_color):
            if self._detect_capture(nb):
                return True
        return False

    def get_empty_points(self):
        """
        Return:
            The empty points on the board
        """
        return where1d(self.board == EMPTY)

    def __init__(self, size):
        """
        Creates a Go board of given size
        """
        assert 2 <= size <= MAXSIZE
        self.reset(size)

    def reset(self, size):
        """
        Creates a start state, an empty board with the given size
        The board is stored as a one-dimensional array
        See GoBoardUtil.coord_to_point for explanations of the array encoding
        """
        self.size = size
        self.NS = size + 1
        self.WE = 1
        self.ko_recapture = None
        self.current_player = BLACK
        self.maxpoint = size * size + 3 * (size + 1)
        self.board = np.full(self.maxpoint, BORDER, dtype = np.int32)
        self.liberty_of = np.full(self.maxpoint, NULLPOINT, dtype = np.int32)
        self._initialize_empty_points(self.board)
        self._initialize_neighbors()

    def copy(self):
        b = SimpleGoBoard(self.size)
        assert b.NS == self.NS
        assert b.WE == self.WE
        b.ko_recapture = self.ko_recapture
        b.current_player = self.current_player
        assert b.maxpoint == self.maxpoint
        b.board = np.copy(self.board)
        return b

    def row_start(self, row):
        assert row >= 1
        assert row <= self.size
        return row * self.NS + 1

    def _initialize_empty_points(self, board):
        """
        Fills points on the board with EMPTY
        Argument
        ---------
        board: numpy array, filled with BORDER
        """
        for row in range(1, self.size + 1):
            start = self.row_start(row)
            board[start : start + self.size] = EMPTY

    def _on_board_neighbors(self, point):
        nbs = []
        for nb in self._neighbors(point):
            if self.board[nb] != BORDER:
                nbs.append(nb)
        return nbs

    def _initialize_neighbors(self):
        """
        precompute neighbor array.
        For each point on the board, store its list of on-the-board neighbors
        """
        self.neighbors = []
        for point in range(self.maxpoint):
            if self.board[point] == BORDER:
                self.neighbors.append([])
            else:
                self.neighbors.append(self._on_board_neighbors(point))

    def is_eye(self, point, color):
        """
        Check if point is a simple eye for color
        """
        if not self._is_surrounded(point, color):
            return False
        # Eye-like shape. Check diagonals to detect false eye
        opp_color = GoBoardUtil.opponent(color)
        false_count = 0
        at_edge = 0
        for d in self._diag_neighbors(point):
            if self.board[d] == BORDER:
                at_edge = 1
            elif self.board[d] == opp_color:
                false_count += 1
        return false_count <= 1 - at_edge # 0 at edge, 1 in center

    def _is_surrounded(self, point, color):
        """
        check whether empty point is surrounded by stones of color.
        """
        for nb in self.neighbors[point]:
            nb_color = self.board[nb]
            if nb_color != color:
                return False
        return True

    def _stone_has_liberty(self, stone):
        lib = self.find_neighbor_of_color(stone, EMPTY)
        return lib != None

    def _get_liberty(self, block):
        """
        Find any liberty of the given block.
        Returns None in case there is no liberty.
        block is a numpy boolean array
        """
        for stone in where1d(block):
            lib = self.find_neighbor_of_color(stone, EMPTY)
            if lib != None:
                return lib
        return None

    def _has_liberty(self, block):
        """
        Check if the given block has any liberty.
        Also updates the liberty_of array.
        block is a numpy boolean array
        """
        lib = self._get_liberty(block)
        if lib != None:
            assert self.get_color(lib) == EMPTY
            for stone in where1d(block):
                self.liberty_of[stone] = lib
            return True
        return False

    def _block_of(self, stone):
        """
        Find the block of given stone
        Returns a board of boolean markers which are set for
        all the points in the block
        """
        marker = np.full(self.maxpoint, False, dtype = bool)
        pointstack = [stone]
        color = self.get_color(stone)
        assert is_black_white(color)
        marker[stone] = True
        while pointstack:
            p = pointstack.pop()
            neighbors = self.neighbors_of_color(p, color)
            for nb in neighbors:
                if not marker[nb]:
                    marker[nb] = True
                    pointstack.append(nb)
        return marker

    def _fast_liberty_check(self, nb_point):
        lib = self.liberty_of[nb_point]
        if lib != NULLPOINT and self.get_color(lib) == EMPTY:
            return True # quick exit, block has a liberty
        if self._stone_has_liberty(nb_point):
            return True # quick exit, no need to look at whole block
        return False

    def _detect_capture(self, nb_point):
        """
        Check whether opponent block on nb_point is captured.
        Returns boolean.
        """
        if self._fast_liberty_check(nb_point):
            return False
        opp_block = self._block_of(nb_point)
        return not self._has_liberty(opp_block)

    def _detect_and_process_capture(self, nb_point):
        """
        Check whether opponent block on nb_point is captured.
        If yes, remove the stones.
        Returns the stone if only a single stone was captured,
            and returns None otherwise.
        This result is used in play_move to check for possible ko
        """
        if self._fast_liberty_check(nb_point):
            return None
        opp_block = self._block_of(nb_point)
        if self._has_liberty(opp_block):
            return None
        captures = list(where1d(opp_block))
        self.board[captures] = EMPTY
        self.liberty_of[captures] = NULLPOINT
        single_capture = None
        if len(captures) == 1:
            single_capture = nb_point
        return single_capture

    def play_move(self, point, color):
        """
        Play a move of color on point
        Returns boolean: whether move was legal
        """
        assert is_black_white(color)
        # Special cases
        if point == PASS:
            self.ko_recapture = None
            self.current_player = GoBoardUtil.opponent(color)
            return True
        elif self.board[point] != EMPTY:
            return False
        if point == self.ko_recapture:
            return False

        # General case: deal with captures, suicide, and next ko point
        opp_color = GoBoardUtil.opponent(color)
        in_enemy_eye = self._is_surrounded(point, opp_color)
        self.board[point] = color
        single_captures = []
        neighbors = self.neighbors[point]
        for nb in neighbors:
            if self.board[nb] == opp_color:
                single_capture = self._detect_and_process_capture(nb)
                if single_capture != None:
                    single_captures.append(single_capture)
        if not self._stone_has_liberty(point):
            # check suicide of whole block
            block = self._block_of(point)
            if not self._has_liberty(block): # undo suicide move
                self.board[point] = EMPTY
                return False
        self.ko_recapture = None
        if in_enemy_eye and len(single_captures) == 1:
            self.ko_recapture = single_captures[0]
        self.current_player = GoBoardUtil.opponent(color)
        return True

    def neighbors_of_color(self, point, color):
        """ List of neighbors of point of given color """
        nbc = []
        for nb in self.neighbors[point]:
            if self.get_color(nb) == color:
                nbc.append(nb)
        return nbc

    def find_neighbor_of_color(self, point, color):
        """ Return one neighbor of point of given color, or None """
        for nb in self.neighbors[point]:
            if self.get_color(nb) == color:
                return nb
        return None

    def _neighbors(self, point):
        """ List of all four neighbors of the point """
        return [point - 1, point + 1, point - self.NS, point + self.NS]

    def _diag_neighbors(self, point):
        """ List of all four diagonal neighbors of point """
        return [point - self.NS - 1,
                point - self.NS + 1,
                point + self.NS - 1,
                point + self.NS + 1]

    def _point_to_coord(self, point):
        """
        Transform point index to row, col.

        Arguments
        ---------
        point

        Returns
        -------
        x , y : int
        coordination of the board  1<= x <=size, 1<= y <=size .
        """
        if point is None:
            return 'pass'
        row, col = divmod(point, self.NS)
        return row, col

    def is_legal_gomoku(self, point, color):
        """
            Check whether it is legal for color to play on point, for the game of gomoku
            """
        return self.board[point] == EMPTY

    def play_move_gomoku(self, point, color):
        """
            Play a move of color on point, for the game of gomoku
            Returns boolean: whether move was legal
            """
        assert is_black_white(color)
        assert point != PASS
        if self.board[point] != EMPTY:
            return False
        self.board[point] = color
        self.current_player = GoBoardUtil.opponent(color)
        return True

    def _point_direction_check_connect_gomoko(self, point, shift):
        """
        Check if the point has connect5 condition in a direction
        for the game of Gomoko.
        """
        color = self.board[point]
        count = 1
        d = shift
        p = point
        while True:
            p = p + d
            if self.board[p] == color:
                count = count + 1
                if count == 5:
                    break
            else:
                break
        d = -d
        p = point
        while True:
            p = p + d
            if self.board[p] == color:
                count = count + 1
                if count == 5:
                    break
            else:
                break
        assert count <= 5
        return count == 5

    def _direction_check_connect_gomoko(self, point, shift, max):
        """
        Check if the point has connect4 condition in a direction
        for the game of Gomoko.
        """
        color = self.board[point]
        count = 1
        pointWin = []
        d = shift
        p = point
        while True:
            p = p + d
            if self.board[p] == color:
                count = count + 1
                if count == max:
                    if self.is_legal(p+d,color):
                        pointWin.append(p+d)
                    elif self.is_legal(point+(-shift), color):
                        pointWin.append(point+(-shift))
                    break
            else:
                break
        d = -d
        p = point
        while True:
            p = p + d
            if self.board[p] == color:
                count = count + 1
                if count == max:
                    if self.is_legal(p+d,color):
                        pointWin.append(p+d)
                    break
            else:
                break
       # assert count <= max
        return count == max, pointWin

    def point_check_game_end_gomoku(self, point):
        """
            Check if the point causes the game end for the game of Gomoko.
            """
        # check horizontal
        if self._point_direction_check_connect_gomoko(point, 1):
            return True

        # check vertical
        if self._point_direction_check_connect_gomoko(point, self.NS):
            return True

        # check y=x
        if self._point_direction_check_connect_gomoko(point, self.NS + 1):
            return True

        # check y=-x
        if self._point_direction_check_connect_gomoko(point, self.NS - 1):
            return True

        return False

    def point_check_game_end_move_gomoku(self, point, max):
        """
            Check if the point causes the game end for the game of Gomoko.
            """
        # check horizontal
        check, pointToWin = self._direction_check_connect_gomoko(point, 1, max)
        if check:
            return pointToWin

        # check vertical
        check, pointToWin = self._direction_check_connect_gomoko(point, self.NS, max)
        if check:
            return pointToWin

        # check y=x
        check, pointToWin = self._direction_check_connect_gomoko(point, self.NS + 1, max)
        if check:
            return pointToWin

        # check y=-x
        check, pointToWin = self._direction_check_connect_gomoko(point, self.NS - 1, max)
        if check:
            return pointToWin

        return False

    def check_game_end_move_gomoku_win_counterwin(self, max):
        """
            Check if the game ends for the game of Gomoku.
            """
        white_points = where1d(self.board == WHITE)
        black_points = where1d(self.board == BLACK)
        win = []
        for point in white_points:
            pointWin = self.point_check_game_end_move_gomoku(point, max)
            if pointWin and pointWin not in win:
                win.append(pointWin)
        blackwin = []
        for point in black_points:
            pointWin = self.point_check_game_end_move_gomoku(point, max)
            if pointWin and pointWin not in blackwin:
                blackwin.append(pointWin)
        return win, blackwin

    def check_game_end_move_gomoku(self, color, max):
        """
            Check if the game ends for the game of Gomoku.
            """
        white_points = where1d(self.board == WHITE)
        black_points = where1d(self.board == BLACK)
        win = []
        if color == 2:
            for point in white_points:
                pointWin = self.point_check_game_end_move_gomoku(point, max)
                if pointWin:
                    win.append(pointWin)
            if len(win) > 0:
                return True, win
        else:
            for point in black_points:
                pointWin = self.point_check_game_end_move_gomoku(point, max)
                if pointWin:
                    win.append(pointWin)
            if len(win) > 0:
                return True, win
        return False, None

    def check_game_end_gomoku(self):
        """
            Check if the game ends for the game of Gomoku.
            """
        white_points = where1d(self.board == WHITE)
        black_points = where1d(self.board == BLACK)

        for point in white_points:
            if self.point_check_game_end_gomoku(point):
                return True, WHITE

        for point in black_points:
            if self.point_check_game_end_gomoku(point):
                return True, BLACK

        return False, None
  
    def direction_check_connect_gomoko(self, point, shift, max):
        """
        Check if the point has connect4 condition in a direction
        for the game of Gomoko.
        """
        color = self.board[point]
        count = 1
        pointWin = []
        d = shift
        p = point
        while True:
            p = p + d
            if self.board[p] == color:
                count = count + 1
                if count == max:
                    if self.is_legal(p+d,color):
                        pointWin.append(p+d)
                    elif self.is_legal(point+(-shift), color):
                        pointWin.append(point+(-shift))
                    break
            else:
                break
        d = -d
        p = point
        while True:
            p = p + d
            if self.board[p] == color:
                count = count + 1
                if count == max:
                    if self.is_legal(p+d,color):
                        pointWin.append(p+d)
                    break
            else:
                break
        return count == max, pointWin
    def order_the_point(self,color):
        white_points = where1d(self.board == WHITE)
        black_points = where1d(self.board == BLACK)
        final_final_list = []
        final_4 = []
        final_3 = []
        final_2 = []
        final_1 = []
        if color == 2:
            for point in white_points:
                # check 4 block first:
                # here we need 2 lists to track the duplicate elements
                if self.check_n(point,4)!= False:
                    list_temp = self.check_n(point,4)
                    list_4 = [x for x in list_temp if x not in final_4]
                    # for all points
                    final_4 = final_4 + list_4

            for point in white_points:
                if self.check_n(point,3)!= False:
                    list_temp = self.check_n(point,3)
                    # remove the duplication
                    list_3 = [x for x in list_temp if x not in final_3]
                    # combine these 2
                    final_3 = final_3 + list_3
            final_3 = [x for x in final_3 if x not in final_4]
            final_final_list = final_4 + final_3
            for point in white_points:
                if self.check_n(point,2)!= False:
                    list_temp = self.check_n(point,2)
                    # remove the duplication
                    list_2 = [x for x in list_temp if x not in final_2]
                    final_2 = final_2 + list_2
            final_2 = [x for x in final_2 if x not in final_final_list]
            final_final_list = final_final_list + final_2
            for point in white_points:
                if self.check_n(point,1)!= False:
                    list_temp = self.check_n(point,1)
                    # remove the duplication
                    list_1 = [x for x in list_temp if x not in final_1]
                    final_1 = final_1 + list_1
            final_1 = [x for x in final_1 if x not in final_final_list]
            final_final_list = final_final_list + final_1
            list_temp = self.generate_legal_moves(color)
            total_list = [x for x in list_temp if x not in final_final_list]
            final_final_list = final_final_list + total_list

        else:
            for point in black_points:
                # check 4 block first:
                # here we need 2 lists to track the duplicate elements
                if self.check_n(point,4)!= False:
                    list_temp = self.check_n(point,4)
                    list_4 = [x for x in list_temp if x not in final_4]
                    # for all points
                    final_4 = final_4 + list_4

            for point in black_points:
                if self.check_n(point,3)!= False:
                    list_temp = self.check_n(point,3)
                    # remove the duplication
                    list_3 = [x for x in list_temp if x not in final_3]
                    # combine these 2
                    final_3 = final_3 + list_3
            final_3 = [x for x in final_3 if x not in final_4]
            final_final_list = final_4 + final_3
            for point in black_points:
                if self.check_n(point,2)!= False:
                    list_temp = self.check_n(point,2)
                    # remove the duplication
                    list_2 = [x for x in list_temp if x not in final_2]
                    final_2 = final_2 + list_2
            final_2 = [x for x in final_2 if x not in final_final_list]
            final_final_list = final_final_list + final_2
            for point in black_points:
                if self.check_n(point,1)!= False:
                    list_temp = self.check_n(point,1)
                    # remove the duplication
                    list_1 = [x for x in list_temp if x not in final_1]
                    final_1 = final_1 + list_1
            final_1 = [x for x in final_1 if x not in final_final_list]
            final_final_list = final_final_list + final_1
            list_temp = self.generate_legal_moves(color)
            total_list = [x for x in list_temp if x not in final_final_list]
            final_final_list = final_final_list + total_list
        return final_final_list

        #what we need here is to boost the speed of minimax by order the emptyList
    def check_n(self, point, max):
        list_p = []
        # check horizontal
        check, pointToWin = self.direction_check_connect_gomoko(point, 1, max)
        if check:
            list_p = list_p + pointToWin

        # check vertical
        check, pointToWin = self.direction_check_connect_gomoko(point, self.NS, max)
        if check:
            list_p = list_p + pointToWin

        # check y=x
        check, pointToWin = self.direction_check_connect_gomoko(point, self.NS + 1, max)
        if check:
            list_p = list_p + pointToWin

        # check y=-x
        check, pointToWin = self.direction_check_connect_gomoko(point, self.NS - 1, max)
        if check:
            list_p = list_p + pointToWin
        if list_p == []:
            return False
        else:
            list_r = list(set(list_p))
            return list_r

    def generate_legal_moves(self,color):
        """
        generate a list of all legal moves on the board.
        Does not include the Pass move.

        Arguments
        ---------
        board : np.array
            a SIZExSIZE array representing the board
        color : {'b','w'}
            the color to generate the move for.
        """
        moves = self.get_empty_points()
        legal_moves = []
        for move in moves:
            legal_moves.append(move)
        return legal_moves
    def undo(self,point):
        #print(1)
        self.board[point] = 0
        
        
    def final_check(self, first, second, points, empty, count):
        
        
        if first == True:
            if count >= points:
                if empty == 1:
                    return True
        elif second == True:
            if count >= points:
                if empty == 2: 
                    return True
        elif count >= points:
            return True
        else:
            return False
    
    def straight_check(self, point, shift, color, points, empty1, empty2):
        
        # dir  check
        count = 1
        emp_cell = 0
        d = shift
        p = point
        while True:
            p = p + d
            if self.board[p] == color:
                count = count + 1
            else:
                if self.board[p] == EMPTY:
                    emp_cell = emp_cell + 1
                break    

        p = point
        while True:
            p = p - d
            if self.board[p] == color:
                count = count + 1
            else:
                if self.board[p] == EMPTY:
                    emp_cell = emp_cell + 1
                break
            
        return self.final_check(empty1,empty2, points, emp_cell, count)
          

    
    def open_four(self, color): 
        # if you have a move that creates an open four position of type .XXXX., then play it. 
        # Examples of this scenario are: .X.XX. and .XXX..
     
        found_points = []
        empty_pts = where1d(self.board == 0)
        
        for point in empty_pts:
            if self.straight_check(point, 1, color, 4, False, True): #f (1)
                found_points.append(point)
            elif self.straight_check(point, self.NS, color, 4, False, True):
                found_points.append(point)
            elif self.straight_check(point, self.NS + 1, color, 4, False, True):
                found_points.append(point)
            elif self.straight_check(point, self.NS - 1, color, 4, False, True):
                found_points.append(point)
        
        
        
        return found_points 
    
    
    def block_open_four(self, color):
        # play a move that prevents the opponent from getting an open four. For example, the situation ..OOO.. can be blocked by moves .XOOO.. or ..OOOX.
        
        found_points = []
        empty_pts = where1d(self.board == 0)
        
        versus_color = GoBoardUtil.opponent(color)
        
        for point in empty_pts:




            if self.straight_check(point, 1, versus_color, 4, True, False):
                if point not in found_points:
                    found_points.append(point)
            elif self.straight_check(point, self.NS , versus_color, 4, True, False):
                if point not in found_points:
                    found_points.append(point)
            elif self.straight_check(point, self.NS+1, versus_color, 4, True, False):
                if point not in found_points:
                    found_points.append(point)
            elif self.straight_check(point, self.NS-1, versus_color, 4, True, False):
                if point not in found_points:
                    found_points.append(point)



            if self.straight_check(point, 1, versus_color, 3, True, False):
                if point not in found_points:
                    found_points.append(point)
            elif self.straight_check(point, self.NS , versus_color, 3, True, False):
                if point not in found_points:
                    found_points.append(point)
            elif self.straight_check(point, self.NS+1, versus_color, 3, True, False):
                if point not in found_points:
                    found_points.append(point)
            elif self.straight_check(point, self.NS-1, versus_color, 3, True, False):
                if point not in found_points:
                    found_points.append(point)
            
            if self.straight_check(point, 1, versus_color, 4, False, True):
                if point not in found_points:
                    found_points.append(point)
            elif self.straight_check(point, self.NS , versus_color, 4, False, True):
                if point not in found_points:
                    found_points.append(point)
            elif self.straight_check(point, self.NS+1, versus_color, 4, False, True):
                if point not in found_points:
                    found_points.append(point)
            elif self.straight_check(point, self.NS-1, versus_color, 4, False, True):
                if point not in found_points:
                    found_points.append(point)
                
        return found_points

    