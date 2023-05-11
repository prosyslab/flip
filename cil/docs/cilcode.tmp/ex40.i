# 1 "cilcode.tmp/ex40.c"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "cilcode.tmp/ex40.c"
int main(void) {
# 1 "cilcode.tmp/ex40.c"
  int x, y, z;
  return &(x ? y : z) - & (x++, x);
}
