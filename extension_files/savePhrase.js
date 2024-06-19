async function refreshToken(url) {
    var requestOptions = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include' // for cookie
    };

    try {
        const response = await fetch(url, requestOptions);
        if (!response.ok) {
            throw new Error('Ошибка при выполнении запроса: ' + response.statusText);
        }
        const data = await response.json();
        console.log('Ответ сервера:', data);
        tokenStorage.setToken(data.access_token, data.exp);
    } catch (error) {
        console.error('Произошла ошибка:', error.message);
    }
}

function createTokenStorage() {
    let token = null;
    let exp = null;

    function setToken(newToken, expiresAt) {
        token = newToken;
        exp = new Date(expiresAt + "Z");
    }

    function getToken() {
        return token;
    }

    function isTokenExpired() {
        return new Date() > exp;
    }

    return {
        setToken,
        getToken,
        isTokenExpired
    };
}

const tokenStorage = createTokenStorage();

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'popupData') {
        console.log('Данные из popup.js:', message.data);
        tokenStorage.setToken(message.data.access_token, message.data.exp);
    } else if (message.type === 'getToken') {
        sendResponse({ token: tokenStorage.getToken() });
        return true; // Указываем, что ответ будет отправлен асинхронно
    }
});

async function postData(url = '') {
    let accessToken = tokenStorage.getToken();

    console.log("old_tok: " + accessToken);

    if (tokenStorage.isTokenExpired()) {
        console.log("Токен истек, обновляем...");
        await refreshToken('http://127.0.0.1:8000/login/refresh');
        accessToken = tokenStorage.getToken();
    }

    console.log("new_tok: " + accessToken);

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + accessToken,
        },
    });

    if (!response.ok) {
        throw new Error('Ошибка при выполнении запроса: ' + response.statusText);
    }

    return response.json();
}

function savePhrase(object) {
    console.log('Привет от JavaScript!');
    const phrase = object.selectionText;
    console.log(phrase);
    postData(`http://127.0.0.1:8000/user/save-phrase?word=${encodeURIComponent(phrase)}`);
}

chrome.contextMenus.create({
    id: "savePhrase2",
    title: "Сохранить текст",
    contexts: ["selection"]
});

chrome.contextMenus.onClicked.addListener(savePhrase);
