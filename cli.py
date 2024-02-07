#!/usr/bin/env python3
import typing as t

import sys

if sys.version_info.major < 3 or sys.version_info.minor < 6:
    raise RuntimeError("This script requires Python 3.6 or later.")

try:
    import typer
    import rich
    import jinja2
except ImportError:
    raise RuntimeError(
        "Please, install required third-party modules via `pip install -r requirements.txt`."
    )

import re
import os
import shutil

from pathlib import Path
from subprocess import run as run_command
from dataclasses import dataclass


ROOT_PATH = Path(__file__).parent.absolute()

TEMPLATES_ROOT = ROOT_PATH / "templates"
SOURCES_ROOT = ROOT_PATH / "sources"
ORIGINAL_SOURCES_ROOT = SOURCES_ROOT / "original"
DECOMPILED_SOURCES_ROOT = SOURCES_ROOT / "decompiled"
MODS_ROOT = SOURCES_ROOT / "mods"

TOOLS_ROOT = ROOT_PATH / "tools"
QUICKBMS_ROOT = TOOLS_ROOT / "quickbms"
QUICKBMS_EXECUTABLE = QUICKBMS_ROOT / (
    "quickbms.exe" if os.name == "nt" else "quickbms"
)
QUICKBMS_SCRIPTS_ROOT = QUICKBMS_ROOT / "bms_scripts"


@dataclass
class MHK_GAME:
    id: str
    name: str
    data_filename: str

    @property
    def data_path(self) -> Path:
        return ORIGINAL_SOURCES_ROOT / self.id / self.data_filename

    @property
    def bms_script_path(self) -> Path:
        return QUICKBMS_SCRIPTS_ROOT / (self.id + ".bms")

    def mod_root_path(self, mod_id: t.Optional[str] = None) -> Path:
        path = MODS_ROOT / self.id
        if mod_id is not None:
            path = path / mod_id

        return path


MHK_GAMES = {
    "mhk_extra": MHK_GAME(
        id="mhk_extra", name="Moorhuhn Kart: Extra", data_filename="mhke.dat"
    ),
    "mhk_2_en": MHK_GAME(
        id="mhk_2_en", name="Moorhuhn Kart 2 (en)", data_filename="mhk2-00.dat"
    ),
    "mhk_2_de": MHK_GAME(
        id="mhk_2_de", name="Moorhuhn Kart 2 (de)", data_filename="mhk2-00.dat"
    ),
    "mhk_3": MHK_GAME(id="mhk_3", name="Moorhuhn Kart 3", data_filename="data.sar"),
}


QUICKBMS_COMMANDS = {
    "recompile": lambda bms_script_path, original_path, modified_path: run_command(
        [
            QUICKBMS_EXECUTABLE,
            "-.",
            "-w",
            "-r",
            "-r",
            "-r",
            bms_script_path,
            original_path,
            modified_path,
        ],
        check=True,
    )
}


VALID_MOD_ID_REGEX = r"[a-zA-Z0-9_\.]{1,260}"


def is_valid_mod_id(mod_id: str):
    if re.match(VALID_MOD_ID_REGEX, mod_id) is not None:
        return True

    raise ValueError(
        f"Invalid mod ID: {mod_id}. Mod IDs may contain alphanumeric characters, dots and underscores only."
    )


CLI = typer.Typer(
    name="MHK-MODS CLI",
    help="A CLI for creating and compiling mods for the Moorhuhn Kart games.",
    epilog="MHK-MODS is an open-source project: https://github.com/SKevo18/mhk-mods",
    no_args_is_help=True,
)


