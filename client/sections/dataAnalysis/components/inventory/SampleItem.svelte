<script>
    import {getStatus} from "../../../clinicaltools"

    export let sample
</script>

<p class="text-center text-s">
<ul>
    <li> {sample.fyr_id}</li>
    <li> Status : {getStatus(String(sample.status))}</li>
    {#if sample.provider_id}
        <li> Provider : {sample.provider_id}</li>
        <li> Patient ID 1 : {sample.sample_id1}</li>
        <li> Patient ID 2 : {sample.sample_id2}</li>
    {/if}
    {#if sample.report > -3}
        <li> Report = {sample.report}</li>
        {#if sample.invalid_plate}
            <li> The {sample.dataset_id} experiment plate was marked as INVALID</li>
        {/if}
    {/if}
    {#if sample.rack_position}
        <li> Rack = {sample.rack_id}</li>
        <li> Position = {sample.rack_position}</li>
    {/if}
</ul>