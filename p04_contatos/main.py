import re
import unicodedata

from pymongo.errors import ConnectionFailure, DuplicateKeyError, OperationFailure, PyMongoError

from conexao import conectar


PARTE_EMAIL = r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+"
FORMATO_EMAIL = (
    rf'(?=[^@]{{1,64}}@){PARTE_EMAIL}(?:\.{PARTE_EMAIL})*@'
    r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}'
)
FORMATO_TELEFONE = (
    r'(?=(?:[^0-9]*[0-9]){8,15}[^0-9]*$)'
    r'\+?(?:[0-9]+[ .-]?)?(?:\([0-9]{2,3}\) ?)?[0-9]+(?:[ .-][0-9]+)*'
)
MENSAGEM_TELEFONE_INVALIDO = 'Telefone inválido. Use de 8 a 15 dígitos, como (11) 90000-0001.'
VALIDACAO = {
    'validator': {
        '$jsonSchema': {
            'bsonType': 'object',
            'required': ['nome', 'nome_busca', 'email', 'telefone'],
            'properties': {
                'nome': {'bsonType': 'string', 'pattern': r'\S'},
                'nome_busca': {'bsonType': 'string', 'pattern': r'\S'},
                'email': {
                    'bsonType': 'string',
                    'maxLength': 254,
                    'pattern': rf'\A{FORMATO_EMAIL}\z',
                },
                'telefone': {'bsonType': 'string', 'pattern': rf'\A{FORMATO_TELEFONE}\z'},
                'empresa': {'bsonType': 'string', 'pattern': r'\S'},
            },
        },
    },
    'validationLevel': 'moderate',
    'validationAction': 'error',
}


def normalizar_nome(nome):
    decomposto = unicodedata.normalize('NFD', nome.casefold())
    return ''.join(letra for letra in decomposto if not unicodedata.combining(letra)).strip()


def preparar_contatos(banco):
    contatos = banco['contatos_p04']
    opcoes = contatos.options()
    if any(opcoes.get(chave) != valor for chave, valor in VALIDACAO.items()):
        try:
            banco.create_collection(contatos.name, check_exists=False, **VALIDACAO)
        except OperationFailure as erro:
            if erro.code != 48:
                raise
            banco.command('collMod', contatos.name, **VALIDACAO)

    contatos.create_index('email', unique=True)
    contatos.create_index('nome')

    sem_nome_busca = {'nome_busca': {'$exists': False}}
    for contato in contatos.find({**sem_nome_busca, 'nome': {'$type': 'string'}}, {'nome': 1}):
        nome = contato['nome']
        contatos.update_one(
            {**sem_nome_busca, '_id': contato['_id'], 'nome': nome},
            {'$set': {'nome_busca': normalizar_nome(nome)}},
        )

    return contatos


def adicionar(contatos):
    nome = input('Nome: ').strip()
    email = input('E-mail: ').strip().lower()
    telefone = input('Telefone: ').strip()
    nome_busca = normalizar_nome(nome)
    if not all((nome_busca, email, telefone)):
        print('Preencha o nome, o e-mail e o telefone.')
        return
    if len(email) > 254 or not re.fullmatch(FORMATO_EMAIL, email):
        print('E-mail inválido.')
        return
    if not re.fullmatch(FORMATO_TELEFONE, telefone):
        print(MENSAGEM_TELEFONE_INVALIDO)
        return

    empresa = input('Empresa ou organização (opcional): ').strip()
    contato = {
        'nome': nome,
        'nome_busca': nome_busca,
        'email': email,
        'telefone': telefone,
    }
    if empresa:
        contato['empresa'] = empresa

    try:
        contatos.insert_one(contato)
        print('Contato salvo!')
    except DuplicateKeyError:
        print('E-mail já utilizado.')


def buscar(contatos):
    trecho = normalizar_nome(input('Parte do nome: '))
    if not trecho:
        print('Informe um trecho do nome.')
        return

    filtro = {'nome_busca': {'$regex': re.escape(trecho)}}
    campos = {'_id': 0, 'nome': 1, 'email': 1, 'telefone': 1, 'empresa': 1}
    encontrados = list(contatos.find(filtro, campos).sort('nome', 1))
    if not encontrados:
        print('Nenhum contato encontrado.')
        return

    for contato in encontrados:
        print(f"{contato['nome']} | {contato['email']} | {contato['telefone']}")
        if contato.get('empresa'):
            print(f"Empresa ou organização: {contato['empresa']}")


def atualizar(contatos):
    email = input('E-mail do contato: ').strip().lower()
    telefone = input('Novo telefone: ').strip()
    if not email or not telefone:
        print('Preencha o e-mail e o novo telefone.')
        return
    if not re.fullmatch(FORMATO_TELEFONE, telefone):
        print(MENSAGEM_TELEFONE_INVALIDO)
        return

    resultado = contatos.update_one({'email': email}, {'$set': {'telefone': telefone}})
    print('Telefone atualizado!' if resultado.matched_count else 'Contato não encontrado.')


def remover(contatos):
    email = input('E-mail do contato: ').strip().lower()
    if not email:
        print('Informe o e-mail.')
        return

    resultado = contatos.delete_one({'email': email})
    print('Contato excluído!' if resultado.deleted_count else 'Contato não encontrado.')


def main():
    try:
        cliente = conectar()
    except (PyMongoError, ValueError):
        print('Confira o valor de MONGO_URI no arquivo .env.')
        return 1

    with cliente:
        return executar_agenda(cliente['laboratorio_python'])


def executar_agenda(banco):
    try:
        contatos = preparar_contatos(banco)
    except ConnectionFailure:
        print('Não foi possível conectar ao MongoDB. Confira o servidor e a MONGO_URI.')
        return 1
    except DuplicateKeyError:
        print('Há e-mails repetidos no banco. Confira a coleção contatos_p04 no Compass.')
        return 1
    except PyMongoError:
        print('Não foi possível preparar a agenda. Confira o acesso e as permissões do MongoDB.')
        return 1

    acoes = {'1': adicionar, '2': buscar, '3': atualizar, '4': remover}
    while True:
        print('\n[1] Adicionar [2] Buscar [3] Atualizar telefone [4] Remover [0] Sair')
        opcao = input('Opção: ').strip()
        if opcao == '0':
            return 0

        acao = acoes.get(opcao)
        if acao is None:
            print('Opção inválida.')
            continue

        try:
            acao(contatos)
        except ConnectionFailure:
            print('Conexão com o MongoDB indisponível. Confira o estado do contato ao reconectar.')
        except PyMongoError:
            print('O MongoDB recusou a operação. Confira os dados e as permissões.')


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (EOFError, KeyboardInterrupt):
        print('\nAgenda encerrada.')
