import unittest

from p04_contatos.validacao import email_valido, normalizar_nome, telefone_valido


class TesteEmail(unittest.TestCase):
    def test_aceita_formatos_validos(self):
        for email in ['ana@example.com', 'a+b@mail.com.br', 'jose.silva@x.com.br']:
            with self.subTest(email=email):
                self.assertTrue(email_valido(email))

    def test_rejeita_formatos_invalidos(self):
        for email in ['', 'abc', 'ana@', '@x.com', 'ana@x', 'ana silva@x.com', 'ana@@x.com',
                      'a..b@x.com', '.ana@x.com', 'ana@x..com', 'a' * 250 + '@x.com']:
            with self.subTest(email=email):
                self.assertFalse(email_valido(email))


class TesteTelefone(unittest.TestCase):
    def test_aceita_formatos_validos(self):
        for tel in ['11900000001', '(11) 90000-0001', '+55 (11) 90000-0001',
                    '01234567', '+123456789012345']:
            with self.subTest(telefone=tel):
                self.assertTrue(telefone_valido(tel))

    def test_rejeita_formatos_invalidos(self):
        for tel in ['', '   ', 'abc', '11ABC0000', '1234567', '1234567890123456',
                    '11 9000-0001x', '(11 90000-0001']:
            with self.subTest(telefone=tel):
                self.assertFalse(telefone_valido(tel))


class TesteNormalizarNome(unittest.TestCase):
    def test_sem_acento_caixa_e_espacos_repetidos(self):
        self.assertEqual(normalizar_nome('  JOSÉ   da Conceição '), 'jose da conceicao')

    def test_vazio(self):
        self.assertEqual(normalizar_nome('   '), '')


if __name__ == '__main__':
    unittest.main()
