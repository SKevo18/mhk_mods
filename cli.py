#!/usr/bin/env python3
import typing as t

import sys
if sys.version_info.major < 3 or sys.version_info.minor < 6:
    raise RuntimeError('This script requires Python 3.6 or later.')

try:
    import typer
    import rich
except ImportError:
    raise RuntimeError('Please, install required third-party modules via `pip install -r requirements.txt`.')

import os
import shutil

from enum import Enum
from pathlib import Path
from dataclasses import dataclass


ROOT_PATH = Path(__file__).parent.absolute()

SOURCES_ROOT = ROOT_PATH / 'sources'
ORIGINAL_SOURCES_ROOT = SOURCES_ROOT / 'original'
MODS_ROOT = SOURCES_ROOT / 'mods'

QUICKBMS_ROOT = ROOT_PATH / 'quickbms'
QUICKBMS_EXECUTABLE = QUICKBMS_ROOT / ('quickbms.exe' if os.name == 'nt' else 'quickbms')
QUICKBMS_SCRIPTS_ROOT = QUICKBMS_ROOT / 'bms_scripts'


@dataclass
class MHK_GAME:
    id: str
    data_filename: str


    @property
    def data_path(self) -> Path:
        return ORIGINAL_SOURCES_ROOT / self.id / self.data_filename

    @property
    def bms_script_path(self) -> Path:
        return QUICKBMS_SCRIPTS_ROOT / (self.id + '.bms')

    def mod_root_path(self, mod_id: str) -> Path:
        return MODS_ROOT / self.id / mod_id


MHK_GAMES = {
    'mhk_extra': MHK_GAME(id='mhk_extra', data_filename='mhke.dat'),
    'mhk_2_en': MHK_GAME(id='mhk_2_en', data_filename='mhk2-00.dat'),
    'mhk_2_de': MHK_GAME(id='mhk_2_de', data_filename='mhk2-00.dat'),
    'mhk_3': MHK_GAME(id='mhk_3', data_filename='data.sar')
}


QUICKBMS_COMMANDS = {
    "recompile": lambda bms_script_path, original_path, modified_path: os.system(f"{QUICKBMS_EXECUTABLE} -. -w -r -r -r {bms_script_path} {original_path} {modified_path}")
}


CLI = typer.Typer()



@CLI.command(help="Creates a new mod. This will create the necessary directory structure in `./source/mods`.")
def new(
    game_id: str = typer.Argument(help=f"The ID of the game to compile the mod for. Can be one of: {', '.join(MHK_GAMES.keys())}", default=...), # type: ignore
    mod_id: str = typer.Argument(help="The ID of the mod (must be unique).", default=...)
):

    try:
        game = MHK_GAMES[game_id]
    except KeyError:
        rich.print(f"[red][yellow]{game_id}[/yellow] must be one of: [bright_black]{', '.join(MHK_GAMES.keys())}[/bright_black][/red]")
        raise typer.Exit(1)

    mod_root_path = game.mod_root_path(mod_id)


    # Create directory structure:
    try:
        rich.print(f"[orange3]Creating directory structure for [yellow]{game.id}[/yellow]...[/orange3]")
        (mod_root_path / 'source').mkdir(parents=True, exist_ok=False)

    except FileExistsError:
        rich.print(f"[red]The structure for [yellow]{mod_id}[/yellow] already exists [bright_black]({mod_root_path})[/bright_black], aborting![/red]")
        raise typer.Exit(1)


    # Create README.md files:
    rich.print(f"[orange3]Creating [yellow]README[/yellow] files...[/orange3]")
    (mod_root_path / 'source' / 'README.md').write_text("# Copy modified game assets from `./sources/decompiled` here. Make sure the directory structure stays the same! It is good practice to only include modified files here. Remove this file when you are done\n")
    (mod_root_path / 'README.md').write_text(f"# {mod_id} for {game.id}\n\n## Installation\n\nReplace original data file in game's installation directory with modified `{game.data_filename}`\n")


    rich.print(f"[bright_green]Done! Make sure to run [bright_black]python cli.py compile {game.id} {mod_id}[/bright_black] after you are done![/bright_green]")
    typer.Exit()



