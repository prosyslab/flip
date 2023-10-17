# 1 "cilcode.tmp/ex13.c"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "cilcode.tmp/ex13.c"
  int x = 5;
  int main() {
    int x = 6;
    {
      int x = 7;
      return x;
    }
    return x;
  }
