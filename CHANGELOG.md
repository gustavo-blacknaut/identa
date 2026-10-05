# Changelog

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto usa [versionamento semântico](https://semver.org/lang/pt-BR/).

## [0.1.0] - 2026-10-04

Primeira versão.

### Leitura de documentos
- RG (modelos estaduais e nacional), CNH com MRZ e cartão CPF, com identificação automática do tipo.
- Correção de perspectiva e orientação, recorte de foto, assinatura e polegar.
- Confiança do OCR por campo e releitura do CPF quando o dígito verificador não fecha.
- OCR local com RapidOCR (PP-OCRv5 em ONNX Runtime) em CPU, DirectML ou CUDA, com escolha automática do dispositivo e Tesseract de reserva.

### Cadastro
- Pessoas consolidadas por CPF, com edição, verificação e dados complementares de todos os documentos.
- Listas com busca, filtros na URL, ordenação e paginação no servidor.
- Exclusão completa de documento ou pessoa, com confirmação digitada.
- Link de envio remoto de uso único.

### Contas e segurança
- Configuração inicial do primeiro administrador e convites por e-mail com link de uso único.
- Confirmação de e-mail, redefinição de senha, troca de senha e de e-mail, 2FA TOTP com códigos de recuperação.
- Papéis administrador, revisor e leitor, com permissões configuráveis.
- Bloqueio temporário por conta e limite de tentativas por IP.
- Sessões com refresh token rotativo, listáveis e revogáveis.
- Imagens criptografadas com AES-256-GCM e auditoria de todas as ações.

### Operação
- PostgreSQL no Docker Compose e SQLite fora dele, com as mesmas migrations e comando de cópia entre os dois.
- Configurações validadas na inicialização e ajustáveis em execução pelo administrador.
- Retenção com exclusão automática e compressão opcional dos originais.
- Interface em Next.js, responsiva de 360 a 1920 px, em português e inglês, com tema claro e escuro.

[0.1.0]: https://github.com/gustavo-blacknaut/identa/releases/tag/v0.1.0
