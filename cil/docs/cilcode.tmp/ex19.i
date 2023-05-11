# 1 "cilcode.tmp/ex19.c"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "cilcode.tmp/ex19.c"
int main(void) {
# 1 "cilcode.tmp/ex19.c"
   int x, y;
   for(int i = 0; i<5; i++) {
      if(i == 5) continue;
      if(i == 4) break;
      i += 2;
   }
   while(x < 5) {
     if(x == 3) continue;
     x ++;
   }
}
