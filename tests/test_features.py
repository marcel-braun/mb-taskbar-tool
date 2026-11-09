from collections import namedtuple

import pytest

from mbtaskbar.features import cpu, disk, ram

Usage = namedtuple("Usage", "total used free percent")
Part = namedtuple("Part", "device mountpoint fstype opts")
VMem = namedtuple("VMem", "total used percent")

GB = 1024**3


def test_cpu(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cpu.psutil, "cpu_percent", lambda interval=None: 42.4)
    f = cpu.CpuFeature()
    m = f.update()
    assert m[0].percent == 42.4
    assert f.icon_text(m) == "42"


def test_ram(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ram.psutil, "virtual_memory", lambda: VMem(16 * GB, 8 * GB, 50.0))
    f = ram.RamFeature()
    m = f.update()
    assert m[0].value_text == "8.0 / 16.0 GB"
    assert f.icon_text(m) == "50"


def test_disk_all_drives_skips_cdrom(monkeypatch: pytest.MonkeyPatch) -> None:
    parts = [
        Part("C:\\", "C:\\", "NTFS", "rw,fixed"),
        Part("D:\\", "D:\\", "NTFS", "rw,fixed"),
        Part("E:\\", "E:\\", "", "cdrom"),
    ]
    usage = {"C:\\": Usage(100 * GB, 80 * GB, 20 * GB, 80.0), "D:\\": Usage(100 * GB, 10 * GB, 90 * GB, 10.0)}
    monkeypatch.setattr(disk.psutil, "disk_partitions", lambda all=False: parts)
    monkeypatch.setattr(disk.psutil, "disk_usage", lambda p: usage[p])
    f = disk.DiskFeature()
    m = f.update()
    assert [x.label for x in m] == ["C:", "D:"]
    assert f.icon_text(m) == "80"


def test_disk_selected_and_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def usage(p: str) -> Usage:
        if p == "X:\\":
            raise OSError("not ready")
        return Usage(100 * GB, 50 * GB, 50 * GB, 50.0)

    monkeypatch.setattr(disk.psutil, "disk_usage", usage)
    f = disk.DiskFeature()
    f.configure({"drives": ["C:\\", "X:\\"]})
    assert [x.label for x in f.update()] == ["C:"]


def test_disk_no_data_icon() -> None:
    assert disk.DiskFeature().icon_text([]) == "-"
