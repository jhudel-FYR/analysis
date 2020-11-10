

function addOne(type) {
    switch (type) {
        case 'component' :
            // TODO: validate if component was already added
            if ($(`#quantitytemplate`).val() > 0) {
                display(inputs=['typetemplate', 'nametemplate', 'quantitytemplate', 'unittemplate'],
                output='component');
            }
            break;
    }
}

let componentcount = 1;

function display(inputs, output) {
    let inputfield = document.createElement("input");
    inputfield.name = output + getCounter(output);
    inputfield.style.visibility = 'hidden';

    let outputvalue = document.createElement("a");
    outputvalue.id = output + getCounter(output);
    for (var i = 0; i < inputs.length; i++) {
        let entry = document.getElementById(inputs[i]);
        let value = entry.value;
        if (entry.checked) {
            value += ' bidirectional';
        } else if (i > 0) {
            value = ' ' + entry.value;
        }

        outputvalue.innerText += value;
        inputfield.value += value;
    }

    outputvalue.innerHTML += '<br>';
    let displayedoutput = document.getElementById(output);
    displayedoutput.appendChild(outputvalue);
    displayedoutput.appendChild(inputfield);

    switch (output) {
        case 'component': componentcount += 1; break;
    }
}

function deleteOne(output) {
    document.getElementById(output + (getCounter(output)-1)).remove();
    switch (output) {
        case 'component': componentcount -= 1; break;
    }
}

function getCounter(table) {
    switch (table) {
        case 'component': return componentcount;
    }
}

let swaps = [];
let errors = [];
let customGroups = [];
let defaultGroups;
let groupSelector;
let swapEditor;
let useDefaultGroups = true;
let gIndex = 0;
let riv;

let plate = 'normal';
let plateCols = 12;
let plateRows = 'ABCDEFGH';


// el represents a well in the table
function currentHeaderOf(el) {
    const i = Array.prototype.indexOf.call(el.parentNode.children, el);
    const l = [];
    const n = [];
    for (let i = 0; i < plateRows.length; i++) {
        l.push(plateRows[i])
    }
    for (let i = 1; i < plateCols + 1; i ++) {
        if (i < 10) {
            n.push('0'+String(i))
        }
        else {
            n.push(String(i))
        }
    }
    return `${l[Math.floor(i / plateCols)]}${n[i % plateCols]}`;
}

function setupSwapEditor(editor) {

    // update panel to reflect any previous swaps (if tab as been changed)
    swaps.forEach(swap => {
        const n1 = editor.querySelector(`[data-header="${swap[0]}"]`);
        const n2 = editor.querySelector(`[data-header="${swap[1]}"]`);
        swapNodes(n1, n2);
        const s1 = editor.querySelector(`[data-header="${swap[0]}"]`);
        const s2 = editor.querySelector(`[data-header="${swap[1]}"]`);
        [s1, s2].forEach((item) => {
            if (item.dataset.header !== currentHeaderOf(item)) {
                item.classList.add("swapped-well")
            } else {
                item.classList.remove("swapped-well")
            }
        })
        
    });

    swapEditor = new Sortable(editor, {
        swap: true,
        swapClass: "highlighted-well",
        chosenClass: "selected",
        animation: 150,
        onEnd: function(evt) {
            if (evt.oldIndex === evt.newIndex) {
                return;
            }
            const rows = [];
            for (let i = 0; i < plateRows.length; i++) {
                rows.push(plateRows[i])
            }
            function indexToCoords(i) {
                const row = rows[Math.floor(i / plateCols)];
                const col = i % plateCols + 1;
                let douleDigit = ("0" + col).slice(-2); // Ensure 2 digits
                return row + douleDigit;
            }
            const swapCoords = [indexToCoords(evt.oldIndex), indexToCoords(evt.newIndex)]
            swaps.push(swapCoords);

            // This is the essentially the same as the function defined at the top of 
            // setupSwapEditor but there are scoping issues calling it from here.
            [evt.swapItem, evt.item].forEach((item, i) => {
                if (item.dataset.header !== swapCoords[i]) {
                    item.classList.add("swapped-well")
                } else {
                    item.classList.remove("swapped-well")
                }
            });
            rebuildInfoPanel("swaps")
        }
    });
    return swapEditor;
}

