const path = require('node:path');
const express = require('express');
const helmet = require('helmet');
const morgan = require('morgan');
const engine = require('ejs-mate');
const connectDatabase = require('./db');
const routes = require('./routes');

const app = express();
const port = Number(process.env.PORT) || 3000;

app.engine('ejs', engine);
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

app.use(helmet({ contentSecurityPolicy: false }));
app.use(morgan(process.env.NODE_ENV === 'production' ? 'combined' : 'dev'));
app.use(express.urlencoded({ extended: false, limit: '10kb' }));
app.use(express.static(path.join(__dirname, 'public')));

app.get('/healthz', (_req, res) => res.status(200).json({ status: 'ok' }));
app.use('/', routes);

app.use((req, res) => {
  res.status(404).send('Not found');
});

app.use((err, _req, res, _next) => {
  console.error(err);
  res.status(500).send('An unexpected error occurred.');
});

async function start() {
  try {
    await connectDatabase();
    app.listen(port, '0.0.0.0', () => {
      console.log(`ToDo app listening on port ${port}`);
    });
  } catch (error) {
    console.error('Unable to start application:', error);
    process.exit(1);
  }
}

start();
