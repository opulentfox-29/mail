var xhr = new XMLHttpRequest();
var api_url = "/api/";
url = window.location.href.split('/').slice(-2, -1)[0]

main = {}

if (url === 'folders') {
    buttons = document.getElementById('buttons');
    buttons.innerHTML = `
    <button class="btn btn-primary" type="button" id="btn_create_folder" onclick="create_folder()">create folder</button>
    <button class="btn btn-primary" type="button" id="btn_refresh" onclick="refresh()">refresh</button>
    `
    refresh()
}
if (url === 'login') {
    btn_login.onclick = login
}

function _request (data) {
    if (data['url'] === 'login') {
        if (data['status'] === 'err'){
            var err = document.getElementById('err-text');
            err.textContent = data['err'];
        }
        if (data['status'] === 'redirect') {
            window.location.replace("http://127.0.0.1:8000/folders/");
        }
    }
    if (data['url'] === 'folders') {
        var folders = data['data']
        main['folders'] = folders
        set_folders(folders)
    }
    if (data['url'] === 'messages') {
        if (data['status'] === 'read_message') {
            var scroll = document.getElementById('scroll');
            scroll.innerHTML = data['message'];
        }
    }

}


function _send (url, method, dict=null) {
    var body = document.getElementsByTagName('body')[0];
    body.style.pointerEvents = 'none';
    xhr.open(method, url, false);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            json = JSON.parse(xhr.responseText);
        }
    };
    var data = JSON.stringify(dict);
    xhr.send(data);
    body.style.pointerEvents = '';
    _request(json)
    return json;
}

function post (dict=null) {
    return _send(api_url, "POST", dict)
}

function get (data=null) {
    var url = api_url;
    if (data) {
        var url = api_url + "?data=" + encodeURIComponent(JSON.stringify(data));
    }

    return _send(api_url, "GET")
}

function login () {
    var login = document.getElementById('login').value;
    var password = document.getElementById('password').value;
    var duck_name = document.getElementById('duck_name').value;

    post({
        url: 'login',
        login: login,
        password: password,
        duck_name: duck_name,
    });

}

function refresh() {
    get({
        'url': 'folders',
        'status': 'refresh'
    });
}

function set_folders (folders=null) {
    if (folders !== null) {
        main['folders'] = folders;
    }
    var folders = main['folders'];
    var scroll = document.getElementById('scroll');
    scroll.innerHTML = null;

    buttons = document.getElementById('buttons');
    buttons.innerHTML = `
        <button class="btn btn-primary" type="button" id="btn_create_folder" onclick="create_folder()">create folder</button>
        <button class="btn btn-primary" type="button" id="btn_refresh" onclick="refresh()">refresh</button>
    `

    for (folder_num in folders) {
        var folder = folders[folder_num]
        if (folder['invisible_folder']) {continue;}
        if (folder['unread']) {var unread = 'btn-primary';} else {var unread = 'btn-secondary';}
        let code = `
        <div class="d-grid mb-1">
            <button class="btn ${unread} folders" onclick="redirect_to_message(${folder_num});" "type="button">
                ${folder['folder_name']} • ${folder['str_time']}
            </button>
        </div>
        `
        scroll.innerHTML = code + scroll.innerHTML;
    }
}

function redirect_to_message(folder_num=null) {
    if (folder_num !== null) {
        main['folder_num'] = folder_num;
    }
    var folders = main['folders']
    folder_num = main['folder_num'];
    var folder = folders[folder_num];
    main['folder'] = folder;
    messages = folder['messages'];
    main['messages'] = messages

    buttons = document.getElementById('buttons');
    buttons.innerHTML = `
        <button class="btn btn-primary" type="button" onclick="set_folders()">Back</button>
        <button class="btn btn-primary" type="button" id="btn_rename_folder" onclick="rename_folder()">rename folder</button>
        <button class="btn btn-primary" type="button" id="btn_del_folder" onclick="delete_folder()">delete folder</button>
        <button class="btn btn-primary" type="button" id="btn_send_message" onclick="send_message()">send message</button>
        <input class="form-control" type="text" value="TO: ${folder['sender']}" disabled readonly>
    `

    var scroll = document.getElementById('scroll');
    scroll.innerHTML = null;

    for (message_num in messages) {
        var message = messages[message_num]
        if (message['unread']) {var unread = 'btn-primary';} else {var unread = 'btn-secondary';}
        if (message['i_sender']) {var symbol = '⮬';} else {var symbol = ' ';}
        let code = `
        <div class="d-grid mb-1">
            <button class="btn ${unread} folders" onclick="read_message(${message_num});" "type="button">
                ${symbol} ${message['subject']} • ${message['str_time']}
            </button>
        </div>
        `
        scroll.innerHTML = scroll.innerHTML + code;
    }
}