function toggleError(wellEl) {
    wellEl.classList.toggle("marked-error");
    const excelHeader = wellEl.getAttribute("data-header");
    let errIndex = errors.indexOf(excelHeader);
    if (errIndex >= 0) {
        errors.splice(errIndex, 1);
    } else {
        errors.push(excelHeader)
    }
}

function setupErrorEditor(plateEditor) {
    const wells = plateEditor.querySelectorAll('.well');
    
    wells.forEach((well) => {
        well.setAttribute("onclick", "toggleError(this); rebuildInfoPanel('errors')");
        let isMarkedError = errors.find(coords => coords === well.dataset.header);
        if (isMarkedError) {
            well.classList.add("marked-error")
        }
    });
}

function setupGroupEditor(type) {
    let selectedCSS;

    switch (type) {
        case "group":
            selectedCSS = "selected";
            break;
        case "replicate":
            selectedCSS = "selected-triangle";
            break;
    }

    groupSelector = Selection.create({
        // Class for the selection-area
        class: 'selection',
        // All elements in this container can be selected
        selectables: [`#plate-editor > .selectable-well`],
        // The container is also the boundary in this case
        boundaries: [`#plate-editor`]
    }).on('start', ({inst, selected, oe}) => {
        // Remove class if the user isn't pressing the control key or ⌘ key
        if (!oe.ctrlKey && !oe.metaKey) {
            // Unselect all elements
            for (const el of selected) {
                el.classList.remove('selected', 'selected-triangle');
                inst.removeFromSelection(el);
            }
            // Clear previous selection
            inst.clearSelection();
        }
    }).on('move', ({changed: {removed, added}}) => {
        // Add a custom class to the elements that where selected.
        for (const el of added) {
            el.classList.add(selectedCSS);
        }
        // Remove the class from elements that where removed
        // since the last selection
        for (const el of removed) {
            el.classList.remove('selected', 'selected-triangle');
        }
    }).on('stop', ({inst}) => {
        // Remember selection in case the user wants to add smth in the next one
        inst.keepSelection();
    });
    groupSelector.disable();
}


function wellIsInReplicate(group, cell) {
    return group.replicates.find((replicate) => replicate.wells.find(well => well.excelheader === cell));
}

function wellIsGrouped(cell) {
    return customGroups.find((group) => group.wells.find(well => well.excelheader === cell));
}

// Plate editor is built from scratch to match each div to a corresponding well ID
function buildPlateTemplate() {
    const editorTemplate = document.createElement("div");
    editorTemplate.id = "plate-editor";
    if (plate === 'large-plate'){
        editorTemplate.style.gridTemplateColumns = 'repeat(24, 1fr)';
    }
    for (let i = 0; i < plateRows.length; i ++){
        let row = plateRows[i];
        for (let col = 1; col < plateCols + 1; col ++) {
            if (col < 10) {
                col = '0'+String(col);
            }
            const wellTemplate = document.createElement("div");
            wellTemplate.classList.add("well");
            wellTemplate.classList.add(plate);
            const header = `${row + col}`;
            const well = wells.find(well => well.excelheader === header);
            if (well) {
                wellTemplate.setAttribute('data-id', well._id);
                if (useDefaultGroups === false && !wellIsGrouped(well.excelheader)) {
                    wellTemplate.classList.add("well", "selectable-well");
                }
            } else {
                wellTemplate.classList.add('empty-well');
            }
            wellTemplate.setAttribute('data-header', header);
            wellTemplate.innerHTML = `<p>${header}</p>${ well ? '<div class="sm-well-triangle"></div>' : '' }`;
            editorTemplate.append(wellTemplate);
        }
    }
    return editorTemplate;
}



