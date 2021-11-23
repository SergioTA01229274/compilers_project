from ply import yacc
import lexer
import sys
import argparse
from lexer import tokens, literals, reserved


def arg_parser():
    parser = argparse.ArgumentParser(description= "YACC parcer")
    parser.add_argument("-f", "--file", nargs="?", help="Program file input")
    var_args = vars(parser.parse_args())
    return var_args


class Node:
    def __init__(self, type, children=None, parent=None, ptype=None):
        self.type = type
        if children:
            self.children = children
        else:
            self.children = []
        if parent:
            self.parent = parent
        else:
            self.parent = None
        if ptype:
            self.ptype = ptype
        else:
            self.ptype = None

def setParentOfChildren(node):
    for child in node.children:
        if isinstance(child, Node):
            child.parent = node

def hasGreaterPrecedence(a, b): # This function compares wheter a has greater precedence than b
    if a in '^':
        return True
    elif a in '*/' and b in '*/':
        return True
    elif a in '*/' and b in '+-':
        return True
    elif a in '+-' and b in '+-':
        return True
    else:
        return False

def treeFromInfix(tmp_tree):
    stack = []
    res = []
    while tmp_tree:
        e = tmp_tree.pop()
        if e == '(':
            stack.append(e)
        elif e == ')':
            while stack and stack[-1] != '(':
                res.append(stack.pop())
            if stack[-1] == '(':
                stack.pop()
            else:
                sys.exit(f'ERROR: Invalid expression at {stack[-1]}')
        elif e in '+-/*^':
            while stack and hasGreaterPrecedence(stack[-1], e):
                res.append(stack.pop())
            stack.append(e)
        else:
            res.append(e)

    while stack:
        res.append(stack.pop())

    stack = []
    tmp_tree = res
    while tmp_tree:
        e = tmp_tree.pop(0)
        if isinstance(e, Node):
            stack.append(e)
        elif e == '(':
            sys.exit("ERROR: Invalid expression.")
        elif e in '+-*/^':
            if len(stack) < 2:
                sys.exit("ERROR: Invalid expression.")
            else:
                a2 = stack.pop()
                if not isinstance(a2, Node):
                    a2 = Node(a2)
                a1 = stack.pop()
                if not isinstance(a1, Node):
                    a1 = Node(a1)
                tmpNode = Node(e, children=[a1, a2])
                setParentOfChildren(tmpNode)
                stack.append(tmpNode)
        else:
            stack.append(e)
    if len(stack) != 1:
        sys.exit("ERROR: Invalid expression.")
    else:
        e = stack.pop()
        if not isinstance(e, Node):
            e = Node(e)
        return e
                

# Parsing rules

def p_block(p):
    '''
    block : stmt block 
            | stmt
    '''
    if len(p) > 2:
        p[0] = Node('block', children=[p[1], p[2]])
        setParentOfChildren(p[0])
    else:
        p[0] = p[1]

def p_stmt(p):
    '''
    stmt : simplestmt ';' 
        | flowctlr 
        | stmtprint ';'
    '''
    p[0] = p[1]

def p_flowctlr(p):
    '''
    flowctlr : IF '(' boolexpr ')' '{' block '}' elif else
    '''
    if len(p) > 2:
        children = [p[3], p[6]] # Here we insert boolexpr and block since the other literals are useless
        if p[8]:
            children.append(p[8])
        if p[9]:
            children.append(p[9])
        p[0] = Node('if', children=children)
        setParentOfChildren(p[0])

def p_flowctlr_while(p):
    '''
    flowctlr : WHILE '(' boolexpr ')' '{' block '}'
    '''
    if len(p) > 2:
        children = [p[3], p[6]] # Here we insert boolexpr and block since the other literals are useless
        p[0] = Node('while', children=children)
        setParentOfChildren(p[0])

def p_elif(p):
    '''
    elif : ELIF '(' boolexpr ')' '{' block '}' elif 
        | lambda
    '''
    if len(p) > 2:
        children = [p[3], p[6]]
        if p[8]:
            children.append(p[8])
        p[0] = Node('elif', children=children)
        setParentOfChildren(p[0])

def p_else(p):
    '''
    else : ELSE '{' block '}' 
        | lambda
    '''
    if len(p) > 2:
        elseNode = Node('else', [p[3]])
        setParentOfChildren(elseNode)
        p[0] = elseNode
        setParentOfChildren(p[0])

