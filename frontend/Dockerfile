FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 19000 19001 19006

CMD ["npm", "run", "web"]