function attachSummaryInfo(cpanel) {
    cpanel = cpanel || document.getElementById("tmp-cpanel-summary").content.cloneNode(true);
    attachSwapInfo(cpanel);
    attachErrorInfo(cpanel);
    attachGroupInfo(cpanel);
    return cpanel;
}

function attachSwapInfo(cpanel) {
    cpanel = cpanel || document.getElementById("tmp-cpanel-swapper").content.cloneNode(true);
    const swapContainer = cpanel.getElementById("swapped-wells-summary");
    if (swaps.length > 0) {
        swaps.forEach((swapPair) =>{
            const swapRow = document.getElementById("tmp-swap-row").content.cloneNode(true);
            swapRow.querySelector(".swap-left").appendChild(document.createTextNode(swapPair[0]));
            swapRow.querySelector(".swap-right").appendChild(document.createTextNode(swapPair[1]));
            swapContainer.appendChild(swapRow);
        })
    } else {
        swapContainer.appendChild(document.createTextNode("No swaps!"))
    }
    return cpanel;
}

function attachErrorInfo(cpanel) {
    cpanel = cpanel || document.getElementById("tmp-cpanel-errors").content.cloneNode(true);
    const errorContainer = cpanel.getElementById("error-wells-summary");
    if (errors.length > 0) {
        errors.forEach((errorWell) =>{
            const errorRow = document.getElementById("tmp-error-row").content.cloneNode(true);
            errorRow.querySelector(".error-row").appendChild(document.createTextNode(errorWell));
            errorContainer.appendChild(errorRow);
        })
    } else {
        errorContainer.appendChild(document.createTextNode("No Errors!"))
    }
    return cpanel;
}

function setWellColor(well, tag) {
    const wellDiv = document.querySelector(`[data-header='${well.excelheader}']`);
    if (wellDiv) {
        const tri = wellDiv.querySelector(".sm-well-triangle");
        tri.classList.add(tag);
    }
}
 
function renderReplicateSummaryRow(replicate, rIdx, group, container, gIdx) {
    const repRow = document.getElementById("tmp-rep-row-summary").content.cloneNode(true);

    repRow.querySelector(".rep-label").innerHTML = replicate.label;
    repRow.querySelector(".rep-designation").innerHTML = replicate.designation;
    const row = repRow.querySelector(".gr-row-grid");
    row.setAttribute('data-rep', `${gIdx}-${rIdx}`)
    row.setAttribute('onmouseover', `highlight('rep', '${gIdx}-${rIdx}')`);
    row.setAttribute('onmouseout', `removeHighlight('rep', '${gIdx}-${rIdx}')`);

    container.appendChild(repRow);
    const triangles = container.querySelectorAll(".triangle");
    triangles[triangles.length- 1].classList.add(`rep-${rIdx+1}`);
    replicate.wells.forEach(well => setWellColor(well, `rep-well-tri-${rIdx+1}`));
}

function renderEditReplicateRow(replicate, rIdx, group, container, gIdx) {
    const repRow = document.getElementById("tmp-rep-row-editable").content.cloneNode(true);

    const ig = customGroups.findIndex((g) => g.id === group.id);
    const ir = group.replicates.findIndex(r => r.id === replicate.id);

    const input = repRow.querySelector(".gr-name-input");
    const desi = repRow.querySelector(".gr-designation");
    const delBtn = repRow.querySelector(".rep-row-btn");

    const row = repRow.querySelector(".gr-row-grid");
    row.setAttribute('data-rep', `${gIdx}-${rIdx}`)
    row.setAttribute('onmouseover', `highlight('rep', '${gIdx}-${rIdx}')`);
    row.setAttribute('onmouseout', `removeHighlight('rep', '${gIdx}-${rIdx}')`);

    input.setAttribute("rv-value", `customGroups.${ig}.replicates.${ir}.label`);
    desi.setAttribute("rv-value", `customGroups.${ig}.replicates.${ir}.designation`);
    delBtn.setAttribute("onclick", `removeReplicate(${group.id}, ${replicate.id})`);
    rivets.bind(input, { customGroups: customGroups });
    rivets.bind(desi, { customGroups: customGroups });


    container.appendChild(repRow);

    const triangles = container.querySelectorAll(".triangle");
    triangles[triangles.length - 1].classList.add(`rep-${rIdx+1}`);

    replicate.wells.forEach(well => setWellColor(well, `rep-well-tri-${rIdx+1}`));
    if (group.replicates.length === rIdx + 1 && hasWellsAvailable(group)) {
        renderPlusOneRow(rIdx + 1, container, group.id);
    }
}

