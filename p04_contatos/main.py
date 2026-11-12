import re

from pymongo.errors import DuplicateKeyError, PyMongoError


def adicionar(contatos):
    nome = input('Nome: ').strip()
    email = input('E-mail: ').strip().lower()
    telefone = input('Telefone: ').strip()
    if not all([nome, email, telefone]):
        print('Preencha o nome, o e-mail e o telefone.')
        return

    empresa = input('Empresa ou organização (opcional): ').strip()
    contato = {'nome': nome, 'email': email, 'telefone': telefone}
    if empresa:
        contato['empresa'] = empresa

    try:
        contatos.insert_one(contato)
        print('Contato salvo!')
    except DuplicateKeyError:
        print('E-mail já utilizado.')


def buscar(contatos):
    trecho = input('Parte do nome: ').strip()
    if not trecho:
        print('Informe um trecho do nome.')
        return

    filtro = {'nome': {'$regex': re.escape(trecho), '$options': 'i'}}
    encontrados = list(contatos.find(filtro, {'_id': 0}).sort('nome', 1))
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
        from conexao import banco

        contatos = banco['contatos_p04']
        contatos.create_index('email', unique=True)
    except DuplicateKeyError:
        print('Há e-mails repetidos no banco. Confira a coleção contatos_p04 no Compass.')
        return 1
    except PyMongoError:
        print('Não foi possível preparar a agenda. Confira a conexão e as permissões do MongoDB.')
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
        except PyMongoError:
            print('O MongoDB não confirmou a operação. Confira a conexão e busque o contato.')


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (EOFError, KeyboardInterrupt):
        print('\nAgenda encerrada.')
