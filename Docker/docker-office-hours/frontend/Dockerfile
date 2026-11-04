FROM node:18-alpine
WORKDIR /app
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=${REACT_APP_API_URL}
COPY package*.json ./
RUN npm install --silent
COPY public/ ./public/
COPY src/ ./src/
RUN npm run build
RUN npm install -g serve
EXPOSE 3000
CMD ["serve", "-s", "build", "-l", "3000"]
