"""
 Main driver file. Responsible for handling user input and displaying current game state.
"""

import pygame as p
import ChessEngine
import AiMoveFinder

WIDTH = HEIGHT = 512  # alternatively: 400
DIMENSION = 8  # chessboard is 8x8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

'''
    Initialize global dic of images. Called only one time, to save resources
'''


def load_images():
    pieces = ['wp', 'bp', 'wR', 'bR', 'wN', 'bN', 'wB', 'bB', 'wQ', 'bQ', 'wK', 'bK']
    for piece in pieces:
        # resize and load image
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))


'''
    Main driver handles user input and updating graphics
'''


def draw_text(screen, text):
    font = p.font.SysFont('Comic Sans',32, True, False)
    text_object = font.render(text, 0, p.Color('Black'))
    text_location = p.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH/2 -text_object.get_width()/2, HEIGHT/2 - text_object.get_height()/2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, 0, p.Color("Gray"))
    screen.blit(text_object, text_location.move(2, 2))


def main():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine.GameState()
    valid_moves = gs.get_valid_moves()
    move_made = False # flag variable for when move is made -> for generating new valid moves
    animate = False # flag variable for enabling animation
    load_images()
    running = True
    sq_selected = () # no square selected initially, keeps track of last click of user (tuple: (row, col))
    player_clicks = [] # keep track of player clicks (two tuples: [(6, 4), (4, 4)])
    game_over = False
    # player vs player, player vs ai
    player_one = True # true if player is white, false if ai is white
    player_two = False
    ai = AiMoveFinder.AiMoveFinder()
    while running:
        # determine if ai needs to play a move
        human_turn = (gs.white_to_move and player_one) or (not gs.white_to_move and player_two)
        for e in p.event.get():
            # close on clicking X
            if e.type == p.QUIT:
                running = False
            # mouse click event
            elif e.type == p.MOUSEBUTTONDOWN:
                if not game_over and human_turn:
                    location = p.mouse.get_pos() # (x, y) location of mouse
                    col = location[0]//SQ_SIZE
                    row = location[1]//SQ_SIZE
                    if sq_selected == (row, col): #user clicked same square twice
                        sq_selected = ()
                        player_clicks = []
                    else:
                        sq_selected = (row, col)
                        player_clicks.append(sq_selected) # append for both 1st and 2nd click
                    if len(player_clicks) == 2: # make move
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], gs.board)
                        print(move.get_chess_notation())
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                gs.make_move(valid_moves[i])
                                move_made = True
                                animate = True
                                sq_selected = () # reset user clicks
                                player_clicks = []
                        if not move_made:
                            player_clicks = [sq_selected]

            # key handlers
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z: # undo when z pressed
                    gs.undo_move()
                    move_made = True
                    animate = False # animation cancelled when move is undone
                    game_over = False
                if e.key == p.K_r: # reset board with r
                    gs = ChessEngine.GameState()
                    valid_moves = gs.get_valid_moves()
                    sq_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False

        # ai move finder
        if not game_over and not human_turn:
            move = ai.find_best_move_minmax(gs, valid_moves)
            gs.make_move(move)
            move_made = True
            animate = True

        if move_made:
            if animate:
                animate_move(gs.moveLog[-1], screen, gs.board, clock)
            valid_moves = gs.get_valid_moves()
            move_made = False
            animate = False

        draw_game_state(screen, gs, valid_moves,sq_selected)

        if gs.check_mate:
            game_over = True
            if gs.white_to_move:
                draw_text(screen, 'Black wins by checkmate')
            else:
                draw_text(screen, 'White wins by checkmate')
        elif gs.stale_mate:
            game_over = True
            draw_text(screen, 'Stalemate')

        clock.tick(MAX_FPS)
        p.display.flip()

'''
    Move highlighting
'''
def highlight_squares(screen, gs, valid_moves, sq_selected):
    if sq_selected != ():
        r, c = sq_selected
        if gs.board[r][c][0] == ('w' if gs.white_to_move else 'b'): # sq_selected is piece that can be moved
            # highlight selected square
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100) # [0, 255]
            s.fill(p.Color('blue'))
            screen.blit(s, (c*SQ_SIZE, r*SQ_SIZE))
            # highlight moves from that square
            s.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.start_row == r and move.start_col == c:
                    screen.blit(s, (SQ_SIZE*move.end_col, SQ_SIZE*move.end_row))


'''
    responsible for graphics within current game state
'''
def draw_game_state(screen, gs, valid_moves, sq_selected):
    draw_board(screen) # draws squares on board
    highlight_squares(screen, gs, valid_moves, sq_selected)
    draw_pieces(screen, gs.board) # draw pieces on top of board


def draw_board(screen):
    global colors
    colors = [p.Color("papayawhip"), p.Color("saddlebrown")]

    for row in range(DIMENSION):
        for col in range(DIMENSION):
            color = colors[((row+col)%2)]
            # Rect(top, left, dim1, dim2)
            p.draw.rect(screen, color, p.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE))


def draw_pieces(screen, board):
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            piece = board[row][col]
            if(piece != "--"):
                screen.blit(IMAGES[piece], p.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE))

'''
    Animation for moves
'''
def animate_move(move, screen, board, clock):
    global colors
    dR = move.end_row - move.start_row
    dC = move.end_col - move.start_col
    frames_per_square = 10
    frame_count = (abs(dR) + abs(dC)) * frames_per_square
    for frame in range(frame_count + 1):
        r, c = (move.start_row + dR * frame/frame_count, move.start_col + dC * frame/frame_count)
        draw_board(screen)
        draw_pieces(screen, board)
        # erase the piece moved from ending square
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = p.Rect(move.end_col*SQ_SIZE, move.end_row*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, end_square)
        # draw captured piece onto rectangle
        if move.piece_captured != '--':
            screen.blit(IMAGES[move.piece_captured], end_square)
        # draw moving piece
        screen.blit(IMAGES[move.piece_moved], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)


# convention for using main
if __name__ == "__main__":
    main()
