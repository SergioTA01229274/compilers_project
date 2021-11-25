import sys
import re
import copy

class variable:
    def __init__(self,value,type):
        self.type=type
        self.value=value

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

variables={}

def getVartype(node, varName):
    if node in variables.keys() and varName in (o.value for o in variables[node]):
        return [x for x in variables[node] if x.value == varName][0].type
    if node.type == "else" or node.type == "elif":
        currentNode = node.parent
        while((currentNode.type == "if" or currentNode.type == "elif") and currentNode.parent):
            currentNode = currentNode.parent
        return getVartype(currentNode, varName)
    if node.parent:
        return getVartype(node.parent, varName)
    else:
        return None

def findScopeNode(node):
    if(node.type in ["block", "for", "if", "elif", "else", "while"]):
        return node
    if(node.parent):
        return findScopeNode(node.parent)
    return Node('Self')

def isVarInTree(node,varName):
    if node.children:
        for child in node.children:
            isVarInTree(child,varName)
    elif node.type==varName:
        sys.exit('Asignación inválida')

def printVariables(r):
    if r.type=="declaration":
        print(r.children[0].type+" declarado como "+r.children[1].type+ " dentro de "+findScopeNode(r).type)
        scopeNode = findScopeNode(r)
        if scopeNode in variables.keys():
            variables[scopeNode].append(variable(r.children[0].type,r.children[1].type))
        else:
            variables[scopeNode]=[variable(r.children[0].type,r.children[1].type)]
    if r.children:
        for child in r.children:
            printVariables(child)

def isWithinScope(node, varName):
    if node in variables.keys() and varName in (o.value for o in variables[node]):
        return True
    if node.type=="else" or node.type=="elif":
        currentNode=node.parent
        while((currentNode.type=="if" or currentNode.type=="elif")):
            currentNode = currentNode.parent
            if currentNode == None:
                return False
        return isWithinScope(currentNode, varName)
    if node.parent:
        return isWithinScope(node.parent,varName)
    else:
        return False

def treeNumtypeCheck(node):
    if node.children:
        if not node.type in ["+","-","/","*","^"]:
            sys.exit('[!] ERROR: Invalid number assignment.')
        for child in node.children:
            treeNumtypeCheck(child)
        if node.children[0].ptype == node.children[1].ptype:
            node.ptype=node.children[0].ptype
        else:
            for i in range(len(node.children)):
                if node.children[i].ptype=="int":
                    parseNode=Node('intToFloat',ptype="float")
                    node.children[i].parent=parseNode
                    parseNode.children.append(node.children[i])
                    node.children[i]=parseNode
            node.ptype="float"
    else:
        if(re.fullmatch(r'-?\d+',node.type)):
            node.ptype="int"
        elif(re.fullmatch(r'-?\d+\.\d+', node.type)):
            node.ptype="float"
        else:
            if((node.type[0]=="-" and not isWithinScope(node,node.type[1:])) or (node.type[0] != "-" and not isWithinScope(node,node.type))):
                if node.type in ['true', 'false'] and node.parent.type in ['<', '>', '==', '!=']:
                    sys.exit(f'[!] ERROR: Cannot compare boolean with number.')
                elif (re.fullmatch(r'true',node.type) or re.fullmatch(r'false',node.type)) and node.parent.type == 'assignment':
                    sys.exit(f'[!] ERROR: Cannot assign boolean to number.') 
                elif re.fullmatch(r'[A-Za-z_][\w_]*',node.type):
                    if not isWithinScope(findScopeNode(node), node.type):
                        sys.exit(f'[!] ERROR: Variable \'{node.type}\' not declared within scope.')
                    sys.exit(f'[!] ERROR: Cannot convert \'{node.type}\' to number.')
            if(node.type[0]=="-"):
                vartype=getVartype(node,node.type[1:])
            else:
                vartype=getVartype(node,node.type)
            node.ptype=vartype

def treeBooltypeCheck(node):
    if not node.children:
        if node.type != "true" and node.type != "false":
            if not isWithinScope(node, node.type):
                sys.exit(f'[!] ERROR: Variable {node.type} not declared within scope.')
            vartype=getVartype(node,node.type)
            if vartype != "boolean":
                sys.exit(f'[!] ERROR: Cannot convert {vartype} to boolean.')
    elif node.type in ["==","!="]:
        if(node.children[0].type in ["+","-","/","*","^"] or re.match(r'-?\d+', node.children[0].type)):
            treeNumtypeCheck(node.children[0])
            treeNumtypeCheck(node.children[1])
        elif(node.children[0].type in ["==","!=","<",">",">=","<=","and","or","true","false"]):
            treeNumtypeCheck(node.children[0])
            treeNumtypeCheck(node.children[1])
        else:
            child0type=getVartype(node,node.children[0].type)
            if child0type == "float" or child0type == "int":
                treeNumtypeCheck(node.children[1])
            elif child0type == "boolean":
                treeBooltypeCheck(node.children[1])
            else:
                sys.exit(f'[!] ERROR: Variable {node.children[0].type} already declared within scope.')
    elif node.type in ["<",">","<=",">="]:
        treeNumtypeCheck(node.children[0])
        treeNumtypeCheck(node.children[1])
    elif node.type in ["and","or"]:
        treeBooltypeCheck(node.children[0])
        treeBooltypeCheck(node.children[1])

def setVariables(r):
    if(r.type == "declaration"):
        if isWithinScope(r,r.children[0].type):
            sys.exit(f'[!] ERROR: Variable {r.children[0].type} already declared within scope.')
        scopeNode = findScopeNode(r)
        if scopeNode in variables.keys():
            variables[scopeNode].append(variable(r.children[0].type,r.children[1].type))
        else:
            variables[scopeNode]=[variable(r.children[0].type,r.children[1].type)]
    if r.children:
        for child in r.children:
            setVariables(child)


def semanticAnalysis(r, numLine):
    checkChildren = True
    if(r.type=="assignment"):
        correcttype=""
        if r.children[0].type=="declaration":
            correcttype = r.children[0].children[1].type
            varName = r.children[0].children[0].type
            isVarInTree(r.children[1], varName)
        elif (not isWithinScope(r,r.children[0].type)):
            sys.exit(f'[!] ERROR at line {numLine}. Variable {r.children[0].type} not declared within scope.')
        else:
            correcttype=getVartype(r,r.children[0].type)
        if correcttype == "int" or correcttype == "float":
            treeNumtypeCheck(r.children[1])
            if correcttype == "float" and r.children[1].ptype == "int":
                parseNode=Node('intToFloat', ptype="float")
                r.children[1].parent=parseNode
                parseNode.children=[r.children[1]]
                r.children[1]=parseNode
            elif r.children[1].ptype != correcttype:
                sys.exit(f'[!] ERROR at line {numLine}. Cannot convert {r.children[1].ptype} to {correcttype}.')
        elif correcttype == "boolean":
            treeBooltypeCheck(r.children[1])
        checkChildren = False
    elif(r.type in ["+","-","/","*","^"] or re.match(r'-?\d+',r.type)):
        treeNumtypeCheck(r)
        checkChildren = False
    elif(r.type in ["==","!=","<",">",">=","<=","and","or","true","false"]):
        treeBooltypeCheck(r)
        checkChildren = False
    if r.children and checkChildren:
        for child in r.children:
            semanticAnalysis(child, numLine + 1)
