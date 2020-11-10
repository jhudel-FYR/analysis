import svelte from 'rollup-plugin-svelte';
import css from "rollup-plugin-css-only";
import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import livereload from 'rollup-plugin-livereload';
import { terser } from 'rollup-plugin-terser';
import sveltePreprocess from 'svelte-preprocess';
import typescript from '@rollup/plugin-typescript';
import serve from 'rollup-plugin-serve';


const production = !process.env.ROLLUP_WATCH;
console.log(`Building for ${production ? 'production' : 'development'}`);


export default {
	input: 'client/main.ts',
	output: {
		sourcemap: true,
		format: 'iife',
		name: 'app',
		file: 'flaskr/static/build/bundle.js'
	},
	plugins: [
		css({ output: "flaskr/static/build/extra.css" }),
		svelte({
			// enable run-time checks when not in production
			dev: !production,
			// we'll extract any component CSS out into
			// a separate file - better for performance
			css: css => {
				css.write('flaskr/static/build/bundle.css');
			},
			preprocess: sveltePreprocess({ postcss: true }),
		}),

		// If you have external dependencies installed from
		// npm, you'll most likely need these plugins. In
		// some cases you'll need additional configuration -
		// consult the documentation for details:
		// https://github.com/rollup/plugins/tree/master/packages/commonjs
		resolve({
			browser: true,
			dedupe: ['svelte']
		}),
		commonjs(),
		typescript({ sourceMap: !production }),

		// In dev mode, call `npm run start` once
		// the bundle has been generated
		!production && serve({
			open: true,
			contentBase: 'flaskr/static',
			host: 'localhost',
			port: 5555
		}),

		// Watch the `public` directory and refresh the
		// browser on changes when not in production
		!production && livereload('./flaskr/static'),

		// If we're building for production (npm run build
		// instead of npm run dev), minify
		production && terser()
	],
	watch: {
		clearScreen: false
	}
};
