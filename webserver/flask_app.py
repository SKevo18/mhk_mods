from flask import Flask, render_template, abort

from webserver.fastapi_app import MHKM_FASTAPI_APP
from cli import MHK_GAME, MHK_GAMES


MHKM_FLASK_APP = Flask(__name__)


def _get_game(game_id: str) -> MHK_GAME:
    game = MHK_GAMES.get(game_id)
    if game is None:
        return abort(404, f"Game with ID `{game_id}` was not found.")

    return game



@MHKM_FLASK_APP.get('/')
def index():
    return render_template("games.html")


@MHKM_FLASK_APP.get('/<string:game_id>')
def game(game_id: str):
    return render_template("game.html", game=_get_game(game_id))
