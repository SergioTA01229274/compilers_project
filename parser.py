from ply import yacc
import lexer
import sys
from lexer import tokens, literals, reserved
import semantic
import argparse

tNodes = {}
lNodes = {}
res_3AC = ''

tCounter = 1
lCounter = 1


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

def p_flowctlr_for(p):
    '''
    flowctlr : FOR '(' simplestmt ';' boolexpr ';' simplestmt ')' '{' block '}'
    '''
    if len(p) > 6:
        children = [p[3], p[5], p[7], p[10]] 
        p[0] = Node('for', children=children)
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

def p_simplestmt_iter(p):
    '''
    simplestmt : NAME PLUSITER
                | NAME MINUSITER
    '''
    p[0] = Node('iter', [Node(p[1]), Node(p[2])])
    setParentOfChildren(p[0])

def p_simplestmt_assign_non_dec(p):
    '''
    simplestmt : INT NAME 
                | FLOAT NAME
                | BOOLEAN NAME
    '''
    p[0] = Node('declaration', [Node(p[2]), Node(p[1])])
    setParentOfChildren(p[0])

def p_simplestmt_assign_num(p):
    '''
    simplestmt : INT NAME '=' numexpr 
                | FLOAT NAME '=' numexpr
                | BOOLEAN NAME '=' numexpr
    '''
    d = Node('declaration', [Node(p[2]), Node(p[1])])
    setParentOfChildren(d)
    p[0] = Node('assignment', [d, treeFromInfix(p[4])])
    setParentOfChildren(p[0])

def p_simplestmt_assign_expr(p):
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

def p_numexpr_parenthesis(p):
    '''
    numexpr : '(' numexpr ')'
    '''
    p[0] = []
    for i in p[2]:
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
        | TRUE
        | FALSE
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
    p[0] = Node(p[2], [Node(p[1]), treeFromInfix(p[3])])
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
        sys.exit(f'[!] Syntax error at line {p.lineno}. Cause of the problem is \'{p.value}\'')
    else:
        sys.exit("Syntax error at EOF")

def printChildren(node, level=0):
    print((' ' * level) + str(node.type))
    if node.children:
        for child in node.children:
            printChildren(child, level + 1)

