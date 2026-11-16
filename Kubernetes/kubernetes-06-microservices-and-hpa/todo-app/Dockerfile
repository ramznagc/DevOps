FROM node:20-alpine

ENV NODE_ENV=production
WORKDIR /usr/src/app

COPY app/package.json ./
RUN npm install --omit=dev && npm cache clean --force

COPY app/ ./

USER node
EXPOSE 3000

CMD ["node", "app.js"]
