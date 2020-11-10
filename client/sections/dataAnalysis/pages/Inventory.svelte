<script>
    import {getStatus} from "../../clinicaltools"
    import {getReport} from "../../clinicaltools"
    import SampleItem from "../components/inventory/SampleItem.svelte";
    import {onMount} from 'svelte'
    import List from "../components/inventory/List.svelte";
    import SampleExcelUpload from "../components/inventory/SampleExcelUpload.svelte";


    let sample_list;
    let sample;
    let sample_id;
    let provider;
    let primary_id;
    let secondary_id;
    let sample_status = 0;
    let new_status;
    let rack_id;
    let rack_position;
    let ref;
    let samples = [];

    async function startExperiment() {
        const response = await fetch(`clinical/startexperiment/${sample.rack_id}`, {
            method: 'POST',
        });
        if (response.status === 200) {
            // TODO: download maestro templates here
            return
        }
    }

    async function editSample() {
        let formData = new FormData();
        // TODO: can this be a loop?
        if (provider !== undefined) {
            formData.append('provider_id', provider);
        }
        if (primary_id !== undefined) {
            formData.append('sample_id1', primary_id);
        }
        if (secondary_id !== undefined) {
            formData.append('sample_id2', secondary_id);
        }
        if (new_status !== sample_status) {
            formData.append('status', new_status);
        }
        if (rack_id !== undefined) {
            formData.append('rack_id', rack_id);
        }
        if (rack_position !== undefined) {
            formData.append('rack_position', rack_position);
        }
        let response = await fetch(`clinical/sample/${sample.fyr_id}`, {
            method: 'POST',
            body: formData
        });
        if (response.status === 200) {
            alert('Sample information updated!');
            ref.focus();
            getSample()
        }
    }

    async function getSample() {
        const response = await fetch(`clinical/sample/${sample_id.toUpperCase()}`);
        sample = await response.json();
        if (response.ok) {
            sample_status = sample.status;
            new_status = sample.status;
            sample_id = '';
            ref.focus();
        } else {
            alert(sample.message);
            sample = undefined;
        }
    }

    async function getAllSamples() {
        const response = await fetch(`clinical/samples`);
        $: samples = await response.json();
        if (response.ok) {
        } else {
        }
    }

    function filterSamples(variable) {

    }

    function refresh() {
        ref.focus();
        getAllSamples()
    }

    onMount(() => {
        refresh()
    })

</script>


<div class="flex items-center justify-evenly bg-grey-lighter print:hidden">
    <div class="mb-4">
        <label class="block text-gray-700 text-sm font-bold mb-2" for="fyr_id">
            Scan a FYR Collection Tube:
        </label>
        <input class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
               id="fyr_id" type="text" placeholder="FYR id"
               bind:value={sample_id}
               on:change={getSample}
               bind:this={ref}>
    </div>
    <div class="flex mb-4">
        {#if sample}
            <SampleItem sample={sample}/>
        {/if}
    </div>
</div>
        <input type="text" id="test"/>


<div class="flex items-center justify-evenly bg-grey-lighter print:hidden">
    {#if sample}
        <div class="mb-8">
            {#if sample.status === 0}
                <div class="bg-blue-100 border-t border-b border-blue-500 text-blue-700 px-4 py-3" role="alert">
                    <p class="font-bold">Registered a new Tube</p>
                    <p class="text-sm"></p>
                </div>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="provider">
                    Add a Provider:
                </label>
                <input class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                       id="provider" type="text" placeholder="provider" bind:value={provider}>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="primary_id">
                    Add Patient IDs:
                </label>
                <input class="shadow appearance-none border rounded py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                       id="primary_id" type="text" placeholder="primary id" bind:value={primary_id}>
                <input class="shadow appearance-none border rounded py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                       id="secondary_id" type="text" placeholder="secondary id" bind:value={secondary_id}>
            {:else if sample.status === 1}
                <div class="bg-blue-100 border-t border-b border-blue-500 text-blue-700 px-4 py-3" role="alert">
                    <p class="font-bold">Patient IDs have been assigned</p>
                    <p class="text-sm">Sample is still checked out</p>
                </div>
            {:else if sample.status === 2}
                <div class="bg-blue-100 border-t border-b border-blue-500 text-blue-700 px-4 py-3" role="alert">
                    <p class="font-bold">Sample was checked in!</p>
                    <p class="text-sm">To begin a new Rack Assignment, please go to the associated tab.</p>
                </div>
                <label class="block text-gray-700 text-sm font-bold mb-2" for="rack_id">
                    Manually select the Rack ID:
                </label>
                <select class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                        id="rack_id" bind:value={rack_id}>
                    {#each {length: 10} as _, i}
                        <option value={i}>{ i }</option>
                    {/each}
                </select>

                <label class="block text-gray-700 text-sm font-bold mb-2" for="rack_position">
                    Manually select the Rack Position:
                </label>
                <select class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                        id="rack_position" bind:value={rack_position}>
                    {#each {length: 90} as _, i}
                        <option value={i+1}>{i+1}</option>
                    {/each}
                </select>

            {:else if sample.status === 3}
                <div class="bg-blue-100 border-t border-b border-blue-500 text-blue-700 px-4 py-3" role="alert">
                    <p class="font-bold"> Sample is assigned to Rack: {sample.rack_id} and
                        Position: {sample.rack_position}.</p>
                    <p class="text-sm"></p>
                </div>
<!--                <form on:submit|preventDefault={startExperiment}>-->
<!--                    <button class="bg-transparent hover:bg-blue-500 text-blue-700 font-semibold hover:text-white py-2 px-4 border border-blue-500 hover:border-transparent rounded">-->
<!--                        Initiate an Experiment?-->
<!--                    </button>-->
<!--                </form>-->
            {:else if sample.status === 4}
            <div class="bg-blue-100 border-t border-b border-blue-500 text-blue-700 px-4 py-3" role="alert">
                    <p class="font-bold"> An experiment has been initiated</p>
                    <p class="text-sm">Sample is in Rack: {sample.rack_id}</p>
                </div>
            {:else if sample.status === 5}
            <div class="bg-blue-100 border-t border-b border-blue-500 text-blue-700 px-4 py-3" role="alert">
                    <p class="font-bold">This sample was tested as part of experiment {sample.dataset_id}</p>
                    <p class="text-sm">Results: {getReport(sample.report)}</p>
                </div>
            {:else }

            {/if}
            <label class="block text-gray-700 text-sm font-bold mb-2" for="status">
                To edit the status (for corrections only):
            </label>
            <select class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                    id="status" bind:value={new_status}>
                {#each {length: 6} as _, i}
                    <option name={i} value={i}>{i}: {getStatus(i)}</option>
                {/each}
            </select>
            <form on:submit|preventDefault={editSample}>
                <button class="flex bg-transparent hover:bg-blue-500 text-blue-700 font-semibold hover:text-white py-2 px-4 border border-blue-500 hover:border-transparent rounded"
                        type="submit">
                    Submit Changes
                </button>
            </form>
        </div>
    {/if}
</div>

<List samples={samples}/>

<SampleExcelUpload/>

