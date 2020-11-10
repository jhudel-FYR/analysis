<script>
    import List from "../components/inventory/List.svelte";
    import SampleItem from "../components/inventory/SampleItem.svelte";

    let sample;
    let sample_id;
    let ref;
    let samples = [];
    let success = false;
    let verification;


    async function getSample() {
        const response = await fetch(`clinical/sample/${sample_id.toUpperCase()}`);
        sample = await response.json();
        if (response.ok) {
            if (sample.status !== 1) {
                alert('This sample does not have valid patient information. Please edit in the Inventory Tab if this is incorrect.');
                sample = undefined;
            }
            ref.focus();
        } else {
            alert(sample.message);
            sample = undefined;
        }
    }


    async function checkInSample() {
        const formData = new FormData();
        formData.append('verification', verification);
        const response = await fetch(`clinical/checkinsample/${sample_id.toUpperCase()}`, {
            method: 'POST',
            body: formData
        });
        if (response.ok) {
            success = true;
            sample_id = '';
            ref.focus();
        } else {
            let response_message = await response.json();
            alert(response_message.message);
            success = false;
        }
    }

    async function getAllSamples() {
        const formData = new FormData();
        formData.append('status', 1);
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
            {#if sample }
                <form on:submit|preventDefault={checkInSample}>
                    <div class="block">
                        <label class="text-gray-700 text-sm font-bold mb-2" for="provider">
                            Continue without secondary verification:
                        </label>
                        <input type="radio" class="form-radio" name="verification" value="verified"
                               bind:group={verification}>
                    </div>
                    <div class="block">
                        <label class="text-gray-700 text-sm font-bold mb-2" for="primary_id">
                            Verified with another ID:s
                        </label>
                        <input type="radio" class="form-radio" name="verification" value="overridden"
                               bind:group={verification}>
                    </div>
                    <div class="block">
                        <label class="text-gray-700 text-sm font-bold mb-2" for="primary_id">
                            Verification failed:
                        </label>
                        <input type="radio" class="form-radio" name="verification" value="mismatch"
                               bind:group={verification}>
                    </div>
                    <button class="bg-transparent hover:bg-blue-500 text-blue-700 font-semibold hover:text-white py-2 px-4 border border-blue-500 hover:border-transparent rounded">
                        Submit
                    </button>
                </form>
            {/if}
            {#if success}
                <div class="bg-blue-100 border-t border-b border-blue-500 text-blue-700 px-4 py-3" role="alert">
                    <p class="font-bold">Sample is checked in!</p>
                    <p class="text-sm"></p>
                </div>
            {/if}
        </div>
    {/if}
</div>

<List samples={samples}/>