function read_message(message_num) {
    var messages = main['messages']
    message = messages[message_num]
    main['message'] = message;

    buttons = document.getElementById('buttons');
    buttons.innerHTML = `
        <button class="btn btn-primary" type="button" onclick="redirect_to_message()">Back</button>
        <button class="btn btn-primary" type="button" id="btn_delete_message" onclick="delete_message()">delete message</button>
        <input class="form-control" type="text" value="FROM: ${message['sender_address']}" disabled readonly>
    `
    var scroll = document.getElementById('scroll');
    scroll.innerHTML = null;

    post({
        'url': 'messages',
        'status': 'read_message',
        'id': message['id'],
    });
}

function create_folder() {
    var modal = document.getElementById('modal');
    if (modal) {
        modal.remove();
    }
    else {
        var body = document.getElementsByTagName('body')[0];
        body.innerHTML = `
            <div class="modal-content rounded-4 shadow" id="modal">
              <div class="modal-header border-bottom-0">
                <h1 class="modal-title fs-5">Create folder</h1>
                <button type="button" class="btn-close" data-bs-dismiss="modal" onclick="document.getElementById('modal').remove();"></button>
              </div>
              <div class="modal-body py-0">
                <div class="form-outline form-white mb-4">
                    <input id="folder_name" class="form-control form-control-lg"/>
                    <label class="form-label" for="folder_name">folder name</label>
                </div>
                <div class="form-outline form-white mb-4">
                    <input id="description" class="form-control form-control-lg"/>
                    <label class="form-label" for="description">description</label>
                </div>
              </div>
              <div class="modal-footer flex-column border-top-0">
                <button type="button" class="btn btn-lg btn-primary w-100 mx-0 mb-2" onclick="create_folder_ok()">ok</button>
                <button type="button" class="btn btn-lg btn-light w-100 mx-0" onclick="document.getElementById('modal').remove();"
                    data-bs-dismiss="modal">cancel</button>
              </div>
            </div>
        ` + body.innerHTML
    }
}

function create_folder_ok() {
    var modal = document.getElementById('modal');
    var folder_name = document.getElementById('folder_name').value;
    var description = document.getElementById('description').value;

    post({
        'url': 'folders',
        'status': 'create folder',
        'folder_name': folder_name,
        'description': description,
    });
    modal.remove();
}

function rename_folder() {
    var modal = document.getElementById('modal');
    if (modal) {
        modal.remove();
    }
    else {
        var body = document.getElementsByTagName('body')[0];
        body.innerHTML = `
            <div class="modal-content rounded-4 shadow" id="modal">
              <div class="modal-header border-bottom-0">
                <h1 class="modal-title fs-5">Rename folder</h1>
                <button type="button" class="btn-close" data-bs-dismiss="modal" onclick="document.getElementById('modal').remove();"></button>
              </div>
              <div class="modal-body py-0">
                <div class="form-outline form-white mb-4">
                    <input id="folder_name" class="form-control form-control-lg"/>
                    <label class="form-label" for="folder_name">new name</label>
                </div>
                <div class="form-outline form-white mb-4">
                    <input id="description" class="form-control form-control-lg"/>
                    <label class="form-label" for="description">description</label>
                </div>
              </div>
              <div class="modal-footer flex-column border-top-0">
                <button type="button" class="btn btn-lg btn-primary w-100 mx-0 mb-2" onclick="rename_folder_ok()">ok</button>
                <button type="button" class="btn btn-lg btn-light w-100 mx-0" onclick="document.getElementById('modal').remove();"
                    data-bs-dismiss="modal">cancel</button>
              </div>
            </div>
        ` + body.innerHTML
    }
}

function rename_folder_ok() {
    var modal = document.getElementById('modal');
    var folder_name = document.getElementById('folder_name').value;
    var description = document.getElementById('description').value;
    var folder = main['folder']

    post({
        'url': 'folders',
        'status': 'rename folder',
        'folder': folder,
        'folder_name': folder_name,
        'description': description,
    });
    modal.remove();
}

