# Benchmark de OCR: CPU x GPU (DirectML)

Medido em 04/10/2026 22:04 com `scripts/benchmark.py`. Imagens sintéticas de documento
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
| CPU | 1 | 4858 ms | 4858 ms | 0.21 | 4.0 s | 1125 MB | - | CPUExecutionProvider |
| CPU | 8 | 2743 ms | 2135 ms | 0.36 | 3.1 s | 1365 MB | - | CPUExecutionProvider |
| CPU | 32 | 3307 ms | 3478 ms | 0.30 | 1.4 s | 1378 MB | - | CPUExecutionProvider |
| GPU (DirectML) | 1 | 829 ms | 829 ms | 1.21 | 4.2 s | 391 MB | 1041 MB | CPUExecutionProvider, DmlExecutionProvider |
| GPU (DirectML) | 8 | 852 ms | 838 ms | 1.17 | 3.6 s | 545 MB | 1042 MB | CPUExecutionProvider, DmlExecutionProvider |
| GPU (DirectML) | 32 | 848 ms | 862 ms | 1.18 | 3.8 s | 564 MB | 1074 MB | CPUExecutionProvider, DmlExecutionProvider |

## Comparação

- Lote de 1: CPU 4858 ms x GPU 829 ms por imagem (GPU 5.9x mais rápida)
- Lote de 8: CPU 2743 ms x GPU 852 ms por imagem (GPU 3.2x mais rápida)
- Lote de 32: CPU 3307 ms x GPU 848 ms por imagem (GPU 3.9x mais rápida)