function renderPlusOneRow(i, container, gId) {
    const rowTmp = document.getElementById("tmp-rep-row-summary").content.cloneNode(true);

    const row = rowTmp.querySelector(".gr-row-grid");
    row.classList.add("no-select", "pointer");
    row.setAttribute("onclick", `startSelection('replicate', ${gId})`);
    row.querySelector(".rep-designation").innerHTML = "Add Replicate <img src='/static/images/icons/plus-square-fyr-action.svg' alt='Add Replicate' class='rep-row-btn'/>";
    container.appendChild(row);
    const triangles = container.querySelectorAll(".triangle");
    triangles[triangles.length - 1].classList.add(`rep-${i+1}`);
}

function setGroupSelectables(gId) {
    const group = customGroups.find(group => group.id === gId);
    document.querySelectorAll(".selectable-well").forEach(node => node.classList.remove("selectable-well"));
    const selectors = group.wells.map(well => `[data-header="${well.excelheader}"]`).join(', ');
    const groupWells = Array.from(document.querySelectorAll(selectors));
    const availWells = groupWells.filter((node) => {
        return !group.replicates.find((replicate) => {
            return replicate.wells.find(well => well.excelheader === node.dataset.header)
        })
    });
    availWells.forEach(node => {
        node.classList.add("selectable-well");
        node.classList.remove(gId)
    })
}

function startSelection(type, gId) {
    const confBtn = document.getElementById("confirm-select-btn");
    toggleEditorFocus();

    switch (type) {
        case "group":
            confBtn.setAttribute("onclick", "confirmGroupSelection()");
            setupGroupEditor(type);
            setMessage("Drag to select new group from available cells. Hold ctrl (cmd on mac) to add to selection.");
            break;
        case "replicate":
            setGroupSelectables(gId);
            confBtn.setAttribute("onclick", `confirmReplicateSelection(${gId})`);
            setupGroupEditor(type);
            setMessage("Drag to select replicate within group. Hold ctrl (cmd on mac) to add to selection.", `gr-${gId}`);
            break;
    }
    groupSelector.enable();
}

function confirmGroupSelection() {
    const wellNodes = groupSelector.getSelection();
    let gId;
    if (wellNodes && wellNodes.length > 0) {
        gId = ++gIndex;
        const wells = wellNodes.map(node =>  { return { excelheader: node.dataset.header }} );
        const newGroup = { id: gId, wells, replicates: [], repCnt: 0 };
        customGroups.push(newGroup);
        document.getElementById("group-editor-btn").click();
    } 
    groupSelector.destroy();
    groupSelector = null;
    updateView();
    if (wellNodes && wellNodes.length > 0) {
        startSelection("replicate", gId)
    }
}


function updateView() {
    document.getElementById("group-editor-btn").click();
    toggleEditorFocus();
    clearMessage();
}

function confirmReplicateSelection(groupId) {
    const wellNodes = groupSelector.getSelection();
    const group = customGroups.find(group => group.id === groupId);
    if (wellNodes && wellNodes.length > 0) {
        const wells = wellNodes.map(node =>  { return { excelheader: node.dataset.header }} );
        const newReplicate = {
            id: ++group.repCnt,
            wells,
            label: "",
            designation: "UNK"
        };
        group.replicates.push(newReplicate);
    }
    groupSelector.destroy()
    groupSelector = null;
    updateView();
    if (wellNodes && wellNodes.length > 0 && hasWellsAvailable(group)) {
        startSelection("replicate", groupId)
    }
}