@CLI.command(help="Injects the modified assets back into the game archive.")
def compile(
    game_id: str = typer.Argument(help=f"The ID of the game to compile the mod for. Can be one of: {', '.join(MHK_GAMES.keys())}", default=...), # type: ignore
    mod_id: str = typer.Argument(help="The ID of the mod to compile.", default=...)
):

    try:
        game = MHK_GAMES[game_id]
    except KeyError:
        rich.print(f"[red][yellow]{game_id}[/yellow] must be one of: [bright_black]{', '.join(MHK_GAMES.keys())}[/bright_black][/red]")
        raise typer.Exit(1)

    mod_root_path = game.mod_root_path(mod_id)
    source_root = (mod_root_path / 'source')

    modded_data_file = (mod_root_path / game.data_filename)
    temp_data_file = modded_data_file.with_stem(f".{modded_data_file.stem}")



    # Check if mod directory exists:
    if not mod_root_path.exists():
        rich.print(f"[red]The mod folder for [yellow]{mod_id}[/yellow] [bright_black]({mod_root_path})[/bright_black] does not exist![/red]")
        raise typer.Exit(1)


    # Check if `README` is present in the `source` directory:
    if 'README' in [path.stem for path in source_root.iterdir()]:
        rich.print(f"[red][yellow]README[/yellow] file is present in the [bright_black]{source_root}[/bright_black] directory, remove it first![/red]")
        raise typer.Exit(1)


    # Check if `source` directory is empty:
    if len(list(source_root.iterdir())) <= 0:
        rich.print(f"[red]The [yellow]source[/yellow] directory for [yellow]{mod_id}[/yellow] is empty![/red]")
        raise typer.Exit(1)



    # Ensure that correct data files exist
    if modded_data_file.exists():
        rich.print(f"[red]Modded data file for [bright_black]{game_id}[/bright_black] ([bright_black]{modded_data_file}[/bright_black]) already exists![/red]")
        yes = input("\nOverwrite? Answering with 'y' or 'Y' will remove the file above and restart the whole process, answering with anything else will terminate the execution.\nYour choice: ")

        if yes.lower() == 'y':
            rich.print("[yellow]Answered '[bright_green]y/Y[/bright_green]', repeating the whole process...[/yellow]")
            modded_data_file.unlink()

            return compile(game_id=game_id, mod_id=mod_id)

        else:
            rich.print("[yellow][bright_red]Not 'y/Y'[/bright_red], exitting...[/yellow]")
            raise typer.Exit(1)


    if not temp_data_file.exists():
        rich.print(f"[yellow]Original data file for [bright_black]{game_id}[/bright_black] does not exist, copying it from original source...[/yellow]")

        try:
            shutil.copyfile(game.data_path, temp_data_file)
        except FileNotFoundError:
            rich.print(f"[red]Original data file for [bright_black]{game_id}[/bright_black] does not exist (expected: [bright_black]{game.data_path}[/bright_black])![/red]")
            raise typer.Exit(1)



    # Run QuickBMS:
    rich.print("[orange3]Injecting game assets back via QuickBMS...[/orange3]")
    QUICKBMS_COMMANDS['recompile'](game.bms_script_path, temp_data_file, source_root)

    # Rename temp mod:
    temp_data_file.rename(modded_data_file)



@CLI.command(help="Compiles all mods from their source.")
def compile_all(game_id: str = typer.Argument(help=f"The ID of the game to compile all mods for. Can be one of: {', '.join(MHK_GAMES.keys())}", default=None)): # type: ignore
    if game_id is not None and game_id not in MHK_GAMES.keys():
        rich.print(f"[red][yellow]{game_id}[/yellow] must be one of: [bright_black]{', '.join(MHK_GAMES.keys())}[/bright_black][/red]")
        raise typer.Exit(1)


    mod_ids: t.Dict[str, t.List[Path]] = {}

    rich.print("[orange3]Scanning mod paths...[/orange3]")
    if game_id is None:
        for game_id in MHK_GAMES.keys():
            game_mods_root = MODS_ROOT / game_id

            if game_mods_root.exists():
                mod_ids.setdefault(game_id, [])
                mod_ids[game_id].extend([path for path in game_mods_root.iterdir() if path.is_dir()])

            else:
                rich.print(f"[yellow]Skipping [bright_black]{game_mods_root}[/bright_black] because it doesn't exist...[/yellow]")

    else:
        game_mods_root = MODS_ROOT / game_id

        if game_mods_root.exists():
            mod_ids[game_id] = [path for path in game_mods_root.iterdir() if path.is_dir()]

        else:
            rich.print(f"[red]There are no mods for [bright_black]{game_id}[/bright_black]![/red]")
            raise typer.Exit(1)


    for game_id, mod_roots in mod_ids.items():
        for mod_root in mod_roots:
            mod_id = mod_root.stem
            rich.print(f"[yellow]Compiling: {game_id}/{mod_id}[/yellow]")

            try:
                compile(game_id=game_id, mod_id=mod_id)
            except typer.Exit:
                continue

    rich.print("[bright_green]Done![/bright_green]")



if __name__ == '__main__':
    CLI()
