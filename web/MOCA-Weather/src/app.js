const express = require('express');
const mongoose = require('mongoose');
const cookieParser = require('cookie-parser');
const bcrypt = require('bcrypt');
const fs = require('fs');
const cron = require('node-cron');
const { Client: SSHClient, utils: { generateKeyPairSync } } = require('ssh2');
const SFTPClient = require('ssh2-sftp-client');

const models = require('./models');

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());
app.set('view engine', 'ejs');
app.use(express.static('public'));

// Connect to MongoDB
mongoose.connect(process.env.MONGO_URI, { useNewUrlParser: true, useUnifiedTopology: true })
    .then(async () => {
        console.log('MongoDB connected')

        // Create target user
        const user_count = await models.User.countDocuments();

        if (user_count === 0) {

            const pubkey = fs.readFileSync('keys/id_rsa.pub', 'utf-8');
            const privkey = fs.readFileSync('keys/id_rsa', 'utf-8');

            const user = await models.User.create({
                username: 'target',
                password: 'password'
            })

            // Add relative device
            const device = await models.Device.create({
                userId: user.userId,
                name: 'target',
                host: 'device',
                port: '2222',
                username: 'target',

                pubkey,
                privkey,

                configuration : {
                    cpu_temperature: '/usr/bin/cpu_temp',
                    temperature: '/usr/bin/temp',
                    humidity: '/usr/bin/humidity'
                }
            })

            const session = await models.Session.create({
                userId: user.userId,
            })

            console.log(`User ${user.userId} created`);
            console.log(`Device ${device.deviceId} created`);
            console.log(`Session ${session.sessionId} created`)
        }

    })
    .catch(err => console.error('MongoDB connection error:', err));

app.get('/', (req, res) => {
    res.render('index');
});

app.get('/register', (req, res) => {
    res.render('register', { error: null });
})

const createSession = async (res, userId) => {
    const new_session = await models.Session.create({
        userId,
    })

    res.cookie('session', new_session.sessionId, {
        httpOnly: true,
        secure: false,
        sameSite: 'lax'
    })

    res.redirect('/');
}


app.post('/register', async (req, res) => {
    const { username, password } = req.body;

    if (typeof username !== 'string' || typeof password !== 'string') {
        return res.render('register', { error: 'Invalid email or password' });
    }

    // Check if user already exists
    const userExists = await models.User.findOne({
        username
    })

    if (userExists) {
        return res.render('register', { error: 'User already exists' });
    }

    if (password.length < 8) {
        return res.render('register', { error: 'Password must be at least 8 characters long' });
    }

    const user = await models.User.create({
        username,
        password: await bcrypt.hash(password, 10)
    })

    await createSession(res, user.userId);
})

app.get('/login', (req, res) => {
    res.render('login', { error: null });
})

app.post('/login', async (req, res) => {
    const { username, password } = req.body;

    if (typeof username !== 'string' || typeof password !== 'string') {
        return res.render('login', { error: 'Invalid email or password' });
    }

    const user = await models.User.findOne({
        username,
    })

    if (!user) {
        return res.render('login', { error: 'Invalid email or password' });
    }

    if (!await bcrypt.compare(password, user.password)) {
        return res.render('login', { error: 'Invalid email or password' });
    }

    await createSession(res, user.userId)
})



app.use((req, res, next) => {
    if (!req.cookies.session) {
        return res.redirect('/login');
    }

    models.Session.findOne({ sessionId: req.cookies.session })
        .then(session => {
            models.User.findOne({
                userId: session.userId
            }).then(user => {
                req.user = user;
                next();
            })
        })
        .catch(err => {
            res.redirect('/login');
        })
})

app.get('/devices', async (req, res) => {
    const devices = await models.Device.find({
        userId: req.user.userId
    });

    res.render('device-list', { devices });
})

app.get('/device/:deviceId', async (req, res) => {

    const deviceId = req.params.deviceId;

    if (typeof deviceId !== 'string') {
        return res.status(404).send('Device not found');
    }

    const device = await models.Device.findOne({
        deviceId: deviceId,
        userId: req.user.userId
    })

    if (!device) {
        return res.status(404).send('Device not found');
    }

    const measures = await models.Measure.find({ deviceId: deviceId })
    res.render('device', { device, measures });
})

