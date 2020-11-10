<script>
    import {getStatus} from "../../../clinicaltools"
    import {getReport} from "../../../clinicaltools"

    export let samples;

    let reportTotals = [];
    let providerTotals = [];

    $: if (samples.length > 0) {
        getReportTotals();
        getProviderTotals();
    }

    function getReportTotals() {
        [-3, -2, -1, 0, 1].forEach(r => {
            reportTotals.push({
                'report': r,
                'count': samples.filter(x => x.report === r).length
            })
        });
        reportTotals = reportTotals;
    }

    function getProviderTotals() {
        const unique = [...new Set(samples.map(item => item.provider_id))];
        unique.forEach(p => {
            providerTotals.push({
                'provider': p,
                'count': samples.filter(x => x.provider_id === p).length
            })
        });
        providerTotals = providerTotals;
    }

</script>


<form>
    <div class="border-gray-400 mt-4">
    </div>
    <!--    <h2 class="text-2xl text-gray-900">Patient Search:</h2>-->
    <!--    <div class="flex mt-4">-->
    <!--        <div class='px-3 mb-6'>-->
    <!--            <label class='block uppercase tracking-wide text-gray-700 text-xs font-bold mb-2'>First Patient ID</label>-->
    <!--            <input class='appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-400 shadow-inner rounded-md py-3 px-4 leading-tight focus:outline-none  focus:border-gray-500'-->
    <!--                   type='text' required>-->
    <!--        </div>-->
    <!--        <div class='px-3 mb-6'>-->
    <!--            <label class='block uppercase tracking-wide text-gray-700 text-xs font-bold mb-2'>Second Patient ID</label>-->
    <!--            <input class='appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-400 shadow-inner rounded-md py-3 px-4 leading-tight focus:outline-none  focus:border-gray-500'-->
    <!--                   type='text' required>-->
    <!--        </div>-->

    <!--        <button class="mb-6 mt-6 ml-6 bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded inline-flex items-center">-->
    <!--            <svg viewBox="0 0 20 20" fill="currentColor" class="fill-current mr-2 w-4 h-4"-->
    <!--                 className="document-search w-6 h-6">-->
    <!--                <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2h-1.528A6 6 0 004 9.528V4z"/>-->
    <!--                <path fillRule="evenodd"-->
    <!--                      d="M8 10a4 4 0 00-3.446 6.032l-1.261 1.26a1 1 0 101.414 1.415l1.261-1.261A4 4 0 108 10zm-2 4a2 2 0 114 0 2 2 0 01-4 0z"-->
    <!--                      clipRule="evenodd"/>-->
    <!--            </svg>-->
    <!--            <span>Search</span>-->
    <!--        </button>-->
    <!--    </div>-->

    <div class="flex flex-col">
        <div class="-my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
            <div class="py-2 align-middle inline-block min-w-full sm:px-6 lg:px-8">
                <div class="shadow overflow-hidden border-b border-gray-200 sm:rounded-lg">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead>
                        <tr>
                            <th class="px-6 py-3 bg-gray-50 text-left text-xs leading-4 font-medium text-gray-500 uppercase tracking-wider">
                                FYR ID
                            </th>
                            <th class="px-6 py-3 bg-gray-50 text-left text-xs leading-4 font-medium text-gray-500 uppercase tracking-wider">
                                Provider
                            </th>
                            <th class="px-6 py-3 bg-gray-50 text-left text-xs leading-4 font-medium text-gray-500 uppercase tracking-wider">
                                Primary ID
                            </th>
                            <th class="px-6 py-3 bg-gray-50 text-left text-xs leading-4 font-medium text-gray-500 uppercase tracking-wider">
                                Secondary ID
                            </th>
                            <th class="px-6 py-3 bg-gray-50 text-left text-xs leading-4 font-medium text-gray-500 uppercase tracking-wider">
                                Status
                            </th>
                            <th class="px-6 py-3 bg-gray-50 text-center text-xs leading-4 font-medium text-gray-500 uppercase tracking-wider">
                                Result
                            </th>
                        </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                        {#each samples as item}
                            <tr>
                                <td class="px-6 py-4 whitespace-no-wrap">
                                    <div class="content-left">
                                        <div class="ml-4 text-sm leading-5 text-gray-900">
                                            {item.fyr_id}
                                        </div>
                                    </div>
                                </td>
                                <td class="px-6 py-4 whitespace-no-wrap text-sm leading-5 text-gray-900">
                                    {item.provider_id}
                                </td>
                                <td class="px-6 py-4 whitespace-no-wrap text-sm leading-5 text-gray-900">
                                    {item.sample_id1}
                                </td>
                                <td class="px-6 py-4 whitespace-no-wrap text-sm leading-5 text-gray-900">
                                    {item.sample_id2}
                                </td>
                                <td class="px-6 py-4 text-center whitespace-no-wrap">
                                    {getStatus(item.status)}
                                </td>
                                <td class="px-6 py-4 text-center whitespace-no-wrap">
                                    {#if item.report === 1}
                                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                                  {getReport(item.report)}
                                </span>
                                    {:else if item.report === 0}
                                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                                  {getReport(item.report)}
                                </span>
                                        {:else if item.report === -1}
                                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-grey-100 text-grey-800">
                                  {getReport(item.report)}
                                </span>
                                        {:else if item.report === -2}
                                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                                  {getReport(item.report)}
                                </span>
                                    {:else}
                                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full text-gray-900">
                                  {getReport(item.report)}
                                </span>
                                    {/if}
                                </td>
                            </tr>
                        {/each}
                        </tbody>
                        <tfoot>
                        <tr>
                            {#each reportTotals as totals}
                                <td class="px-6 py-4 whitespace-no-wrap text-sm leading-5 text-gray-900">
                                    {getReport(totals.report)} Total: {totals.count}
                                </td>
                            {/each}
                        </tr>
                        <tr>
                            {#each providerTotals as totals}
                                <td class="px-6 py-4 whitespace-no-wrap text-sm leading-5 text-gray-900">
                                    Provider {totals.provider}: {totals.count}
                                </td>
                            {/each}
                        </tr>
                        </tfoot>
                    </table>
                </div>
            </div>
        </div>
    </div>

</form>