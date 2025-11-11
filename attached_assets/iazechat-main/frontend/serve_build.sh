#!/bin/bash
cd /app/frontend
exec ./node_modules/.bin/serve -s build -l 3000 --no-clipboard
