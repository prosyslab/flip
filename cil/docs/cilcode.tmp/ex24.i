# 1 "cilcode.tmp/ex24.c"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "cilcode.tmp/ex24.c"
  int dangerous() {
    char array[10];
    scanf("%s",array);
  }

  int main () {
    return dangerous();
  }
