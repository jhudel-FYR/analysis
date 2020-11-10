<script>
    import ListItemForPDF from "./ListItemforPDF.svelte";
    import FYRlogo from "../FYRlogo.svelte";
    import ListItemforPDF from "./ListItemforPDF.svelte";

    export let samples = [];
    export let provider = '';

    let numSamples = samples.length;

</script>

<div class="-mx-4 sm:-mx-8 px-4 sm:px-8 py-4 overflow-x-auto">
    <div class="inline-block min-w-full shadow rounded-lg overflow-hidden">
        <table class="min-w-full leading-normal ">
            <thead>
            <div class="bg-white pb-4 px-6 rounded-md w-full">
                <p class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
                    <FYRlogo/>
                <br>
                <div class="block whitespace-no-wrap text-md text-gray-700">The provider, <b>{ provider }</b>, and <b>FYR Diagnostics</b> acknowledge delivery of <b>{numSamples}</b> samples
                    on today's date:____________.
                </div>
            </div>
            <br>
            <tr>
                <th class="px-5 py-3 border-b-2 border-gray-200 bg-gray-100 text-left text-sm font-semibold text-gray-600 uppercase tracking-wider">
                    FYR ID
                </th>
                <th class="px-5 py-3 border-b-2 border-gray-200 bg-gray-100 text-left text-sm font-semibold text-gray-600 uppercase tracking-wider">
                    ID #1
                </th>
                <th class="px-5 py-3 border-b-2 border-gray-200 bg-gray-100 text-left text-sm font-semibold text-gray-600 uppercase tracking-wider">
                    ID #2
                </th>
                <th class="px-5 py-3 border-b-2 border-gray-200 bg-gray-100 text-left text-sm font-semibold text-gray-600 uppercase tracking-wider">
                    Date Collected
                </th>
            </tr>
            </thead>
            <tbody>
            {#each samples as sample}
                <ListItemforPDF {...sample}/>
            {/each}
            </tbody>

            <tfoot>
            <tr>
                <td class="px-5 py-5 bg-white text-sm w-1/4 h-12 w-1/4 h-12">
                    <p class="text-gray-900 whitespace-no-wrap">
                        Delivered By:</p></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td></td>
                <td class="px- py-5 bg-white text-sm w-1/4 h-12 border-t border-gray-500">
                    <p class="text-gray-900 whitespace-no-wrap">
                        Printed Name</p></td>
                <td class="px-5 py-5 bg-white text-sm w-1/4 h-12 border-t border-gray-500">
                    <p class="text-gray-900 whitespace-no-wrap">
                        Signature</p></td>
                <td class="px-5 py-5 bg-white text-sm w-1/4 h-12 border-t border-gray-500">
                    <p class="text-gray-900 whitespace-no-wrap">
                        Date</p></td>
            <tr>
                <td class="px-5 py-5 bg-white text-sm w-1/4 h-12">
                    <p class="text-gray-900 whitespace-no-wrap">
                        Received By:</p></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td></td>
                <td class="px-5 py-5 bg-white text-sm w-1/4 h-12 border-t border-gray-500">
                    <p class="text-gray-900 whitespace-no-wrap">
                        Printed Name</p></td>
                <td class="px-5 py-5 bg-white text-sm w-1/4 h-12 border-t border-gray-500">
                    <p class="text-gray-900 whitespace-no-wrap">
                        Signature</p></td>
                <td class="px-5 py-5 bg-white text-sm w-1/4 h-12 border-t border-gray-500">
                    <p class="text-gray-900 whitespace-no-wrap">
                        Date</p></td>
            </tr>
            </tfoot>
        </table>
    </div>
</div>