from game.logging import FileGameLogger, NullGameLogger
from game.models import PlayerType, Role
from tests.conftest import add_player, make_game


def test_null_game_logger_does_not_create_file(tmp_path):
    logger = NullGameLogger()
    game = make_game()
    add_player(game, 1, Role.CITIZEN)

    logger.log_game_setup(game.players, None)
    logger.log("TEST", "content")

    assert logger.log_file is None
    assert logger.session_dir is None
    assert list(tmp_path.iterdir()) == []


def test_file_game_logger_splits_main_and_player_logs(tmp_path):
    logger = FileGameLogger(log_dir=tmp_path)
    game = make_game({Role.MAFIA: 1, Role.CITIZEN: 1})
    ai_player = add_player(game, 1, Role.MAFIA, player_type=PlayerType.AI)
    human_player = add_player(game, 2, Role.CITIZEN, player_type=PlayerType.HUMAN)

    logger.log_game_setup(game.players, human_player)
    logger.log_ai_request(
        ai_player,
        system_prompt="system",
        user_prompt="user",
        action_type="kill",
    )
    logger.log_ai_response(
        ai_player,
        "3",
        reasoning="Думаю, что игрок 3 подозрителен.",
    )
    logger.log_action_retry(
        ai_player,
        "ожидается число",
        raw_input="abc",
        action_type="kill",
    )
    logger.log_text("СОБЫТИЕ", "Игрок 3 изгнан.")

    main_content = logger.log_file.read_text(encoding="utf-8")
    player_logs = list(logger.players_log_dir.glob("*.log"))
    ai_log = next(
        path for path in player_logs if path.name.startswith("player_01_")
    )
    ai_content = ai_log.read_text(encoding="utf-8")

    assert "SYSTEM PROMPT" not in main_content
    assert "СОБЫТИЕ" in main_content
    assert "Игрок 3 изгнан" in main_content
    assert "SYSTEM PROMPT" in ai_content
    assert "REASONING" in ai_content
    assert "Думаю, что игрок 3 подозрителен" in ai_content
    assert "ПОВТОР ВВОДА" in ai_content
    assert len(player_logs) == 2

    human_log = next(
        path for path in player_logs if path.name.startswith("player_02_")
    )
    assert human_log.exists()
