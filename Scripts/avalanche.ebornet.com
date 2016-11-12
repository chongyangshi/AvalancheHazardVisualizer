server {
    listen  5.39.93.149:80;
    listen [2001:41d0:8:b295::]:80;
    server_name avalanche.ebornet.com;
    rewrite ^(.*) https://$host$1 permanent;
}

server {
    listen  5.39.93.149:443;
    listen [2001:41d0:8:b295::]:443;
    ssl on;
    ssl_certificate /etc/nginx/ssl/ebornet_wc_cert.pem;
    ssl_certificate_key /etc/nginx/ssl/ebornet_wc_key.pem;

    ssl_session_timeout 5m;

    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers "EECDH+CHACHA20:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:!3DES:!MD5";
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
	
    server_name avalanche.ebornet.com;
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
}
