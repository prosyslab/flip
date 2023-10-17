# 1 "cilcode.tmp/ex7.c"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "cilcode.tmp/ex7.c"
int main() {
  enum {
     FIVE = 5,
     SIX, SEVEN,
     FOUR = FIVE - 1,
     EIGHT = sizeof(double)
  } x = FIVE;
 return x;
}
