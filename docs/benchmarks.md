# Benchmark de OCR: CPU x GPU (DirectML)

Medido em 04/10/2026 13:12 com `scripts/benchmark.py`. Imagens sintéticas de documento
(RG fictício fotografado em perspectiva, pré-processado como no sistema) e uma página de calibração.
Cada linha é um processo novo; a primeira imagem é descartada como aquecimento e não entra na média.

## Máquina

| Item | Valor |
| --- | --- |
| CPU | AMD Ryzen 5 1600 Six-Core Processor (6 núcleos / 12 threads) |
| GPU | AMD Radeon RX590 GME (8170 MB) |
| Driver da GPU | 31.0.21924.61 |
| RAM total | 19.9 GB |
| Sistema | Microsoft Windows 10 Pro (build 10.0.19045) |
| Python | 3.12.15 |
| Pacotes | onnxruntime-directml 1.24.4, rapidocr 3.9.2 |

## Resultados

| Dispositivo | Lote | Tempo médio por imagem | Mediana | Imagens/s | Inicialização | Pico de RAM | Pico de VRAM | Providers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| CPU | 1 | 1854 ms | 1854 ms | 0.54 | 1.6 s | 1125 MB | - | CPUExecutionProvider |
| CPU | 8 | 1956 ms | 1921 ms | 0.51 | 1.5 s | 1403 MB | - | CPUExecutionProvider |
| CPU | 32 | 2159 ms | 1831 ms | 0.46 | 1.4 s | 1386 MB | - | CPUExecutionProvider |
| GPU (DirectML) | 1 | 766 ms | 766 ms | 1.31 | 3.3 s | 335 MB | 1041 MB | CPUExecutionProvider, DmlExecutionProvider |
| GPU (DirectML) | 8 | 775 ms | 776 ms | 1.29 | 3.7 s | 517 MB | 1042 MB | CPUExecutionProvider, DmlExecutionProvider |
| GPU (DirectML) | 32 | 776 ms | 786 ms | 1.29 | 3.3 s | 565 MB | 1074 MB | CPUExecutionProvider, DmlExecutionProvider |

## Comparação

- Lote de 1: CPU 1854 ms x GPU 766 ms por imagem (GPU 2.4x mais rápida)
- Lote de 8: CPU 1956 ms x GPU 775 ms por imagem (GPU 2.5x mais rápida)
- Lote de 32: CPU 2159 ms x GPU 776 ms por imagem (GPU 2.8x mais rápida)
