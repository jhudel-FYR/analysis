<script>
    import List from "../components/inventory/List.svelte";

    let zip;
    let result;
    let dataset_id;
    let files;
    let submitting = false;
    let disabled = false;
    let samples = [];

    async function uploadResults() {
        disabled = true;
        const formData = new FormData();
        formData.append('files', files[0]);
        dataset_id = files[0].name.substring(0, 9);
        const response = await fetch('inventory/upload', {
            method: 'POST',
            body: formData
        });
        if (response.status === 200) {
            fetchZip();
        }
    }

    async function fetchZip() {
        const response = await fetch(`inventory/download/${dataset_id}`);
        if (response.status === 200) {
            submitting = true;
            zip = response.json();
        }
    }

    async function getAllSamples() {
        const formData = new FormData();
        formData.append('status', 5);
        const response = await fetch(`inventory/samples`, {
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


<div class="flex items-center justify-evenly bg-grey-lighter">
    <label class="w-64 flex flex-col items-center px-4 py-6 bg-white text-gray-800 rounded-lg shadow-lg tracking-wide uppercase border border-gray-800 cursor-pointer hover:bg-gray-800 hover:text-white">
        <svg class="w-8 h-8" fill="currentColor" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
            <path d="M16.88 9.1A4 4 0 0 1 16 17H5a5 5 0 0 1-1-9.9V7a3 3 0 0 1 4.52-2.59A4.98 4.98 0 0 1 17 8c0 .38-.04.74-.12 1.1zM11 11h3l-4-4-4 4h3v3h2v-3z"/>
        </svg>
        {#if files }
            {files[0].name}
        {:else }
            <span class="mt-2 text-base leading-normal">Select INFO File</span>
        {/if}
        <input type='file' class="hidden" bind:files/>
    </label>

    <label class="w-64 flex flex-col items-center px-4 py-6 bg-white text-gray-800 rounded-lg shadow-lg tracking-wide uppercase border border-gray-800 cursor-pointer hover:bg-green-800 hover:text-white">
        <svg viewBox="0 0 20 20" fill="currentColor" class="arrow-circle-right w-6 h-6">
            <path fill-rule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z"
                  clip-rule="evenodd"></path>
        </svg>
        <span class="mt-2 text-base leading-normal">Get Results!</span>
        <input type='button' class="hidden" on:click={uploadResults} {disabled}/>
    </label>

    {#if submitting}
        {#await zip}
            <p>...processing</p>
        {:then zipfile}
            <a href="{zipfile}" download>
                <button class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded inline-flex items-center">
                    <svg class="fill-current w-4 h-4 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                        <path d="M13 8V2H7v6H2l8 8 8-8h-5zM0 18h20v2H0v-2z"/>
                    </svg>
                    <span>Download</span>
                </button>
            </a>
        {/await}
    {/if}

</div>

<List samples={samples}/>