app.get('/device', async (req, res) => {
    res.render('device-setup', { error: null });
})

app.post('/device', async (req, res) => {
    var { name, host, username, port } = req.body;
    port = parseInt(port)
    if (typeof host !== 'string' || typeof name !== 'string' || typeof username !== 'string' || isNaN(port)) {
        return res.render('device-setup', { error: 'Invalid name or host' });
    }

    const deviceCount = await models.Device.countDocuments({
        userId: req.user.userId
    })

    if (deviceCount >= 5) {
        return res.render('device-setup', { error: 'You can only have 5 devices' });
    }

    const keypair = generateKeyPairSync('rsa', { bits: 4096 });

    const pubkey = keypair.public;
    const privkey = keypair.private;

    const device = await models.Device.create({
        userId: req.user.userId,
        name,
        host,
        username,
        port,

        pubkey,
        privkey
    })

    res.redirect(`/device/${device.deviceId}`);
})

app.get('/device/:deviceId/config', async (req, res) => {
    const deviceId = req.params.deviceId;

    if (typeof deviceId !== 'string') {
        return res.status(404).send('Device not found');
    }

    const device = await models.Device.findOne({
        deviceId: deviceId,
        userId: req.user.userId
    })

    if (!device) {
        return res.status(404).send('Device not found');
    }

    res.render('device-config', { config: device.configuration, error: null });
})

app.post('/device/:deviceId/config', async (req, res) => {
    const deviceId = req.params.deviceId;

    if (typeof deviceId !== 'string') {
        return res.status(404).send('Device not found');
    }

    const device = await models.Device.findOne({
        deviceId: deviceId,
        userId: req.user.userId
    })

    if (!device) {
        return res.status(404).send('Device not found');
    }

    const configuration = {};

    const cpu_temperature = req.body.cpu_temperature;
    const temperature = req.body.temperature;
    const humidity = req.body.humidity;

    configuration.cpu_temperature = (cpu_temperature && typeof cpu_temperature === 'string') ? cpu_temperature : device.configuration.cpu_temperature
    configuration.temperature = (temperature && typeof temperature === 'string') ? temperature : device.configuration.temperature
    configuration.humidity = (humidity && typeof humidity === 'string') ? humidity : device.configuration.humidity

    device.configuration = configuration;
    await device.save();

    res.redirect(`/device/${device.deviceId}`);
})

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});

const measure_task = async () => {
    const devices = await models.Device.find()

    console.log(`Measuring ${devices.length} devices`)

    devices.forEach(async device => {
        // Uploading agent and configuration
        const sftp = new SFTPClient();

        try {
            await sftp.connect({
                host: device.host,
                port: device.port,
                username: device.username,
                privateKey: device.privkey
            })

            // upload agent
            await sftp.put('/app/agent/agent', '/tmp/agent');
            await sftp.chmod('/tmp/agent', 0o777)

            // upload configuration
            const data = Buffer.from(JSON.stringify(device.configuration))
            await sftp.put(data, '/tmp/config.json');

            await sftp.end();
        }
        catch (err) {
            console.error(err.message);

            // if error occurs, remove the device and skip it
            await models.Device.deleteOne({ deviceId: device.deviceId });
            return;
        }

        console.log("Correctly uploaded agent and configuration")

        const conn = new SSHClient();

        conn.on('ready', () => {
            conn.exec('/tmp/agent', (err, stream) => {

                if (err) {
                    return;
                }

                stream.on('close', (code, signal) => {
                    conn.end();
                })
                    .on('data', async (data) => {
                        try {
                            const measurement = JSON.parse(data);

                            const record = await models.Measure.create({
                                deviceId: device.deviceId,
                                cpu_temperature: measurement.cpu_temperature,
                                temperature: measurement.temperature,
                                humidity: measurement.humidity
                            })
                        }
                        catch (err) {
                            console.error(err.message);
                        }
                    }).stderr.on('data', (data) => {
                        console.error('STDERR: ' + data);
                    });
            });
        }).connect({
            host: device.host,
            port: device.port,
            username: device.username,
            privateKey: device.privkey,
        });

    })

}

cron.schedule('* * * * *', measure_task);