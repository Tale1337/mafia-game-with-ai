from game.models import Player, PlayerType


API_LMSTUDIO = "http://127.0.0.1:1234"

def get_player_message(player: Player, messages: Messa):
    if player.player_type == PlayerType.AI:

