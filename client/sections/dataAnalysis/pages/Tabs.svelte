<script>
    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();

    export let activeTab;

    function changeActiveTab(changeToTab) {
        dispatch('tabChange', changeToTab)
    }

</script>


<div class="print:hidden">
    <!-- Start section divider tabs -->
    <ul class="flex justify-center mb-8 width-3/4">
        <li class="w-full border-b-2 border-solid border-gray-500"></li>
<!--        <li class="{activeTab === "exp-upload" ? "active-tab" : "inactive-tab"}"  on:click={ () => { changeActiveTab("exp-upload") }}>-->

<!--        <svg viewBox="0 0 20 20" fill="currentColor" class="cloud-upload w-6 h-6">-->
<!--            <path d="M5.5 13a3.5 3.5 0 01-.369-6.98 4 4 0 117.753-1.977A4.5 4.5 0 1113.5 13H11V9.413l1.293 1.293a1 1 0 001.414-1.414l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13H5.5z"></path>-->
<!--            <path d="M9 13h2v5a1 1 0 11-2 0v-5z"></path>-->
<!--        </svg>-->
<!--        <span>Upload</span>-->
<!--        </li>-->
<!--        <li class="{activeTab === "revisit" ? "active-tab" : "inactive-tab"}" on:click={ () => { changeActiveTab("revisit") }}>-->

<!--        <svg viewBox="0 0 20 20" fill="currentColor" class="beaker w-6 h-6">-->
<!--            <path fill-rule="evenodd"-->
<!--                  d="M7 2a1 1 0 00-.707 1.707L7 4.414v3.758a1 1 0 01-.293.707l-4 4C.817 14.769 2.156 18 4.828 18h10.343c2.673 0 4.012-3.231 2.122-5.121l-4-4A1 1 0 0113 8.172V4.414l.707-.707A1 1 0 0013 2H7zm2 6.172V4h2v4.172a3 3 0 00.879 2.12l1.027 1.028a4 4 0 00-2.171.102l-.47.156a4 4 0 01-2.53 0l-.563-.187a1.993 1.993 0 00-.114-.035l1.063-1.063A3 3 0 009 8.172z"-->
<!--                  clip-rule="evenodd"></path>-->
<!--        </svg>-->
<!--        <span>Revisit</span>-->
<!--        </li>-->
        <li class="{activeTab === "new-experiment" ? "active-tab" : "inactive-tab"}" on:click={ () => { changeActiveTab("new-experiment") }}>

        <svg viewBox="0 0 20 20" fill="currentColor" class="library w-6 h-6">
        <path fill-rule="evenodd"
              d="M10.496 2.132a1 1 0 00-.992 0l-7 4A1 1 0 003 8v7a1 1 0 100 2h14a1 1 0 100-2V8a1 1 0 00.496-1.868l-7-4zM6 9a1 1 0 00-1 1v3a1 1 0 102 0v-3a1 1 0 00-1-1zm3 1a1 1 0 012 0v3a1 1 0 11-2 0v-3zm5-1a1 1 0 00-1 1v3a1 1 0 102 0v-3a1 1 0 00-1-1z"
              clip-rule="evenodd"></path>
        </svg>
        <span>Upload New Experiment</span>
        </li>

        <li class="{activeTab === "search-experiments" ? "active-tab" : "inactive-tab"}" on:click={ () => { changeActiveTab("search-experiments") }}>
        <!--<svg viewBox="0 0 20 20" fill="currentColor" class="library w-6 h-6">
        <path fill-rule="evenodd"
              d="M10.496 2.132a1 1 0 00-.992 0l-7 4A1 1 0 003 8v7a1 1 0 100 2h14a1 1 0 100-2V8a1 1 0 00.496-1.868l-7-4zM6 9a1 1 0 00-1 1v3a1 1 0 102 0v-3a1 1 0 00-1-1zm3 1a1 1 0 012 0v3a1 1 0 11-2 0v-3zm5-1a1 1 0 00-1 1v3a1 1 0 102 0v-3a1 1 0 00-1-1z"
              clip-rule="evenodd"></path>
        </svg>
        -->
        <svg viewBox="0 0 20 20" fill="currentColor" class="library w-6 h-6">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16l2.879-2.879m0 0a3 3 0 104.243-4.242 3 3 0 00-4.243 4.242zM21 12a9 9 0 11-18 0 9 9 0 0118 0z"  clip-rule="evenodd">
            </path>
        </svg>
        <span>Search Previous Experiments</span>
        </li>
        
        <li class="w-full border-b-2 border-solid border-gray-500"></li>
    </ul>
</div>


<style>

    .active-tab {
        @apply px-4 cursor-pointer border-solid border-2 border-b-0 border-gray-500 rounded-t whitespace-no-wrap;
    }

    .active-tab > span {
        @apply text-center inline-block py-2 pr-4;
    }

    .inactive-tab {
        @apply px-4 cursor-pointer border-solid border-b-2 border-gray-500 rounded-t whitespace-no-wrap;
    }

    .inactive-tab > span {
        @apply text-center inline-block text-gray-500 py-2 pr-4;
    }

    .inactive-tab > svg, .active-tab > svg {
        @apply inline pl-1;
    }

    .inactive-tab:hover {
        @apply bg-gray-200;
    }

</style>