# --- ЭТАП 1: Сборка React-приложения ---
FROM node:18-alpine AS builder

WORKDIR /app

# --- КЛЮЧЕВЫЕ ИЗМЕНЕНИЯ ДЛЯ КЭШИРОВАНИЯ ---
# 1. Сначала копируем ТОЛЬКО файлы с зависимостями
COPY web_client/package.json web_client/package-lock.json* ./

# 2. Устанавливаем зависимости. Этот слой будет кэширован.
RUN npm install
# --- КОНЕЦ ИЗМЕНЕНИЙ ---

# 3. Теперь копируем остальной код.
# Если изменится только код, Docker начнет с этого шага,
# а `npm install` возьмет из кэша.
COPY web_client/ ./

# Собираем React-приложение
RUN npm run build


# --- ЭТАП 2: Запуск в Nginx ---
FROM nginx:alpine

# Копируем ТОЛЬКО результат сборки из первого этапа
COPY --from=builder /app/build /usr/share/nginx/html

# Копируем нашу конфигурацию Nginx
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]