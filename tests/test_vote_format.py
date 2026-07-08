from game.models import Action, ActionType, GameStage, Role
from game.prompts.prompt_builder import PromptBuilder
from game.vote_format import format_vote_action, format_votes_so_far
from tests.conftest import add_player, add_vote, make_game


def test_format_vote_action_handles_abstain_and_target():
    game = make_game({Role.MAFIA: 1, Role.CITIZEN: 2})
    voter = add_player(game, 1, Role.CITIZEN)
    target = add_player(game, 2, Role.MAFIA)

    abstain = add_vote(game, voter, None)
    vote = add_vote(game, voter, target)

    assert format_vote_action(abstain) == "Игрок 1 → воздержался"
    assert format_vote_action(vote) == "Игрок 1 → Игрок 2"


def test_user_prompt_includes_votes_so_far_for_next_voter():
    game = make_game({Role.MAFIA: 1, Role.CITIZEN: 2})
    voter_1 = add_player(game, 1, Role.CITIZEN)
    voter_2 = add_player(game, 2, Role.CITIZEN)
    target = add_player(game, 3, Role.MAFIA)
    votes_so_far = [add_vote(game, voter_1, target)]

    prompt = PromptBuilder.get_user_prompt(
        game,
        voter_2,
        ActionType.VOTE,
        votes_so_far=votes_so_far,
    )

    assert "Текущее голосование (уже проголосовали):" in prompt
    assert "Игрок 1 → Игрок 3" in prompt
