# Green OCR

Sistema web para extração de dados de documentos brasileiros (RG, CNH, CPF) a partir de fotos de frente e verso, com revisão manual dos campos e armazenamento local em SQLite. Pensado para ser reaproveitado em fluxos de admissão de funcionários e cadastro de clientes.

> Projeto em desenvolvimento. Esta versão contém a base: schema do banco, migrations, validadores e armazenamento criptografado das imagens.

## Privacidade (LGPD)

- Imagens e dados ficam somente no servidor onde o sistema roda; nenhum serviço externo é chamado.
- Todas as imagens (originais, processadas e miniaturas) são gravadas criptografadas com AES-256-GCM. A chave fica na variável `GREEN_OCR_ENCRYPTION_KEY`; sem ela a aplicação não inicia e os arquivos não podem ser lidos.
- Guarde a chave em local seguro: se ela for perdida, as imagens não podem ser recuperadas.

## Requisitos

- Docker e Docker Compose

## Configuração

```bash
cp .env.example .env
docker compose --profile tests run --rm tests python -m app.cli generate-key
```

Cole a chave gerada em `GREEN_OCR_ENCRYPTION_KEY` e gere outra para `GREEN_OCR_SECRET_KEY`.

## Rodando

```bash
docker compose up -d --build app
```

A aplicação fica em `http://127.0.0.1:8090` (porta configurável por `GREEN_OCR_PORT`). As migrations são aplicadas automaticamente na inicialização.

## Testes

```bash
docker compose --profile tests run --rm --build tests
```

## Banco de dados

| Tabela | Conteúdo |
|---|---|
| `people` | Dados consolidados por pessoa, deduplicados por CPF |
| `documents` | Um registro por documento processado, com campos extraídos em colunas, confiança e status de revisão |
| `document_images` | Caminhos das imagens criptografadas (original, processada, miniatura) por lado do documento |
| `users` | Usuários com acesso ao sistema |
| `audit_log` | Registro de ações (acesso, alteração, exclusão) sem dados pessoais |

As migrations ficam em `migrations/versions` e são gerenciadas pelo Alembic.

## Licença

MIT. Veja [LICENSE](LICENSE).
