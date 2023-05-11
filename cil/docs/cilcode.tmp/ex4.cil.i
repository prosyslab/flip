# 1 "cilcode.tmp/ex4.cil.c"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "cilcode.tmp/ex4.cil.c"
# 2 "cilcode.tmp/ex4.c"
struct foo {
   int x ;
};
# 1 "cilcode.tmp/ex4.c"
int main(void)
{
  struct foo foo ;

  {
# 8 "cilcode.tmp/ex4.c"
  return (foo.x);
}
}
