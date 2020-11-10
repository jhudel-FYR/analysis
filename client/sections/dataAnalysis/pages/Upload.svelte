
<form class="flex items-center justify-evenly bg-grey-lighter" action="{{ url_for('research.upload') }}" method="POST" enctype="multipart/form-data">
<div class="flex items-center justify-evenly bg-grey-lighter">
    <label class="w-64 flex flex-col items-center px-4 py-6 bg-white text-gray-800 rounded-lg shadow-lg tracking-wide uppercase border border-gray-800 cursor-pointer hover:bg-gray-800 hover:text-white">
        <svg class="w-8 h-8" fill="currentColor" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
            <path d="M16.88 9.1A4 4 0 0 1 16 17H5a5 5 0 0 1-1-9.9V7a3 3 0 0 1 4.52-2.59A4.98 4.98 0 0 1 17 8c0 .38-.04.74-.12 1.1zM11 11h3l-4-4-4 4h3v3h2v-3z" />
        </svg>
        <span class="mt-2 text-base leading-normal">Select Info file</span>
        <input name="file1" id="infofile" type="file" oninput="validateFile(this, 'info')" autocomplete="off" accept="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"/>
    </label>

    <label class="w-64 flex flex-col items-center px-4 py-6 bg-white text-gray-800 rounded-lg shadow-lg tracking-wide uppercase border border-gray-800 cursor-pointer hover:bg-gray-800 hover:text-white">
        <svg class="w-8 h-8" fill="currentColor" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
            <path d="M16.88 9.1A4 4 0 0 1 16 17H5a5 5 0 0 1-1-9.9V7a3 3 0 0 1 4.52-2.59A4.98 4.98 0 0 1 17 8c0 .38-.04.74-.12 1.1zM11 11h3l-4-4-4 4h3v3h2v-3z" />
        </svg>
        <span class="mt-2 text-base leading-normal">Select RFU file</span>
        <input name="file2" id="rfufile" type="file" oninput="validateFile(this, 'rfu')" autocomplete="off" accept="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"/>
    </label>

    <label class="w-64 flex flex-col items-center px-4 py-6 bg-white text-gray-800 rounded-lg shadow-lg tracking-wide uppercase border border-gray-800 cursor-pointer hover:bg-green-800 hover:text-white">
        <svg viewBox="0 0 20 20" fill="currentColor" class="arrow-circle-right w-6 h-6"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z" clip-rule="evenodd"></path></svg>
        <span class="mt-2 text-base leading-normal">Submit!</span>
        <input type='button' class="hidden" />
    </label>
</div>
<div>
    <label for="official_results">Get COVID Sample Results</label>
    <input id="official_results" name='official_results' type="checkbox"/>

</div>
</form>