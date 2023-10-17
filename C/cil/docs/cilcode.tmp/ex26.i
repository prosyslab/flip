# 1 "cilcode.tmp/ex26.c"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "cilcode.tmp/ex26.c"
  int foo (int predicate) {
    if (predicate <= 0) {
      return 1;
    } else {
      if (predicate > 5)
        return 2;
      return 3;
    }
  }
