<script lang="ts">
	import Tailwindcss from './Tailwindcss.svelte';
  import { fade } from 'svelte/transition';
  import ClinicalStart from "./sections/dataAnalysis/Start.svelte";

  const links =  {
    inventory: "/inventory",
    research: "/",
    statisticalAnalysis: "/stats",
    colorimetric: "/image",
    genomics: "/genomics/home",
    settings: "/auth/edit",
    logout: "/auth/logout"
  }

  type portals =  "inventory" | "research" | "stats" | "colorimetric" | "genomics";

	let showUserMenu = false;
  let showMobileMenu = false;
  let activePortal: portals = "research"

	const toggleUserMenu = () => { showUserMenu = !showUserMenu }
	const toggleMobileMenu = () => { showMobileMenu = !showMobileMenu }
</script>

<Tailwindcss />
<main>
<div>
  <nav class="bg-gray-800 print:hidden">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <img class="h-8" src="/logo/FYR-logo.png" alt="FYR logo">
          </div>
          <div class="hidden md:block">
            <div class="ml-10 flex items-baseline">
              <a href="{links.inventory}" class:active-portal="{activePortal === 'inventory'}" class:inactive-portal="{activePortal !== 'inventory'}" on:click="{() => activePortal = 'inventory' }" class="ml-4 px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700 focus:outline-none focus:text-white focus:bg-gray-700">Inventory</a>
              <a href="{links.research}" class:active-portal="{activePortal === 'research'}" class:inactive-portal="{activePortal !== 'research'}" on:click="{() => activePortal = 'research' }" class="px-3 py-2 rounded-md text-sm font-medium text-white bg-gray-900 focus:outline-none focus:text-white focus:bg-gray-700">Research</a>
              <a href="{links.statisticalAnalysis}" class:active-portal="{activePortal === 'stats'}" class:inactive-portal="{activePortal !== 'stats'}" on:click="{() => activePortal = 'stats' }" class="ml-4 px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700 focus:outline-none focus:text-white focus:bg-gray-700">Statistical Analysis</a>
              <a href="{links.colorimetric}" class:active-portal="{activePortal === 'colorimetric'}" class:inactive-portal="{activePortal !== 'colorimetric'}" on:click="{() => activePortal = 'colorimetric' }" class="ml-4 px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700 focus:outline-none focus:text-white focus:bg-gray-700">Colorimetric</a>
              <a href="{links.genomics}" class:active-portal="{activePortal === 'genomics'}" class:inactive-portal="{activePortal !== 'genomics'}" on:click="{() => activePortal = 'genomics' }" class="ml-4 px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700 focus:outline-none focus:text-white focus:bg-gray-700">Genomics</a>
            </div>
          </div>
        </div>
        <div class="hidden md:block">
          <div class="ml-4 flex items-center md:ml-6">
            <button class="p-1 border-2 border-transparent text-gray-400 rounded-full hover:text-white focus:outline-none focus:text-white focus:bg-gray-700" aria-label="Notifications">
              <svg class="h-6 w-6" stroke="currentColor" fill="none" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </button>

            <!-- Profile dropdown -->
            <div class="ml-3 relative">
              <div>
                <button on:click={toggleUserMenu} class="max-w-xs flex items-center text-sm rounded-full text-white focus:outline-none focus:shadow-solid" id="user-menu" aria-label="User menu" aria-haspopup="true">
                  <img class="h-8 w-8 rounded-full" src="/images/FYR-logo-profile-placeholder.png" alt="">
                </button>
              </div>

              <!-- Profile dropdown panel, show/hide based on dropdown state. -->
			  {#if showUserMenu}
				<div transition:fade={{duration: 200}} class="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg">
					<div class="py-1 rounded-md bg-white shadow-xs" role="menu" aria-orientation="vertical" aria-labelledby="user-menu">
					<a href="{links.settings}" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" role="menuitem">Settings</a>
					<a href="{links.logout}" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" role="menuitem">Sign out</a>
					</div>
				</div>
			  {/if}
            </div>
          </div>
        </div>
        <div class="-mr-2 flex md:hidden">
          <!-- Mobile menu button -->
          <button on:click={toggleMobileMenu} class="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none focus:bg-gray-700 focus:text-white">
			{#if showMobileMenu}
				<!-- Menu open: "block", Menu closed: "hidden" -->
				<svg class="block h-6 w-6" stroke="currentColor" fill="none" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			{:else}
				<!-- Menu open: "hidden", Menu closed: "block" -->
				<svg class="block h-6 w-6" stroke="currentColor" fill="none" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
				</svg>
			{/if}
          </button>
        </div>
      </div>
    </div>

    <!--      Mobile menu, toggle  based on menu state.    -->
	{#if showMobileMenu}
		<div class="block md:hidden" transition:fade={{duration: 100}}>
		<div class="px-2 pt-2 pb-3 sm:px-3">
			<a href="{links.inventory}" class="block px-3 py-2 rounded-md text-base font-medium text-white bg-gray-900 focus:outline-none focus:text-white focus:bg-gray-700">Inventory</a>
			<a href="{links.research}" class="block px-3 py-2 rounded-md text-base font-medium text-white bg-gray-900 focus:outline-none focus:text-white focus:bg-gray-700">Research</a>
			<a href="{links.statisticalAnalysis}" class="mt-1 block px-3 py-2 rounded-md text-base font-medium text-gray-300 hover:text-white hover:bg-gray-700 focus:outline-none focus:text-white focus:bg-gray-700">Statistical Analysis</a>
			<a href="{links.colorimetric}" class="mt-1 block px-3 py-2 rounded-md text-base font-medium text-gray-300 hover:text-white hover:bg-gray-700 focus:outline-none focus:text-white focus:bg-gray-700">Colorimetric</a>
			<a href="{links.genomics}" class="mt-1 block px-3 py-2 rounded-md text-base font-medium text-gray-300 hover:text-white hover:bg-gray-700 focus:outline-none focus:text-white focus:bg-gray-700">Genomics</a>
		</div>
		<div class="pt-4 pb-3 border-t border-gray-700">
			<div class="flex items-center px-5">
			<div class="flex-shrink-0">
				<img class="h-10 w-10 rounded-full" src="/images/FYR-logo-profile-placeholder.png" alt="">
			</div>
			<div class="ml-3">
				<div class="text-base font-medium leading-none text-white">Brian Bauer</div>
				<div class="mt-1 text-sm font-medium leading-none text-gray-400">brian@fyrdiagnostics.com</div>
			</div>
			</div>
			<div class="mt-3 px-2">
			<a href="{links.settings}" class="mt-1 block px-3 py-2 rounded-md text-base font-medium text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none focus:text-white focus:bg-gray-700">Settings</a>
			<a href="{links.logout}" class="mt-1 block px-3 py-2 rounded-md text-base font-medium text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none focus:text-white focus:bg-gray-700">Sign out</a>
			</div>
		</div>
		</div>
	{/if}
  </nav>

  <header class="bg-white shadow print:hidden">
    <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <h1 class="text-3xl font-bold leading-tight text-gray-900">
         FYR Diagnostics Team Portal
      </h1>
    </div>
  </header>
  <main>
    <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <!-- Replace with your content -->
      <div class="px-4 py-6 sm:px-0">
        <ClinicalStart />
      </div>
      <!-- /End replace -->
    </div>
  </main>
</div>

</main>

<style type="text/postcss">

</style>