function buildLabelDiv(grNum, isBtn=false) {
    const labelDivFragment = document.getElementById("tmp-group-row-summary").content.cloneNode(true);
    const labelDiv = labelDivFragment.querySelector('.gr-number');
    if (!useDefaultGroups) {
        labelDiv.innerHTML = `${grNum} <img class='gr-rem-btn' src='/static/images/icons/x-fyr-warning.svg' onclick='removeGroup(${grNum})'/>`;
    } else {
        labelDiv.innerHTML = grNum;
    }

    if (isBtn) {
        labelDiv.classList.add('gr-add-btn');
        labelDiv.setAttribute('onclick', 'startSelection("group")');
        labelDiv.innerHTML = "<img src='/static/images/icons/plus-white.svg' alt='Add Group' />";
    }
    labelDiv.classList.add(`gr-${grNum}`);
    labelDiv.setAttribute('data-grp', `${grNum}`)
    labelDiv.setAttribute('onmouseover', `highlight('grp', '${grNum}')`);
    labelDiv.setAttribute('onmouseout', `removeHighlight('grp', '${grNum}')`);
    return labelDiv;
}

function hasWellsAvailable(group) {
    return group.wells.find(well => !wellIsInReplicate(group, well.excelheader))
}

function isSummaryView() {
    return document.getElementById("editor-summary-btn").classList.contains("active-editor");
}

function renderGroupSummary(group, i, container, editMode=false) {
    const grid = document.createElement("div");
    grid.classList.add("gr-grid");
    const grNum = i + 1;
    const labelDiv = buildLabelDiv(grNum);
    grid.appendChild(labelDiv);
    container.appendChild(grid);
    
    const renderRow = !useDefaultGroups && editMode ? renderEditReplicateRow : renderReplicateSummaryRow;
    if (group !== "+") {
        group.replicates.forEach((replicate, rIdx) => {
            renderRow(replicate, rIdx, group, grid, i + 1)
        })
        if (group.replicates.length === 0 && !isSummaryView() && hasWellsAvailable(group)) {
            renderPlusOneRow(1, grid, group.id);
        }
    }
}

function renderAddGrBtn(container, grCnt) {
    const grid = document.createElement("div");
    grid.classList.add("gr-grid", "no-select");
    const grNum = grCnt + 1;
    const labelDiv = buildLabelDiv(grNum, true);
    labelDiv.classList.add("pointer");
    grid.appendChild(labelDiv);
    container.appendChild(grid);
}

// Used for plate editor Summary view only
function attachGroupInfo(cpanel) {
    cpanel = cpanel || document.getElementById("tmp-cpanel-groups").content.cloneNode(true);
    const groupsContainer = cpanel.getElementById("groups-summary");
    const groups = useDefaultGroups === true ? defaultGroups : customGroups;
    groups.forEach((group, i) => renderGroupSummary(group, i, groupsContainer));
    return cpanel;
}


// Used for editing groups (but not on summary view)
function attachGroupEditor() {
    const cpanel = document.getElementById("tmp-cpanel-groups").content.cloneNode(true);
    const groupsContainer = cpanel.getElementById("cpanel-groups");
    const groups = useDefaultGroups ? defaultGroups : customGroups;
    groups.forEach((group, i) => renderGroupSummary(group, i, groupsContainer, true));

    if (!useDefaultGroups && wellsAvailableToGroup()) {
        // attach the +1 group btn
        renderAddGrBtn(groupsContainer, groups.length);
    }
    return cpanel;
}

function insertAfter(newNode, referenceNode) {
    referenceNode.parentNode.insertBefore(newNode, referenceNode.nextSibling);
}

