const TelegramBot = require('node-telegram-bot-api');
const config = require('./config');
const Utils = require('./utils');
const Handlers = require('./handlers');

// Initialize
Utils.ensureFilesExist();
const keysData = Utils.loadKeys();
const bot = new TelegramBot(config.TOKEN, { polling: true });
const handlers = new Handlers(bot, keysData);

console.log(`💎 ${config.BOT_NAME} STARTED!`);

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
