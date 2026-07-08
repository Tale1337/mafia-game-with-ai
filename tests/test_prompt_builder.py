from game.allies import assign_mafia_allies
from game.models import Role
from game.prompts.prompt_builder import PromptBuilder
from tests.conftest import add_player, make_game


def test_user_prompt_starts_with_clear_player_identity():
    game = make_game({Role.MAFIA: 2, Role.CITIZEN: 2})
    mafia_1 = add_player(game, 2, Role.MAFIA)
    add_player(game, 3, Role.MAFIA)
    assign_mafia_allies(game.players)

    prompt = PromptBuilder.get_user_prompt(game, mafia_1)

    assert prompt.startswith("Ты — игрок 2.")
    assert "Твоя роль — мафия." in prompt
    assert "Твой союзник-мафиози — игрок 3." in prompt