function colorPlate() {
    const allTags = ["gr-1", "gr-2", "gr-3", "gr-4", "gr-5", "gr-6", "gr-7", "gr-8", "gr-9", "gr-10", "gr-11", "gr-12", "gr-13", "gr-14", "gr-15", "gr-16", "gr-17", "gr-18", "gr-19", "gr-20", "gr-21", "gr-22", "gr-23", "gr-24", "gr-25", "gr-26", "gr-27", "gr-28", "gr-29", "gr-30", "gr-31", "gr-32", "gr-33", "gr-34", "gr-35", "gr-36"];
    const groups = useDefaultGroups ? defaultGroups : customGroups;

    groups.forEach((group, i) => {
        const gIdx = i + 1;
        const tag = `gr-${gIdx}`;

        group.wells.forEach(well => {
            const wellDiv = document.querySelector(`[data-header="${well.excelheader}"]`);
            wellDiv.classList.remove(...allTags, "selectable-well");
            wellDiv.classList.add(tag);

            wellDiv.setAttribute('data-grp', `${gIdx}`);
            wellDiv.setAttribute('onmouseover', `highlight('grp', '${gIdx}')`);
            wellDiv.setAttribute('onmouseout', `removeHighlight('grp', '${gIdx}')`);
        });

        group.replicates.forEach(((replicate, rIdx) => {
            replicate.wells.forEach(well => {
                const wellDiv = document.querySelector(`[data-header="${well.excelheader}"]`);

                wellDiv.setAttribute('data-rep', `${gIdx}-${rIdx}`);
                wellDiv.setAttribute('onmouseover', `highlight('rep', '${gIdx}-${rIdx}');`);
                wellDiv.setAttribute('onmouseout', `removeHighlight('rep', '${gIdx}-${rIdx}');`);
            })
        }))
    })
}

// Remove info panel and rebuild from scratch
function rebuildInfoPanel(type) {
    const oldPanel = document.querySelector(".summary-details");
    oldPanel.parentNode.removeChild(oldPanel);

    let cpanel;

    switch (type) {
        case "summary":
            cpanel = attachSummaryInfo();
            colorPlate();
            break;

        case "groups":
            cpanel = attachGroupEditor();
            colorPlate();
            break;

        case "swaps":
            cpanel = attachSwapInfo();
            break;

        case "errors":
            cpanel = attachErrorInfo();
            break;
    }
    const container = document.getElementById('plate-editor-container');
    container.appendChild(cpanel);
    if (type === "groups") {
        setActiveButton(useDefaultGroups === true ? "gr-sel-def-btn" : "gr-sel-cus-btn", "groups")
    }
}

function plateEditorSetup(type) {
    type = type instanceof Event ? "summary" : type;
    const editor = buildPlateTemplate(type);
    const container = document.getElementById('plate-editor-container');
    let cpanel;

    switch (type) {
        case "summary":
            container.appendChild(editor);
            cpanel = attachSummaryInfo();
            break;

        case "groups":
            container.appendChild(editor);
            cpanel = attachGroupEditor();
            break;

        case "swaps":
            setupSwapEditor(editor);
            container.appendChild(editor);
            cpanel = attachSwapInfo();
            break;

        case "errors":
            setupErrorEditor(editor);
            container.appendChild(editor);
            cpanel = attachErrorInfo();
            break;
    }

    container.appendChild(cpanel);
    if (type === "summary" || type === "groups") {
        colorPlate()
    }
    if (type === "groups") {
        setActiveButton(useDefaultGroups === true ? "gr-sel-def-btn" : "gr-sel-cus-btn", "groups")
    }
}

function setActiveButton(activeId, groupTag) {
    const btn = document.getElementById(activeId);
    if (!btn) {
        return
    }

    const btnGroup = document.querySelectorAll(groupTag);
    btnGroup.forEach(btn => btn.classList.remove("active-editor"));
    btn.classList.add("active-editor");
}