def p_simplestmt_assign_num(p):
    '''
    simplestmt : IDEC NAME '=' numexpr 
                | FDEC NAME '=' numexpr
    '''
    d = Node('declaration', [Node(p[2]), Node(p[1])])
    setParentOfChildren(d)
    p[0] = Node('assignment', [d, treeFromInfix(p[4])])
    setParentOfChildren(p[0])

def p_simplestmt_assign_expr(p): # Found a bug in this declarations
    '''
    simplestmt : NAME '=' numexpr
    '''
    p[0] = Node('assignment', [Node(p[1]), treeFromInfix(p[3])])
    setParentOfChildren(p[0])


def p_expr_numexpr(p):
    '''
    expr : numexpr
    '''
    p[0] = treeFromInfix(p[1])

def p_numexpr_num(p):
    '''
    numexpr : num
    '''
    p[0] = [p[1]]

def p_numexpr_arith(p):
    '''
    numexpr : numexpr arith numexpr
    '''
    p[0] = []
    for i in p[1]:
        p[0].append(i)
    p[0].append(p[2])
    for i in p[3]:
        p[0].append(i)

def p_arith(p):
    '''
    arith : '+' 
            | '-' 
            | '*' 
            | '/' 
            | '^'
    '''
    p[0] = p[1]

def p_num(p):
    '''
    num : INUMBER 
        | FNUMBER 
        | NAME
    '''
    p[0] = p[1]

def p_neg_num(p):
    '''
    num : '-' INUMBER 
        | '-' FNUMBER 
        | '-' NAME
    '''

def p_expr_bool_bin(p):
    '''
    boolexpr : boolexpr AND boolexpr
            | boolexpr OR boolexpr
            | boolexpr EQUALS boolexpr
            | boolexpr NOTEQUALS boolexpr 
    '''
    p[0] = Node(p[2], [p[1], p[3]])
    setParentOfChildren(p[0])

def p_expr_bool_num_name(p):
    '''
    boolexpr : NAME EQUALS numexpr
            | NAME NOTEQUALS numexpr
            | NAME GRTOEQTHAN numexpr
            | NAME LESSOEQTHAN numexpr
            | NAME '<' numexpr
            | NAME '>' numexpr
    '''
    p[0] = Node(p[2], [p[1], treeFromInfix(p[3])])
    setParentOfChildren(p[0])

def p_expr_bool_parenthesis(p):
    '''
    boolexpr : '(' boolexpr ')'
    '''
    p[0] = p[2]

def p_expr_bool_boolop(p):
    '''
    boolexpr : boolop
    '''
    p[0] = p[1]

def p_boolop(p):
    '''
    boolop : numcomp 
            | boolval
    '''
    p[0] = p[1]

def p_boolval(p):
    '''
    boolval : TRUE 
            | FALSE 
            | NAME
    '''
    p[0] = Node(p[1])


def p_numcomp(p):
    '''
    numcomp : numexpr EQUALS numexpr
            | numexpr NOTEQUALS numexpr
            | numexpr GRTOEQTHAN numexpr
            | numexpr LESSOEQTHAN numexpr
            | numexpr '<' numexpr
            | numexpr '>' numexpr
    '''
    p[0] = Node(p[2], [treeFromInfix(p[1]), treeFromInfix(p[3])])
    setParentOfChildren(p[0])

def p_stmtprint(p):
    '''
    stmtprint : PRINT '(' expr ')'
    '''
    p[0] = Node(p[1], [p[3]])
    setParentOfChildren(p[0])

def p_lambda(p):
    'lambda :'
    pass

def p_error(p):
    if p:
        print(p)
        print("Syntax error at '%s'" % p.value)
    else:
        print("Syntax error at EOF")

def printChildren(node, level=0):
    if isinstance(node, str):
        print((' ' * level) + node)
    else:
        print((' ' * level) + str(node.type))
        if node.children:
            for child in node.children:
                printChildren(child, level + 1)


parser = yacc.yacc()

if __name__ == '__main__':
    try:
        user_args = arg_parser()
        if user_args["file"]:
            with open(user_args['file'], 'r') as file:
                file_content = file.read()
                root = parser.parse(lexer=lexer.lexer_obj, input=file_content)
                
                if root == None:
                    sys.exit("Syntax error.")
                printChildren(root)

    except OSError:
        print("Error when trying to read the file. Check if file is present.") 
    
    