@CLI.command(
    help="Creates a new mod. This will create the necessary directory structure in `./source/mods`."
)
def new(
    game_id: str = typer.Argument(
        help=f"The ID of the game to compile the mod for. Can be one of: {', '.join(MHK_GAMES.keys())}",
        default=...,
    ),
    mod_id: str = typer.Argument(
        help="The ID of the mod (must be unique).", default=...
    ),
):
    def _copy_template(source_path: Path, destination_root: Path):
        shutil.copytree(source_path, destination_root)
        jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(destination_root), keep_trailing_newline=True
        )

        for path in destination_root.rglob("*.*"):
            rich.print(f"Copying `{path}`...")
            template = jinja_env.get_template(
                str(path.relative_to(destination_root).as_posix())
            )
            rendered = template.render(
                {"mod_title": mod_id.replace("_", " ").title(), "game": game}
            )

            path.write_text(rendered)

    is_valid_mod_id(mod_id)

    try:
        game = MHK_GAMES[game_id]
    except KeyError:
        rich.print(
            f"[red][yellow]{game_id}[/yellow] must be one of: [bright_black]{', '.join(MHK_GAMES.keys())}[/bright_black][/red]"
        )
        raise typer.Exit(1)

    mod_root_path = game.mod_root_path(mod_id)

    # Create directory structure:
    rich.print(
        f"[orange3]Creating directory structure for [yellow]{game.id}[/yellow]...[/orange3]"
    )

    if mod_root_path.exists():
        rich.print(
            f"[red]The [yellow]{mod_id}[/yellow] mod already exists [bright_black]({mod_root_path})[/bright_black], aborting![/red]"
        )
        raise typer.Exit(1)

    _copy_template(TEMPLATES_ROOT / "new_mod", mod_root_path)

    rich.print(
        f"[bright_green]Done! Make sure to run [bright_black]python cli.py compile {game.id} {mod_id}[/bright_black] after you are done![/bright_green]"
    )
    typer.Exit()


@CLI.command(
    help="Validates if modified file size is not larger than original (so it can be re-imported)."
)
def validate(
    game_id: str = typer.Argument(
        help=f"The ID of the game to validate the mod for. Can be one of: {', '.join(MHK_GAMES.keys())}",
        default=...,
    ),
    mod_id: str = typer.Argument(help="The ID of the mod to validate.", default=...),
):
    is_valid_mod_id(mod_id)
    rich.print(
        f"[orange3]Validating file sizes for [yellow]{game_id}/{mod_id}[/yellow][/orange3]"
    )

    try:
        game = MHK_GAMES[game_id]
    except KeyError:
        rich.print(
            f"[red][yellow]{game_id}[/yellow] must be one of: [bright_black]{', '.join(MHK_GAMES.keys())}[/bright_black][/red]"
        )
        raise typer.Exit(1)

    modded_sources = game.mod_root_path(mod_id) / "source"
    original_sources = DECOMPILED_SOURCES_ROOT / game.id
    sizes = {}

    for original_path in original_sources.rglob("**/*"):
        relative = original_path.relative_to(original_sources)
        sizes[relative] = original_path.stat().st_size

    for modded_path in modded_sources.rglob("**/*"):
        if not modded_path.is_file():
            continue

        relative = modded_path.relative_to(modded_sources)
        original_size = sizes.get(relative)
        size = modded_path.stat().st_size

        if original_size is not None and original_size < size:
            rich.print(
                f"[red]{relative} is larger than original (O:{original_size} M:{size})![/red]"
            )

    rich.print("[bright_green]Done![/bright_green]")


