const mongoose = require('mongoose');

const todoSchema = new mongoose.Schema({
  content: {
    type: String,
    required: true,
    trim: true,
    maxlength: 500
  },
  updated_at: {
    type: Date,
    default: Date.now
  }
});

const Todo = mongoose.models.Todo || mongoose.model('Todo', todoSchema);

async function connectDatabase() {
  const uri = process.env.DBHOST || 'mongodb://db:27017/express-todo';
  await mongoose.connect(uri, {
    serverSelectionTimeoutMS: 10000
  });
  console.log('Connected to MongoDB');
}

module.exports = connectDatabase;
module.exports.Todo = Todo;
