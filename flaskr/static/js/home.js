// Example of authors after being built:
// [
//   {
//     name: 'AA',
//     sets: [ { author: "AA", date: "20200305", index: "c", name: "20200305b_AA", version: "2.22"}, ...], 
//   }, ... 
// ]
const authors = [];


// The startup options
function initPage() {
    sortSetsByAuth();
    attachAuthOpts();
    initialValidation();
}

// Builds the 'authors' global variable from the data that we have received from Flask.
// See example of 'authors' at it's declaration above.
function sortSetsByAuth() {
    datasetOpts.forEach((set) => {
        const props = splitName(set.name)
        const merged = { ...set, ...props }

        foundAuth = authors.find(auth => auth.name === merged.author)
        foundAuth ? foundAuth.sets.push(merged) : authors.push({name: merged.author, sets: [merged]})
    })
    authors.sort((a, b) => (a.author > b.author) ? 1 : -1)
}


// Builds options for dropdown list of all available initials. -> AA, JH, BB
// Creates list for 'select', then copies the elements to 'calendar-select'
function attachAuthOpts() {
    const authorOptionsList = document.getElementById("author-selection");
    authors.forEach((auth, key, map) => {
        const newOpt = document.createElement("OPTION");
        newOpt.setAttribute("value", auth.name)
        newOpt.innerHTML = auth.name;
        authorOptionsList.appendChild(newOpt);
    })

    // Copy all the drop down options to our other drop down selector
    const calAuthorOptsLists = document.getElementById("cal-author-selection")
    calAuthorOptsLists.innerHTML = authorOptionsList.innerHTML;
}


// Verifies that the value parameter represents an actual dataset.
function validateSelection(value) {
    const initials = value.slice(-2);
    const authorSets = authors.find(author => author.name === initials).sets;
    const verified = authorSets.find((set) => set.name === value);
    if (verified) {
        return true;
    } else {
        console.log(`${value} was not an option received from the server!`);
        return false;
    }
}


// Initializes a flatpickr calendar with appropriate whitelisted dates and onChange function.
// It only shows dates that the selected person prepared experiments on and the default date
// is their most recent experiment. The initialization of the "a/b/c" dropdown list is triggered
// based on the autofilled most recent experiment.
function updateCalendar(initials) {
    fpOpts = {
        dateFormat: "Ymd", // YYYYMMDD - same as our file naming scheme.
        onChange: (selectedDates, dateStr, instance) => attachIndexOpts(dateStr)
    }
    if (initials === "") {
        // A function to disable all dates.
        fpOpts.disable = [date => true]; 
    } else {
        const authorSets = authors.find((author => author.name === initials)).sets;
        const dates = authorSets.map(set => set.date);

        dates.sort((a, b) => (a > b) ? 1 : -1);
        const mostRecentDate = dates[dates.length - 1];
        fpOpts.enable = dates;
        fpOpts.defaultDate = mostRecentDate;
        attachIndexOpts(mostRecentDate)
    }
    flatpickr("#flatpickr", fpOpts);
}


// Builds the drop down list of available dates for a given pair of initials.
// This is for the 'select' option, not Calendar.
function attachDateOpts(initials) {
    let dateOptsList = document.getElementById("date-selection");

    if (dateOptsList) {
        // Clear all options from the dropdown list
        dateOptsList.innerHTML = "";
    } else {
        // Create the dropdown list element to contain the options.
        dateOptsList = document.createElement("SELECT")
        dateOptsList.setAttribute("id", "date-selection");
        dateOptsList.classList.add("selection")
        dateOptsList.setAttribute("oninput", "updateExpPreview(this)")
        document.getElementById("dropdowncontainer").appendChild(dateOptsList); 
    }

    // Create the dropdown list with dates only from the given initials.
    authorSets = authors.find((author) => author.name === initials).sets;
    authorSets.sort((a, b) => (a.name < b.name) ? 1 : -1)

    authorSets.forEach(set => appendOptionElem(set, "fullDate", dateOptsList))
    updateExpPreview(dateOptsList[0]);
}


// Same as above, but for experiment indices: a, b, c, etc. Used after calendar date selection.
// Very similar to above. Could likely combine them, but there are enough parameters that it may affect readability.
function attachIndexOpts(dateStr) {
    let calIndexList = document.getElementById("cal-index-selection");

    if (calIndexList) {
        // Clear all options from the dropdown list
        calIndexList.innerHTML = "";
    } else {
        // Create the dropdown list element to contain the options.
        calIndexList = document.createElement("SELECT")
        calIndexList.setAttribute("id", "cal-index-selection");
        calIndexList.classList.add("selection")
        calIndexList.setAttribute("oninput", "updateExpPreview(this)")
        document.getElementById("flatpickr-container").appendChild(calIndexList); 
    }

    const authorInits = document.getElementById("cal-author-selection").value
    const author = authors.find(auth => auth.name === authorInits)
    const opts = author.sets.filter(set => set.date === dateStr);
    opts.sort((a, b) => (a.index < b.index) ? 1 : -1)

    // Create the dropdown list with indices only from the given initials and date.
    opts.forEach(set => appendOptionElem(set, "index", calIndexList))
    updateExpPreview(calIndexList[0]);
}


// This creates an OPTION element using the 'displayText' property from 'set'
// and appends it to listElem (should be the parent SELECT element);
// Just to shorten up the two similar functions above...
function appendOptionElem(set, displayText, listElem) {
    const opt = document.createElement("OPTION");
    opt.setAttribute("value", set.name);
    opt.innerHTML = set[displayText];
    listElem.appendChild(opt);
}


// Displays the actual name of the experiment that will be requested if the 
// user clicks the submit button. (Or a message indicating file upload)
function updateExpPreview(elem) {
    const container = elem.closest(".input-tile");
    const input = container.querySelector(".selection");
    let previewText = "";

    if (input.value && validateSelection(input.value)) {
        previewText = `Selected: ${input.value}`;
    } else if (input.value) {
        previewText = "Invalid Selection";
    } else {
        previewText = "No Selection";
    }

    const preview = container.querySelector(".selected-experiment-preview");
    preview.innerHTML = `<b>${previewText}</b>`;
}


// Styles the file input backgrounds to reflect whether the filename matches what we expect.
function validateFile(elem, expected) {
    // Can't apply psuedo elements to inputs so we need the parent element
    const parent = elem.parentElement;
    const files = elem.files;

    if (files && files[0]) {
        // Gets the file name without the extension.
        const name = files[0].name.substring(0, files[0].name.lastIndexOf('.')).toLowerCase();
        
        if (name.endsWith(expected)) {
            remClass(parent, "invalidinput");
            addClass(parent, "validinput");
        } else {
            remClass(parent, "validinput");
            addClass(parent, "invalidinput");
        }
    } else {
        remClass(parent, ["validinput", "invalidinput"]);
    }
}


// Used to validate inputs on page load (useful when the inputs have been saved from a previous visit)
function initialValidation() {
    const info = document.getElementById("infofile");
    const rfu = document.getElementById("rfufile");
    validateFile(info, "info");
    validateFile(rfu, "rfu");
}

function goToInput(elem) {
    const input = elem.closest(".input-tile").querySelector(".selection");
    if (input && input.value) {
        window.location.href = inputURL + input.value;
    }
}

function deleteSelection(elem) {
    const input = elem.closest(".input-tile").querySelector(".selection");
    if (input && input.value) {
        fetch(deleteURL + input.value, {
            method: 'delete'
        }).then(function(response) {
            location.reload();
        })
    }
}