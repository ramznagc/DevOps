function normalizeTodoContent(value) {
  if (typeof value !== 'string') return '';
  return value.trim().slice(0, 500);
}

module.exports = { normalizeTodoContent };
