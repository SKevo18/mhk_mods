import typing as t

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse

from pathlib import Path
from cli import MHK_GAMES, MHK_GAME


MHKM_FASTAPI_APP = FastAPI(root_path='/api')
GITHUB_ROOT = 'https://github.com/SKevo18/mhk_mods/tree/main/sources/mods'


def _get_game(game_id: str) -> MHK_GAME:
    game = MHK_GAMES.get(game_id)
    if game is None:
        raise HTTPException(404, f"Game with ID `{game_id}` was not found.")

    return game


@MHKM_FASTAPI_APP.get("/")
def get_game_ids() -> t.Dict[str, str]:
    all_games = {}

    for game_id, game in MHK_GAMES.items():
        all_games[game_id] = game.name

    return all_games




@MHKM_FASTAPI_APP.get("/{game_id}")
def get_mod_ids_for_game(game_id: str) -> t.List[str]:
    game = _get_game(game_id)
    root_path = game.mod_root_path()

    if root_path.exists():
        return [path.stem for path in root_path.iterdir() if path.is_dir()]

    else:
        raise HTTPException(404, f"Game `{game_id}` has no mods.")



@MHKM_FASTAPI_APP.get("/{game_id}/{mod_id}/thumbnail")
def get_thumbnail(game_id: str, mod_id: str):
    game = _get_game(game_id)
    thumbnail_file = game.mod_root_path(mod_id) / 'thumbnail.png'

    if thumbnail_file.exists():
        return FileResponse(thumbnail_file, media_type='image/png')

    else:
        raise HTTPException(404, f"Thumbnail for `{game_id}/{mod_id}` does not exist.")



@MHKM_FASTAPI_APP.get("/{game_id}/{mod_id}")
def get_mod_data(game_id: str, mod_id: str) -> t.Dict[str, t.Any]:
    game = _get_game(game_id)
    root = game.mod_root_path(mod_id)
    data = {
        "game_id": game_id,
        "mod_id": mod_id,
        "download_url": '/api' + MHKM_FASTAPI_APP.url_path_for('download_mod', game_id=game_id, mod_id=mod_id),
        "source": GITHUB_ROOT + f'/{game_id}/{mod_id}',
        "meta": {
            "title": None,
            "description": None,
            "readme": None,
            "thumbnail": None,
        }
    }

    readme = root / 'README.md'
    thumbnail = root / 'thumbnail.png'


    if readme.exists():
        readme_text = readme.read_text()

        title = next(line for line in readme_text.splitlines() if line.startswith('# ')).removeprefix('# ')
        description = next(line for line in readme_text.splitlines() if line.startswith('> ')).removeprefix('> ')

        data['meta']['title'] = title
        data['meta']['description'] = description
        data['meta']['readme'] = readme_text


    if thumbnail.exists():
        data['meta']['thumbnail'] = MHKM_FASTAPI_APP.url_path_for('get_thumbnail', game_id=game_id, mod_id=mod_id)


    return data



@MHKM_FASTAPI_APP.get("/{game_id}/{mod_id}/download")
def download_mod(game_id: str, mod_id: str):
    def _iter_mod_file(mod_file: Path):
        with open(mod_file, 'rb') as f:
            while chunk := f.read((1024 * 1024) * 25):
                yield chunk


    game = _get_game(game_id)
    mod_file = game.mod_root_path(mod_id) / game.data_filename

    if not mod_file.exists():
        raise HTTPException(404, f"Mod file for `{game_id}/{mod_id}` does not exist!")

    headers = {'Content-Length': str(mod_file.stat().st_size), 'Content-Disposition': f'attachment; filename="{game.data_filename}"'}
    return StreamingResponse(_iter_mod_file(mod_file), headers=headers, media_type='application/octet-stream')
