# agendacontatos

## Como executar

Instale o Python 3.11 ou mais recente e inicie o MongoDB local ou use um cluster MongoDB Atlas. Execute os comandos na raiz do projeto.

### Windows (PowerShell)

```powershell
py -m venv .venv
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Linux ou macOS

```bash
python3 -m venv .venv
[ -f .env ] || cp .env.example .env
.venv/bin/python -m pip install -r requirements.txt
```

Para MongoDB local na porta 27017, mantenha o valor padrão de `MONGO_URI` no `.env`. Para Atlas, substitua esse valor pela URI do cluster. Use uma conta com acesso de leitura e escrita e permissão para configurar a coleção e os índices.

### Iniciar a agenda

**Windows (PowerShell)**

```powershell
.venv\Scripts\python.exe -m p04_contatos.main
```

**Linux ou macOS**

```bash
.venv/bin/python -m p04_contatos.main
```

## Como executar os testes

Use uma conexão MongoDB com permissão para criar e remover bancos temporários.

**Windows (PowerShell)**

```powershell
.venv\Scripts\python.exe -m unittest -v p04_contatos
```

**Linux ou macOS**

```bash
.venv/bin/python -m unittest -v p04_contatos
```
