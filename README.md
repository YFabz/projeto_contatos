# Agenda de Contatos (Projeto 04 — MongoDB + Python)

Projeto 04 da atividade [MongoDB + Python](https://github.com/perabru/ProjetoBD-4Bimestre). A agenda funciona no terminal e permite **adicionar** contatos, **buscar por parte do nome**, **atualizar o telefone** e **remover pelo e-mail**. Os dados ficam em uma coleção do MongoDB, acessada com PyMongo.

**Desafios extras implementados**

1. Campo opcional `empresa` (empresa ou organização).
2. Validação de e-mail e telefone, no Python e também no servidor (`$jsonSchema`).
3. Busca que ignora maiúsculas, acentos e espaços repetidos (`jose` encontra `José`).
4. Testes automatizados, com e sem servidor MongoDB.

## Ambiente

| Item | Versão |
| --- | --- |
| Python | 3.9 ou mais recente |
| MongoDB Community Server (local) ou Atlas | em execução |
| pymongo | 4.10 ou mais recente (4.x) |
| python-dotenv | 1.x |
| MongoDB Compass | opcional, para ver os dados |

## Como executar

Abra o terminal **na pasta que contém este README** (a raiz do projeto) e deixe o MongoDB ligado.

**Windows (PowerShell)**

```powershell
py -m venv .venv
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m p04_contatos.main
```

**Linux ou macOS**

```bash
python3 -m venv .venv
[ -f .env ] || cp .env.example .env
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m p04_contatos.main
```

Esses comandos podem ser repetidos em qualquer computador: nada é recriado se já existir. A conexão usa `MONGO_URI` do arquivo `.env` (padrão: `mongodb://localhost:27017/`). Para o Atlas, troque pelo endereço do cluster. O `.env` fica só na sua máquina (está no `.gitignore`). A pasta `.venv` não deve ser copiada entre computadores: crie outra com os comandos acima. A conta do banco precisa poder criar coleções, validadores e índices.

## Estrutura do código

| Arquivo | Responsabilidade |
| --- | --- |
| `conexao.py` | `conectar()`: lê `MONGO_URI` do `.env` e devolve o `MongoClient`. |
| `p04_contatos/validacao.py` | Formatos de e-mail e telefone, normalização do nome. Não acessa o banco. |
| `p04_contatos/repositorio.py` | Coleção, validador, índices e operações (criar, buscar, atualizar, remover). Não usa `input` nem `print`. |
| `p04_contatos/main.py` | Menu no terminal e mensagens ao usuário. |
| `tests/` | Testes automatizados (`unittest`). |

## Modelo de dados

Banco `laboratorio_python`, coleção `contatos_p04`. Exemplo de documento:

```json
{
  "nome": "Ana Silva",
  "nome_busca": "ana silva",
  "email": "ana@example.com",
  "telefone": "(11) 90000-0001",
  "empresa": "Papelaria Central"
}
```

- `email`: sempre em minúsculas (assim `ANA@EXAMPLE.COM` e `ana@example.com` são o mesmo contato).
- `telefone`: texto digitado pelo usuário, com 8 a 15 dígitos (aceita `+`, parênteses, espaço, ponto e hífen). Por ser texto, preserva o zero inicial.
- `empresa`: opcional; o campo não existe quando não é informado.
- `nome_busca`: nome em minúsculas, sem acentos e sem espaços repetidos. É o campo consultado na busca.

**Índices** (criados automaticamente)

| Índice | Para quê |
| --- | --- |
| `email_1` (único) | Impede dois contatos com o mesmo e-mail; o MongoDB devolve `DuplicateKeyError`. |
| `nome_busca_1` | A busca filtra e ordena por este campo, então a ordem alfabética ignora acentos. |

**Validador `$jsonSchema`** (integridade no servidor, `validationLevel: moderate`): `nome`, `nome_busca`, `email` e `telefone` são obrigatórios e do tipo texto; nome sem apenas espaços; e-mail com até 254 caracteres e formato válido; telefone com formato válido. Dados fora das regras são recusados pelo MongoDB (erro 121), mesmo que alguém grave direto pelo Compass. Contatos antigos sem `nome_busca` são atualizados na inicialização.

## Como a busca funciona

O texto digitado passa pela mesma normalização do `nome_busca` e é procurado com `$regex` depois de `re.escape`. Por isso é tratado como **texto literal**: digitar `.*` ou `((` não vira expressão regular nem causa erro.

## Validações e tratamento de erros

| Situação | Comportamento |
| --- | --- |
| Nome, e-mail ou telefone vazio | `Preencha o nome, o e-mail e o telefone.` |
| E-mail inválido (`abc`, `ana@`, `a..b@x.com`) | `E-mail inválido.` |
| Telefone com letras ou fora de 8–15 dígitos | `Telefone inválido. Use de 8 a 15 dígitos, como (11) 90000-0001.` |
| E-mail repetido (inclusive em maiúsculas) | `E-mail já utilizado.` |
| Busca vazia | `Informe um trecho do nome.` |
| Contato inexistente (atualizar ou remover) | `Contato não encontrado.` |
| Opção de menu inválida | `Opção inválida.` |
| `MONGO_URI` inválida | `Confira o valor de MONGO_URI no arquivo .env.` |
| Servidor MongoDB desligado | `Não foi possível conectar ao MongoDB...` (espera até 5 s e encerra) |
| Conexão perdida durante uma operação | `Conexão com o MongoDB indisponível...`; o menu continua |
| Sem permissão para preparar a coleção | `Não foi possível preparar a agenda...` |
| E-mails repetidos já existentes no banco | `Há e-mails repetidos no banco...` |
| Dependências não instaladas | Mensagem pedindo `pip install -r requirements.txt` |
| Ctrl+C ou fim da entrada | `Agenda encerrada.` |

## Como executar os testes

Da raiz do projeto, com o ambiente virtual criado:

```powershell
.venv\Scripts\python.exe -m unittest -v
```

```bash
.venv/bin/python -m unittest -v
```

- **Sem servidor** (sempre rodam): validação de formatos, operações do repositório e todo o menu em um banco em memória, além das falhas de conexão simuladas.
- **Com MongoDB ligado**: os mesmos cenários do menu rodam no servidor real, mais os testes do validador `$jsonSchema` e dos índices. Cada teste usa um banco temporário, apagado ao final. Se o servidor estiver desligado, esses testes são **pulados** (aparecem como `skipped`).

Resultado esperado: todos `ok`; sem servidor, a classe `TestAgendaMongoDB` aparece como `skipped`.

## Roteiro de demonstração

| Passo | Ação | Resultado esperado |
| --- | --- | --- |
| 1 | Opção 1: `Ana Silva`, `ana@example.com`, `(11) 90000-0001`, empresa `Papelaria Central`. Depois `Bruno Lima`, `bruno@example.com`, `11900000003`, empresa vazia. | `Contato salvo!` duas vezes. |
| 2 | Opção 2: buscar `sILv`. | Ana Silva com e-mail, telefone e empresa. |
| 3 | Opção 1 com e-mail `ANA@EXAMPLE.COM`. | `E-mail já utilizado.` |
| 4 | Opção 1 com e-mail `abc`; depois com telefone `abc`. | `E-mail inválido.` e `Telefone inválido...` |
| 5 | Opção 3: `ana@example.com`, novo telefone `11 90000-0002`; buscar `ana`. | `Telefone atualizado!` e o novo número aparece. |
| 6 | Opção 2: buscar `jose` (ou `.*`). | `Nenhum contato encontrado.` |
| 7 | Opção 4: remover `ana@example.com`; buscar `ana`. | `Contato excluído!` e `Nenhum contato encontrado.` |
| 8 | No Compass: `laboratorio_python` → `contatos_p04` → Indexes e Validation. | Bruno salvo; `email_1` único; `nome_busca_1`; regras do validador. |

Ao terminar, remova também o Bruno (opção 4) para a demonstração poder ser repetida, principalmente se o banco for compartilhado (Atlas).

## Evidências de execução

Salve os prints na pasta `docs/` e referencie aqui (a imagem aparece no GitHub):

<!-- ![Terminal: cadastro, busca e erros](docs/terminal.jpg) -->
<!-- ![Compass: documentos e índices](docs/compass.jpg) -->
<!-- ![Testes: unittest -v](docs/testes.jpg) -->

## Conclusão

Descreva em poucas linhas: o que o grupo aprendeu sobre índice único, `$regex` e `$jsonSchema`, as dificuldades encontradas e o que melhorou durante o projeto.
