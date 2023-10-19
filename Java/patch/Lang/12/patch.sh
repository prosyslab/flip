#!/bin/bash

grep -rl "(Enum," | xargs sed -i 's/(Enum,/(/g'
grep -rl "ValuedEnum = ((ValuedEnum) (it.next()));" | xargs sed -i "s/ValuedEnum = ((ValuedEnum) (it\.next()))\;/for (it = list\.iterator()\; it\.hasNext()\;) {\nValuedEnum enum = (ValuedEnum) it\.next()\;\nif (enum\.getValue() == value) {\nreturn enum\;\n}\n}\nreturn null\;/g"
grep -rl "<MultiBackgroundInitializerResults>" | xargs sed -i "s/<MultiBackgroundInitializerResults>/<MultiBackgroundInitializer.MultiBackgroundInitializerResults>/g"
