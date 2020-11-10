<script>
    import List from "../components/inventory/List.svelte";
    import SampleExcelUpload from "../components/inventory/SampleExcelUpload.svelte";


    let sample;
    let sample_id;
    let ref;
    let samples = [];
    let initialized = false;

    async function initSample() {
        const response = await fetch(`clinical/initsample/${sample_id.toUpperCase()}`);
        sample = await response;
        if (response.ok) {
            initialized = true;
            sample_id = '';
            ref.focus();
        } else {
            let response_message = await response.json();
            alert(response_message.message);
            initialized = false;
        }
    }

    async function getAllSamples() {
        const formData = new FormData();
        formData.append('status', 0);
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
        <label class="block text-gray-700 text-sm font-bold mb-2" for="fyr_id">
            Scan a FYR Collection Tube:
        </label>
        <input class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
               id="fyr_id" type="text" placeholder="FYR id"
               bind:value={sample_id}
               on:change={initSample}
               bind:this={ref}>
    </div>
</div>
<input type="text" id="test"/>


<div class="flex items-center justify-evenly bg-grey-lighter print:hidden">
    {#if sample}
        <div class="mb-8">
            {#if initialized }
                <div class="bg-blue-100 border-t border-b border-blue-500 text-blue-700 px-4 py-3" role="alert">
                    <p class="font-bold">Initialized a new Tube</p>
                    <p class="text-sm"></p>
                </div>
                <!--                <label class="block text-gray-700 text-sm font-bold mb-2" for="provider">-->
                <!--                    Continue without secondary verification:-->
                <!--                </label>-->
                <!--                <input class="shadow appearance-none border rounded py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"-->
                <!--                       id="verification" type="radio" bind:value={verification}>-->
                <!--                <label class="block text-gray-700 text-sm font-bold mb-2" for="primary_id">-->
                <!--                    Verified with another ID:-->
                <!--                </label>-->
                <!--                <input class="shadow appearance-none border rounded py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"-->
                <!--                       id="verification" type="radio" bind:value={verification}>-->
                <!--                <label class="block text-gray-700 text-sm font-bold mb-2" for="primary_id">-->
                <!--                    Verification failed:-->
                <!--                </label>-->
                <!--                <input class="shadow appearance-none border rounded py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"-->
                <!--                       id="verification" type="radio" bind:value={verification}>-->
            {/if}
        </div>
    {/if}
</div>

<List samples={samples}/>

<SampleExcelUpload/>

