const puppeteer = require('puppeteer');
const { v4: uuidv4 } = require('uuid');
const fs = require('fs');
const readline = require('readline');
const DEBUG_PORT = process.env.DEBUG_PORT;

setTimeout(() => {
    console.log('Timeout');
    process.exit(1);
}, 35000);

// Create interface for reading data from stdin
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
});

// Initialize an empty string to accumulate input data
let inputData = '';

// Read input data
rl.on('line', (line) => {
    inputData += line;
});

// Once input stream ends, parse the JSON and print values
rl.on('close', async () => {
    const { html } = JSON.parse(inputData); 

    try {
        const browser = await puppeteer.launch({
            headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox', `--remote-debugging-port=${DEBUG_PORT}`]
        });
        const page = await browser.newPage();

        await page.setContent(html);

        const pdf = await page.pdf({ format: 'A4' });

        await browser.close();

        // Write the PDF file to the disk
        console.log(pdf.toString('base64'));
    } catch (error) {
        console.log(error)
    }

    process.exit(0);
});
