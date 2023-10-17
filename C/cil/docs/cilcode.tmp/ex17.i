# 1 "cilcode.tmp/ex17.c"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "cilcode.tmp/ex17.c"
int main(void) {
# 1 "cilcode.tmp/ex17.c"
  int x;
  int y = x ? 2 : 4;
  int z = x || y;

  if(x && y) { return 0; } else { return 1; }


  if(x && y || z) { x ++; y ++; z ++; x ++; y ++; return z; }
}
