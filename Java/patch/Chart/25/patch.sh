#!/bin/bash

grep -rl "import static java\.awt\.print\.Printable\.NO_SUCH_PAGE" . | xargs sed -i 's/import static java\.awt\.print\.Printable\.NO_SUCH_PAGE//g'
grep -rl "import static java\.awt\.print\.Printable\.PAGE_EXISTS" . | xargs sed -i 's/import static java\.awt\.print\.Printable\.PAGE_EXISTS//g'
