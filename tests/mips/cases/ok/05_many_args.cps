function f(a: integer, b: integer, c: integer, d: integer, e: integer, g: integer): integer { return a+b+c+d+e+g; }
print(f(1,2,3,4,5,6));
function g(x: integer): integer { return f(x,x,x,x,x,x); }
print(g(g(1)));
