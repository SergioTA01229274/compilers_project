import sys
import signal

tokens = (
    'NAME', 'INUMBER','FNUMBER', 'PLUS', 'MINUS', 'ASSIGN', 'PRINT', 'IDEC', 'FDEC'
)

def t_PLUS(t):
    r'\+'
    t.value = str(t.value)
    return t

def t_MINUS(t):
    r'\-'
    t.value = str(t.value)
    return t

def t_ASSIGN(t):
    r'\='
    t.value = str(t.value)
    return t

def t_IDEC(t):
    r'int'
    t.value = str(t.value)
    return t

def t_FDEC(t):
    r'float'
    t.value = str(t.value)
    return t

def t_PRINT(t):
    r'print'
    t.value = str(t.value)
    return t

def t_NAME(t):
    r'[a-z]'
    t.value = str(t.value)
    return t

def t_FNUMBER(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_INUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")

def t_error(t):
    if str(t.value[0]) == ' ' or str(t.value[0]) == '\t':
        t.lexer.skip(1)
    else:
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

class Node:
    val = ''
    type = ''
    childrens = []
    def __init__(self, val, type, childrens=[]):
        self.val = val
        self.type = type
        self.childrens = childrens

# Build the lexer
import ply.lex as lex
lexer = lex.lex()

# Parsing rules
precedence = (    
    ('right', 'UMINUS'),
)
names = {}
abstract_tree = []

def p_statement_declare_float(p):
    'statement : FDEC NAME is_assign'
    tmp_node = Node(p[2], 'FLOAT')
    new_node = Node(p[3], 'ASSIGN', [tmp_node, p[3]])
    abstract_tree.append(new_node)
    names[p[2]] = {"type":"FLOAT","value":p[3].val}

def p_statement_declare_int(p):
    'statement : IDEC NAME is_assign'
    if p[3].type == 'FLOAT':
        print('Cannot asign a float to an int.')
    else:
        tmp_node = Node(p[2], 'INT')
        new_node = Node(p[3], 'ASSIGN', [tmp_node, p[3]])
        abstract_tree.append(new_node)
        names[p[2]] = {"type":"INT","value":p[3].val}

def p_is_assign(p):
    '''is_assign : ASSIGN expression
                | '''
    p[0] = Node(0, 'INT')
    if len(p) > 2:
        p[0].type = p[2].type
        p[0].val = p[2].val
        p[0].children = [p[2]]

def p_statement_print(p):
    'statement : PRINT expression'
    try:
        tmp_var = 0 + p[2]
        tmp_node = Node(p[2], 'PRINT')
        abstract_tree.append(tmp_node)
        print(f'{tmp_var}')
    except TypeError:
        print("Cannot print the variable. Variable is not declared or hasn't bein initialized.")

def p_expression_inumber(p):
    "expression : INUMBER"
    p[0] = Node(p[1], 'INT')

def p_expression_fnumber(p):
    "expression : FNUMBER"    
    p[0] = Node(p[1], 'FLOAT')

def p_statement_assign(p):
    'statement : NAME ASSIGN expression'
    try:
        names[p[1]]["value"] = p[3]
        p[0] = Node(0, 'INT', )
    except LookupError:
        print("Undefined name '%s'" % p[1])
        print("You must declare a variable before using the calculator")
    
def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression'''
    if p[2] == '+':
        p[0] = p[1] + p[3]
    elif p[2] == '-':
        p[0] = p[1] - p[3]

def p_expression_uminus(p):
    "expression : '-' expression %prec UMINUS"
    p[0] = -p[2]

def p_expression_group(p):
    "expression : '(' expression ')'"
    p[0] = p[2]

def p_expression_name(p):
    "expression : NAME"
    try:
        p[0] = names[p[1]]["value"]
    except LookupError:
        print("Undefined name '%s'" % p[1])
        p[0] = None

def p_error(p):
    global line_cont
    if p:
        print("Error at line %d" % line_cont)
        print("Syntax error at '%s'" % p.value)
    else:
        print("Syntax error at EOF")


"""
data = 'i g\ng = 20'
lexer.input(data)
while True:
    tok = lexer.token()
    if not tok: 
        break
    print(tok)
"""

import ply.yacc as yacc
parser = yacc.yacc()

data = ''
def signal_handler(sig, frame):
    print('\nExiting yacc parser...')
    print('\nGetting the tokens that were generated from the input...\n')
    lexer.input(data)
    while True:
        tok = lexer.token()
        if not tok: 
            break
        print(tok)
    print('\nShowing AST...\n')
    for node in abstract_tree:
        print(node.type, node.val.val)
        print('\t')

    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
"""

file = open('ac_program.txt')
content = file.read()
print(content)
yacc.parse(content)

"""

global line_cont
line_cont = 1
while True:
    try:
        s = input('calc > ')
    except EOFError:
        break
    if not s:
        continue 
    data += s
    yacc.parse(s)
    line_cont += 1