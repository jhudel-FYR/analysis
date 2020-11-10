function goTo(location) {
    window.location.href = "/%s".replace('%s', location)
}

function remClass(elem, names) {
    if (Array.isArray(names)) {
        names.forEach((name) => elem.classList.remove(name))
    } else {
        elem.classList.remove(names);
    }
}

function addClass(elem, names) {
    if (Array.isArray(names)) {
        names.forEach((name) => elem.classList.add(name))
    } else {
        elem.classList.add(names);
    }
}

// Dissects a name string into it's useful parts.
function splitName(name) {
    const tmp = name.split("_");

    const author = tmp[tmp.length - 1];                         // "AA" or "TB" etc...
    const fullDate = tmp[0];                                    // "20200505a"
    const date = fullDate.substring(0, fullDate.length - 1);    // "20200505"
    const index = fullDate[fullDate.length - 1];                // "a"
    return { author, fullDate, date, index }
}

// Prevents subsequent link click events from firing
function disableLink(link) {
    link.onclick = function(event) {
        event.preventDefault();
    }
}

function disableButton(btn, msg) {
    btn.disabled = true;
    remClass(btn, ["action", "warning"]);
    addClass(btn, "disabled");
    btn.innerHTML = msg;
}

function enableButton(btn, msg, btnType) {
    btn.disabled = false;
    remClass(btn, "disabled");
    addClass(btn, btnType || "action");
    btn.innerHTML = msg;
}