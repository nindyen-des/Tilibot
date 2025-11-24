const TelegramBot = require('node-telegram-bot-api');
const express = require('express');
const config = require('./config');
const Utils = require('./utils');
const Handlers = require('./handlers');

// Initialize Express app for Render health checks
const app = express();
const PORT = process.env.PORT || 3000;

// Basic health check endpoint
app.get('/', (req, res) => {
  res.json({ 
    status: 'OK', 
    bot: config.BOT_NAME,
    timestamp: new Date().toISOString()
  });
});

// Health check for Render
app.get('/health', (req, res) => {
  res.status(200).send('OK');
});

// Start the web server
app.listen(PORT, () => {
  console.log(`🌐 Web server running on port ${PORT}`);
});

// Initialize bot
Utils.ensureFilesExist();
const keysData = Utils.loadKeys();
const bot = new TelegramBot(config.TOKEN, { polling: true });
const handlers = new Handlers(bot, keysData);

console.log(`💎 ${config.BOT_NAME} STARTED!`);
console.log(`🤖 Bot is running in polling mode`);
console.log(`🌐 Health check available at port ${PORT}`);

// Command handlers
bot.onText(/\/start/, (msg) => handlers.start(msg));
bot.onText(/\/key (.+)/, (msg) => handlers.redeemKey(msg));
bot.onText(/\/generate/, (msg) => {
  const chatId = msg.chat.id.toString();
  if (!keysData.user_keys[chatId]) {
    return bot.sendMessage(chatId, `${config.EMOJIS.error} Redeem a key first using /key <your_key>`);
  }
  bot.sendMessage(chatId, `${config.EMOJIS.generate} Select domain:`, {
    reply_markup: Utils.createDomainMenu()
  });
});

// Callback queries
bot.on('callback_query', (query) => handlers.handleCallback(query));

// Text messages (for conversations)
bot.on('message', (msg) => {
  if (msg.text && !msg.text.startsWith('/')) {
    handlers.handleTextMessage(msg);
  }
});

// Error handling
bot.on('error', (error) => console.error('Bot error:', error));
bot.on('polling_error', (error) => console.error('Polling error:', error));

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('Bot shutting down...');
  bot.stopPolling();
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('Bot shutting down...');
  bot.stopPolling();
  process.exit(0);
});
