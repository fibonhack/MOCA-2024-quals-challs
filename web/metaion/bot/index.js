const express = require('express');
const puppeteer = require('puppeteer');

const app = express();
app.use(express.json());
const port = 3000;


app.post('/report_to_admin', async (req, res) => {
    try {
        const url = req.body.url
        console.log(url)
        // Launch Puppeteer
        const browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox']
        }
        );
        const page = await browser.newPage();
        // Visit Backend
        const flag_cookie = {
            name: 'flag',
            value: process.env.FLAG,
            path:'/',
            domain: 'metaion-backend', // Adjust this to match the domain
            httpOnly: false,
            secure: false,
            sameSite: 'Strict'
          };
        await page.setCookie(flag_cookie)
        await page.goto(url);
        await new Promise(r => setTimeout(r, 1500));
        await browser.close();
        res.status(201).send('Done');
    } catch (error) {
        console.error('Error', error);
        res.status(500).send('Something went wrong');
    }
});

app.listen(port, () => {
    console.log(`Admin is running at http://localhost:${port}`);
});