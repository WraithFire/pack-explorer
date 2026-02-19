# 📦 Pack Explorer

**Pack Explorer** is a GUI tool for browsing and modifying pack files in _Pokémon Mystery Dungeon: Explorers of Sky_.

Pack files (.bin) are containers used by the game to bundle multiple assets together—such as sprites, effects, dungeon data, and more. This tool lets you open these containers, view their contents, and easily import or export entries.

Known pack files:

- EFFECT/effect.bin
- DUNGEON/dungeon.bin
- MONSTER/monster.bin
- MONSTER/m_attack.bin
- MONSTER/m_ground.bin
- BALANCE/m_level.bin

**Note:** The game may contain additional pack files not listed here.

## 💾 Installation

You can download pre-built **executables** from the [Releases Page](https://github.com/WraithFire/pack-explorer/releases/latest).
These are ready-to-run builds for Windows and macOS.

If you prefer, you can also [run from source code](#linuxrun-from-source-code) — especially handy if your antivirus really hates unknown executables.

## Windows

1. Download **`pack_explorer_windows.zip`**
2. Extract the ZIP file and open the extracted folder
3. Double-click **`pack_explorer.exe`** to run.

> ⚠️ If Windows Defender warns you about an unrecognized app:
>
> - Click **"More info"**
> - Then click **"Run anyway"**

## macOS

**For Intel Macs:**

1. Download **`pack_explorer_mac_intel.dmg`**
2. Open the DMG file and drag **Pack Explorer** into **Applications**

**For Apple Silicon (M1/M2/M3):**

1. Download **`pack_explorer_mac_arm64.dmg`**
2. Open the DMG file and drag **Pack Explorer** into **Applications**

> ⚠️ If macOS blocks the app:
>
> - Open **System Preferences → Security & Privacy**
> - Click **"Open Anyway"** for _Pack Explorer_

## Linux/Run from source code

**Requirements:**

- Python 3.9 or higher
- pip (Python package manager)
- tkinter (Python Tk GUI toolkit)

**Installation Steps:**

1. **Get the source code:**
   You can either **clone the repository** or **download the ZIP file** from this repository.
    - **Option 1: Clone the repository (recommended)**

        ```bash
        git clone https://github.com/WraithFire/pack-explorer
        ```

    - **Option 2: Download the ZIP file**
        - Direct link: [Download ZIP](https://github.com/WraithFire/pack-explorer/archive/refs/heads/master.zip)
        - After downloading, extract the ZIP file to your desired location.
        - Once extracted, **open terminal** in the extracted folder, **skip Step 2**, and continue from **Step 3** below.

2. **Navigate into the project directory:**

    ```bash
    cd pack-explorer
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    **Optional:** To enable sprite preview in the GUI, install the optional dependency:

    ```bash
    pip install -r requirements-optional.txt
    ```

4. **Run the application:**

    ```bash
    python pack_explorer.py
    ```

## 🙏 Acknowledgement

This project uses code derived from [skytemple-files](https://github.com/SkyTemple/skytemple-files):

- **pmd_pack/model.py** - Pack parsing/serialization logic based on `skytemple_files.container.pmd_pack`
- **pmd_pack/pkdpx.py** - PKDPX compression/decompression logic based on `skytemple_files.compression_container.pkdpx`
- **pmd_pack/file_types.py** - File type detection logic derived from skytemple-files file format handlers (BGP, DPL, SCREEN, AT4PX, etc.)

Special thanks to:

- **psy_commando** - for research and documentation on pack files and various file formats.
- **SkyTemple Contributors** - for their research and implementing parsers for various file formats.

## 🤝 Contributing

Contributions are welcome!
If you have ideas, improvements, or bug fixes:

- Open an **issue**
- Or submit a **pull request**

## 📜 License

This project is licensed under the **GNU General Public License v3.0**.
See the [LICENSE](LICENSE) file for full terms.
