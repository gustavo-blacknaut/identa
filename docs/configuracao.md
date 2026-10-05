# Configuração

A API lê variáveis com prefixo `IDENTA_` do ambiente ou de um arquivo `.env` na pasta em que roda. Tudo é validado na inicialização: valor inválido ou ausente faz a API parar com uma mensagem que cita a variável, por exemplo:

```
Configuração inválida:
  - IDENTA_SECRET_KEY: obrigatória, com pelo menos 32 caracteres (gere com: python -m identa.cli generate-key)
  - IDENTA_UPLOAD_FORMATS: formatos aceitos: jpeg, png, webp, heic; recebido: 'jpeg,gif'
```

`python -m identa.cli check-config` faz a mesma validação sem subir o servidor.

A coluna **Em execução** marca o que o administrador pode mudar em *Configurações* sem reiniciar. Nesses casos a variável é só o valor padrão; o que for salvo na tela fica no banco e vale até alguém clicar em "Usar padrão".

## Segredos e armazenamento

| Variável | Padrão | Obrigatória | Em execução | Descrição |
| --- | --- | --- | --- | --- |
| `IDENTA_SECRET_KEY` | — | sim | não | Assina os cookies de sessão e cifra o segredo do 2FA no banco. Mínimo de 32 caracteres. Trocar invalida sessões e 2FA ativos. |
| `IDENTA_ENCRYPTION_ENABLED` | `true` | não | não | Criptografa imagens com AES-256-GCM. Desligado, grava sem criptografia; arquivos antigos criptografados continuam legíveis se a chave estiver definida. |
| `IDENTA_ENCRYPTION_KEY` | — | com criptografia | não | Chave de 32 bytes em base64 (`python -m identa.cli generate-key`). Cifra as imagens e os campos CPF, RG, CNH, MRZ, texto do OCR e dados extraídos. Sem ela nada disso pode ser lido. |
| `IDENTA_ENCRYPTION_OLD_KEYS` | vazio | não | não | Chaves anteriores, separadas por vírgula. Servem só para ler dados e arquivos ainda não recifrados. Ver *Rotação de chave* em [seguranca.md](seguranca.md). |
| `IDENTA_DATABASE_URL` | `sqlite:///./data/identa.db` | não | não | `sqlite:///caminho.db` ou `postgresql://usuario:senha@host:5432/banco`. No Compose é montada a partir de `POSTGRES_*`. |
| `IDENTA_STORAGE_DIR` | `./storage` | não | não | Pasta das imagens. No Compose, volume `storage` em `/data/storage`. |
| `IDENTA_PUBLIC_URL` | vazio | não | não | Base dos links enviados por e-mail. Vazio usa o endereço da requisição. |

## E-mail

| Variável | Padrão | Obrigatória | Em execução | Descrição |
| --- | --- | --- | --- | --- |
| `IDENTA_SMTP_HOST` | vazio | não | não | Servidor SMTP. Vazio desliga o envio: convites e links de redefinição aparecem para o administrador copiar. |
| `IDENTA_SMTP_PORT` | `587` | não | não | Porta do SMTP. |
| `IDENTA_SMTP_SECURITY` | `starttls` | não | não | `starttls`, `ssl` ou `none`. |
| `IDENTA_SMTP_USER` / `IDENTA_SMTP_PASSWORD` | vazio | não | não | Credenciais, se o servidor exigir. |
| `IDENTA_SMTP_FROM` | — | com SMTP | não | Remetente das mensagens. |

