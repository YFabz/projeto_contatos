"""Banco e coleção em memória, só com o que a agenda usa (testes sem servidor)."""
import re

from pymongo.errors import DuplicateKeyError, OperationFailure


class _Resultado:
    def __init__(self, matched=0, deleted=0):
        self.matched_count = matched
        self.deleted_count = deleted


class _Cursor:
    """Como no MongoDB: ordena os documentos completos e só depois aplica a projeção."""

    def __init__(self, docs, projecao=None):
        self._docs = docs
        self._projecao = projecao

    def sort(self, campo, sentido=1):
        ordenados = sorted(self._docs, key=lambda d: d.get(campo, ''), reverse=sentido < 0)
        return _Cursor(ordenados, self._projecao)

    def _projetar(self, doc):
        if not self._projecao:
            return doc
        excluir = {k for k, v in self._projecao.items() if v == 0}
        incluir = {k for k, v in self._projecao.items() if v == 1}
        return {k: v for k, v in doc.items()
                if k not in excluir and (not incluir or k in incluir or k == '_id')}

    def __iter__(self):
        return iter([self._projetar(d) for d in self._docs])


class ColecaoFalsa:
    def __init__(self, nome='contatos_p04'):
        self.name = nome
        self.docs = []
        self._proximo_id = 1
        self._opcoes = {}

    def options(self):
        return dict(self._opcoes)

    def create_index(self, *args, **kwargs):
        return None

    def _casa(self, doc, filtro):
        for campo, cond in filtro.items():
            if isinstance(cond, dict) and '$regex' in cond:
                if not re.search(cond['$regex'], doc.get(campo, '')):
                    return False
            elif isinstance(cond, dict) and '$exists' in cond:
                if (campo in doc) != cond['$exists']:
                    return False
            elif isinstance(cond, dict) and cond.get('$type') == 'string':
                if not isinstance(doc.get(campo), str):
                    return False
            elif doc.get(campo) != cond:
                return False
        return True

    def insert_one(self, doc):
        if any(d['email'] == doc['email'] for d in self.docs):
            raise DuplicateKeyError('E11000 duplicate key error (email)')
        self.docs.append(dict(doc, _id=self._proximo_id))
        self._proximo_id += 1

    def find(self, filtro=None, projecao=None):
        achados = [d for d in self.docs if self._casa(d, filtro or {})]
        return _Cursor(achados, projecao)

    def find_one(self, filtro=None):
        return next(iter(self.find(filtro)), None)

    def count_documents(self, filtro):
        return len(list(self.find(filtro)))

    def update_one(self, filtro, mudanca):
        for d in self.docs:
            if self._casa(d, filtro):
                d.update(mudanca['$set'])
                return _Resultado(matched=1)
        return _Resultado()

    def delete_one(self, filtro):
        for d in self.docs:
            if self._casa(d, filtro):
                self.docs.remove(d)
                return _Resultado(deleted=1)
        return _Resultado()


class BancoFalso:
    def __init__(self):
        self._colecoes = {}

    def __getitem__(self, nome):
        return self._colecoes.setdefault(nome, ColecaoFalsa(nome))

    def __getattr__(self, nome):
        if nome.startswith('_'):
            raise AttributeError(nome)
        return self[nome]

    def create_collection(self, nome, check_exists=True, **opcoes):
        colecao = self[nome]
        if colecao._opcoes or colecao.docs:  # como o servidor: NamespaceExists
            raise OperationFailure('NamespaceExists', code=48)
        colecao._opcoes = dict(opcoes)
        return colecao

    def command(self, comando, nome, **opcoes):
        assert comando == 'collMod'
        self[nome]._opcoes.update(opcoes)
