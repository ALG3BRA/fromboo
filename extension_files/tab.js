document.addEventListener('DOMContentLoaded', async () => {
  const wordList = document.getElementById('wordList');
  const favoritesOnlyCheckbox = document.getElementById('favoritesOnly');
  const sortOrderRadios = document.querySelectorAll('input[name="sortOrder"]');
  const partOfSpeechFilter = document.getElementById('partOfSpeechFilter');
  const dateFilter = document.getElementById('dateFilter'); // Добавлено

  async function fetchWords() {
    const token = await getToken();

    if (!token) {
      wordList.innerHTML = '<p>Не удалось получить токен доступа. Пожалуйста, авторизуйтесь заново.</p>';
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/user/my-words', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Ошибка при выполнении запроса: ' + response.statusText);
      }

      const words = await response.json();
      if (!Array.isArray(words)) {
        throw new Error('Некорректный формат данных');
      }
      renderWords(words);
    } catch (error) {
      wordList.innerHTML = `<p>Произошла ошибка: ${error.message}</p>`;
    }
  }

  function renderWords(words) {
    const favoritesOnly = favoritesOnlyCheckbox.checked;
    const sortOrder = document.querySelector('input[name="sortOrder"]:checked').value;
    const partOfSpeech = partOfSpeechFilter.value;
    const selectedDate = dateFilter.value; // Добавлено

    let filteredWords = words
      .filter(word => !favoritesOnly || word.is_favorite)
      .filter(word => !partOfSpeech || word.part_of_speech === partOfSpeech)
      .filter(word => !selectedDate || new Date(word.added_at).toISOString().split('T')[0] === selectedDate); // Добавлено

    if (sortOrder === 'time') {
      filteredWords = filteredWords.sort((a, b) => new Date(b.added_at) - new Date(a.added_at));
    } else if (sortOrder === 'alphabet') {
      filteredWords = filteredWords.sort((a, b) => a.word.localeCompare(b.word));
    }

    wordList.innerHTML = '';

    filteredWords.forEach(word => {
      const wordItem = document.createElement('div');
      wordItem.className = `word-item${word.is_favorite ? ' favorite' : ''}`;

      wordItem.innerHTML = `
        <div class="word">${word.word}</div>
        <div class="translation">${word.translation}</div>
        <div class="part-of-speech">${word.part_of_speech}</div>
        <button class="edit-btn" data-id="${word.word_id}">Изменить перевод</button>
      `;

      wordList.appendChild(wordItem);
    });

    document.querySelectorAll('.edit-btn').forEach(button => {
      button.addEventListener('click', event => {
        const wordId = event.target.getAttribute('data-id');
        const newTranslation = prompt('Введите новый перевод:');
        const newPos = prompt('Введите новую часть речи:');
        if (newTranslation && newPos) {
          updateWord(wordId, newTranslation, newPos);
        }
      });
    });
  }

  async function updateWord(wordId, translation, pos) {
    const token = await getToken();

    if (!token) {
      alert('Не удалось получить токен доступа. Пожалуйста, авторизуйтесь заново.');
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/user/set-custom-translation', {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ word_id: wordId, translation, pos })
      });

      if (!response.ok) {
        throw new Error('Ошибка при выполнении запроса: ' + response.statusText);
      }

      fetchWords();
    } catch (error) {
      alert(`Произошла ошибка: ${error.message}`);
    }
  }

  async function getToken() {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage({ type: "getToken" }, (response) => {
        if (response.token) {
          resolve(response.token);
        } else {
          reject(new Error('Не удалось получить токен'));
        }
      });
    });
  }

  favoritesOnlyCheckbox.addEventListener('change', fetchWords);
  sortOrderRadios.forEach(radio => radio.addEventListener('change', fetchWords));
  partOfSpeechFilter.addEventListener('change', fetchWords);
  dateFilter.addEventListener('change', fetchWords); // Добавлено

  fetchWords();
});
