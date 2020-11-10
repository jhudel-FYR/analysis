
function disableUpdateLink(link) {
        btn = link.firstChild;
        disableButton(btn, "Updating Graphs...");
        disableLink(link);
    }

// This downloads the zip immediately in the background and provides a
// save dialogue to the user after the download is complete.
// It displays % of download complete, though this may not be interesting
// given 1MB-ish zips on modern connections.
function downloadZip(btn, downloadURL) {
    originalBtnText = btn.innerHTML;
    const xhr = new XMLHttpRequest();
    const formData = new FormData(document.getElementById("graphs-form")); 

    xhr.open("POST", downloadURL);
    xhr.responseType = 'blob';
    xhr.onprogress = function(e) {
        const pct = (e.loaded / e.total) * 100;
        btn.innerHTML = `${pct}% Complete`;
    }
    xhr.onload = function(e){ 
        if (this.status == 200) {
            // Create a hidden link element pointing to our response blob (could be skipped but allows us to name the file)
            let blob = new Blob([this.response], {type: 'application/zip'});
            let a = document.createElement("a");
            a.style = "display: none";
            document.body.appendChild(a);

            // Create a DOMString representing the blob and point the link element towards it
            let url = window.URL.createObjectURL(blob);
            a.href = url;
            a.download = `${id}.zip`;  // filename

            // Programatically click the link to trigger the download
            a.click();
            // Release the reference to the file by revoking the Object URL
            window.URL.revokeObjectURL(url);

            enableButton(btn, originalBtnText);
        } else {
            enableButton(btn, `Failure code: ${this.status} | Try Again?`, "warning");
        }
    }; 
    xhr.send(formData);

    disableButton(btn, "Starting Download...")
}

function disableAndDownloadSimple(btn, e, downloadURL) {
    // Stop the default form submission behavior (btn also represents an event)
    e.preventDefault()

    originalAction = btn.form.action;
    originalBtnText = btn.value;

    // Change the form action and submit.
    btn.form.action = downloadURL;
    btn.form.submit();
    btn.disabled = true;
    btn.value = "Starting Download...";

    // Set form and button back to normal. (Download button will be re-enabled after 15 seconds)
    btn.form.action = originalAction;
    setTimeout(function() {
        console.log('hello', btn.value)
        btn.disabled = false;
        btn.value = originalBtnText;
    }, 15000)
}
