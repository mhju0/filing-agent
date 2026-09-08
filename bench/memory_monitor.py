"""Sample macOS pressure and Ollama RSS; RSS is not total unified-memory usage."""

import json
import re
import subprocess
import threading
import time
import urllib.request


def command(*args):
    return subprocess.check_output(args, text=True, timeout=3).strip()


def snapshot():
    result = {"monotonic_seconds": time.monotonic()}
    try:
        result["swap"] = command("sysctl", "-n", "vm.swapusage")
        match = re.search(r"used = ([\d.]+)M", result["swap"])
        result["swap_used_mib"] = float(match[1]) if match else None
        result["pressure_level"] = command("sysctl", "-n", "kern.memorystatus_vm_pressure_level")
        processes = command("ps", "-axo", "rss=,comm=").splitlines()
        result["ollama_rss_kib"] = sum(int(line.split()[0]) for line in processes
                                       if "ollama" in line.lower())
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open("http://127.0.0.1:11434/api/ps", timeout=2) as response:
            result["loaded_models"] = json.load(response).get("models", [])
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result["error"] = str(exc)
    return result


class Monitor:
    def __enter__(self):
        self.samples = [snapshot()]
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.sample, daemon=True)
        self.thread.start()
        return self

    def sample(self):
        while not self.stop.wait(1):
            self.samples.append(snapshot())

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join(timeout=10)
        self.samples.append(snapshot())

    def summary(self):
        return {"samples": self.samples,
                "peak_ollama_rss_kib": max((s.get("ollama_rss_kib", 0) for s in self.samples), default=0),
                "peak_swap_used_mib": max((s.get("swap_used_mib") or 0 for s in self.samples), default=0),
                "pressure_levels": sorted({s.get("pressure_level", "unknown") for s in self.samples}),
                "caveat": "One-second samples; process RSS can double-count shared pages and excludes some GPU allocations. Swap is system-wide, including existing apps."}
