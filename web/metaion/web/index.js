const express = require('express')
const path = require('path');
const createDOMPurify = require('dompurify');
const { JSDOM } = require('jsdom');
const app = express()
const port = 5000

app.set('view engine', 'ejs');

app.use(function(req, res, next) {
    res.setHeader("Content-Security-Policy", "script-src 'unsafe-inline' https://khm0.googleapis.com/ https://cdn.jsdelivr.net/npm/marked@4.0.12/marked.min.js https://cdn.jsdelivr.net/npm/texme@1.2.2 https://cdn.jsdelivr.net/npm/mathjax@3.2.0/es5/tex-mml-chtml.js")
    res.setHeader("X-Frame-Options","DENY")
    next();
});

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '/static/index.html'));
})

app.get('/euler', (req, res) => {
    res.sendFile(path.join(__dirname, '/static/euler.html'));
})

app.get('/render', (req, res) => {
    if(typeof req.query.formula === "string"){
        const window = new JSDOM('').window;
        const DOMPurify = createDOMPurify(window);
        const clean = DOMPurify.sanitize(req.query.formula,{ALLOWED_TAGS: ['a','p']});
        res.setHeader("Content-Type","text/html; charset=utf-8")
        res.render('../static/render',{formula: clean});
    }else{
        res.sendFile(path.join(__dirname, '/static/error.html'));
    }
})

app.get('/report', (req, res) => {
    const url = req.query.url
    if(typeof url === "string" && (url.startsWith("https://") || url.startsWith("http://"))){
        fetch("http://metaion-admin:3000/report_to_admin", {
            "method":"POST",
            "headers":{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                "url": url
            })
        }).then(e=>console.log(e.text))
        res.json({"message":"url reported"})
    }else{
        res.sendFile(path.join(__dirname, '/static/error.html'));
    }
})

app.listen(port, () => {
  console.log(`Metaion listening on port ${port}`)
})