@CLI.command(help="Injects the modified assets back into the game archive.")
def compile(
    game_id: str = typer.Argument(
        help=f"The ID of the game to compile the mod for. Can be one of: {', '.join(MHK_GAMES.keys())}",
        default=...,
    ),
    mod_id: str = typer.Argument(help="The ID of the mod to compile.", default=...),
    force: bool = typer.Option(
        help="Overwrites the mod file, if it already exists.", default=False
    ),
):
    is_valid_mod_id(mod_id)

    try:
        game = MHK_GAMES[game_id]
    except KeyError:
        rich.print(
            f"[red][yellow]{game_id}[/yellow] must be one of: [bright_black]{', '.join(MHK_GAMES.keys())}[/bright_black][/red]"
        )
        raise typer.Exit(1)

    mod_root_path = game.mod_root_path(mod_id)
    source_root = mod_root_path / "source"

    modded_data_file = mod_root_path / game.data_filename
    temp_data_file = modded_data_file.with_stem(f".{modded_data_file.stem}")

    # Check if mod directory exists:
    if not mod_root_path.exists():
        rich.print(
            f"[red]The mod folder for [yellow]{mod_id}[/yellow] [bright_black]({mod_root_path})[/bright_black] does not exist![/red]"
        )
        raise typer.Exit(1)

    # Check if `README` is present in the `source` directory:
    if "README" in [path.stem for path in source_root.iterdir()]:
        rich.print(
            f"[red][yellow]README[/yellow] file is present in the [bright_black]{source_root}[/bright_black] directory, remove it first![/red]"
        )
        raise typer.Exit(1)

    # Check if `source` directory is empty:
    if len(list(source_root.iterdir())) <= 0:
        rich.print(
            f"[red]The [yellow]source[/yellow] directory for [yellow]{mod_id}[/yellow] is empty![/red]"
        )
        raise typer.Exit(1)

    # Ensure that correct data files exist:
    if modded_data_file.exists():
        rich.print(
            f"[red]Modded data file for [bright_black]{game_id}[/bright_black] ([bright_black]{modded_data_file}[/bright_black]) already exists![/red]"
        )

        if force:
            rich.print("[yellow]Overwritting, because `force` is on.[/yellow]")
            modded_data_file.unlink(missing_ok=True)

        else:
            yes = input(
                "\nOverwrite? Answering with 'y' or 'Y' will remove the file above and restart the whole process, answering with anything else will terminate the execution.\nYour choice: "
            )

            if yes.lower() == "y":
                rich.print(
                    "[yellow]Answered '[bright_green]y/Y[/bright_green]'[/yellow]"
                )
                modded_data_file.unlink(missing_ok=True)

            else:
                rich.print(
                    "[yellow][bright_red]Not 'y/Y'[/bright_red], exitting...[/yellow]"
                )
                raise typer.Exit(1)

    if not temp_data_file.exists():
        rich.print(
            f"[yellow]Copying original data file for [bright_black]{game_id}[/bright_black] from source...[/yellow]"
        )

        try:
            shutil.copyfile(game.data_path, temp_data_file)

        except FileNotFoundError:
            rich.print(
                f"[red]Original data file for [bright_black]{game_id}[/bright_black] does not exist (expected: [bright_black]{game.data_path}[/bright_black])![/red]"
            )
            raise typer.Exit(1)

    # Run QuickBMS:
    rich.print("[orange3]Repacking game...[/orange3]")

    _repack(game, temp_data_file, source_root)

    # Rename temp mod:
    temp_data_file.rename(modded_data_file)
    rich.print(
        f"[bright_green]Done! Find the modded data file at [bright_black]{modded_data_file}[/bright_black]![/bright_green]"
    )


def _repack(game: MHK_GAME, temp_data_file: Path, source_root: Path):
    if game.id in ("mhk_2_en", "mhk_2_de"):
        # need to create temporary path with all assets:
        temp_mod_path = source_root / "data.temp"
        shutil.copytree(DECOMPILED_SOURCES_ROOT / game.id / "data", temp_mod_path)
        shutil.copytree(source_root / "data", temp_mod_path, dirs_exist_ok=True)

        rich.print(f"Running phenomediapacker on {temp_mod_path}...")
        run_command(
            [
                TOOLS_ROOT / "phenomediapacker" / "build" / "phenomediapacker",
                temp_mod_path,
                temp_data_file,
            ],
            check=True,
        )
        shutil.rmtree(temp_mod_path)
    else:
        QUICKBMS_COMMANDS["recompile"](
            game.bms_script_path, temp_data_file, source_root
        )


@CLI.command(help="Compiles all mods from their source.")
def compile_all(
    game_id: t.Optional[str] = typer.Argument(
        help=f"The ID of the game to compile all mods for. Can be one of: {', '.join(MHK_GAMES.keys())}. If `None`, then all games are compiled.",
        default=None,
    ),
    force: bool = typer.Option(
        help="Overwrites the mod file, if it already exists.", default=False
    ),
):
    if game_id is not None and game_id not in MHK_GAMES.keys():
        rich.print(
            f"[red][yellow]{game_id}[/yellow] must be one of: [bright_black]{', '.join(MHK_GAMES.keys())}[/bright_black][/red]"
        )
        raise typer.Exit(1)

    mod_ids: t.Dict[str, t.List[Path]] = {}

    rich.print("[orange3]Scanning mod paths...[/orange3]")
    if game_id is None:
        for game_id in MHK_GAMES.keys():
            game_mods_root = MODS_ROOT / game_id

            if game_mods_root.exists():
                mod_ids.setdefault(game_id, [])
                mod_ids[game_id].extend(
                    [
                        path
                        for path in game_mods_root.iterdir()
                        if path.is_dir() and not path.stem.startswith(".")
                    ]
                )

            else:
                rich.print(
                    f"[yellow]Skipping [bright_black]{game_mods_root}[/bright_black] because it doesn't exist...[/yellow]"
                )

    else:
        game_mods_root = MODS_ROOT / game_id

        if game_mods_root.exists():
            mod_ids[game_id] = [
                path
                for path in game_mods_root.iterdir()
                if path.is_dir() and not path.stem.startswith(".")
            ]

        else:
            rich.print(
                f"[red]There are no mods for [bright_black]{game_id}[/bright_black]![/red]"
            )
            raise typer.Exit(1)

    for game_id, mod_roots in mod_ids.items():
        for mod_root in mod_roots:
            mod_id = mod_root.stem
            rich.print(f"[yellow]Compiling: {game_id}/{mod_id}[/yellow]")

            try:
                compile(game_id=game_id, mod_id=mod_id, force=force)
            except typer.Exit:
                continue

    rich.print("[bright_green]Done![/bright_green]")