function removeActiveEditor() {
    if (groupSelector) {
        groupSelector.disable();
    }
    let editor = document.getElementById("plate-editor");
    editor.parentNode.removeChild(editor);
    let panel = document.querySelector(".summary-details");
    panel.parentNode.removeChild(panel);
}


// reduces data we transmit back to the server to just the necessary properties.
function reduceGroups(groups) {
    const reduced = groups.map((group) => {
        return {
            wells: group.wells.map(well => well.excelheader),
            replicates: group.replicates.map(repl => {
                return {
                    label: repl.label,
                    designation: repl.designation,
                    wells: repl.wells.map(well => well.excelheader)
                }
            })
        }
    });
    return reduced;
}


// Ensures that all wells have been added to a group and a replicate
function isSubmittable(groups) {
    let submittable = true;
    wells.forEach(well => {
        const grp = groups.find(group => {
            return group.wells.some(grWell => grWell.excelheader === well.excelheader)
        });
        if (!grp || !wellIsInReplicate(grp, well.excelheader)) {
            submittable = false;
        }
    });
    return submittable;
}

// Executes on form submit
function prepareSubmission(e) {
    const data = {
        swaps: swaps,
        errors: errors,
        groups: null
    };
    // TODO: edit this to allow for multiple templates
    let plate_template = document.getElementById("COVID default");
    if (!useDefaultGroups){
        if (isSubmittable(customGroups) || plate_template.checked ) {
            data.groups = reduceGroups(customGroups);
            const inputEl = document.getElementById("json");
            inputEl.value = encodeURIComponent(JSON.stringify(data));
        } else {
            // Stop form from submitting
            e.preventDefault();
        }
    }
}

function changeEditor(activeBtnTag, type) {
    setActiveButton(activeBtnTag, ".editor-selectors");
    removeActiveEditor();
    plateEditorSetup(type)
}

function groupBy(data, key) {
  return data.reduce(function(storage, item) {
    let group = item[key];
    storage[group] = storage[group] || [];
    storage[group].push(item);
    return storage; 
  }, {});
}

function resetSwaps() {
    swaps = [];
    changeEditor(null, "swaps")
}

function resetErrors() {
    errors = [];
    changeEditor(null, "errors")
}

function checkPlateSize() {
    lastWell = (wells[Object.keys(wells)[Object.keys(wells).length - 1]]);
    let row = lastWell.excelheader.split('')[0];
    let col = parseFloat(lastWell.excelheader.split('')[1] + lastWell.excelheader.split('')[2]);
    if (row in ['I', 'J', 'K', 'L', 'M', 'N', 'O', 'P'] || col > 12) {
        plate = 'large-plate';
        plateCols = 24;
        plateRows = 'ABCDEFGHIJKLMNOP';
    }
}

function setup() {
    checkPlateSize();

    let grouped = groupBy(wells, 'group');
    const sorted = Object.entries(grouped).sort((a,b) => a[0].group - b[0].group);
    sorted.forEach(group => {
        let replicates = groupBy(group[1], 'replicate_id');
        group.push(Object.entries(replicates));
    });
    defaultGroups = Object.freeze(sorted.map(group => {
        return {
            id: group[0],
            wells: group[1],
            replicates: group[2].map(replicate => { 
                return { 
                    id: replicate[0],
                    wells: replicate[1],
                    label: replicate[1][0].label,
                    designation: replicate[1][0].designation || "UNK" }
                })
        }
    }));
    plateEditorSetup("summary");
    rivets.configure({
        // Attribute prefix in templates
        prefix: 'rv',
        // Preload templates with initial data on bind
        preloadData: true,
        // Root sightglass interface for keypaths
        rootInterface: '.',
        // Template delimiters for text bindings
        templateDelimiters: ['{', '}'],
        // Augment the event handler of the on-* binder
        handler: function(target, event, binding) {
          this.call(target, event, binding.view.models)
        }
      });
}

function useDefault() {
    useDefaultGroups = true;
    changeEditor(null, "groups")
}

function useCustom() {
    useDefaultGroups = false;
    changeEditor(null, "groups")
}

