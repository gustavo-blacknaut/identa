# Contribuindo

1. Abra uma issue antes de mudanças grandes, para combinar a abordagem.
2. Crie um branch a partir de `main`.
3. Rode localmente o que o CI roda:

   ```bash
   cd apps/api && ruff check . && pytest
   cd apps/web && npm run lint && npm run typecheck && npm test
   ```

4. Se mudar a API, atualize o contrato usado pela interface:

   ```bash
   cd apps/api && python -m identa.cli export-openapi --output openapi.json
   cd apps/web && npm run api:types
   ```

5. Commits curtos no formato [Conventional Commits](https://www.conventionalcommits.org/pt-br/) (`feat:`, `fix:`, `docs:`...).
6. Nunca use documentos reais em testes, issues ou capturas de tela. Gere dados fictícios com `tests/synthetic.py`.

Novos tipos de documento entram como um parser em `apps/api/identa/parsers/` registrado com `@register`.