def generateTAC(node):
    global tCounter
    global lCounter
    global res_3AC
    
    if node.type in ["block"]:
        for child in node.children:
            generateTAC(child)
    elif node.type == "declaration":
        child_type = node.children[1].type
        res_3AC += f'{child_type} decl({node.children[0].type})\n' 
        tNodes[node]=node.children[0].type
    elif node.type == "assignment":
        generateTAC(node.children[0])
        generateTAC(node.children[1])
        res_3AC += f'{tNodes[node.children[0]]} := {tNodes[node.children[1]]}\n' 
    elif node.type == "intToFloat":
        generateTAC(node.children[0])
        res_3AC += f't{str(tCounter)} := {node.type}({tNodes[node.children[0]]})\n'
        tNodes[node]=f't{str(tCounter)}'
        tCounter+=1
    elif node.type in ["+","-","/","*","^"]:
        generateTAC(node.children[0]) # Recursion is applied in case the children are more arithmetic expresions
        generateTAC(node.children[1])
        res_3AC += f't{str(tCounter)} := {tNodes[node.children[1]]} {node.type} {tNodes[node.children[0]]}\n'
        tNodes[node]=f't{str(tCounter)}'
        tCounter+=1
    elif node.type in ['iter']:
        generateTAC(node.children[0])
        res_3AC += f't{str(tCounter)} := {tNodes[node.children[0]]} {node.children[1].type[0]} 1\n'
        res_3AC += f'{tNodes[node.children[0]]} := t{str(tCounter)}\n'

        tNodes[node.children[0]]=f't{str(tCounter)}'
        tCounter+=1
    elif node.type == 'else':
        for child in node.children:
            generateTAC(child)
        res_3AC += f'goto L{lNodes[node.parent]}\n'
    elif node.type in ["!=","==","<",">","<=",">="]:
        generateTAC(node.children[0]) # Recursion is applied in case the children are logical comparisson operators: and, or
        generateTAC(node.children[1])
        res_3AC += f'({tNodes[node.children[0]]} {node.type} {tNodes[node.children[1]]}) IFGOTO L{str(lCounter)}\n'
        res_3AC += f't{str(tCounter)} := false\n'
        if node.parent.type == 'for':
            res_3AC += f'goto L{str(lCounter+2)}\n'
        else:
            res_3AC += f'goto L{str(lCounter+1)}\n'
        res_3AC += f'\nL{str(lCounter)}\n'
        res_3AC += f't{str(tCounter)} := true\n'
        res_3AC += f'goto L{str(lCounter+2)}\n'
        if node.parent.type != 'for':
            res_3AC += f'\nL{str(lCounter+1)}\n'
        
        tNodes[node]=f't{str(tCounter)}'
        tCounter+=1
        lCounter+=2
    elif node.type == "and":
        generateTAC(node.children[0])
        generateTAC(node.children[1])
        res_3AC += f'({tNodes[node.children[0]]}) IFGOTO L{str(lCounter)}\n'
        res_3AC += f't{str(tCounter)} := false\n'
        res_3AC += f'goto L{str(lCounter+2)}\n'
        res_3AC += f'\nL{str(lCounter)}\n'
        res_3AC += f'{tNodes[node.children[1]]}) IFGOTO L{str(lCounter+1)}\n'
        res_3AC += f't{str(tCounter)} := false\n'
        res_3AC += f'goto L{str(lCounter+2)}\n'
        res_3AC += f'\nL{str(lCounter+1)}\n'
        res_3AC += f't{str(tCounter)} := true\n'
        res_3AC += f'\nL{str(lCounter+2)}\n'
        tNodes[node]=f't{str(tCounter)}'
        tCounter+=1
        lCounter+=3
    elif node.type == "or":
        generateTAC(node.children[0])
        generateTAC(node.children[1])
        res_3AC += f'{tNodes[node.children[0]]}) IFGOTO L{str(lCounter)}\n'
        res_3AC += f'{tNodes[node.children[1]]}) IFGOTO L{str(lCounter)}\n'
        res_3AC += f't{str(tCounter)} := false\n'
        res_3AC += f'goto L{str(lCounter+1)}\n'
        res_3AC += f'\nL{str(lCounter)}\n'
        res_3AC += f't{str(tCounter)} := true\n'
        res_3AC += f'\nL{str(lCounter+1)}\n'
        tNodes[node]=f't{str(tCounter)}'
        tCounter+=1
        lCounter+=2
    elif node.type == 'print':
        generateTAC(node.children[0])
        res_3AC += f'print({tNodes[node.children[0]]})\n'
    elif node.type in ["if","elif"]:
        generateTAC(node.children[0])
        res_3AC += f'{tNodes[node.children[0]]}) IFGOTO L{str(lCounter)}\n'
        res_3AC += f'goto L{str(lCounter+1)}\n'
        res_3AC += f'\nL{str(lCounter)}\n'
        saveLCount = lCounter
        lCounter+=2
        generateTAC(node.children[1])
        saveLCount2=lCounter
        if node.type == "if":
            res_3AC += f'goto L{str(lCounter)}\n'
            lNodes[node] = str(lCounter)
            lCounter+=1
        else:
            lNodes[node]=lNodes[node.parent]
            res_3AC += f'goto L{lNodes[node.parent]}\n'
        res_3AC += f'\nL{str(saveLCount+1)}\n'
        if len(node.children) == 4:
            generateTAC(node.children[3])
        if len(node.children) > 2:
            generateTAC(node.children[2])
            
        if node.type == "if":
            res_3AC += f'\nL{str(saveLCount2)}\n'
    elif node.type == "while":
        generateTAC(node.children[0])
        res_3AC += f'\nL{str(lCounter)}'
        res_3AC += f'({tNodes[node.children[0]]}) IFGOTO L{str(lCounter+1)}'
        res_3AC += f'goto L{str(lCounter+2)}'
        res_3AC += f'\n while L{str(lCounter+1)}'
        saveLCount=lCounter
        lCounter+=3
        generateTAC(node.children[1])
        res_3AC += f'goto L{str(saveLCount)}'
        res_3AC += f'\nL{str(saveLCount+2)}'
    elif node.type == "for":
        res_3AC += f'\n\'FOR\' L{str(lCounter)}\n'
        generateTAC(node.children[0])
        lCounter += 1
        res_3AC += f'goto L{str(lCounter+1)}\n'
        saveLCount=lCounter
        res_3AC += f'\n\'FOR\' L{str(lCounter + 1)}\n'
        generateTAC(node.children[1])
        res_3AC += f'\n\'FOR\' L{str(lCounter)}\n'
        res_3AC += f'({tNodes[node.children[1]]}) IFGOTO L{str(lCounter + 1)}\n'
        res_3AC += f'goto L{str(lCounter+2)}\n'
        res_3AC += f'\n\'FOR\' L{str(lCounter+1)}\n'
        generateTAC(node.children[2])
        generateTAC(node.children[3])
        res_3AC += f'goto L{str(saveLCount + 1)}\n'
        
        res_3AC += f'\nL{str(lCounter+2)}\n'
        saveLCount2=lCounter
        lCounter+=4
    
    elif not node.children:
        if node.type[0] == "-":
            res_3AC += f't{str(tCounter)} := 0 - {node.type[1:]}\n'
            tNodes[node]=f't{str(tCounter)}'
            tCounter+=1
        else:
            tNodes[node]=node.type

parser_obj = yacc.yacc()

if __name__ == '__main__':
    try:
        user_args = arg_parser()
        if user_args["file"]:
            with open('test.txt', 'r') as file:
                file_content = file.read()
                root = parser_obj.parse(lexer=lexer.lexer_obj, input=file_content)
                if root == None:
                    sys.exit("Syntax error. No content on file !")
                
                semantic.setVariables(root)
                semantic.semanticAnalysis(root, 1)
                generateTAC(root)
                print(res_3AC)
    except OSError:
        print("Error when trying to read the file. Check if file is present.") 

