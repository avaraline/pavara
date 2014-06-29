import ast

class SafePyFunction(object):
    def __init__(self, args, body, env):
        self.args = args
        self.body = body
        self.env = env
    def call(self, *argvals):
        env = self.env.push()
        for k, v in zip(self.args.args, argvals):
            env.assign(k.id, v)

        evaluate(self.body, env)
        return env.returnval

class Env(object):
    def __init__(self, variables=None):
        if variables is None:
            variables = [{}]
        self.variables = variables
        self.returnval = None

    def lookup(self, name):
        for env in reversed(self.variables):
            if name in env:
                return env[name]
        else:
            raise Exception("variable not found: %s" % name)

    def assign(self, name, value):
        for env in reversed(self.variables):
            if name in env:
                env['name'] = value
                return
        self.variables[-1][name] = value

    def push(self):
        return Env(self.variables + [{}])

def assign(tree, env, val):
    if isinstance(tree, ast.Name):
        env.assign(tree.id, val)
    elif isinstance(tree, ast.Attribute):
        obj = evaluate(tree.value, env)
        setter = 'set_' + tree.attr
        if hasattr(obj, 'set_' + tree.attr):
            getattr(obj, setter)(val)
        else:
            setattr(obj, tree.attr, val)
    else:
        print 'unsupported assignment', tree

def evaluate(tree, env):
    if isinstance(tree, ast.Module):
        return evaluate(tree.body, env)
    elif isinstance(tree, list):
        results = []
        for statement in tree:
            if isinstance(statement, ast.Expr):
                results.append(evaluate(statement.value, env))
            elif isinstance(statement, ast.FunctionDef):
                env.assign(statement.name, SafePyFunction(statement.args, statement.body, env))
            elif isinstance(statement, ast.Assign):
                v = evaluate(statement.value, env)
                if isinstance(v, int) or isinstance(v, float) or isinstance(v, SafePyFunction):
                    assign(statement.targets[0], env, v)
                else:
                    print "unsafe assignment rejected", v
            elif isinstance(statement, ast.Return):
                env.returnval = evaluate(statement.value, env)
            else:
                print statement
        return results
    elif isinstance(tree, ast.Name):
        return env.lookup(tree.id)
    elif isinstance(tree, ast.BinOp):
        left = evaluate(tree.left, env)
        right = evaluate(tree.right, env)
        if isinstance(tree.op, ast.Add):
            return left + right
        elif isinstance(tree.op, ast.Sub):
            return left - right
        else:
            print "unknown operator", tree.op
    elif isinstance(tree, ast.Num):
        return tree.n
    elif isinstance(tree, ast.Attribute):
        obj = evaluate(tree.value, env)
        return getattr(obj, tree.attr)
    else:
        print "unsupported syntax", type(tree)

def safe_eval(script, env=None):
    if env is None:
        env = Env()
    return evaluate(ast.parse(script), env), env

print ast.dump(ast.parse('one.two = 1'))