@CLI.command(
    help="Merges two mods together. Files from first mods are prioritized (e. g.: if the modified file exists in both mods, the one from the first mod will overwrite the second)."
)
def merge(
    game_id: str = typer.Argument(
        help=f"The ID of the game to merge the mods for. Can be one of: {', '.join(MHK_GAMES.keys())}",
        default=...,
    ),
    merged_mod_id: str = typer.Argument(help="The new (merged) mod ID.", default=...),
    mod_ids: t.List[str] = typer.Argument(
        help="Mod IDs to combine, e. g.: 'cli.py merge mhk_2_en new_mod example_mod abc_mod 123_mod'",
        default=...,
    ),
):
    def _merge_unique_lines(
        original_file: Path, file: Path, merge_with: Path, merged_file: Path
    ):
        for path in [original_file, file, merge_with]:
            if not path.exists():
                raise FileNotFoundError(f"{path} does not exist!")

        merged = []
        with original_file.open() as f_original, file.open() as f, merge_with.open() as f_mw:
            for original_line, first_line, second_line in zip(f_original, f, f_mw):
                if original_line != first_line:
                    merged.append(first_line)
                elif original_line != second_line:
                    merged.append(second_line)
                else:
                    merged.append(original_line)

        merged_file.write_text("".join(merged))

    def _merge_directories(new_directory: Path, merge_paths: t.List[Path]):
        new_directory.mkdir(parents=True)

        for path_root in merge_paths:
            for to_copy in path_root.rglob("**/*"):
                relative = to_copy.relative_to(path_root)
                copy_to = new_directory / relative
                rich.print(f"Copy {to_copy} to {copy_to}")

                if to_copy.is_dir():
                    copy_to.mkdir(parents=True, exist_ok=True)

                else:
                    if copy_to.exists():
                        rich.print(
                            f"{copy_to} already exists, comparing it to original and merging unique lines..."
                        )
                        try:
                            _merge_unique_lines(
                                DECOMPILED_SOURCES_ROOT / game_id / relative,
                                to_copy,
                                copy_to,
                                copy_to,
                            )
                            rich.print(
                                f"Successfuly created new merged file {copy_to}. [yellow]But check it, just in case...[/yellow]"
                            )

                        except Exception as exception:
                            rich.print(
                                f"[red]Failed to merge {to_copy} with {copy_to}: {exception}[/red]"
                            )
                            continue

                    else:
                        shutil.copy2(to_copy, copy_to)

    if len(mod_ids) < 2:
        rich.print("[red]Please, specify 2 or more mods to merge together.[/red]")
        raise typer.Exit(1)

    game = MHK_GAMES[game_id]
    mod_sources = [
        game.mod_root_path(mod_id) / "source"
        for mod_id in mod_ids
        if is_valid_mod_id(mod_id)
    ]

    for mod_path in mod_sources:
        if not mod_path.exists():
            rich.print(
                f"[red][bright_black]{mod_path}[/bright_black] does not exist![/red]"
            )
            raise typer.Exit(1)

    new(game_id=game_id, mod_id=merged_mod_id)

    rich.print(
        f"[orange3]Creating a new [yellow]{merged_mod_id}[/yellow] merged mod from mods [yellow]{', '.join(mod_ids)}[/yellow]...[/orange3]"
    )
    merged_mod_source_path = game.mod_root_path(merged_mod_id) / "source"

    shutil.rmtree(merged_mod_source_path)
    _merge_directories(merged_mod_source_path, mod_sources)

    rich.print("[orange3]Compiling...[/orange3]")
    compile(game_id=game_id, mod_id=merged_mod_id)


if __name__ == "__main__":
    CLI()
