def load_tests(loader, tests, pattern):
    from contextlib import redirect_stdout
    from io import StringIO
    from unittest import TestCase
    from unittest.mock import patch
    from uuid import uuid4

    from pymongo.errors import ConnectionFailure, DuplicateKeyError, WriteError

    from conexao import conectar
    from p04_contatos.main import executar_agenda, preparar_contatos

    class TestFalhasDeConexao(TestCase):
        def test_servidor_indisponivel_ao_iniciar(self):
            saida = StringIO()
            with (
                patch('p04_contatos.main.preparar_contatos', side_effect=ConnectionFailure),
                redirect_stdout(saida),
            ):
                self.assertEqual(executar_agenda(None), 1)
            self.assertIn('Não foi possível conectar ao MongoDB.', saida.getvalue())

        def test_menu_continua_apos_perder_conexao(self):
            saida = StringIO()
            with (
                patch('p04_contatos.main.preparar_contatos'),
                patch('p04_contatos.main.buscar', side_effect=ConnectionFailure),
                patch('builtins.input', side_effect=['2', '0']),
                redirect_stdout(saida),
            ):
                self.assertEqual(executar_agenda(None), 0)
            self.assertIn('Conexão com o MongoDB indisponível.', saida.getvalue())

    class TestAgenda(TestCase):
        @classmethod
        def setUpClass(cls):
            cls.cliente = conectar()
            cls.addClassCleanup(cls.cliente.close)
            cls.cliente.admin.command('ping')

        def setUp(self):
            self.banco = self.cliente[f'agendacontatos_teste_{uuid4().hex}']
            self.addCleanup(self.cliente.drop_database, self.banco.name)

        def executar(self, *entradas):
            saida = StringIO()
            with patch('builtins.input', side_effect=entradas + ('0',)), redirect_stdout(saida):
                self.assertEqual(executar_agenda(self.banco), 0, saida.getvalue())
            return saida.getvalue()

        def test_rejeita_email_invalido(self):
            saida = self.executar('1', 'José', 'abc', '11900000001')
            self.assertIn('E-mail inválido.', saida)
            self.assertEqual(self.banco.contatos_p04.count_documents({}), 0)

        def test_rejeita_telefone_invalido_no_cadastro_e_na_atualizacao(self):
            saida = self.executar(
                '1', 'José', 'jose@example.com', 'abc',
                '1', 'José', 'jose@example.com', '+55 (11) 90000-0001', '',
                '3', 'jose@example.com', '11ABC0000',
            )
            self.assertEqual(saida.count('Telefone inválido.'), 2)
            contatos = self.banco.contatos_p04
            self.assertEqual(contatos.count_documents({}), 1)
            self.assertEqual(contatos.find_one()['telefone'], '+55 (11) 90000-0001')

        def test_busca_literal_sem_acentos_em_contatos_novos_e_antigos(self):
            self.banco.contatos_p04.insert_one({
                'nome': 'José Antigo', 'email': 'antigo@example.com', 'telefone': '11900000001',
            })
            saida = self.executar(
                '1', 'José Novo', 'novo@example.com', '11900000002', 'Papelaria',
                '2', 'jose', '2', 'JOSÉ', '2', '.*',
            )
            self.assertEqual(saida.count('José Antigo |'), 2)
            self.assertEqual(saida.count('José Novo |'), 2)
            self.assertEqual(saida.count('Empresa ou organização: Papelaria'), 2)
            self.assertIn('Nenhum contato encontrado.', saida)

        def test_atualiza_remove_e_rejeita_email_duplicado(self):
            saida = self.executar(
                '1', 'Ana', 'ana@example.com', '11900000001', '',
                '1', 'Outra Ana', 'ANA@EXAMPLE.COM', '11900000002', '',
                '3', 'ANA@EXAMPLE.COM', '01900000002', '2', 'ana',
                '4', 'ana@example.com', '2', 'ana',
            )
            self.assertIn('E-mail já utilizado.', saida)
            self.assertIn('Telefone atualizado!', saida)
            self.assertIn('Ana | ana@example.com | 01900000002', saida)
            self.assertIn('Contato excluído!', saida)
            self.assertIn('Nenhum contato encontrado.', saida)
            self.assertEqual(self.banco.contatos_p04.count_documents({}), 0)

        def test_corrige_telefone_invalido_de_contato_antigo(self):
            contatos = self.banco.contatos_p04
            contatos.insert_one({'nome': 'José', 'email': 'jose@example.com', 'telefone': 'abc'})
            saida = self.executar('3', 'jose@example.com', '11900000001', '2', 'jose')
            self.assertIn('Telefone atualizado!', saida)
            self.assertIn('José | jose@example.com | 11900000001', saida)

        def test_campos_vazios_e_contato_inexistente(self):
            saida = self.executar(
                '9', '1', ' ', 'ana@example.com', '11900000001', '2', ' ',
                '3', 'ana@example.com', ' ', '4', ' ',
                '3', 'ana@example.com', '11900000001', '4', 'ana@example.com',
            )
            self.assertIn('Opção inválida.', saida)
            self.assertIn('Preencha o nome, o e-mail e o telefone.', saida)
            self.assertIn('Informe um trecho do nome.', saida)
            self.assertIn('Preencha o e-mail e o novo telefone.', saida)
            self.assertIn('Informe o e-mail.', saida)
            self.assertEqual(saida.count('Contato não encontrado.'), 2)
            self.assertEqual(self.banco.contatos_p04.count_documents({}), 0)

        def test_limites_de_digitos_do_telefone(self):
            saida = self.executar(
                '1', 'Ana', 'ana@example.com', '1234567',
                '1', 'Ana', 'ana@example.com', '01234567', '',
                '3', 'ana@example.com', '1234567890123456',
                '3', 'ana@example.com', '+123456789012345',
            )
            self.assertEqual(saida.count('Telefone inválido.'), 2)
            self.assertEqual(saida.count('Contato salvo!'), 1)
            self.assertEqual(saida.count('Telefone atualizado!'), 1)
            self.assertEqual(self.banco.contatos_p04.find_one()['telefone'], '+123456789012345')

        def test_mongodb_aplica_o_esquema_e_os_indices(self):
            contatos = preparar_contatos(self.banco)
            indices = contatos.index_information()
            self.assertTrue(indices['email_1']['unique'])
            self.assertEqual(indices['nome_1']['key'], [('nome', 1)])
            valido = {
                'nome': 'Ana', 'nome_busca': 'ana',
                'email': 'ana@example.com', 'telefone': '11900000001',
            }
            for campo, valor in [('nome', ''), ('email', 'abc'), ('telefone', 'letras')]:
                with self.subTest(campo=campo), self.assertRaises(WriteError) as erro:
                    contatos.insert_one({**valido, campo: valor})
                self.assertEqual(erro.exception.code, 121)

            contatos.insert_one(valido)
            with self.assertRaises(DuplicateKeyError):
                contatos.insert_one({**valido, 'nome': 'Outra Ana'})
            with self.assertRaises(WriteError) as erro:
                contatos.update_one({'email': 'ana@example.com'}, {'$set': {'telefone': 'abc'}})
            self.assertEqual(erro.exception.code, 121)

    tests.addTests(loader.loadTestsFromTestCase(TestAgenda))
    tests.addTests(loader.loadTestsFromTestCase(TestFalhasDeConexao))
    return tests
