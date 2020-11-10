<script lang="ts">
    import {fade} from "svelte/transition"
    import UploadTab from "./pages/Upload.svelte";
    import InitializationTab from "./pages/Initialization.svelte";
    import OrdersTab from "./pages/Orders.svelte";
    import ResultsTab from "./pages/Results.svelte";
    import RevisitTab from "./pages/Revisit.svelte";
    import InventoryTab from "./pages/Inventory.svelte";
    import Tabs from "./pages/Tabs.svelte"
    import ExperimentTab from "./pages/Experiment.svelte";


    type tabNames = "new-experiment" | "search-experiments";

    interface tabChangeEvent {
        detail: tabNames;
    }

    let activeTab: tabNames = "new-experiment";


    function isActiveTab(thisTab: tabNames): boolean {
        return thisTab === activeTab;
    }

    function setActiveTab(tabName: tabNames): void {
        activeTab = tabName;
    }

    function setActiveTabEventHandler(e: tabChangeEvent): void {
        activeTab = e.detail;
    }
</script>


<Tabs on:tabChange={setActiveTabEventHandler} activeTab={activeTab} />


{#if activeTab === "new-experiment"}
    <UploadTab/>
{:else if activeTab === "search-experiments"}
    <RevisitTab/>
{/if}

