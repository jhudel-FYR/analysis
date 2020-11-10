<script>
    import Flatpickr from 'svelte-flatpickr'
    import 'flatpickr/dist/flatpickr.css'
    import '../../../../node_modules/flatpickr/dist/themes/dark.css'
 
    let date = null
    const flatpickrOptions = {
        enableTime: false,
        dateFormat: "Ymd",
        onChange: (selectedDates, dateStr, instance) => {
            console.log('Options onChange handler')
        }
    }
</script>


<form action="{{ }}" method="POST" enctype="multipart/form-data">
<div class="flex items-center justify-evenly bg-grey-lighter mb-5">
    <span class="mt-1 leading-normal font-medium text-gray-800 text-xl">You can select an existing dataset: </span>
    <div class="space-y-1">
        <div class="relative">
          <span class="inline-block w-full rounded-md shadow-sm">
            <button type="button" aria-haspopup="listbox" aria-expanded="true" aria-labelledby="listbox-label" class="cursor-default relative w-full rounded-md border border-gray-300 bg-white pl-3 pr-10 py-2 text-left focus:outline-none focus:shadow-outline-blue focus:border-blue-300 transition ease-in-out duration-150 sm:text-sm sm:leading-5">
              <div class="flex items-center space-x-3">
                <span class="block truncate">
                  JK
                </span>
              </div>
              <span class="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
                <svg class="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="none" stroke="currentColor">
                  <path d="M7 7l3-3 3 3m0 6l-3 3-3-3" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </span>
            </button>
          </span>
          <div class="absolute mt-1 w-full rounded-md bg-white shadow-lg">
            <ul tabindex="-1" role="listbox" aria-labelledby="listbox-label" aria-activedescendant="listbox-item-3" class="max-h-56 rounded-md py-1 text-base leading-6 shadow-xs overflow-auto focus:outline-none sm:text-sm sm:leading-5">

              <!-- More options... -->
            </ul>
          </div>
        </div>
    </div>
    <div>
        <Flatpickr options="{ flatpickrOptions }" bind:value={date} element="#my-picker">
            <div class="flatpickr cursor-default relative w-full rounded-md border border-gray-300 bg-white pl-5 pr-5 py-5 text-left focus:outline-none focus:shadow-outline-blue focus:border-grey-300 transition ease-in-out duration-150 sm:text-sm sm:leading-5" id="my-picker">
                <input type="text" name="date" placeholder="Select Initials First..." data-input>
            </div>
        </Flatpickr>
    </div>
    <div class="space-y-1">
        <div class="relative">
        <span class="inline-block w-full rounded-md shadow-sm">
            <button type="button" name="letter" aria-haspopup="listbox" aria-expanded="true" aria-labelledby="listbox-label" class="cursor-default relative w-full rounded-md border border-gray-300 bg-white pl-15 pr-5 py-5 text-left focus:outline-none focus:shadow-outline-blue focus:border-grey-300 transition ease-in-out duration-150 sm:text-sm sm:leading-5">
                <option name="None"></option> 
            <span class="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
                <svg class="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="none" stroke="currentColor">
                <path d="M7 7l3-3 3 3m0 6l-3 3-3-3" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
            </span>
        </button>
        </span>
        </div>
    </div>
    <span class="selected-experiment-preview font-extrabold text-gray-800 text-xl">No Selection</span>
</div>

<div class="flex items-center justify-evenly bg-grey-lighter mt-10">

    <label class="w-64 flex flex-col items-center px-2 py-3 bg-white text-gray-800 rounded-lg shadow-lg tracking-wide uppercase border border-gray-800 cursor-pointer hover:bg-red-800 hover:text-white">
        <svg viewBox="0 0 20 20" fill="currentColor" class="x-circle w-8 h-8">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
        </svg>
        <span class="mt-2 text-base leading-normal">Delete</span>
        <input type='button' class="hidden" />
    </label>

    <label class="w-64 flex flex-col items-center px-2 py-3 bg-white text-gray-800 rounded-lg shadow-lg tracking-wide uppercase border border-gray-800 cursor-pointer hover:bg-green-800 hover:text-white">
        <svg viewBox="0 0 20 20" fill="currentColor" class="arrow-circle-right w-8 h-8">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z" clip-rule="evenodd"></path>
        </svg>
        <span class="mt-2 text-base leading-normal">Submit</span>
        <input type='button' class="hidden" />
    </label>
</div>
</form>