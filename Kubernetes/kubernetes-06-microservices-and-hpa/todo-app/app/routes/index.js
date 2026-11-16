const express = require('express');
const mongoose = require('mongoose');
const { Todo } = require('../db');
const { normalizeTodoContent } = require('../utils');

const router = express.Router();

router.get('/', async (_req, res, next) => {
  try {
    const todos = await Todo.find().sort({ updated_at: -1 }).lean();
    res.render('index', { title: 'ToDo List', todos });
  } catch (error) {
    next(error);
  }
});

router.post('/create', async (req, res, next) => {
  try {
    const content = normalizeTodoContent(req.body.content);
    if (!content) return res.status(400).send('ToDo content is required.');
    await Todo.create({ content, updated_at: new Date() });
    res.redirect('/');
  } catch (error) {
    next(error);
  }
});

router.post('/destroy/:id', async (req, res, next) => {
  try {
    if (!mongoose.isValidObjectId(req.params.id)) {
      return res.status(400).send('Invalid ToDo ID.');
    }
    await Todo.findByIdAndDelete(req.params.id);
    res.redirect('/');
  } catch (error) {
    next(error);
  }
});

router.get('/edit/:id', async (req, res, next) => {
  try {
    if (!mongoose.isValidObjectId(req.params.id)) {
      return res.status(400).send('Invalid ToDo ID.');
    }
    const todo = await Todo.findById(req.params.id).lean();
    if (!todo) return res.status(404).send('ToDo not found.');
    res.render('edit', { title: 'Edit ToDo', todo });
  } catch (error) {
    next(error);
  }
});

router.post('/update/:id', async (req, res, next) => {
  try {
    if (!mongoose.isValidObjectId(req.params.id)) {
      return res.status(400).send('Invalid ToDo ID.');
    }
    const content = normalizeTodoContent(req.body.content);
    if (!content) return res.status(400).send('ToDo content is required.');
    const todo = await Todo.findByIdAndUpdate(
      req.params.id,
      { content, updated_at: new Date() },
      { new: true, runValidators: true }
    );
    if (!todo) return res.status(404).send('ToDo not found.');
    res.redirect('/');
  } catch (error) {
    next(error);
  }
});

module.exports = router;
