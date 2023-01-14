import socket
import re

HOST = "138.68.183.154"
PORT = 31034

def precedence(op):
     
    if op == '+' or op == '-':
        return 2
    if op == '*' or op == '/':
        return 1
    return 0
 
def applyOp(a, b, op):
    if op == '+': return a + b
    if op == '-': return a - b
    if op == '*': return a * b
    if op == '/': return a // b
 

def evaluate(tokens):
    # stack to store integer values.
    values = []
     
    # stack to store operators.
    ops = []
    i = 0
     
    while i < len(tokens):
         
        # Current token is a whitespace,
        # skip it.
        if tokens[i] == ' ':
            i += 1
            continue
         
        # Current token is an opening
        # brace, push it to 'ops'
        elif tokens[i] == '(':
            ops.append(tokens[i])
         
        # Current token is a number, push
        # it to stack for numbers.
        elif tokens[i].isdigit():
            val = 0
             
            # There may be more than one
            # digits in the number.
            while (i < len(tokens) and
                tokens[i].isdigit()):
             
                val = (val * 10) + int(tokens[i])
                i += 1
             
            values.append(val)
             
            # right now the i points to
            # the character next to the digit,
            # since the for loop also increases
            # the i, we would skip one
            #  token position; we need to
            # decrease the value of i by 1 to
            # correct the offset.
            i -= 1
         
        # Closing brace encountered,
        # solve entire brace.
        elif tokens[i] == ')':
         
            while len(ops) != 0 and ops[-1] != '(':
                val2 = values.pop()
                val1 = values.pop()
                op = ops.pop()
                 
                values.append(applyOp(val1, val2, op))
             
            # pop opening brace.
            ops.pop()
         
        # Current token is an operator.
        else:
            # While top of 'ops' has same or
            # greater precedence to current
            # token, which is an operator.
            # Apply operator on top of 'ops'
            # to top two elements in values stack.
            while (len(ops) != 0 and
                precedence(ops[-1]) >=
                   precedence(tokens[i])):
                         
                val2 = values.pop()
                val1 = values.pop()
                op = ops.pop()
                 
                values.append(applyOp(val1, val2, op))
             
            # Push current token to 'ops'.
            ops.append(tokens[i])
         
        i += 1
     
    # Entire expression has been parsed
    # at this point, apply remaining ops
    # to remaining values.
    while len(ops) != 0:
         
        val2 = values.pop()
        val1 = values.pop()
        op = ops.pop()
                 
        values.append(applyOp(val1, val2, op))
     
    # Top of 'values' contains result,
    # return it.
    return values[-1]


def data_string(data: bytes) -> str:
    stringdata = data.decode('utf-8')
    return stringdata

def eval_expression(data: str) -> str:
    for line in data.splitlines():
        p = re.compile('\[[0-9]+\]')

        if p.match(line):
            expression = line[7:-4]
            return f"{evaluate(expression)}"

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        while True:
            data = s.recv(2048)
            data_str = data_string(data)

            print(data_str)

            value = eval_expression(data_str)

            if value:
                print(value)
                try:
                    s.send(value.encode() + b"\n")
                    # s.send(b"\n")
                except Error as e:
                    print(e)
                    exit(-1)
            else:
                break

if __name__ == "__main__":
    main()