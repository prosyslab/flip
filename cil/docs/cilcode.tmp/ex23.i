# 1 "cilcode.tmp/ex23.c"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "cilcode.tmp/ex23.c"
  int foo (int predicate) {
    int x = 0;
    switch (predicate) {
      case 0: return 111;
      case 1: x = x + 1;
      case 2: return (x+3);
      case 3: break;
      default: return 222;
    }
    return 333;
  }
