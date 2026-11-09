# Build: pyinstaller build/mbtaskbar.spec --distpath dist --workpath build/tmp
from pathlib import Path

root = Path(SPECPATH).parent

a = Analysis(
    [str(root / "src" / "mbtaskbar" / "__main__.py")],
    pathex=[str(root / "src")],
    datas=[(str(root / "assets" / "app.ico"), "assets")],
    hiddenimports=["mbtaskbar.features.calendar_week", "mbtaskbar.features.cpu",
                   "mbtaskbar.features.ram", "mbtaskbar.features.disk"],
    excludes=["tkinter"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="MbTaskbarTool",
    icon=str(root / "assets" / "app.ico"),
    console=False,
    upx=False,
)
