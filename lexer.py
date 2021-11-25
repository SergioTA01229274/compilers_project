import sys
from ply import lex

reserved = {'and': 'AND', 
            'or':'OR',
            'while':'WHILE',
            'for':'FOR',
            'if':'IF',
            'elif':'ELIF',
            'else':'ELSE',
            'true':'TRUE',
            'false':'FALSE',
            'print':'PRINT'
}

tokens = list(reserved.values()) + [
    'NAME', 'INUMBER','FNUMBER', 'BOOLEAN','INT', 'FLOAT', 'EQUALS', 'NOTEQUALS', 'GRTOEQTHAN', 'LESSOEQTHAN', 'PLUSITER', 'MINUSITER'
]

literals = ['-', '+', '*', '^', '/', '=', '>', '<', '(', ')', '{', '}', ';']
t_EQUALS = r'=='
t_NOTEQUALS = r'!='
t_GRTOEQTHAN = r'>='
t_LESSOEQTHAN = r'<='
t_PLUSITER = r'\+\+'
t_MINUSITER = r'\-\-'
t_INUMBER = r'\d+'
t_FNUMBER = r'\d+\.\d+'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")

def t_error(t):
    if str(t.value[0]) == ' ' or str(t.value[0]) == '\t':
        t.lexer.skip(1)
    else:
        sys.exit(f'[!] ERROR: Illegal character {t.value[0]}')
        t.lexer.skip(1)

def t_INT(t):
    r'int'
    t.value = str(t.value)
    return t

def t_FLOAT(t):
    r'float'
    t.value = str(t.value)
    return t

def t_BOOLEAN(t):
    r'boolean'
    t.value = str(t.value)
    return t

def t_PRINT(t):
    r'print'
    t.value = str(t.value)
    return t

def t_AND(t):
    r'and'
    t.value = str(t.value)
    return t

def t_OR(t):
    r'or'
    t.value = str(t.value)
    return t

def t_WHILE(t):
    r'while'
    t.value = str(t.value)
    return t

def t_FOR(t):
    r'for'
    t.value = str(t.value)
    return t

def t_IF(t):
    r'if'
    t.value = str(t.value)
    return t

def t_ELIF(t):
    r'elif'
    t.value = str(t.value)
    return t

def t_ELSE(t):
    r'else'
    t.value = str(t.value)
    return t

def t_TRUE(t):
    r'true'
    t.value = str(t.value)
    return t

def t_FALSE(t):
    r'false'
    t.value = str(t.value)
    return t

def t_NAME(t):
    r'[A-Za-z_][\w_]*'
    t.value = str(t.value)
    return t

lexer_obj = lex.lex()