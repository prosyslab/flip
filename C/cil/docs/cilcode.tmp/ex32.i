# 1 "cilcode.tmp/ex32.c"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "cilcode.tmp/ex32.c"
int x = 5;
int f() {
  int x = 3;
  {
    extern int x;
    return x;
  }
}