Para desenvolvimento, `docker compose --profile dev up -d mailpit` sobe o [Mailpit](https://mailpit.axllent.org/) em `http://127.0.0.1:8025`. Use `IDENTA_SMTP_HOST=mailpit` (ou `127.0.0.1` fora do Docker com a porta 1025 publicada), `IDENTA_SMTP_PORT=1025` e `IDENTA_SMTP_SECURITY=none`.

## OCR

| Variável | Padrão | Obrigatória | Em execução | Descrição |
| --- | --- | --- | --- | --- |
| `IDENTA_OCR_ENGINE` | `rapidocr` | não | não | `rapidocr` (ONNX) ou `tesseract`. O Tesseract também é usado se o RapidOCR não iniciar. |
| `IDENTA_OCR_DEVICE` | `auto` | não | sim | `auto`, `cpu` ou `gpu`. Ver [benchmarks.md](benchmarks.md). |
| `IDENTA_OCR_LANGUAGES` | `por` | não | não | Idiomas do Tesseract. O RapidOCR usa o modelo latino PP-OCRv5, que cobre português. |
| `IDENTA_OCR_MODEL_DIR` | `./models` | não | não | Onde ficam os modelos ONNX (`python -m identa.cli download-models`). |
| `IDENTA_OCR_WARMUP` | `true` | não | não | Prepara o motor ao subir, para a primeira leitura não esperar. |
| `IDENTA_OCR_PASSES` | `3` | não | sim | Quantas vezes a imagem é lida, cada vez com um efeito (contraste e nitidez, preto e branco, escurecimento). As leituras extras só rodam se algum campo vier vazio, inválido ou com confiança abaixo de 90%; cada campo fica com o valor de maior confiança, e o CPF só é trocado por um que passe no dígito verificador. |

## Envio, imagens e retenção

| Variável | Padrão | Obrigatória | Em execução | Descrição |
| --- | --- | --- | --- | --- |
| `IDENTA_UPLOAD_MAX_MB` | `15` | não | sim | Limite por imagem, de 1 a 100 MB. |
| `IDENTA_UPLOAD_FORMATS` | `jpeg,png,webp,heic` | não | sim | Formatos aceitos. O formato é detectado pelo conteúdo, não pela extensão. |
| `IDENTA_IMAGE_QUALITY` | `88` | não | sim | Qualidade JPEG das imagens processadas, recortes e originais recomprimidos. |
| `IDENTA_COMPRESS_ORIGINALS` | `false` | não | sim | Regrava o original em JPEG, sem metadados, com no máximo `IDENTA_ORIGINAL_MAX_SIDE` pixels. |
| `IDENTA_ORIGINAL_MAX_SIDE` | `3000` | não | não | Maior lado do original recomprimido. |
| `IDENTA_RETENTION_DAYS` | `0` | não | sim | Apaga documentos processados há mais de N dias, com imagens e recortes. `0` mantém para sempre. |
| `IDENTA_RETENTION_INTERVAL_HOURS` | `24` | não | não | Intervalo da verificação de retenção. |
| `IDENTA_BACKGROUND_JOBS` | `true` | não | não | Liga a retenção automática e o preparo do OCR. |

## Contas e sessões

| Variável | Padrão | Obrigatória | Em execução | Descrição |
| --- | --- | --- | --- | --- |
| `IDENTA_PASSWORD_MIN_LENGTH` | `10` | não | sim | Tamanho mínimo da senha. |
| `IDENTA_PASSWORD_REQUIRE_MIXED` | `true` | não | sim | Exige letras com números ou símbolos. A senha nunca pode conter o e-mail. |
| `IDENTA_LOGIN_MAX_ATTEMPTS` | `5` | não | sim | Erros seguidos que bloqueiam a conta. Além disso, cada IP tem limite de 20 tentativas em 5 minutos. |
| `IDENTA_LOGIN_LOCK_MINUTES` | `15` | não | sim | Duração do bloqueio. Um administrador pode desbloquear antes. |
| `IDENTA_ACCESS_MINUTES` | `15` | não | não | Validade do cookie de acesso. |
| `IDENTA_REFRESH_DAYS` | `30` | não | sim | Duração máxima de uma sessão desde o login. Renovar o acesso não estende esse prazo. |
| `IDENTA_SESSION_IDLE_HOURS` | `12` | não | sim | Sessão sem nenhuma renovação por mais que isto exige novo login. |
| `IDENTA_INVITE_HOURS` | `72` | não | sim | Validade do convite. |
| `IDENTA_RESET_MINUTES` | `60` | não | não | Validade do link de redefinição de senha. |
| `IDENTA_VERIFY_HOURS` | `48` | não | não | Validade do link de confirmação de e-mail. |
| `IDENTA_SCAN_LINK_HOURS` | `48` | não | sim | Validade padrão do link de envio remoto. |
| `IDENTA_SECURE_COOKIES` | `false` | não | não | Marca os cookies como `Secure`. Ligue quando houver HTTPS. |

## Instância e interface

| Variável | Padrão | Obrigatória | Em execução | Descrição |
| --- | --- | --- | --- | --- |
| `IDENTA_INSTANCE_NAME` | `Identa` | não | sim | Nome no menu, no login e nos e-mails. O logotipo é enviado pela tela de Configurações. |
| `IDENTA_DEFAULT_THEME` | `system` | não | sim | Tema para quem ainda não escolheu: `system`, `light` ou `dark`. |
| `IDENTA_DEFAULT_LANGUAGE` | `pt-BR` | não | sim | Idioma padrão da interface e dos e-mails: `pt-BR` ou `en`. Cada pessoa pode trocar em *Minha conta*. |
| `IDENTA_TIMEZONE` | `America/Sao_Paulo` | não | sim | Fuso das datas exibidas e da auditoria. |

## Papéis e permissões

Há três papéis: administrador, revisor e leitor. O administrador tem tudo e é o único que gerencia usuários e configurações. As permissões de revisor e leitor são editadas em *Configurações > Permissões por papel*; o padrão é:

| Permissão | Revisor | Leitor |
| --- | --- | --- |
| Consultar pessoas e documentos | sim | sim |
| Enviar documentos | sim | não |
| Revisar e reprocessar | sim | não |
| Apagar documentos | sim | não |
| Ver imagens originais | sim | não |
| Editar e verificar pessoas | sim | não |
| Apagar pessoas | não | não |
| Gerar links de envio | sim | não |
| Ver auditoria | não | não |

A API confere a permissão em cada rota; a interface só esconde o que o papel não pode usar.

## Interface web

| Variável | Padrão | Obrigatória | Descrição |
| --- | --- | --- | --- |
| `IDENTA_API_URL` | `http://127.0.0.1:8000` | não | Endereço interno da API. O Next encaminha `/api/*` para ele (rewrites), então o navegador só fala com a origem da interface e não há CORS. É lido no `next build` e na execução; no Compose vale `http://api:8000`. |

## Docker Compose

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `IDENTA_BIND` | `127.0.0.1` | Interface de rede em que a porta da interface é publicada. `0.0.0.0` libera para a rede local. |
| `IDENTA_PORT` | `8090` | Porta da interface no host. A API, o PostgreSQL e o Mailpit não são publicados, exceto o painel do Mailpit em `127.0.0.1`. |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | `identa`, `identa`, — | Banco criado no primeiro `up`. A senha é obrigatória. |
| `MAILPIT_PORT` | `8025` | Porta do painel do Mailpit. |
