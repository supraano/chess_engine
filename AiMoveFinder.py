from keras.models import Sequential, load_model, model_from_json
import numpy as np
import chess
from operator import attrgetter
import ChessEngine

class AiMoveFinder:
    # one-hot-encoded pieces
    __chess_dict = {
        'bp': [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'wp': [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        'bN': [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'wN': [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        'bB': [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'wB': [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        'bR': [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        'wR': [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
        'bQ': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        'wQ': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
        'bK': [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
        'wK': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        '--': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    }

    DEPTH = 2

    def __init__(self):
        self.model = self.__load_keras_model('chess', 'mse', 'adam')

    def __load_keras_model(self, dataset, loss, optimizer):
        json_file = open('models/' + dataset + '_best_model' + '.json', 'r')
        loaded_model_json = json_file.read()
        json_file.close()
        model = model_from_json(loaded_model_json)
        model.compile(optimizer=optimizer, loss=loss, metrics=None)
        model.load_weights('models/' + dataset + '_best_model' + '.h5')
        return model

    def find_best_move_minmax(self, gs, valid_moves):
        global next_move
        next_move = None
        alpha = 0
        beta = 1
        self.__find_move_min_max(gs, valid_moves, alpha, beta, self.DEPTH, gs.white_to_move)
        return next_move

    # plus alpha beta pruning
    def __find_move_min_max(self, gs, valid_moves, alpha, beta, depth, white_to_move):
        global next_move
        if depth == 0:
            return self.predict_score(gs.board)
        if white_to_move:
            max_score = 0
            for move in valid_moves:
                gs.make_move(move)
                next_moves = gs.get_valid_moves()
                score = self.__find_move_min_max(gs, next_moves, alpha, beta, depth - 1, not white_to_move)
                if score > max_score:
                    max_score = score
                    alpha = max(alpha, score)
                    if depth == self.DEPTH:
                        next_move = move
                gs.undo_move()
                if beta <= alpha:
                    break
            return max_score
        else:
            min_score = 1
            for move in valid_moves:
                gs.make_move(move)
                next_moves = gs.get_valid_moves()
                score = self.__find_move_min_max(gs, next_moves, alpha, beta, depth - 1, not white_to_move)
                if score < min_score:
                    min_score = score
                    beta = min(beta, score)
                    if depth == self.DEPTH:
                        next_move = move
                gs.undo_move()
                if beta <= alpha:
                    break
            return min_score

    # calculates score of board based on player with an advantage: [0, 1]
    def predict_score(self, board):
        # transform into one hot encoded
        translated = np.array(self.__translate_to_one_hot(board))
        value = self.model.predict(translated.reshape(1, 8, 8, 12))
        return value

    def __translate_to_one_hot(self, board):
        one_hot_encoded = []
        for row in board:
            one_hot_row = []
            for piece in row:
                one_hot_row.append(self.__chess_dict[piece])
            one_hot_encoded.append(one_hot_row)
        one_hot_encoded.reverse()
        return one_hot_encoded

