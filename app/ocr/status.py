import sys
from pathlib import Path

from app.ocr.adapters import list_adapters
from app.ocr.devices import installed_onnx_packages, package_conflict
from app.ocr.factory import get_ocr_engine


def describe_engine(engine, requested: str) -> dict[str, str]:
    choice = getattr(engine, "device", None)
    statistics = getattr(engine, "statistics", None)
    adapters = list_adapters()
    average = statistics.average_ms if statistics else None
    status = {
        "Motor": getattr(engine, "name", "desconhecido"),
        "Dispositivo solicitado": requested,
        "Dispositivo em uso": choice.label if choice else "-",
        "Motivo": choice.reason if choice else "-",
        "Providers ativos": ", ".join(getattr(engine, "providers", [])) or "-",
        "Adaptador em uso": (
            f"{choice.adapter.name} ({choice.adapter.dedicated_memory_mb} MB)"
            if choice and choice.kind == "dml" and choice.adapter
            else "-"
        ),
        "Adaptadores do sistema": "; ".join(
            f"{adapter.index}: {adapter.name}{' (software)' if adapter.software else ''}" for adapter in adapters
        )
        or ("indisponível fora do Windows" if sys.platform != "win32" else "nenhum"),
        "Pacotes ONNX Runtime": ", ".join(installed_onnx_packages()) or "nenhum",
        "Tempo médio por leitura": f"{average:.0f} ms ({statistics.images} leituras)" if average else "nenhuma leitura ainda",
    }
    if conflict := package_conflict():
        status["Aviso"] = conflict
    return status


def ocr_status(engine_name: str, device: str, model_dir: Path) -> dict[str, str]:
    return describe_engine(get_ocr_engine(engine_name, device, model_dir), device)
