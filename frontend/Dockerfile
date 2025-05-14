FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

ENV VITE_API_BASE_URL=http://localhost:8000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
