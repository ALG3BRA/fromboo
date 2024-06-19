document.addEventListener('DOMContentLoaded', function () {
  var sendButton = document.getElementById('sendButton_1');

  sendButton.addEventListener('click', function () {
    var name = document.getElementById('name_1').value;
    var email = document.getElementById('email_1').value;
    var password = document.getElementById('password_1').value;
    var data = {
      name: name,
      email: email,
      password: password
    };

    fetch('http://127.0.0.1:8000/user/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Ошибка при отправке запроса: ' + response.status);
      }
      return response.json();
    })
    .then(data => {
      console.log('Ответ от сервера:', data);
    })
    .catch(error => {
      errorMessage_1.textContent = 'Ошибка: ' + error.message; // Выводим сообщение об ошибке в элемент errorMessage
    });
  });
});

// Аутентификация
document.addEventListener('DOMContentLoaded', function () {
  var sendButton = document.getElementById('sendButton_2');

  sendButton.addEventListener('click', function () {
    var email_2 = document.getElementById('email_2').value;
    var password_2 = document.getElementById('password_2').value;

    const data = new URLSearchParams();
    data.append('grant_type', '');
    data.append('username', email_2);
    data.append('password', password_2);
    data.append('scope', '');
    data.append('client_id', '');
    data.append('client_secret', '');

    const options = {
    method: 'POST',
    headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
    'accept': 'application/json'
    },
    body: data
    };
    fetch('http://127.0.0.1:8000/login/token', options)
    .then(response => {
      if (!response.ok) {
        throw new Error('Ошибка при отправке запроса: ' + response.status);
      }
      return response.json();
    })
    .then(data => {
      chrome.runtime.sendMessage({ type: "popupData", data: data });
    })
    .catch(error => {
      errorMessage_2.textContent = 'Ошибка: ' + error.message; // Выводим сообщение об ошибке в элемент errorMessage
    });
  });
});

