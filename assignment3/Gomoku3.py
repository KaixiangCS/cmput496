#!/usr/bin/python3
#/usr/local/bin/python3
# Set the path to your python3 above

from gtp_connection import GtpConnection
from board_util import GoBoardUtil, MAXSIZE
from simple_board import SimpleGoBoard

class Gomoku():
    def __init__(self):
        """
        Gomoku player that selects moves randomly
        from the set of legal moves.
        Passe/resigns only at the end of game.
        """
        self.name = "GomokuAssignment2"
        self.version = 1.0
        self.N = 10

    def get_move(self, board, color):
        return GoBoardUtil.generate_random_move_gomoku(board)


    def rulebased(self, board, toPlay):
        winblockwin = self.win_blockwin(board, toPlay)
        if winblockwin:
            return winblockwin
        open4 = self.openfour_cmd(toPlay, board)
        if open4:
            return open4
        blockopen4 = self.blockopenfour_cmd(toPlay, board)
        if blockopen4:
            return blockopen4
        return []
        
    def win_blockwin(self, board, toPlay):
        #check if there is a win condition for both black and white
        whitewin,blackwin = board.check_game_end_move_gomoku_win_counterwin(4)
        if toPlay == 'b':
            #if too play is black: make win and blockwin for black
            if len(blackwin) > 0:
                return(blackwin)
            elif len(whitewin) > 0:
                return(whitewin)
        else:
            #if to play is white then make win and block wins for white
            if len(whitewin) > 0:
                return(whitewin)
            elif len(blackwin) > 0:
                return(blackwin)
        return False

    def readable_move_list(self, movelist, board):
        gtp_moves = []
        for move in movelist:
            move = move[0]
            coords = self.point_to_coord(move, board.size)
            gtp_moves.append(self.format_point(coords, board))
        sorted_moves = ' '.join(sorted(gtp_moves))
        return sorted_moves

    def format_point(self, move, board):
        """
        Return move coordinates as a string such as 'a1', or 'pass'.
        """
        column_letters = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
        #column_letters = "abcdefghjklmnopqrstuvwxyz"
        if move == None:
            return "pass"
        row, col = move
        if not 0 <= row < MAXSIZE or not 0 <= col < MAXSIZE:
            raise ValueError
        return column_letters[col - 1]+ str(row)

    def point_to_coord(self, point, boardsize):
        """
        Transform point given as board array index 
        to (row, col) coordinate representation.
        Special case: PASS is not transformed
        """
        if point == None:
            return None
        else:
            NS = boardsize + 1
            return divmod(point, NS)
    
    def openfour_cmd(self, toPlay, board):
        final_answer = []
        color = toPlay
        points = board.open_four(color)
        if len(points) > 0:
            for point in points:
                final_answer.append(point)
        return final_answer

    def blockopenfour_cmd(self, toPlay, board):
        final_answer = []
        
        color = toPlay
        points = board.block_open_four(color)
        if len(points) > 0:
            for point in points:
                final_answer.append(point)        
        return final_answer




    def simulate(self, board,color, legal_moves, mode):
        winList = []
        if not legal_moves:
            legal_moves = GoBoardUtil.generate_legal_moves_gomoku(board)
        check = board.check_game_end_gomoku()

        if check[0] == True:
            return
        elif legal_moves == []:
            return
        if mode == 'random':
            mode_sim = 'random'
        else:
            mode_sim = 'rule'
        for move in legal_moves:
            s = 0
            for i in range(self.N):
                temp_b = board.copy()
                temp_b.play_move_gomoku(move,color)
                s = s + self.simulate_iter(temp_b,color,mode_sim)
            s = s/10
            winList.append(s)
       
        index = winList.index(max(winList))
        if winList:    
            index = winList.index(max(winList))
        best = legal_moves[index]
        return best

    def simulate_iter(self,board, player, mode):
        is_end,win = board.check_game_end_gomoku()
        if is_end:
            if win == player:
                return 2
            else:
                return 0
        if mode == "random":
            move = GoBoardUtil.generate_random_move_gomoku(board)
        else:
            legalmoves = self.rulebased(board, player)
            if legalmoves:
                move = legalmoves[:1]
                move = move[0]
            else:
                move = GoBoardUtil.generate_random_move_gomoku(board)
        if move == None:
            return 1
        board.play_move_gomoku(move,board.current_player)
        return self.simulate_iter(board, player, mode)

def run():
    """
    start the gtp connection and wait for commands.
    """
    board = SimpleGoBoard(7)
    con = GtpConnection(Gomoku(), board)
    con.start_connection()

if __name__=='__main__':
    run()