function delete_folder() {
    var modal = document.getElementById('modal');
    if (modal) {
        modal.remove();
    }
    else {
        var body = document.getElementsByTagName('body')[0];
        body.innerHTML = `
            <div class="modal-content rounded-4 shadow" id="modal">
              <div class="modal-header border-bottom-0">
                <h1 class="modal-title fs-5">delete folder</h1>
                <button type="button" class="btn-close" data-bs-dismiss="modal" onclick="document.getElementById('modal').remove();"></button>
              </div>
              <div class="modal-body py-0">
              </div>
              <div class="modal-footer flex-column border-top-0">
                <button type="button" class="btn btn-lg btn-primary w-100 mx-0 mb-2" onclick="delete_folder_ok()">ok</button>
                <button type="button" class="btn btn-lg btn-light w-100 mx-0" onclick="document.getElementById('modal').remove();"
                    data-bs-dismiss="modal">cancel</button>
              </div>
            </div>
        ` + body.innerHTML
    }
}

function delete_folder_ok() {
    var modal = document.getElementById('modal');
    var folder = main['folder']

    post({
        'url': 'folders',
        'status': 'delete folder',
        'folder': folder,
    });
    modal.remove();
}

function send_message() {
    var modal = document.getElementById('modal');
    if (modal) {
        modal.remove();
    }
    else {
        var body = document.getElementsByTagName('body')[0];
        body.innerHTML = `
            <div class="modal-content rounded-4 shadow" id="modal">
              <div class="modal-header border-bottom-0">
                <h1 class="modal-title fs-5">Send message</h1>
                <button type="button" class="btn-close" data-bs-dismiss="modal" onclick="document.getElementById('modal').remove();"></button>
              </div>
              <div class="modal-body py-0">
                <div class="form-outline form-white mb-4">
                    <input id="address" class="form-control form-control-lg"/>
                    <label class="form-label" for="address">address</label>
                </div>
                <div class="form-outline form-white mb-4">
                    <input id="subject" class="form-control form-control-lg"/>
                    <label class="form-label" for="subject">subject</label>
                </div>
                <div class="form-outline form-white mb-4">
                    <input id="message" class="form-control form-control-lg"/>
                    <label class="form-label" for="message">message</label>
                </div>
              </div>
              <div class="modal-footer flex-column border-top-0">
                <button type="button" class="btn btn-lg btn-primary w-100 mx-0 mb-2" onclick="send_message_ok()">ok</button>
                <button type="button" class="btn btn-lg btn-light w-100 mx-0" onclick="document.getElementById('modal').remove();"
                    data-bs-dismiss="modal">cancel</button>
              </div>
            </div>
        ` + body.innerHTML
    }
}

function send_message_ok() {
    var modal = document.getElementById('modal');
    var address = document.getElementById('address').value;
    var subject = document.getElementById('subject').value;
    var message = document.getElementById('message').value;
    var folder = main['folder'];

    post({
        'url': 'folders',
        'status': 'send message',
        'folder': folder,
        'address': address,
        'subject': subject,
        'message': message,
    });
    modal.remove();
}

function delete_message() {
    var modal = document.getElementById('modal');
    if (modal) {
        modal.remove();
    }
    else {
        var body = document.getElementsByTagName('body')[0];
        body.innerHTML = `
            <div class="modal-content rounded-4 shadow" id="modal">
              <div class="modal-header border-bottom-0">
                <h1 class="modal-title fs-5">delete message</h1>
                <button type="button" class="btn-close" data-bs-dismiss="modal" onclick="document.getElementById('modal').remove();"></button>
              </div>
              <div class="modal-body py-0">
              </div>
              <div class="modal-footer flex-column border-top-0">
                <button type="button" class="btn btn-lg btn-primary w-100 mx-0 mb-2" onclick="delete_message_ok()">ok</button>
                <button type="button" class="btn btn-lg btn-light w-100 mx-0" onclick="document.getElementById('modal').remove();"
                    data-bs-dismiss="modal">cancel</button>
              </div>
            </div>
        ` + body.innerHTML
    }
}

function delete_message_ok() {
    var modal = document.getElementById('modal');
    var message = main['message']

    post({
        'url': 'read message',
        'status': 'delete message',
        'id': message['id'],
    });
    modal.remove();
}
