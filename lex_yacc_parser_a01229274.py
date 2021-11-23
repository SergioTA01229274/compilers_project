import sys
import signal



# Build the lexer
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
        tmp_var = 0 + p[2].val
        print(f'{tmp_var}')
        tmp_node = Node(p[2], 'PRINT')
        abstract_tree.append(tmp_node)
        
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
        tmp_node = Node(p[1], 'INT')
        new_node = Node(p[2], 'ASSIGN', [tmp_node, p[3]])
        abstract_tree.append(new_node)
    except LookupError:
        print("Undefined name '%s'" % p[1])
        print("You must declare a variable before using the calculator")
    
def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression'''
    if p[2] == '+':
        p[0] = p[1] + p[3]
        tmp_node = Node()
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



global data
data = ''

def signal_handler(sig, frame):
    print('\nExiting yacc parser...')
    print('\nGetting the tokens that were generated from the input...\n')
    global data
    lexer.input(data)
    while True:
        tok = lexer.token()
        if not tok: 
            break
        print(tok)
    print('\nShowing AST...\n')

    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

global line_cont
line_cont = 1

