const messages = [
  'Ты невероятная, и у тебя всё получится!',
  'Сегодня твой день — используй его на полную!',
  'Ты достойна всего самого лучшего!',
  'Всё, что ты задумала, обязательно сбудется!',
  'Ты сильная, умная и очень классная!',
  'Мир улыбается тебе — улыбайся в ответ!',
  'Ты вдохновляешь окружающих своим примером!',
  'Каждый день ты становишься только лучше!',
  'Твои мечты ближе, чем кажется!',
  'Ты заслуживаешь счастья и радости!',
  'Верь в себя — ты можешь всё!',
  'Ты — источник света и позитива!',
  'Сегодня будет отличный день!',
  'Ты справишься со всем, что встретится на пути!',
  'Ты уникальна и неповторима!',
  'Твои усилия обязательно принесут плоды!',
  'Ты достойна любви и уважения!',
  'Смело иди к своим целям — всё получится!',
  'Ты — чудо!',
  'Всё, что ты делаешь, важно и ценно!'
];

function getMessageOfDay() {
  const now = new Date();
  const start = new Date(now.getFullYear(), 0, 0);
  const diff = now - start;
  const oneDay = 1000 * 60 * 60 * 24;
  const dayOfYear = Math.floor(diff / oneDay);
  return messages[dayOfYear % messages.length];
}

function setTheme(theme) {
  document.body.className = '';
  if (theme === 'dark') document.body.classList.add('theme-dark');
  if (theme === 'color') document.body.classList.add('theme-color');
  localStorage.setItem('inspire-theme', theme);
}

function nextTheme(current) {
  if (current === 'light') return 'dark';
  if (current === 'dark') return 'color';
  return 'light';
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('message').textContent = getMessageOfDay();
  let theme = localStorage.getItem('inspire-theme') || 'light';
  setTheme(theme);
  document.getElementById('themeBtn').onclick = () => {
    theme = nextTheme(theme);
    setTheme(theme);
  };
}); 