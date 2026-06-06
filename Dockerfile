# Použijeme odlehčený webový server Nginx
FROM nginx:alpine

# Zkopírujeme naši stránku do složky, odkud Nginx servíruje web
COPY index.html /usr/share/nginx/html/index.html

# Exponujeme port 80 do okolí
EXPOSE 80