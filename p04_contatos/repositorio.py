"""Acesso ao MongoDB: coleção, índices, validador e operações da agenda.

Nenhuma função daqui usa input() ou print(); a conversa com o usuário
fica em main.py. Assim a lógica pode ser testada sem digitar nada.
"""
import re

from pymongo.errors import OperationFailure

from p04_contatos.validacao import (FORMATO_EMAIL, FORMATO_TELEFONE, ContatoInvalido,
                                    MENSAGEM_TELEFONE_INVALIDO, email_valido,
                                    normalizar_nome, telefone_valido)

NOME_COLECAO = 'contatos_p04'

# Integridade também no servidor: o MongoDB recusa dados fora destas regras.
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


def preparar_contatos(banco):
    """Cria ou atualiza coleção, validador e índices; devolve a coleção.

    É seguro chamar a cada execução: nada é recriado se já estiver correto.
    """
    contatos = banco[NOME_COLECAO]
    opcoes = contatos.options()
    if any(opcoes.get(chave) != valor for chave, valor in VALIDACAO.items()):
        try:
            banco.create_collection(contatos.name, check_exists=False, **VALIDACAO)
        except OperationFailure as erro:
            if erro.code != 48:  # 48 = a coleção já existe
                raise
            banco.command('collMod', contatos.name, **VALIDACAO)

    contatos.create_index('email', unique=True)  # impede e-mail repetido
    contatos.create_index('nome_busca')          # apoia a busca e a ordenação por nome

    # Contatos antigos (sem nome_busca) passam a aparecer na busca.
    sem_nome_busca = {'nome_busca': {'$exists': False}}
    for contato in contatos.find({**sem_nome_busca, 'nome': {'$type': 'string'}}, {'nome': 1}):
        nome = contato['nome']
        contatos.update_one(
            {**sem_nome_busca, '_id': contato['_id'], 'nome': nome},
            {'$set': {'nome_busca': normalizar_nome(nome)}},
        )
    return contatos


def criar_contato(contatos, nome, email, telefone, empresa=''):
    """Valida e grava. Levanta ContatoInvalido ou DuplicateKeyError (e-mail repetido)."""
    nome = ' '.join(nome.split())
    email = email.strip().lower()
    telefone = telefone.strip()
    empresa = ' '.join(empresa.split())
    nome_busca = normalizar_nome(nome)
    if not all((nome_busca, email, telefone)):
        raise ContatoInvalido('Preencha o nome, o e-mail e o telefone.')
    if not email_valido(email):
        raise ContatoInvalido('E-mail inválido.')
    if not telefone_valido(telefone):
        raise ContatoInvalido(MENSAGEM_TELEFONE_INVALIDO)

    contato = {'nome': nome, 'nome_busca': nome_busca, 'email': email, 'telefone': telefone}
    if empresa:
        contato['empresa'] = empresa
    contatos.insert_one(contato)


def buscar_contatos(contatos, trecho):
    """Contatos cujo nome contém o trecho, sem diferenciar caixa nem acentos."""
    trecho = normalizar_nome(trecho)
    if not trecho:
        raise ContatoInvalido('Informe um trecho do nome.')
    filtro = {'nome_busca': {'$regex': re.escape(trecho)}}  # texto literal, não regex
    campos = {'_id': 0, 'nome': 1, 'email': 1, 'telefone': 1, 'empresa': 1}
    return list(contatos.find(filtro, campos).sort('nome_busca', 1))


def atualizar_telefone(contatos, email, telefone):
    """True se o contato existia e foi atualizado."""
    email = email.strip().lower()
    telefone = telefone.strip()
    if not email or not telefone:
        raise ContatoInvalido('Preencha o e-mail e o novo telefone.')
    if not telefone_valido(telefone):
        raise ContatoInvalido(MENSAGEM_TELEFONE_INVALIDO)
    resultado = contatos.update_one({'email': email}, {'$set': {'telefone': telefone}})
    return resultado.matched_count > 0


def remover_contato(contatos, email):
    """True se o contato existia e foi removido."""
    email = email.strip().lower()
    if not email:
        raise ContatoInvalido('Informe o e-mail.')
    return contatos.delete_one({'email': email}).deleted_count > 0
