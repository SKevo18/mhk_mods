# Moorhuhn Kart Mods

A CLI tool for decompiling assets of Moorhuhn Kart games and reinjecting them back.

Supports MHK: Extra, MHK 2 and MHK 3.

## How does it work?

The game assets (not source code!) are de-compiled by [QuickBMS](http://aluigi.altervista.org/quickbms.htm), then re-injected back
with modified source.

The workflow is a bit tricky due to limitations on how the game archives work (e. g.: a re-injected file can't be larger in bytes than its original counterpart), but this repository aims to simplify the process by providing a CLI tool.

## Tutorial

### Prerequisites

The script is compatible with Python 3.6+ (latest version is always recommended due to performance improvements). You can download Python from their [official website](https://www.python.org/).

In addition, this repository also uses Git LFS to store the original data files. You can download it from [the official Git LFS website](https://git-lfs.github.com/). Or `apt install git-lfs` on Linux, `brew install git-lfs` on macOS, etc...

### How to compile mods

Because of the big file size of data files, the modded ones are not included in the repository's source code. You can visit [https://mhk-mods.svit.ac](https://mhk-mods.svit.ac), or compile them locally by yourself:

1. Run `python cli.py compile-all` to compile all mods, or just mods for a specific game (`python cli.py compile-all <game_id>`.
    - **Note:** To compile a specific mod, use `python cli.py compile <game_id> <mod_id>`
2. Copy the new data file to game's installation directory. Make sure that the name is exactly the same as old data file.
    - It is a good practice to back up the original data file for your target Moorhuhn Kart game (renaming it is enough)
    - If you screwed up the original, you can download it again from this repo in the `./sources/original` directory

#### Valid game IDs

- `mhk_extra` - Moorhuhn Kart: Extra (XXL version, German);
- `mhk_2_en` - Moorhuhn Kart 2 (English version)
  - Has most bugs from German version patched;
  - Introduces the OoB* glitch in Egypt;
- `mhk_2_de` - Moorhuhn Kart 2 (German version)
  - Unpatched Island "under the water" OoB bug;
  - Unpatched Castle OoB;
- `mhk_3` - Moorhuhn Kart 3 (German);

**\*OoB:** out-of-bounds (when you go outside of the intended track boundaries without being respawned)

### To create new mods

0. Decompile a MHK `.dat`/`.sar` file. Because there weren't any new updates for the original MHK games in ages, this repository already includes the decompiled assets in the `./sources/decompiled` directory. Therefore, it is safe to skip this step.
1. Create a directory structure for the new mod (`python cli.py new <ID of MHK game> <mod ID>`).
2. Add modified files to `./sources/mods/<ID of MHK game>/<mod ID>/sources`.
3. `python cli.py compile <ID of MHK game> <mod ID>`.

This will copy the original data file of the game into the mod root's directory and compile it there.

Please, do not commit modified data files to source control! There is a [webserver](https://github.com/SKevo18/mhk_mods/tree/main/webserver) for this purpose: [https://mhk-mods.svit.ac](https://mhk-mods.svit.ac).

You can check modding notes/guides for specific game, as well as mod sources, by visiting its mod directory:

- [Moorhuhn Kart 3](https://github.com/SKevo18/mhk_mods/tree/main/sources/mods/mhk_3)

#### Valid mod IDs

A mod ID must satisfy the following RegEx: `[a-zA-Z0-9_\.]{1,260}`, that is:

- It must be an alphanumerical string;
- It may contain underscores or dots;
- It must be between 1 and 260 characters long;

You can rename the mod later on by renaming the mod source directory.

## Questions and Answers

### Do you plan to mod other Moorhuhn games?

Modding other Moorhuhn games is definitely possible, but since GitHub LFS storage is limited for free accounts (to store original data files in the source control), it limits my focus on just Moorhuhn Kart mods at the moment.

In the future, I might tweak and expand this repository so that the data files are not stored directly in the git repo, but only present locally on the webserver. So, this repository would only contain the mods' sources, but the webserver could still compile them.

### Where is MHK 4 (Moorhuhn Kart: Thunder)?

As of right now (1st April 2023), there is no known script (at least I haven't found any?) that decompiles MHK 4 assets.
If you are aware of any, please create a PR (add the script to `./quickbms/bms_scripts`).

### Is this tool compatible with Linux?

Yes, the tool will automatically determine if you're running on Windows or other machine (useful in cases where you, for example, use this tool for an [automated webserver](https://github.com/SKevo18/mhk_mods/tree/main/webserver) that serves the modded data files). The Linux `quickbms` executable can be found in the `quickbms/` directory in this repo (as well as the Windows `quickbms.exe` version).

### Is there a version for aarch64 (ARM64) machines?

QuickBMS itself is not compatible with `aarch64`, and since the original author had abandoned the project, it is unlikely that it will be implemented in the foreseeable future. However, since I have migrated to a new server that is `aarch64`, I had the need to run the tool on it (and I did not want to spend additional money to buy a server where QuickBMS can be run natively, just to host the mods website). Here is a comprehensive guide on how to do it on an Ubuntu machine:

1. **Install QEMU**: QEMU is an open-source machine emulator and virtualizer. It can emulate different processor architectures, allowing binaries compiled for one architecture to run on another.

   First, update your package list and install QEMU user emulation:

   ```bash
   sudo apt update
   sudo apt install qemu-user-static
   ```

2. **Set Up the Emulation for x86**: You need to configure the system to use QEMU for x86 binary emulation.

   This can be automatically handled by the `binfmt-support` package which is usually installed with `qemu-user-static`. If not, you can install it manually:

   ```bash
   sudo apt install binfmt-support
   ```

   This should set up your system to automatically use QEMU when an x86 binary is executed.

3. **Install Necessary Libraries**: Your 32-bit application may require certain libraries to run. Since you're on an ARM64 system, you'll need to install the ARM64 versions of these libraries. However, if the application requires specific x86 libraries, you might have to set up a chroot environment with these libraries.

   For basic libraries, you can try installing `libc6:i386`, `libncurses5:i386`, `libstdc++6:i386`, and others depending on your application's requirements:

   ```bash
   sudo dpkg --add-architecture i386
   sudo apt update
   sudo apt install libc6:i386 libncurses5:i386 libstdc++6:i386
   ```

4. **Ready to go**: After setting up QEMU and installing necessary libraries, you can try compiling all mods to see if everything works as expected:

   ```bash
   python cli.py compile-all
   ```

   If it doesn't run as expected, you might need additional libraries or there could be other compatibility issues.

### Which QuickBMS version is used in this repository?

0.12.0, downloaded from [QuickBMS's website](http://aluigi.altervista.org/quickbms.htm)

### I encountered an error while (de/re)compiling the game or the modified game doesn't start/crashes, what do I do?

Modifying the game in this way is like breaking your computer apart and then trying to put it back together and praying that it works.

Since MHK games do not have an official modding tool, this repository is more of an experiment rather than a fully-fleshed out mod manager.
If you have no idea what you are doing, then it is a better idea to try out the existing mods instead by downloading them from the [official website](https://mhk-mods.svit.ac).

## Donate

Like what I do? Consider [sponsoring me](https://github.com/sponsors/SKevo18) here at GitHub!

The money will go towards paying for server fees required to run the [mhk-mods](https://mhk-mods.svit.ac) website and towards developing new mods.
