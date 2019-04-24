import time
from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER, PASS, \
                       MAXSIZE, coord_to_point
import random
import numpy as np
import math
import signal

# Player 1: Current Color
# Player 2: Color going next
class state:
    def __init__(self, sim, win,first, move):
        self.sim = sim
        self.win = win
        # parent
        self.first = first
        self.move = move

def board_num(board):
    new_board = []
    #for stuff in GoBoardUtil.get_twoD_board(board):
        #for stuffs in stuff:
            #if type(stuffs) == np.int32:
                #new_board.append(stuffs)
    #new_board.tolist()
    for lists in GoBoardUtil.get_twoD_board(board):
        lists.tolist()
        for i in lists:
            element = i.item()
            new_board.append(str(element))
            
    return "".join(new_board)

def search2(tree, old):
    back = []
    for stuff in tree:
        monte_state_value = tree[stuff]
        if monte_state_value == old:
            back.append(stuff)
    return back

def sim(board, player1, player2):
    game_end, winner = board.check_game_end_gomoku()
    if game_end == True:
        if winner == player1:
            return 1
        else:
            return 0
    move = GoBoardUtil.generate_random_move_gomoku(board)
    if move == PASS:
        return 0
    board.play_move_gomoku(move, player2)
    return sim(board, player1, GoBoardUtil.opponent(player2))

def sim_do(board, simulation, color):
    wins = 0
    loss = 0
    for i in range(simulation):
        test_board = board.copy()
        end = sim(test_board, color, color)
        if end == 1:
            wins += 1
        if end == 0:
            loss += 1
    
    if loss == 0 and wins > 0:
        return math.inf
    if wins / loss > 1:
        print(wins/loss)
        return wins/loss
    else:
        return 0

def best_move(board, tree, top):
    best_ratio = 0
    best_move = None
    for key in tree:
        state = tree[key]
        print(key, "\n \t", state.win, state.sim, state.move )
        # match the parent first before we are trying to find what is
        # the best_move
        if state.first == top:
            current_ratio = state.win/state.sim
            if best_ratio < current_ratio:
                best_ratio = current_ratio
                best_move = state.move
    return best_move

def BackProp(Monte_Carlo_Tree, first,stop,if_win):
    while (first!= stop):
        Monte_Carlo_Tree[first].simulation +=1
        if if_win:
            Monte_Carlo_Tree[first].win = Monte_Carlo_Tree[first].win + 1
        first = Monte_Carlo_Tree[first].first

def getMAX(tree, keys):

    start_balance = 0

    for stuff in keys:
        new_state = tree[stuff]
        new_balance = state.win / state.sim
        if new_balance > start_balance:
            new_max = stuff
            start_balance = new_balance
    return new_max


def Monte_Carlo_Tree(simple_board, player2):


    ### Start ###
    start_move = PASS
    start = time.time()
    new_move = GoBoardUtil.generate_legal_moves_gomoku(simple_board)
    if len(new_move) == 0:
        return start_move
    test = simple_board.copy()
    first = board_num(test)
    first_copy = first
    monte_tree = {}
    try:
        signal.alarm(55)
        while (time.time() - start )< 56: # 10 second testing
            test = simple_board.copy()

            if start_move != PASS:
                test.play_move_gomoku(start_move, player2)
                player2 = GoBoardUtil.opponent(player2)
                search = board_num(test)
                while search in monte_tree:
                    move_lists = search2(monte_tree, first)
                    if len(move_lists) == 0:
                        print("out of while search in monte_tree")
                        break

                    searching_key = GetMAX(monte_tree, move_lists) # best key ratio in the list (need it!)



                    test.play_move_gomoku(monte_tree[searching_key].move, player2)
                    player2 = GoBoardUtil.opponent(player2)

                new_move = []
                all_moves = GoBoardUtil.generate_legal_moves_gomoku(test)
                if len(all_moves) == 0:
                    break
                for i in range(5):
                    new_move.append(random.choice(all_moves))
            for move in new_move:

                new_search_board = simple_board.copy()
                new_search_board.play_move_gomoku(move, player2)
                ending = sim_do(new_search_board.copy(), 50, player2)
                
                player1 = GoBoardUtil.opponent(player2)

                if (ending > 0 and player2 != player1):
                    game_ending = 1
                #elif (ending == 1 and player2 == player1):
                #    game_ending = 1
                else:
                    game_ending = 0
                print(game_ending, player2)
                if game_ending == 0:
                    # loss move
                    new_state = state(1,0,first,move)
                    BackProp(monte_tree,first,first_copy,False)
                else:
                    print("win state")
                    print(move)
                    new_state = state(1,ending,first,move)
                    BackProp(monte_tree,first,first_copy,True)
                spec_key = board_num(new_search_board)
                monte_tree[spec_key] = new_state
            start_move = best_move(simple_board, monte_tree, first_copy)
            #print(start_move)
        return start_move
        signal.alarm(0)
    except Exception as e:
        if start_move != None:
            return start_move
        else:
            return GoBoardUtil.generate_random_move_gomoku(simple_board)