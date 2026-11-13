"""Agenda de contatos no terminal (Projeto 04).

Execute da raiz do projeto:  python -m p04_contatos.main
(também funciona com:        python p04_contatos/main.py)
"""
import sys
from pathlib import Path

if __package__ in (None, ''):  # executado como script: põe a raiz do projeto no caminho
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from pymongo.errors import ConnectionFailure, DuplicateKeyError, PyMongoError

    from conexao import conectar
    from p04_contatos.repositorio import (atualizar_telefone, buscar_contatos, criar_contato,
                                          preparar_contatos, remover_contato)
    from p04_contatos.validacao import ContatoInvalido
except ImportError as erro:
    print(f'Dependência ausente ({erro}).')
    print('Ative o ambiente virtual e rode: python -m pip install -r requirements.txt')
    raise SystemExit(1)


def adicionar(contatos):
    nome = input('Nome: ')
    email = input('E-mail: ')
    telefone = input('Telefone: ')
    empresa = input('Empresa ou organização (opcional): ')
    try:
        criar_contato(contatos, nome, email, telefone, empresa)
    except ContatoInvalido as erro:
        print(erro)
    except DuplicateKeyError:
        print('E-mail já utilizado.')
    else:
        print('Contato salvo!')


def buscar(contatos):
    try:
        encontrados = buscar_contatos(contatos, input('Parte do nome: '))
    except ContatoInvalido as erro:
        print(erro)
        return
    if not encontrados:
        print('Nenhum contato encontrado.')
        return
    for contato in encontrados:
        print(f"{contato['nome']} | {contato['email']} | {contato['telefone']}")
        if contato.get('empresa'):
            print(f"Empresa ou organização: {contato['empresa']}")


def atualizar(contatos):
    email = input('E-mail do contato: ')
    telefone = input('Novo telefone: ')
    try:
        atualizado = atualizar_telefone(contatos, email, telefone)
    except ContatoInvalido as erro:
        print(erro)
        return
    print('Telefone atualizado!' if atualizado else 'Contato não encontrado.')


def remover(contatos):
    try:
        removido = remover_contato(contatos, input('E-mail do contato: '))
    except ContatoInvalido as erro:
        print(erro)
        return
    print('Contato excluído!' if removido else 'Contato não encontrado.')


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
