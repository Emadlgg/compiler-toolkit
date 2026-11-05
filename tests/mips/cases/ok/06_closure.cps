function mk(): integer {
  let c: integer = 0;
  function inc(): integer { c = c + 1; return c; }
  inc(); inc();
  return inc();
}
print(mk());
