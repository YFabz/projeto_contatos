import unittest

from pymongo.errors import DuplicateKeyError

from p04_contatos import repositorio as repo
from p04_contatos.validacao import ContatoInvalido
from tests.fakes import BancoFalso


class TesteRepositorio(unittest.TestCase):
    def setUp(self):
        self.banco = BancoFalso()
        self.contatos = repo.preparar_contatos(self.banco)
        repo.criar_contato(self.contatos, 'Ana  Silva', 'ANA@example.com',
                           '(11) 90000-0001', ' Papelaria  Central ')
        repo.criar_contato(self.contatos, 'Bruno Lima', 'bruno@example.com', '11900000003')

    def test_grava_campos_normalizados(self):
        ana, bruno = self.contatos.docs
        self.assertEqual(ana['nome'], 'Ana Silva')
        self.assertEqual(ana['nome_busca'], 'ana silva')
        self.assertEqual(ana['email'], 'ana@example.com')
        self.assertEqual(ana['telefone'], '(11) 90000-0001')
        self.assertEqual(ana['empresa'], 'Papelaria Central')
        self.assertNotIn('empresa', bruno)

    def test_email_duplicado_ignora_maiusculas(self):
        with self.assertRaises(DuplicateKeyError):
            repo.criar_contato(self.contatos, 'Outra Ana', 'ANA@EXAMPLE.COM', '11900000009')

    def test_entradas_invalidas_nao_gravam(self):
        casos = [
            (('', 'x@y.com', '11900000009'), 'Preencha o nome, o e-mail e o telefone.'),
            (('Bia', '  ', '11900000009'), 'Preencha o nome, o e-mail e o telefone.'),
            (('Bia', 'sem-arroba', '11900000009'), 'E-mail inválido.'),
            (('Bia', 'bia@y.com', 'abc'), 'Telefone inválido.'),
        ]
        for args, mensagem in casos:
            with self.subTest(args=args):
                with self.assertRaises(ContatoInvalido) as erro:
                    repo.criar_contato(self.contatos, *args)
                self.assertIn(mensagem, str(erro.exception))
        self.assertEqual(len(self.contatos.docs), 2)

    def test_busca_ignora_caixa_acentos_e_espacos_repetidos(self):
        for trecho in ['sILv', 'ana silva', 'ANA   SILVA']:
            with self.subTest(trecho=trecho):
                nomes = [c['nome'] for c in repo.buscar_contatos(self.contatos, trecho)]
                self.assertEqual(nomes, ['Ana Silva'])

    def test_busca_trata_o_texto_como_literal(self):
        self.assertEqual(repo.buscar_contatos(self.contatos, '.*'), [])
        self.assertEqual(repo.buscar_contatos(self.contatos, '(('), [])

    def test_busca_vazia_ou_sem_resultado(self):
        with self.assertRaises(ContatoInvalido):
            repo.buscar_contatos(self.contatos, '   ')
        self.assertEqual(repo.buscar_contatos(self.contatos, 'zzz'), [])

    def test_busca_ordena_por_nome_sem_considerar_acento(self):
        repo.criar_contato(self.contatos, 'Álvaro Dias', 'alvaro@example.com', '11900000004')
        repo.criar_contato(self.contatos, 'Carla Dias', 'carla@example.com', '11900000005')
        repo.criar_contato(self.contatos, 'Bia Dias', 'bia@example.com', '11900000006')
        nomes = [c['nome'] for c in repo.buscar_contatos(self.contatos, 'dias')]
        self.assertEqual(nomes, ['Álvaro Dias', 'Bia Dias', 'Carla Dias'])

    def test_busca_nao_devolve_campos_internos(self):
        resultado = repo.buscar_contatos(self.contatos, 'ana')[0]
        self.assertNotIn('_id', resultado)
        self.assertNotIn('nome_busca', resultado)

    def test_atualizar_telefone(self):
        self.assertTrue(repo.atualizar_telefone(self.contatos, ' ANA@example.com ', '11 90000-0002'))
        self.assertEqual(repo.buscar_contatos(self.contatos, 'ana')[0]['telefone'], '11 90000-0002')
        self.assertFalse(repo.atualizar_telefone(self.contatos, 'nao@existe.com', '11900000002'))

    def test_atualizar_telefone_rejeita_entradas_invalidas(self):
        with self.assertRaises(ContatoInvalido):
            repo.atualizar_telefone(self.contatos, 'ana@example.com', 'abc')
        with self.assertRaises(ContatoInvalido):
            repo.atualizar_telefone(self.contatos, '  ', '11900000002')
        with self.assertRaises(ContatoInvalido):
            repo.atualizar_telefone(self.contatos, 'ana@example.com', ' ')

    def test_remover(self):
        self.assertTrue(repo.remover_contato(self.contatos, 'ana@example.com'))
        self.assertEqual(repo.buscar_contatos(self.contatos, 'ana'), [])
        self.assertFalse(repo.remover_contato(self.contatos, 'ana@example.com'))
        with self.assertRaises(ContatoInvalido):
            repo.remover_contato(self.contatos, ' ')

    def test_preparar_migra_contatos_antigos_e_pode_repetir(self):
        banco = BancoFalso()
        banco['contatos_p04'].docs.append(
            {'_id': 99, 'nome': 'Álvaro  Antigo', 'email': 'a@x.com', 'telefone': '11900000000'})
        for _ in range(2):  # a segunda chamada não pode quebrar nada
            contatos = repo.preparar_contatos(banco)
        self.assertEqual(contatos.docs[0]['nome_busca'], 'alvaro antigo')
        self.assertEqual([c['nome'] for c in repo.buscar_contatos(contatos, 'alvaro')],
                         ['Álvaro  Antigo'])


if __name__ == '__main__':
    unittest.main()
