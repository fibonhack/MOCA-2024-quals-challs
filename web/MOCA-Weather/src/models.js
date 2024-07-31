const mongoose = require('mongoose');
const { v4: uuidv4 } = require('uuid');

const userSchema = new mongoose.Schema({
  userId: {
    type: String,
    default: uuidv4,
    unique: true
  },
  username: {
    type: String,
    required: true,
    unique: true
  },
  password: {
    type: String,
    required: true
  }
}, { timestamps: true });

const sessionSchema = new mongoose.Schema({
  sessionId: {
    type: String,
    default: uuidv4,
    required: true
  },
  userId: {
    type: String,
    required: true
  },
}, { timestamps: true });

const deviceSchema = new mongoose.Schema({
  deviceId: {
    type: String,
    default: uuidv4,
    unique: true
  },
  userId: {
    type: String,
    required: true
  },
  name: {
    type: String,
    required: true
  },
  host: {
    type: String,
    required: true
  },
  port :{
    type: Number,
    required: true
  },
  username: {
    type: String,
    required: true
  },
  configuration : {
    type: Object,
    required: false,
    default: {}
  },

  pubkey: {
    type: String,
    required: true
  },
  privkey: {
    type: String,
    required: true
  }
}, { timestamps: true });

const measureSchema = new mongoose.Schema({
  deviceId: {
    type: String,
    required: true
  },
  cpu_temperature: {
    type: Number,
    required: false
  },
  temperature:{
    type: Number,
    required: false
  },
  humidity: {
    type: Number,
    required: false
  }
}, { timestamps: true });

const User = mongoose.model('User', userSchema);
const Session = mongoose.model('Session', sessionSchema);
const Device = mongoose.model('Device', deviceSchema);
const Measure = mongoose.model('Measure', measureSchema);

module.exports = {
  User,
  Session,
  Device,
  Measure
};