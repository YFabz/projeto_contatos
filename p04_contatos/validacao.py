"""Regras de formato e normalização dos dados do contato (sem acesso ao banco)."""
import re
import unicodedata

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


class ContatoInvalido(ValueError):
    """Dado fora das regras. A mensagem já é própria para mostrar ao usuário."""


def normalizar_nome(nome):
    """Minúsculas, sem acentos e sem espaços repetidos (usado na busca)."""
    decomposto = unicodedata.normalize('NFD', nome.casefold())
    sem_acento = ''.join(letra for letra in decomposto if not unicodedata.combining(letra))
    return ' '.join(sem_acento.split())


def email_valido(email):
    return len(email) <= 254 and re.fullmatch(FORMATO_EMAIL, email) is not None


def telefone_valido(telefone):
    return re.fullmatch(FORMATO_TELEFONE, telefone) is not None
