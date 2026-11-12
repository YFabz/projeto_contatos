# Agenda de Contatos

Projeto 04 da atividade [MongoDB + Python](https://github.com/perabru/ProjetoBD-4Bimestre). A agenda roda no terminal e permite adicionar contatos, buscar por parte do nome, atualizar o telefone e remover pelo e-mail. O desafio extra adiciona um campo opcional para empresa ou organização.

## Como executar

É preciso ter Python 3.11 ou mais recente e acesso ao MongoDB Community Server em execução ou a um cluster MongoDB Atlas. O Compass é opcional e serve para visualizar os dados.

Abra o terminal na pasta que contém este README.

**Windows (PowerShell)**

```powershell
py -m venv .venv
Copy-Item .env.example .env
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m p04_contatos.main
```

**Linux ou macOS**

```bash
python3 -m venv .venv
cp .env.example .env
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m p04_contatos.main
```

Se usar o Atlas, substitua o valor de `MONGO_URI` no arquivo `.env` pela URI do cluster antes de iniciar a agenda. Para MongoDB local na porta padrão, use o valor do exemplo. O arquivo `.env` fica no seu computador.

## Como os contatos são salvos

O banco é `laboratorio_python` e a coleção é `contatos_p04`. O MongoDB cria o campo `_id` automaticamente. Exemplo de contato com empresa:

```json
{
  "nome": "Ana Silva",
  "email": "ana@example.com",
  "telefone": "11900000001",
  "empresa": "Papelaria Central"
}
```

O programa grava e consulta e-mails em minúsculas. Um índice único em `email` impede duplicações. A busca usa `$regex` com a opção `i` e trata os caracteres digitados como texto literal. O telefone é salvo como texto para preservar zeros e símbolos.

## Roteiro de demonstração

| Passo | Ação | Resultado esperado |
| --- | --- | --- |
| 1 | Cadastre Ana Silva com `ana@example.com`, telefone `11900000001` e empresa `Papelaria Central`. Cadastre Bruno Lima com `bruno@example.com` e deixe a empresa vazia. | Os dois contatos são salvos. |
| 2 | Busque por `sILv`. | Aparece Ana Silva, com telefone e empresa. |
| 3 | Tente cadastrar outro contato com `ANA@EXAMPLE.COM` e preencha os demais campos. | A agenda mostra “E-mail já utilizado.” |
| 4 | Altere o telefone de `ana@example.com` para `11900000002` e busque por `ana`. | O novo telefone aparece. |
| 5 | Remova `ana@example.com` e busque por `ana` novamente. | A agenda mostra “Nenhum contato encontrado.” |
| 6 | Abra `laboratorio_python` → `contatos_p04` no Compass. | Bruno continua salvo. Na aba de índices, `email_1` aparece como único. |

Use dados fictícios na apresentação. Para repetir o roteiro com os mesmos e-mails, remova também o contato de Bruno ao final.

## Evidência dos testes

Trechos da saída obtida com MongoDB Community Server 7.0.20, usando os contatos fictícios do roteiro:

```text
Ana Silva | ana@example.com | 11900000001
Empresa ou organização: Papelaria Central
E-mail já utilizado.
Telefone atualizado!
Ana Silva | ana@example.com | 11900000002
Contato excluído!
Nenhum contato encontrado.
Bruno Lima | bruno@example.com | 11900000003
```

A consulta ao banco confirmou que `email_1` é único e que apenas Bruno permaneceu na coleção após a exclusão. Também foram testados campos vazios e a mensagem de erro com o servidor indisponível.
