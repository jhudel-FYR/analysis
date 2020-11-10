<script>
    import List from "../components/inventory/List.svelte";


    let rack;
    let position = 1;
    let sample_id;
    let plate = [];
    let disabled = true;
    let ref;
    let focusing = false;
    let samples = [];
    let status = 3;


    if (rack !== undefined) {
        disabled = false;
    }

    async function editSample() {
        ref.blur();
        let formData = new FormData();
        formData.append('rack_id', rack);
        formData.append('rack_position', position);
        let response = await fetch(`clinical/assignrack/${sample_id}`, {
            method: 'POST',
            body: formData
        });
        if (response.status === 400) {
            let text = await response.json();
            alert(text.message)
        } else if (response.status === 200) {
            position += 1;
            plate.push({'position': position, 'sample': sample_id});
            plate = plate;
        }
        ref.focus();
    }

    async function getAllSamples() {
        const formData = new FormData();
        $: formData.append('status', status);
        const response = await fetch(`clinical/samples`, {
            method: 'POST',
            body: formData
        });
        samples = await response.json();
        if (response.ok) {
        } else {
        }
    }

    function refresh() {
        getAllSamples()
    }

    refresh();

</script>

<div class="flex items-center justify-evenly bg-grey-lighter print:hidden">
    <div class="mb-4">
        <label class="block text-gray-700 text-sm font-bold mb-2" for="rack">
            Scan a Rack:
        </label>
        <input class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
               id="rack" type="text" placeholder='Rack-0' bind:value={rack} required>
    </div>

    <div class="mb-4">
        <label class="block text-gray-700 text-sm font-bold mb-2" for="rack">
            Scan the Tube to place in position {position}:
        </label>
        <input class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
               id="sample_id" type="text" placeholder="fyr id" bind:value={sample_id} bind:this={ref}
               on:change={editSample} {disabled}>
    </div>
</div>
<input type="text" id="test"/>

<div class="flex items-center justify-evenly bg-grey-lighter print:hidden">
    <div class="block text-gray-700 text-sm font-bold mb-2">
        {#each plate as entry}
            <div class="flex md:justify-center">
                <p>S{entry.position}: {entry.sample}</p>
            </div>
        {/each}
    </div>
</div>

<div class="mb-2">
    <label class="block text-gray-700 text-sm font-bold mb-2" for="status">View Initialized
        Experiments:</label>
    <div class="form-switch inline-block align-middle">
        <div class="shadow appearance-none border rounded switch-toggle switch-3 switch-candy">
            <input id="yes" name="status" value="3" type="radio" checked="checked" bind:group={status}/>
            <label for="yes" onclick="">Yes</label>
            <input id="no" name="status" value="4" type="radio" checked="" bind:group={status}/>
            <label for="no" onclick="">No</label>
        </div>
    </div>
</div>

<List samples={samples}/>

<style>

    .switch-toggle {
        float: left;
        background: #f9fefa;
    }

    .switch-toggle input {
        position: absolute;
        opacity: 0;
    }

    .switch-toggle input + label {
        padding: 7px;
        float: left;
        color: #2d98eb;
        cursor: pointer;
    }

    .switch-toggle input:checked + label {
        color: #050403;
        background: #2d98eb;
    }
</style>