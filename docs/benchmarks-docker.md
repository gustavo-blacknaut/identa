# Benchmark de OCR: CPU x GPU (DirectML)

Medido em 04/10/2026 16:09 com `scripts/benchmark.py`. Imagens sintéticas de documento
(RG fictício fotografado em perspectiva, pré-processado como no sistema) e uma página de calibração.
Cada linha é um processo novo; a primeira imagem é descartada como aquecimento e não entra na média.

## Máquina

| Item | Valor |
| --- | --- |
| CPU | AMD Ryzen 5 1600 Six-Core Processor (6 núcleos / 12 threads) |
| GPU | nenhuma |
| Driver da GPU | - |
| RAM da VM do WSL2 | 9.7 GB |
| Sistema | Linux 6.18.40.1-microsoft-standard-WSL2 (build #1 SMP PREEMPT_DYNAMIC Fri Jul 31 22:12:15 UTC 2026) |
| Python | 3.12.15 |
| Pacotes | onnxruntime 1.30.0, rapidocr 3.9.2 |

## Resultados

| Dispositivo | Lote | Tempo médio por imagem | Mediana | Imagens/s | Inicialização | Pico de RAM | Pico de VRAM | Providers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| CPU | 1 | 2107 ms | 2107 ms | 0.47 | 1.2 s | 1229 MB | - | CPUExecutionProvider |
| CPU | 8 | 1901 ms | 1845 ms | 0.53 | 1.1 s | 1568 MB | - | CPUExecutionProvider |
| CPU | 32 | 1772 ms | 1813 ms | 0.56 | 1.1 s | 1584 MB | - | CPUExecutionProvider |

## Comparação

