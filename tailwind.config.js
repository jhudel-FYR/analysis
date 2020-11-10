const production = !process.env.ROLLUP_WATCH;

module.exports = {
    future: {
        removeDeprecatedGapUtilities: true,
    },
    purge: {
        enabled: production,
        content: ["./client/**/*.svelte", "./client/**/*.html"]
    },
    theme: {
        extend: {
            screens: {
                'print': {'raw': 'print'},
                // => @media print { ... }
            }
        }
    },
    plugins: [
        require('@tailwindcss/ui'),
        require('tailwindcss'),
    ]
};
