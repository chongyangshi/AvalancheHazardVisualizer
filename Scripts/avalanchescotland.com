server {
    listen  192.99.1.219:80;
    listen [2607:5300:60:32db::1]:80;
    server_name avalanchescotland.com www.avalanchescotland.com;
    rewrite ^(.*) https://$host$1 permanent;
}

server {
    listen  192.99.1.219:443;
    listen [2607:5300:60:32db::1]:443;
    ssl on;
    ssl_certificate /etc/nginx/ssl/avalanchescotland_crt.pem;
    ssl_certificate_key /etc/nginx/ssl/avalanchescotland_key.pem;

    ssl_session_timeout 5m;

    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers "EECDH+CHACHA20:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:!3DES:!MD5";
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
	
    server_name avalanchescotland.com www.avalanchescotland.com;
    root /home/cesium/;

    location / {
        try_files $uri $uri/ =404;
    }

    location /api {
        rewrite /api/(.*) /$1 break;
        #proxy_pass http://127.0.0.1:5000;
        include uwsgi_params;
        uwsgi_pass unix:/home/BEngProject/wsgi.sock;
    }
    location ~* \.(?:gif|jpe?g|png)$ {
        expires 6h;
        add_header Pragma public;
        add_header Cache-Control "public";
    }
}