function resetAll() {
    swaps = [];
    errors = [];
    useDefault = true;
    changeEditor(null, "summary")
}

function addGroup() {
    const row = document.getElementById("tmp-group-row").content.cloneNode(true);
    const rowCont = document.getElementById("cpanel-groups");
    rowCont.appendChild(row);
}

function toggleEditorFocus() {
    const focus = document.getElementById("focus");
    focus.classList.toggle("enable-focus");
    focus.classList.toggle("hidden");

    const btns = document.getElementById("selection-confirmation");
    if (focus.classList.contains("enable-focus")) {
        btns.classList.remove("hidden");
    } else {
        btns.classList.add("hidden");
    }
}

function setMessage(msg, grSelector) {
    const msgHolder = document.getElementById("message");
    msgHolder.innerHTML = msg;
    if (grSelector) {
        const el = document.querySelector(`.${grSelector}`)
        const color = document.defaultView.getComputedStyle(el,null)["background-color"]
        const colorPreview = document.getElementById("msg-color");
        colorPreview.style.backgroundColor = color;
        colorPreview.classList.remove("hidden")
    }
}

function clearMessage() {
    const div = document.getElementById("message");
    div.innerHTML = "";
    const colorPreview = document.getElementById("msg-color");
    colorPreview.style.backgroundColor = "";
    colorPreview.classList.add("hidden");
}

function cancelSelection() {
    groupSelector.disable();
    groupSelector.clearSelection();
    toggleEditorFocus();
    clearMessage();
    // refresh the screen
    document.getElementById("gr-sel-cus-btn").click();
}

function removeReplicate(groupId, repId) {
    const ig = customGroups.findIndex((g) => g.id === groupId);
    const ir = customGroups[ig].replicates.findIndex(r => r.id === repId);

    customGroups[ig].replicates.splice(ir, 1);
    document.getElementById("gr-sel-cus-btn").click();
}

function removeGroup(groupId) {
    const ig = customGroups.findIndex((g) => g.id === groupId);
    customGroups.splice(ig, 1);
    document.getElementById("gr-sel-cus-btn").click();
}

/**
 * Returns the index of an element within its parent for a selected set of elements
 */
function index(el, selector) {
	let index = 0;

	if (!el || !el.parentNode) {
		return -1;
	}

	/* jshint boss:true */
	while (el === el.previousElementSibling) {
		if ((el.nodeName.toUpperCase() !== 'TEMPLATE') && el !== Sortable.clone && (!selector || matches(el, selector))) {
			index++;
		}
	}

	return index;
}

function swapNodes(n1, n2) {
	let p1 = n1.parentNode,
		p2 = n2.parentNode,
		i1, i2;

	if (!p1 || !p2 || p1.isEqualNode(n2) || p2.isEqualNode(n1)) return;

	i1 = index(n1);
	i2 = index(n2);

	if (p1.isEqualNode(p2) && i1 < i2) {
		i2++;
	}
	p1.insertBefore(n2, p1.children[i1]);
	p2.insertBefore(n1, p2.children[i2]);
}

function removeHighlight(prop, idx) {
    const elements = document.querySelectorAll(`[data-${prop}='${idx}']`);
    elements.forEach(el => el.classList.remove("highlight"));
}

function highlight(prop, idx) {
    if (groupSelector) {
        return;
    }
    const elements = document.querySelectorAll(`[data-${prop}='${idx}']`);
    elements.forEach(el => el.classList.add("highlight"));
}

function wellsAvailableToGroup() {
    if (customGroups.length === 0) {
        return true;
    } 

    const groupedWells = customGroups.reduce((groupedHeaders, group) => {
        const thisGroupHeaders = group.wells.map(well => well.excelheader);
        return groupedHeaders.concat(thisGroupHeaders)
    }, []);
    const difference = wells.filter(well => !groupedWells.includes(well.excelheader));
    if (difference.length > 0) {
        return true;
    }

    return false;
}

window.onload = setup;